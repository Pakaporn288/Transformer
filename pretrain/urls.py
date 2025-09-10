from django.urls import path

from .views import home, train, predict

urlpatterns = [
    # เพิ่มเส้นทาง URL สำหรับแอป pretrain
    path("", home, name="home"),
    path("train/", train, name="train"),
    path("predict/", predict, name="predict"),
]