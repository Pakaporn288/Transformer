from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def pertrain_view(request):
    return render(request, "home.html")

def train(request):
    return render(request, "train.html")

def perdict(request):
    return render(request, "predict.html")

def home(request):
    return render(request, 'pretrain/home.html')

def train_form(request):
    return render(request, 'pretrain/train.html')

def training_progress(request):
    # ตัวอย่างข้อมูล progress
    return JsonResponse({'progress': 0})

