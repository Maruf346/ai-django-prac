from rest_framework.serializers import ModelSerializer
from .models import User, AuthProvider
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate

# OAuth2 imports
from google.oauth2 import id_token
from google.auth.transport import requests
import requests as req
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.base import ContentFile


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
        read_only_fields = ['id', 'email']
        
        
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
        fields = [
            'street', 'city', 'zip_code', 'country'
        ]
        read_only_fields = fields


class UserStatsSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'total_spent'
        ]        
        

class GoogleOAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)
    
    def validate(self, attrs):
        token = attrs.get('id_token')
        
        try:
            google_user = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except Exception:
            raise serializers.ValidationError("Invalid or expired Google token")
        
        # Check if email is verified
        # if not google_user.get('email_verified'):
        #     raise serializers.ValidationError('Google email not verified')
        
        # Extarct data from google response
        email = google_user.get('email')
        if not email:
            raise serializers.ValidationError(
                "Google account has no email. Please use another login method."
            )
            
        first_name = google_user.get('given_name', '')
        last_name = google_user.get('family_name', '')
        picture = google_user.get('picture', '')
        provider_id = google_user.get('sub'),
        
        user, created = User.objects.get_or_create(
            email = email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'provider': AuthProvider.GOOGLE,
                'provider_id': provider_id
            },
        )
                
        if created:
            user.set_unusable_password()
            if picture:
                try:
                    pic = req.get(picture, timeout=5)
                    pic.raise_for_status()
                
                    if pic.status_code == 200:
                        file_name = f'{user.id}_google.jpg'
                        user.profile_picture.save(
                            file_name,
                            ContentFile(pic.content),
                            save=False
                        )
                except Exception:
                    pass
            user.save()
            
        if not created:
            if user.provider == AuthProvider.SELF:
                raise serializers.ValidationError('Account already exists. Please login with email and password')
            elif user.provider != AuthProvider.GOOGLE:
                raise serializers.ValidationError(f'Account already exists. Please login with {user.provider}.')
        
        refresh = RefreshToken.for_user(user)
        
        return {
            'user': UserProfileSerializer(user).data,
            'is_new_user': created,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }


class GitHubOAuthSerializer(serializers.Serializer):
    code = serializers.CharField(requried=True)
    
    def validate(self, attrs):
        code = attrs.get('code')
                
        token_response = req.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code
            },
            timeout=5
        )
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise serializers.ValidationError('Invalid GitHub authorization code')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        user_response = req.get('https://api.github.com/user', headers=headers)
        github_user = user_response.json()
        
        # Extract data
        provider_id = str(github_user.get('id'))
        full_name = github_user.get('name') or ''
        avatar = github_user.get('avatar_url')
        
        # Name handling
        first_name, last_name = '', ''
        if full_name:
            parts = full_name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
            
        # Request for Email
        email_response = req.get('https://api.github.com/user/emails', headers=headers)
        emails = email_response.json()
        
        primary_email = next(
            (e['email'] for e in emails if e.get('primary') and e.get('verified')), None
        )
        if not primary_email:
               raise serializers.ValidationError(
                   'GitHub account has no verified email. Please add one or use another login method.'
               )     
        
        user, created = User.objects.get_or_create(
            email = primary_email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'provider': AuthProvider.GITHUB,
                'provider_id': provider_id
            },
        )
        
        if created:
            user.set_unusable_password()
            
            if avatar:
                try:
                    img = req.get(avatar, timeout=5)
                    img.raise_for_status()
                    
                    user.profile_picture.save(
                        f'{user.id}_github.jpg',
                        ContentFile(img.content),
                        save=False
                    )
                except Exception:
                    pass
            user.save()
            
        if not created:
            if user.provider == AuthProvider.SELF:
                raise serializers.ValidationError('Account already exists. Please login with email and password')
            elif user.provider != AuthProvider.GITHUB:
                raise serializers.ValidationError(f'Account already exists. Please login with {user.provider}.')
        
        refresh = RefreshToken.for_user(user)
        
        return {
            'user': UserProfileSerializer(user).data,
            'is_new_user': created,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }
        

