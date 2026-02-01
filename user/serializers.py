from rest_framework.serializers import ModelSerializer
from .models import User
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate


User = get_user_model()


class UserListSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 
            'email', 'phone_number', 
            'profile_picture', 'gender', 
            'city', 'zip_code', 'country',
            'total_spent',
            'created_at', 'updated_at'
            ]
        read_only_fields = ['id','total_spent', 'created_at', 'updated_at']
        
        
class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 
            'email', 'phone_number', 
            'profile_picture', 'gender',
            'bio', 'street', 'city', 
            'zip_code', 'country',
        ]
        read_only_fields = ['id']
        
        
class UserSignupSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirm_password',
        ]
        
    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        try:
            validate_email(data['email'])
        except ValidationError:
            raise serializers.ValidationError({"email": "Enter a valid email address."})
        
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        confirm_password = validated_data.pop('confirm_password', None)
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user
    
class UserLoginSerializer(ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError({
                "detail": "Email and password are required."
            })

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError({
                "detail": "Invalid email or password."
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "User account is disabled."
            })

        data['user'] = user
        return data


class UserAddressSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = {
            'street', 'city', 'zip_code', 'country'
        }
        read_only_fields = fields
        