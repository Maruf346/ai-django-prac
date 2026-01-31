from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        # login(request, user)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Logged in successfully...!',
            'user': UserProfileSerializer(user, context = {"request": request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }    
        },
        status = status.HTTP_200_OK)
        

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None
    
    def post(self, request):
        # logout(request)
        
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
            logout(request)
        
            return Response(
                {'message': 'Successfully logged out...!'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )