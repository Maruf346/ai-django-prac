from django.contrib import admin
from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("list", UserListViewSet, basename='user_list')
router.register('stats', UserStatsViewSet, basename='stats')

urlpatterns = [
    path("", include(router.urls)),
    
    # OAuth2 logins
    path('auth/google/', GoogleOAuthView.as_view(), name='google-login'),
    path('auth/github/', GitHubOAuthView.as_view(), name='github-login'),
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
