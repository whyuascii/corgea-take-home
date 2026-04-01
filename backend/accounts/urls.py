from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register),
    path("login/", views.login),
    path("logout/", views.logout),
    path("me/", views.me),
    path("change-password/", views.change_password),
    path("forgot-password/", views.forgot_password),
    path("reset-password/", views.reset_password),
]
