from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from server.models import User, UserAuth
import base64
import os
from django.conf import settings
from django.core.files.storage import default_storage


class JWT():
    def generateToken(user):
        refresh_token = RefreshToken.for_user(user)
        refresh_token["user_id"] = str(user.user_id)
        access_token = str(refresh_token.access_token)

        return { refresh_token, access_token }
    
    def verifyToken(request):
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise AuthenticationFailed('Invalid Token')  # No token provided
            
            try:
                token_type, access_token = auth_header.split()
                if token_type.lower() != "bearer":
                    raise AuthenticationFailed("Invalid token type")
            except ValueError:
                raise AuthenticationFailed("Invalid Authorization header format")
            try:
                user_auth = UserAuth.objects.get(access_token = access_token)
                decoded_token = AccessToken(access_token)
                user_id = decoded_token["user_id"]
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed("User not found")
            except UserAuth.DoesNotExist:
                raise AuthenticationFailed('Token record does not exist')
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
            print('Error in verifyToken: ',e)
            raise AuthenticationFailed(str(e))

class Utils():
    def createResponse(self, message, error = None, data = None):
        response = { 'message': message }
        if(data):
            response['data'] = data
        if(error):
            response['error'] = error
        
        return response
    
    def encodeFileToBase64(self, file_path):
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        print('full_path', full_path)

        if not default_storage.exists(full_path):
            return None 

        with open(full_path, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode("utf-8")
        
        return encoded_string