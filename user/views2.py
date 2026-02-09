from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.shortcuts import redirect
from .serializers import *
from rest_framework.response import Response
import jwt
import time


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
        url = f'https://github.com/login/oauth/authorize?{query}'
        
        return redirect(url)
    
    
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


# helper function
def generate_apple_client_secret():
    return jwt.encode(
        {
            'iss': settings.APPLE_TEAM_ID,          # Issuer: Identifies who is signing the token
            'iat': int(time.time()),                # Issued At (current timestamp)
            'exp': int(time.time()) + 86400 * 180,  # Expiry time(180 days); Apple allows max 6 months
            'aud': 'https://appleid.apple.com',     # Audience (Always fixed)
            'sub': settings.APPLE_CLIENT_ID         # Subject: Tells Apple which app this token is for
        },
        settings.APPLE_PRIVATE_KEY,                 # .p8 private key (Must be kept secret)
        algorithm='ES256',                          # Algo: Elliptic Curve signing
        headers={'kid': settings.APPLE_KEY_ID}
    )
    

class AppleLoginRedirectView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        params = {
            'response_type': 'code id_token',   
            'response_code': 'form_post',       # Apple sends response as POST form
            'client_id': settings.APPLE_CLIENT_ID,
            'redirect_uri': settings.APPLE_REDIRECT_URI,
            'scope': 'name email'
        }
        
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        url = f'https://appleid.apple.com/auth/authorize?{query}'
        
        return redirect(url)
    
    
class AppleOAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        id_token = request.data.get('id_token')
        user = request.data.get('user')
        
        if not id_token:
            return redirect(f'{settings.FRONTEND_LOGIN_ERROR_URL}?error=Apple login failed')
        
        try:
            serializer = AppleOAuthCallbackView(data = {'id_token': id_token, 'user': user})
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}'
                f'?error=str{e.detail[0]}'
            )
        
        return Response(serializer.validated_data)

        # Uncomment below to redirect to frontend with tokens in query params
        # return redirect(
        #     f"{settings.FRONTEND_LOGIN_SUCCESS_URL}"
        #     f"?access={serializer.validated_data['tokens']['access']}"
        #     f"&refresh={serializer.validated_data['tokens']['refresh']}"
        #     f"&is_new={serializer.validated_data['is_new_user']}"
        # )



class FacebookLoginRedirectView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        params = {
            'client_id': settings.FACEBOOK_CLIENT_ID,
            'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
            'scope': 'email,public_profile',
            'response_type': 'code'
        }
        
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        url = f'{settings.FACEBOOK_OAUTH_AUTHORIZE_URL}?{query}'
        
        return redirect()
        

class FacebookOAuthCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        code = request.GET.get('code')
        
        if not code:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}?error=Facebook login failed'
            )
        
        token_params = {
            'client_id': settings.FACEBOOK_CLIENT_ID,
            'client_secret': settings.FACEBOOK_CLIENT_SECRET,
            'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
            'code': code
        }
        
        token_response = req.get(
            settings.FACEBOOK_OAUTH_TOKEN_URL,
            params=token_params,
            timeout=5
        )
        
        if token_response.status_code != 200:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}error=Failed to get Facebook access token'
            )
        
        token_data = token_response.json()
            
        access_token = token_data.get('access_token')
        
        if not access_token:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}?error=Invalid Facebook access token'
            )
            
        try:
            serializer = FacebookOAuthSerializer(data={'access_token':access_token})
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return redirect(
                f'{settings.FRONTEND_LOGIN_ERROR_URL}?error={str(e.detail[0])}'     
            )
            
        return Response(serializer.validated_data)  # comment this out when frontend is ready
    
        # Uncomment below to redirect to frontend with tokens in query params
        # return redirect(
        #     f'{settings.FRONTEND_LOGIN_SUCCESS_URL}'
        #     f'?access={serializer.validated_data['tokens']['access']}'
        #     f'refresh={serializer.validated_data['token']['refresh']}'
        #     f'is_new={serializer.validated_data['is_new_user']}'
        # )