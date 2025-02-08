# users/urls.py


from django.urls import path, include
from rest_framework import routers
from .views import \
	UserViewSet, \
	FriendshipViewSet, \
	RegistrationView, \
	UserLoginView, \
	UserLogoutView, \
	OTPVerificationView, \
	redirect_to_42, \
	Callback42View


# Un routeur est utilisé en conjonction avec les ViewSets pour générer automatiquement les URL des endpoints de l'API.
# Il mappe les actions des ViewSets aux routes HTTP correspondantes.

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'friendships', FriendshipViewSet, basename='friendship')




urlpatterns = [
	path('otp_verif/', OTPVerificationView.as_view(), name='otp-verif'),
	path('register/', RegistrationView.as_view(), name='register'),
	path('login/', UserLoginView.as_view(), name='login-user'),
	path('logout/', UserLogoutView.as_view(), name='logout-user'),
    path('', include(router.urls)),
	path('oauth_login/', redirect_to_42, name='oauth-login'),
    path('oauth/callback/', Callback42View.as_view(), name='oauth-callback'),
]
