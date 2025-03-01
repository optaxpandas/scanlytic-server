from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.hashers import make_password
from .models import Table, QR, User, UserAuth
from .serializers import TableSerializer, QRSerializer, UserSerializer
from django.conf import settings




# Create your views here.
class SampleResponse(APIView):
    def get(self, request):
        print('Request: \n', request.method)
        return HttpResponse("This is a simple response")
    
    def post(self, request):
        print('Request: ', request)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignIn(APIView):
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)  # Use request.data instead of request.POST
            if serializer.is_valid():
                email = serializer.validated_data['email']
                if User.objects.filter(email=email).exists():
                    response = createResponse(settings.MESSAGES['EMAIL_ALREADY_EXIST'])
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
            response = createResponse(settings.MESSAGES['BAD_REQUEST'])
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class Me(APIView):
    def get(self, request):
        try:
            response = createResponse(settings.MESSAGES['FOUND_USER'], request.user)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            print('ERROR IN ME: ', error)
            return Response()

def createResponse(message, data):
    response = { 'message': message }
    if(data):
        response['data'] = data
    
    return response
        

def table(request):
    return None

def qr(request):
    return None

def qrReport(request):
    return None

def refresh(request):
    return None

class TableView(APIView):
    # permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request):
        tables = Table.objects.all()
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QRView(APIView):
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

class JWT():
    def verifyToken(request):
        try:
            auth_header = request.headers.get("Authorization")
            print('auth header: ',auth_header)
            if not auth_header:
                raise AuthenticationFailed('Invalid Token')  # No token provided
            
            try:
                token_type, access_token = auth_header.split()
                if token_type.lower() != "bearer":
                    raise AuthenticationFailed("Invalid token type")
            except ValueError:
                raise AuthenticationFailed("Invalid Authorization header format")
            try:
                decoded_token = AccessToken(access_token)  # Decode JWT
                user_id = decoded_token["user_id"]
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed("User not found")
            except Exception as e:
                raise AuthenticationFailed("Invalid or expired token")
            
            request.user = { 
                'user_id': user.user_id,
                'user_name': user.user_name,
                'email': user.email,
                'created_on': user.created_on,
                'updated_on': user.updated_on 
            }
        except Exception as e:
            print('Error in verifyToken: ', e)
            raise AuthenticationFailed('Invalid or Expired Token')