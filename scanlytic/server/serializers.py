from rest_framework import serializers
from .models import Table, QR, User

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['table_id', 'user', 'image', 'file_type', 'content', 'created_on', 'updated_on']

class QRSerializer(serializers.ModelSerializer):
    class Meta:
        model = QR
        fields = ['qr_id', 'user', 'image', 'extracted_data', 'created_on', 'updated_on']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'user_name', 'email', 'password', 'created_on', 'updated_on']
        extra_kwargs = {
            'user_name': {'required': False}  # Make user_name optional
        }
