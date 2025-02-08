from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

def generate_tokens(user):
    """
    Generate access and refresh tokens for a user and return them as strings.
    """
    token = RefreshToken.for_user(user)
    access_token = str(token.access_token)
    refresh_token = str(token)
    
    return access_token, refresh_token

def set_tokens_in_cookies(response, access_token, refresh_token):
    """
    Set the access and refresh tokens in the response as HTTP-only cookies.
    """
    secure_settings=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE')
    samesite_settings=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE')
    httponly_settings=settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY')
    response.set_cookie('access', access_token, httponly=httponly_settings,\
                    secure=secure_settings, samesite=samesite_settings, path="/")
    response.set_cookie('refresh', refresh_token, httponly=httponly_settings,\
                    secure=secure_settings, samesite=samesite_settings, path="/")