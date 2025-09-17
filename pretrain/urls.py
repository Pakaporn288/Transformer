from django import views
from django.urls import path
from . import views

urlpatterns =[
    path("", views.home , name="home"),
    path('training-progress/', views.training_progress, name='training_progress'),
    path('train-form/', views.train_form, name='train_form'),
    


]