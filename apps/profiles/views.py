from django.contrib.auth.tokens import default_token_generator
from django.utils.http import  urlsafe_base64_encode
from django.utils.encoding import  force_bytes
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ChangePasswordSerializer, ChangeEmailSerializer,ProfileSerializer


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeEmailSerializer

    def post(self, request):
        serializer = ChangeEmailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            new_email = serializer.validated_data['email']
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = request.build_absolute_uri(reverse('email-verify')) + f'?uid={uidb64}&token={token}'
            
            send_mail(
                'Activate your new email address',
                f'Please use the following link to activate your new email address: {activation_link}',
                'from@example.com',
                [new_email],
                fail_silently=False,
            )
            user.new_email = new_email
            user.save()
            return Response({"detail": "Activation email sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)