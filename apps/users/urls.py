from django.urls import path
from .views import RegisterView, LoginView, VerifyEmail, RequestPasswordResetEmail, ResetPasswordConfirm

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('email-verify/', VerifyEmail.as_view(), name='email-verify'),
    path('password-reset/', RequestPasswordResetEmail.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', ResetPasswordConfirm.as_view(), name='password-reset-confirm'),
]
