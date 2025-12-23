from rest_framework.views import APIView, status
from rest_framework.response import Response
from .serializers import (
    RegisterSerializer,
    VerifyOtpSerializer,
    LoginRequestOtpSerializer,
    LoginVerifyOtpSerializer,
    ResendOtpSerializer,
    UserSerializer,
    FirebaseAuthSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordVerifyOtpSerializer,
    ResetPasswordSerializer
)
from rest_framework.permissions import(
    IsAuthenticated,
    AllowAny
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "success": True,
            "message": "User registered successfully. Check your email for OTP.",
            "data": {
                "email": user.email
            }
        }, status=status.HTTP_201_CREATED)
    

class VerifyRegisterOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            "success": True,
            "message": "User verified successfully",
        }, status=status.HTTP_200_OK)


class LoginRequestOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginRequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "success": True,
            "message": "OTP sent successfully",
            "data": {
                "email": user.email
            }
        }, status=status.HTTP_200_OK)


class LoginVerifyOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginVerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({
            "success": True,
            "message": "Login successful",
            "data": serializer.validated_data
        }, status=status.HTTP_200_OK)


class ResendOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "OTP resent"},
            status=status.HTTP_200_OK
        )
    

class FirebaseAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FirebaseAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.save()

        except Exception as e:
            return Response({
                "success": False,
                "error": "Firebase authentication failed"
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "data": data
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({
            "success": True,
            "message": "OTP sent"
        }, status=status.HTTP_200_OK)


class ForgotPasswordVerifyOtpView(APIView):
    def post(self, request):
        serializer = ForgotPasswordVerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({
            "success": True,
            "message": "OTP verified successfully",
            "data": serializer.validated_data
        }, status=status.HTTP_200_OK)
    

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({
            "success": True,
            "message": "Password reset successfully"
        }, status=status.HTTP_200_OK)
    

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response({
            "success": True,
            "message": "User profile fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
