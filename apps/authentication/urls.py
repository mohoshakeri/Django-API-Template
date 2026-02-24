from django.urls import path

from .views import *

app_name = "authentication"

urlpatterns = [
    path("", Authentication.as_view(), name="main"),
    path("password/", Password.as_view(), name="password"),
]
