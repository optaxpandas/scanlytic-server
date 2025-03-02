from rest_framework import serializers
from .models import Table, QR, User

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['table_id', 'image', 'file_type', 'content', 'created_on', 'updated_on']

class QRSerializer(serializers.ModelSerializer):
    class Meta:
        model = QR
        fields = ['qr_id', 'user', 'url', 'image', 'first_submission_date', 'last_analysis_date', 'reputation', 'total_malicious_votes', 'total_harmless_votes', 'malicious', 'suspicious', 'harmless', 'security_score', 'risk_level', 'created_on', 'updated_on']

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
    file = serializers.ImageField()

    def validate(self, data):
        file = data.get('file')

        if not file:
            raise serializers.ValidationError('File not found')

        return data