from django.contrib import admin
from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("list", UserListViewSet, basename='user_list')

urlpatterns = [
    path("", include(router.urls)),
    
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('me/', MyProfileView.as_view(), name='me'),
    path('profile/<uuid:id>/', PublicProfileView.as_view(), name='profile')
]
