from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.tokens import  default_token_generator
from django.utils.encoding import force_bytes, smart_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import RegisterSerializer, LoginSerializer, ResetPasswordEmailRequestSerializer, SetNewPasswordSerializer, EmailVerificationSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(smart_bytes(user.pk))
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = f'http://{current_site}{relative_link}?token={token}&uid={uid}'
        email_body = f'Hi {user.username}, Use the link below to verify your email \n{absurl}'
        send_mail(
            'Verify your email',
            email_body,
            'noreply@yourdomain.com',
            [user.email],
        )
        return Response({'email': user.email}, status=status.HTTP_201_CREATED)

class VerifyEmail(APIView):
    serializer_class = EmailVerificationSerializer

    def get(self, request):
        token = request.GET.get('token')
        uidb64 = request.GET.get('uid')
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.get(email=serializer.data['email'])
        if not user.check_password(serializer.data['password']):
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'detail': 'Account not activated'}, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class RequestPasswordResetEmail(APIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': 'No user with this email address.'}, status=status.HTTP_400_BAD_REQUEST)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            current_site = get_current_site(request)
            reset_url = reverse('password-reset-confirm', kwargs={'uidb64': uid, 'token': token})
            reset_url = f"http://{current_site.domain}{reset_url}"
            email_subject = 'Reset Your Password'
            email_body = f'Hello,\n\nUse the link below to reset your password:\n\n{reset_url}'
            send_mail(email_subject, email_body, 'noreply@example.com', [email])
            return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordConfirm(APIView):
    serializer_class = SetNewPasswordSerializer

    def post(self, request, uidb64, token):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = CustomUser.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
                return Response({'error': 'Invalid token or user does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({'success': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid token or user does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)