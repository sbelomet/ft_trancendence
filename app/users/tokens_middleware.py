from typing import Any


class token_middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request) -> Any:
        response = self.get_response(request)
        response['Set-Cookie'] = "token=myvalue;SameSite=Strict;Secure;HttpOnly"
        return (response)