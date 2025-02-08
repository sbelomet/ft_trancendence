from django.urls import path
from . import views

urlpatterns = [
    path("otp/", views.otp, name="otp"),
    path("hub/", views.hub, name="hub"),
	path("about/", views.about, name="about"),
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
	path("logout/", views.login, name="logout"),
    path("game/", views.startGame, name="game"),
    path("register/", views.register, name="register"),
    path("redirect/", views.redirect, name="redirect"),
	path("otp/", views.otp, name="otp"),
    path("pre_login/", views.pre_login, name="pre_login"),
	path("oauth_login/", views.oauth_login, name="oauth_login"),
    path("chat_modal/", views.chat_modal, name="chat_modal"),
	path("profile/<int:user_id>/", views.profile, name="profile"),
	path("settings/", views.settings, name="settings"),
]