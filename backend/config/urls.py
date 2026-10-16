from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Simple health check so Render (and you) can see the API is up."""
    return JsonResponse({"status": "ok", "service": "nepali-diet-backend"})


urlpatterns = [
    path('', health, name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]
