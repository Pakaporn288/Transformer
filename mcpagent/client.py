import asyncio
import os
import sys
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # ตั้งค่า Gemini API Key และสร้างโมเดล
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the .env file")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        
        response = await self.session.list_tools()
        
        # --- ส่วนที่แก้ไขใหม่ทั้งหมด: สร้าง Schema ที่สะอาดขึ้นมาเอง ---
        available_tools = []
        for tool in response.tools:
            # 1. สร้างโครง Schema ใหม่ที่ว่างเปล่าและสะอาด
            clean_schema = {
                "type": "object",
                "properties": {},
                "required": tool.inputSchema.get("required", [])
            }
            
            # 2. คัดลอกเฉพาะข้อมูลที่จำเป็นจาก Schema เดิม
            if tool.inputSchema and 'properties' in tool.inputSchema:
                for prop_name, prop_schema in tool.inputSchema['properties'].items():
                    clean_schema['properties'][prop_name] = {
                        'type': prop_schema.get('type'),
                        'description': prop_schema.get('description', '')
                    }

            # 3. ประกอบร่างเป็น Tool ที่สมบูรณ์โดยใช้ Schema ที่สะอาดแล้ว
            available_tools.append({
                "function_declarations": [{
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": clean_schema  # ใช้ Schema ใหม่ที่เราสร้างขึ้น
                }]
            })
        # -----------------------------------------------------------

        chat = self.model.start_chat()
        
        response = chat.send_message(
            query,
            tools=available_tools
        )
        
        while response.candidates[0].function_calls:
            function_calls = response.candidates[0].function_calls
            
            tool_results = []
            
            print(f"[Gemini wants to call tools: {[fc.name for fc in function_calls]}]")

            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args)

                print(f"[Calling tool {tool_name} with args {tool_args}]")
                result = await self.session.call_tool(tool_name, tool_args)

                tool_results.append({
                    "function_response": {
                        "name": tool_name,
                        "response": {
                            "content": result.content
                        }
                    }
                })

            response = chat.send_message(
                tool_results,
                tools=available_tools
            )

        return response.text

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started with Gemini!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())