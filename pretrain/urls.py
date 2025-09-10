from django import views
from django.urls import path

from .views import home  # นำเข้า view ที่ต้องการ

urlpatterns =[
    path("", home , name="home"),
    path('pertrain/', views.pertrain_view, name='pertrain'),

]