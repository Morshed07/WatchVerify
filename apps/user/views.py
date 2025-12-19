from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import (
    RegisterSerializer,
    VerifyOtpSerializer,
    LoginRequestOtpSerializer,
    LoginVerifyOtpSerializer,
    ResendOtpSerializer,
    GoogleAuthSerializer,
    UserSerializer,
)

# Create your views here.


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User registered successfully. Check your email for OTP."}, status=201)
    

class VerifyRegisterOtpView(APIView):
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "User verified successfully"}, status=200
        )


class LoginRequestOtpView(APIView):
    def post(self, request):
        serializer = LoginRequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP sent successfully"}, status=200)


class LoginVerifyOtpView(APIView):
    def post(self, request):
        serializer = LoginVerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)


class ResendOtpView(APIView):
    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "OTP resent"}, status=200)
    

class GoogleAuthView(APIView):
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        return Response({
            "user": UserSerializer(data["user"]).data,
            "tokens": data["tokens"]
        })


