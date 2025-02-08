from django.http import JsonResponse
from django.shortcuts import redirect

class RestrictOTPAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        #print("RestrictOTPAccessMiddleware called.")
        # Check if the request path is the OTP verification endpoint
        if request.path == '/api/otp_verif/' and not request.session.get('otp_in_progress'):
            return redirect('login-user')
        if request.path.startswith('/api/register/') or \
           request.path.startswith('/api/login/') or \
           request.path.startswith('/api/otp_verif/') or \
           request.path.startswith('/api/oauth/'): 
            if request.user.is_authenticated:
                response_data = {
                'detail': 'You are already logged in. Please log out to access this page.',
                'redirect_url': f'/api/users/{request.user.id}/'
                }
                return JsonResponse(response_data, status=401)
        response = self.get_response(request)
        return response