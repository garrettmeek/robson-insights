from django.contrib import admin
from django.urls import path, include
from .views import LoginView, LogoutView, RegisterView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Base Views
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/<str:token>/', RegisterView.as_view(), name='register'),
    
    # App Views
    path("users/", include("users.urls", namespace="users")),
    path("survey/", include("survey.urls", namespace="survey")),
]
