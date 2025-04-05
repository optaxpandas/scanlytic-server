from rest_framework import serializers
from .models import Table, QR, User
from django.conf import settings
import os
from PIL import Image
import requests

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['table_id', 'image', 'file_type', 'content', 'created_on', 'updated_on']

class QRSerializer(serializers.ModelSerializer):
    class Meta:
        model = QR
        fields = ['qr_id', 'user_id', 'url', 'image', 'first_submission_date', 'last_analysis_date', 'reputation', 'total_malicious_votes', 'total_harmless_votes', 'malicious', 'suspicious', 'harmless', 'security_score', 'risk_level', 'created_on', 'updated_on']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'user_name', 'email', 'password', 'created_on', 'updated_on']
        extra_kwargs = {
            'user_name': {'required': False}  # Make user_name optional
        }

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        return data
    
class UploadTableSerializer(serializers.Serializer):
    file_name = serializers.CharField(required=True)
    image_url = serializers.URLField(required=True)
    format = serializers.ChoiceField(choices=["csv", "xlsx"], required=True)

    def validate(self, data):
        try:
            if(data.get('image_url')):
                data['image_url'] = data.get('image_url')
                data['file_name'] = data.get('file_name')
                
            elif(data.get('file')):
                file = data.get('file')
                name, extension = os.path.splitext(file.name)
                print(extension)

                if(extension not in settings.FILE_EXTENSIONS):
                    raise serializers.ValidationError(f'Invalid file format must be {', '.join(settings.FILE_EXTENSIONS)}')

                if not file:
                    raise serializers.ValidationError('File not found')
                
                image_path = os.path.join(settings.MEDIA_ROOT, file.name)
                with open(image_path, "wb+") as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                image = Image.open(image_path)
                width, height = image.size
                image.close()

                if(width < 50 or width > 10000 or height < 50 or height > 10000):
                    os.remove(image_path)
                    raise serializers.ValidationError('File too small or too large')
                
                data['image_path'] = image_path
                data['name'] = name


            else:
                raise serializers.ValidationError('Neither file nor the file URL /name found')

            return data
        except Exception as error:
            raise error
        
class UploadQrSerializer(serializers.Serializer):
    image_url = serializers.URLField(required=True)

    def saveImage(self, imageUrl):
        try:
            response = requests.get(imageUrl, stream=True)
            response.raise_for_status()  # Raise an error if request fails

            # Extract file name from URL
            filename = os.path.basename(imageUrl.split("?")[0])  # Remove query params if any
            savePath = os.path.join(settings.MEDIA_ROOT, filename)

            # Save image to media folder
            with open(savePath, "wb") as image:
                for chunk in response.iter_content(1024):
                    image.write(chunk)

            return savePath  # Return the local path of the saved image

        except requests.RequestException as e:
            raise serializers.ValidationError(f"Error downloading image: {str(e)}")
        
    def validate(self, data):
        try:
            if not (data['image_url'].startswith(("http://", "https://"))):
                raise serializers.ValidationError("Invalid URL format. Must start with http:// or https://.")
            
            path = self.saveImage(imageUrl=data['image_url'])
            data['path'] = path
            return data
        except Exception as error:
            raise error