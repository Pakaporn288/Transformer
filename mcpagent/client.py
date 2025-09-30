import asyncio
import os
import sys
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API Key not found in .env file")
        genai.configure(api_key=api_key)

        # ใช้โมเดลตัวเดียวที่เสถียรที่สุด
        self.model = genai.GenerativeModel('models/gemini-pro-latest')

    async def connect_to_server(self, server_script_path: str):
        command = "python"
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
        print("\nConnected to server with tools:", [tool.name for tool in response.tools])

    async def process_query(self, query: str) -> str:
        response = await self.session.list_tools()
        
        gemini_tools = []
        for tool in response.tools:
            clean_schema = {
                "type": "object", "properties": {}, "required": tool.inputSchema.get("required", [])
            }
            if tool.inputSchema and 'properties' in tool.inputSchema:
                for prop_name, prop_schema in tool.inputSchema['properties'].items():
                    clean_schema['properties'][prop_name] = {
                        'type': prop_schema.get('type'), 'description': prop_schema.get('description', '')
                    }
            gemini_tools.append({
                "function_declarations": [{"name": tool.name, "description": tool.description, "parameters": clean_schema}]
            })

        # ขั้นตอนที่ 1: ให้ Gemini วางแผนเลือก Tool
        planning_response = self.model.generate_content(query, tools=gemini_tools)
        
        # ตรวจสอบว่า AI ต้องการใช้ Tool หรือไม่
        if not planning_response.candidates[0].content.parts or not planning_response.candidates[0].content.parts[0].function_call:
             print("[No tool needed. Answering directly...]")
             return planning_response.text

        # ขั้นตอนที่ 2: ดึงข้อมูลและเรียกใช้ Tool
        function_call = planning_response.candidates[0].content.parts[0].function_call
        tool_name = function_call.name
        tool_args = {key: value for key, value in function_call.args.items()}

        print(f"[Gemini wants to call tool: {tool_name} with args: {tool_args}]")
        result = await self.session.call_tool(tool_name, tool_args)
        
        # --- ส่วนที่แก้ไข (ใช้เทคนิคเดียวกับเพื่อนของคุณ) ---
        # 3. สร้าง Prompt ใหม่ที่มีทั้งคำถามและผลลัพธ์
        summary_prompt = (
            f"คำถามเดิมคือ: '{query}'\n\n"
            f"ฉันได้ใช้เครื่องมือ '{tool_name}' และได้ผลลัพธ์กลับมาเป็นข้อมูลนี้:\n"
            f"{result.content}\n\n"
            f"จากข้อมูลนี้ ช่วยสรุปเป็นคำตอบที่เข้าใจง่ายสำหรับคำถามเดิมให้หน่อย"
        )
        
        # 4. ส่ง Prompt ใหม่ไปให้ Gemini สรุป
        print("[Summarizing result...]")
        summary_response = self.model.generate_content(summary_prompt)
        # -----------------------------------------------
        
        return summary_response.text

    async def chat_loop(self):
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