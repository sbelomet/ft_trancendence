from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse


User = get_user_model()

def index(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/home_frag.html", None, request)
        response = {
            "name": "Home",
            "content": renderer,
        }
        return JsonResponse(response)
    else:
        return render(request, "home.html")

def register(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/register_frag.html", None, request)
        response = {
            "name": "Register",
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "register.html")

def pre_login(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/pre_login_frag.html", None, request)
        response = {
            "name": "Pre login",
            "content": renderer,
        }
        return JsonResponse(response)
    else:
        return render(request, "pre_login.html")

def login(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/login_frag.html", None, request)
        response = {
            "name": "Login",
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "login.html")
    
def oauth_login(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/oauth_frag.html", None, request)
        response = {
            "name": "OAuth Login",
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "oauth.html")

def chat_modal(request):
    user = request.user
    is_fragment = request.headers.get("fragment")
    if user.is_authenticated and is_fragment:
        renderer = render_to_string("fragments/chat_modal.html", None, request)
        response = { "content": renderer }
        return JsonResponse(response)
    else:
       return JsonResponse({"status": "false", "message":"user not authenticated or forgotten header"}, status=403)

def startGame(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/game_frag.html", None, request)
        response = {
            "name": "Pong game",
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "game.html")

def redirect(request):
    return (render(request, "redirect.html"))

def otp(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/otp_frag.html", None, request)
        response = {
            "name": "OTP",
            "content": renderer,
        }
        return JsonResponse(response)
    else:
        return render(request, "otp.html")

def hub(request):
    from django.contrib.auth.models import AnonymousUser
    user = request.user
    is_fragment = request.headers.get("fragment")

    if isinstance(user, AnonymousUser) and is_fragment:
        renderer = render_to_string("fragments/no_login_frag.html", None, request)
        response = {
            "name": "Hub",
            "content": renderer
        }
        return JsonResponse(response)
    elif isinstance(user, AnonymousUser):
        return render(request, "no_login.html")
    elif is_fragment:
        renderer = render_to_string("fragments/hub_frag.html", None, request)
        response = {
            "name": "Hub",
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "hub.html")
    
def about(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/about_frag.html", None, request)
        response = {
            "name": "About",
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "about.html")

def profile(request, user_id):
    from django.contrib.auth.models import AnonymousUser
    user = request.user
    try:
        profile_id = User.objects.get(id=user_id)
    except User.DoesNotExist:
        profile_id = None
    is_fragment = request.headers.get("fragment")

    if not profile_id and is_fragment:
        renderer = render_to_string(
            "fragments/noprofile_frag.html", None, request
        )
        response = {
            "name": "Profile not found",
            "content": renderer
        }
        return JsonResponse(response)
    elif not profile_id:
        return render(request, "noprofile.html", None)

    if isinstance(user, AnonymousUser) and is_fragment:
        renderer = render_to_string("fragments/no_login_frag.html", None, request)
        response = {
            "name": "Hub",
            "content": renderer
        }
        return JsonResponse(response)
    elif isinstance(user, AnonymousUser):
        return render(request, "no_login.html")

    if is_fragment:
        renderer = render_to_string(
            "fragments/profile_frag.html", {"profile_id": profile_id}, request
        )
        response = {
            "name": profile_id.username,
            "content": renderer
        }
        return JsonResponse(response)
    else:
        return render(request, "profile.html", {"profile_id": profile_id})

def settings(request):
    is_fragment = request.headers.get("fragment")
    if is_fragment:
        renderer = render_to_string("fragments/settings_frag.html", None, request)
        response = {
            "name": "Settings",
            "content": renderer,
        }
        return JsonResponse(response)
    else:
        return render(request, "settings.html")