from rest_framework.views import APIView, status
from rest_framework.response import Response
from .serializers import (
    RegisterSerializer,
    TermsAndConditionsSerializer,
    VerifyOtpSerializer,
    ResendOtpSerializer,
    UserSerializer,
    FirebaseAuthSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordVerifyOtpSerializer,
    ResetPasswordSerializer,
    LoginSerializer
)
from rest_framework.permissions import(
    IsAuthenticated,
    AllowAny
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
from .firebase import verify_firebase_token


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            error_message = list(serializer.errors.values())[0][0]

            return Response({
                "success": False,
                "message": error_message
            }, status=status.HTTP_400_BAD_REQUEST)

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
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # serializer.save() 
        return Response({
            "success": True,
            "message": "User verified successfully",
        }, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        user.last_login = now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'Login successful',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'user': UserSerializer(
                user,
                context={'request': request}
            ).data
        }, status=status.HTTP_200_OK)


class ResendOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            {"message": "OTP resent"},
            status=status.HTTP_200_OK
        )
    

class FirebaseAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FirebaseAuthSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "success": True,
                "data": serializer.validated_data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "error": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FirebaseTokenDebugView(APIView):
    """Debug endpoint - verifies Firebase token properly"""
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token", "")
        
        if not id_token:
            return Response({
                "error": "No id_token provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Properly verify the Firebase token
            decoded = verify_firebase_token(id_token)
            
            return Response({
                "success": True,
                "message": "Token verified successfully",
                "token_data": {
                    "email": decoded.get("email"),
                    "name": decoded.get("name"),
                    "uid": decoded.get("uid"),
                    "aud": decoded.get("aud")
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save() 
        # -----------------------------

        return Response({
            "success": True,
            "message": "OTP sent"
        }, status=status.HTTP_200_OK)


class ForgotPasswordVerifyOtpView(APIView):
    def post(self, request):
        serializer = ForgotPasswordVerifyOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "OTP verified successfully",
            "data": serializer.validated_data
        }, status=status.HTTP_200_OK)
    

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

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


class LanguagePreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        language = request.data.get('language')
        if language not in dict(request.user.Language):
            return Response({
                "success": False,
                "error": "Invalid language preference"
            }, status=status.HTTP_400_BAD_REQUEST)

        request.user.language_preference = language
        request.user.save(update_fields=['language_preference'])

        return Response({
            "success": True,
            "message": "Language preference updated successfully",
            "data": {
                "language": request.user.language_preference
            }
        }, status=status.HTTP_200_OK)


# class TermsAndConditionsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = TermsAndConditionsSerializer(
#             request.user,
#             data=request.data,
#             partial=True
#         )

#         if serializer.is_valid():
#             serializer.save(update_fields=['terms_and_conditions_accepted'])
#             return Response({
#                 "success": True,
#                 "message": "Terms and Conditions acceptance status updated successfully",
#                 "data": serializer.data
#             }, status=status.HTTP_200_OK)

#         return Response({
#             "success": False,
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
