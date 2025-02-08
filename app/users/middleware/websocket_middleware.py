from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady

@database_sync_to_async
def get_user(token):
	from django.contrib.auth import get_user_model
	from django.contrib.auth.models import AnonymousUser
	from rest_framework_simplejwt.tokens import AccessToken
	User = get_user_model()
	try:
		access_token = AccessToken(token)
		user_id = access_token['user_id']
		user = User.objects.get(id=user_id)
		return user
	except Exception as e:
		return AnonymousUser()

@database_sync_to_async
def refresh_access_token(refresh_token):
	from rest_framework_simplejwt.tokens import RefreshToken
	try:
		refresh = RefreshToken(refresh_token)
		new_access_token = str(refresh.access_token)
		new_refresh_token = str(refresh)
		return new_access_token, new_refresh_token
	except Exception as e:
		return None, None

class JWTAuthMiddlewareWS(BaseMiddleware):
	async def __call__(self, scope, receive, send):
		try:
			await database_sync_to_async(apps.check_apps_ready)()
		except AppRegistryNotReady:
			await database_sync_to_async(apps.check_apps_ready)()
		
		from django.contrib.auth.models import AnonymousUser
		cookies = scope['headers']
		access_token = None
		refresh_token = None

		for header in cookies:
			if header[0].decode('utf-8') == 'cookie':
				cookie_string = header[1].decode('utf-8')
				cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookie_string.split('; ')}
				access_token = cookies.get('access', None)
				refresh_token = cookies.get('refresh', None)
				break

		if access_token:
			user = await get_user(access_token) # Returns AnonymousUser if not valid
			if isinstance(user, AnonymousUser) and refresh_token:
				new_access_token, new_refresh_token = await refresh_access_token(refresh_token)
				if new_access_token and new_refresh_token:
					user = await get_user(new_access_token)
					# Update the access token in the cookies
					scope['headers'].append((b'set-cookie', f'access={new_access_token}; Path=/; HttpOnly'.encode()))
					scope['headers'].append((b'set-cookie', f'refresh={new_refresh_token}; Path=/; HttpOnly'.encode()))
		else:
			user = AnonymousUser()

		scope['user'] = user
		return await super().__call__(scope, receive, send)