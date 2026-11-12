from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = (
            'GET, POST, PUT, DELETE, OPTIONS'
        )
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        return response


class ApiCsrfMiddleware(CsrfViewMiddleware):
    """Dispensa CSRF somente em /api/, inclusive nas novas views dos colegas."""

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.path_info.startswith('/api/'):
            return None
        return super().process_view(request, callback, callback_args, callback_kwargs)
