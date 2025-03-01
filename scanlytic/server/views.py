from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from .models import Table, QR, User, UserAuth
from .serializers import QRSerializer, UserSerializer, LoginSerializer
from django.conf import settings
from scanlytic.utils import JWT, Utils


class SignIn(APIView):
    def post(self, request):
        utils = Utils()
        try:
            serializer = UserSerializer(data=request.data)  # Use request.data instead of request.POST
            if serializer.is_valid():
                email = serializer.validated_data['email']
                if User.objects.filter(email=email).exists():
                    response = utils.createResponse(settings.MESSAGES['EMAIL_ALREADY_EXIST'])
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                
                user_data = serializer.validated_data
                user_data['password'] = make_password(user_data['password'])  # Hash the password
                user = User.objects.create(**user_data)
                
                refresh_token = RefreshToken.for_user(user)
                refresh_token["user_id"] = str(user.user_id)
                access_token = str(refresh_token.access_token)
                
                # Store tokens in UserAuth table
                UserAuth.objects.create(
                    user=user,
                    access_token=access_token,
                    refresh_token=str(refresh_token)
                )

                return Response({
                    'user_id': user.user_id,
                    'access_token': access_token,
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as error:
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)
        
class LogIn(APIView):
    def get(self, request):
        utils = Utils()
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']
                
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    response = utils.createResponse(settings.MESSAGES['INVALID_CREDENTIALS'])
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                
                if not user.check_password(password):
                    response = utils.createResponse(settings.MESSAGES['INVALID_CREDENTIALS'])
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                
                refresh_token = RefreshToken.for_user(user)
                refresh_token["user_id"] = str(user.user_id)
                access_token = str(refresh_token.access_token)
                
                # Store tokens in UserAuth table
                UserAuth.objects.create(
                    user=user,
                    access_token=access_token,
                    refresh_token=str(refresh_token)
                )

                return Response({
                    'user_id': user.user_id,
                    'access_token': access_token,
                }, status=status.HTTP_201_CREATED)
            
            return Response(utils.createResponse(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as error:
            print('ERROR IN LOGIN: ',error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message, str(error))
            return Response(response, status=status_code)

class Me(APIView):
    def get(self, request):
        utils = Utils()
        try:
            jwt = JWT()
            jwt.verifyToken(request)            
            response = utils.createResponse(settings.MESSAGES['FOUND_USER'], request.user)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            print('ERROR IN ME: ', error)
            status_code = status.HTTP_403_FORBIDDEN if isinstance(error, AuthenticationFailed) else status.HTTP_500_INTERNAL_SERVER_ERROR
            message = settings.MESSAGES['FORBIDDEN'] if isinstance(error, AuthenticationFailed) else settings.MESSAGES['INTERNAL_SERVER_ERROR']

            response = utils.createResponse(message)
            return Response(response, status=status_code)


def refresh(request):
    return None

class QR(APIView):
    def get(self, request):
        qrs = QR.objects.all()
        serializer = QRSerializer(qrs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = QRSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)