from django.conf import settings


def app_flags(request):
    return {
        "PWA_ENABLED": getattr(settings, "PWA_ENABLED", True),
    }
