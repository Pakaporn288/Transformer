from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "pretrain/home.html")

def train(request):
    print('simulate training process...')
    return render(request, "pretrain/train.html")

def predict(request):
    print('simulate predicting process...')
    return render(request, "pretrain/predict.html")