from django.urls import path
from .views import ChangePasswordView, ChangeEmailView,ProfileView

urlpatterns = [
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),
    path('profile/', ProfileView.as_view(), name="Profile"),
]
