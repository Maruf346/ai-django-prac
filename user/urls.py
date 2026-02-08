from django.contrib import admin
from django.urls import path, include
from .views import *
from .views2 import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("list", UserListViewSet, basename='user_list')
router.register('stats', UserStatsViewSet, basename='stats')

urlpatterns = [
    path("", include(router.urls)),
    
    # OAuth2 logins
    path('auth/google/', GoogleOAuthView.as_view(), name='google-login'),
    path('auth/google2/login/', GoogleLoginRedirectView.as_view(), name='google-login2'),
    path('auth/google2/callback/', GoogleOAuthCallbackView.as_view(), name='google-login2-callback'),
    
    path("auth/apple/login/", AppleLoginRedirectView.as_view(), name='apple-login'),
    path("auth/apple/callback/", AppleOAuthCallbackView.as_view(), name='apple-login-callback'),
    
    path('auth/github/', GitHubOAuthView.as_view(), name='github-login'),
    path('auth/github2/login', GitHubOAuthLoginRedirectView.as_view(), name='github-login2'),
    path('auth/github2/callback', GitHubOAuthCallbackView.as_view(), name='github-login2-callback'),
    
    path('auth/facebook/', FacebookOAuthView.as_view(), name='facebook-login'),
    path('auth/linkedin/', LinkedInOAuthView.as_view(), name='linkedin-login'),
    
    # User endpoints
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('me/', MyProfileView.as_view(), name='me'),
    path('profile/<uuid:id>/', PublicProfileView.as_view(), name='profile'),
    path('addr/<uuid:id>/', PublicAddressView.as_view(), name='address')
]
