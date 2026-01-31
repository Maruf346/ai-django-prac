from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.contrib.auth import login, logout
from .serializers import *

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        # email = request.data.get['email']
        # password = request.data.get['password']
        
        # user = authenticate(email=email, password=password)
        
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        login(request, user)
        
        return Response({
            'message': 'Logged in successfully...!',
            'user': UserProfileSerializer(user, context = {"request": request}).data
        })
        


