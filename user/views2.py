from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.shortcuts import redirect
from .serializers import *
from rest_framework.response import Response


class GoogleLoginRedirectView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token'
                }
            },
            scopes=[
                'openid',
                'email',
                'profile',
            ],
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        
        request.session['google_oauth_state'] = state
        return redirect(authorization_url)
    
    
class GoogleOAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        state = request.session.get('google_oauth_state')
        
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token'
                }
            },
            scopes = [
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ],
            state=state,
            redirect_uri = settings.GOOGLE_REDIRECT_URI
        )
        
        # Extracts code from callback URL --> Sends it to Google’s token endpoint
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        
        # Reuse existing serializer logic
        try:
            serializer = GoogleOAuthSerializer(
                data={'id_token': flow.credentials.id_token}
            )
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}'
                f'?error={str(e.detail[0])}'
            )
        
        return Response(serializer.validated_data)  # comment this out when frontend is ready
    
        # Uncomment below to redirect to frontend with tokens in query params
        # return redirect(
        #     f'{settings.FRONTEND_LOGIN_SUCCESS_URL}'
        #     f'?access={serializer.validated_data['tokens']['access']}'
        #     f'refresh={serializer.validated_data['token']['refresh']}'
        #     f'is_new={serializer.validated_data['is_new_user']}'
        # )
        
        
class GitHubOAuthLoginRedirectView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        params = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'redirect_uri': settings.GITHUB_REDIRECT_URI,
            'scope': 'read: user user:email',
            'allow_signup': 'true'
        }
        
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        return redirect(f'https://github.com/login/oauth/authorize?{query}')
    
    
class GitHubOAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        code = request.GET.get('code')
        
        if not code:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}?error=Github login failed'
            )
        
        try:
            serializer = GitHubOAuthSerializer(data={'code':code})
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return redirect (
                f'{settings.FRONTEND_LOGIN_ERROR_URL}'
                f'?error={str(e.details[0])}'
            )
            
        return Response(serializer.validated_data)    # comment this out when frontend is ready
    
        # Uncomment below to redirect to frontend with tokens in query params
        # return redirect(
        #     f'{settings.FRONTEND_LOGIN_SUCCESS_URL}'
        #     f'?access={serializer.validated_data['tokens']['access']}'
        #     f'&refresh={serializer.validated_data['tokens']['refresh']}'
        #     f'&is_new={serializer.validated_data['is_new_user']}'
        # )
            