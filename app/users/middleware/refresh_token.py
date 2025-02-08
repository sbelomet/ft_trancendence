from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class RefreshTokenMiddleware(MiddlewareMixin):    
    def process_request(self, request):
        
        # Force authentification if header is present
        access_token = request.COOKIES.get('access')
        
        if access_token:
            jwt_authenticator = JWTAuthentication()
            # Try to authenticate using the access token, rest_frameworks expects it to be in header
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            try:
                # Authenticate user using the access token in the Authorization header
                user, validated_token = jwt_authenticator.authenticate(request)
                if user:
                    request.user = user
            except AuthenticationFailed:
                pass

        # If the user is already authenticated, skip further processing
        if request.user.is_authenticated:
            return

        # Attempt to use the refresh token to get a new access token
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            try:
                # Generate a new access token using the refresh token
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)

                # Set the Authorization header with the new access token
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'

                # Re-authenticate the user using the new access token
                jwt_authenticator = JWTAuthentication()
                user, validated_token = jwt_authenticator.authenticate(request)
                request.user = user  # Set the user on the request object
                request.new_access_token = validated_token

            except AuthenticationFailed:
                # If refresh token is invalid, let the request proceed unauthenticated
                pass

    def process_response(self, request, response):
        # If a new access token was generated, update cookies
        if hasattr(request, 'new_access_token'):
            secure_settings=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE')
            samesite_settings=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE')
            httponly_settings=settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY')
            response.set_cookie(
                'access', 
                str(request.new_access_token), 
                httponly=httponly_settings,
                secure=secure_settings, 
                samesite=samesite_settings
            )
        return response
