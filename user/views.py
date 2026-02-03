from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from django.contrib.auth import login, logout, get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.generics import GenericAPIView


User = get_user_model()


class UserListViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserListSerializer
    ordering_fields = ["created_at", "updated_at", "email", "first_name", "last_name", "total_spent"]
    filterset_fields = ["is_active", "gender"]
    ordering = ["-created_at"]
    lookup_field = 'id'
    
 
class UserSignupView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSignupSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                'message': 'Account created successfully...',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            },
            status=status.HTTP_201_CREATED
        )
       

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
        

@extend_schema(
    responses={205: OpenApiResponse(description="Logged out successfully")}
)
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
            
            
class MyProfileView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    
class PublicProfileView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    
class PublicAddressView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    

class UserStatsViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserStatsSerializer
    ordering = ["-total_spent"]
    lookup_field = 'id'
    
    
class GoogleOAuthView(GenericAPIView):
    serializer_class = GoogleOAuthSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
    
class GitHubOAuthView(GenericAPIView):
    serializer_class = GitHubOAuthSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)