from django.shortcuts import redirect

class CustomRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        custom_redirect_url = request.session.pop('custom_redirect_url', None)
        if custom_redirect_url:
            return redirect(custom_redirect_url)

        return response