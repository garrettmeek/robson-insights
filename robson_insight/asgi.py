"""
ASGI config for robson_insight project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

settings_module = 'robson_insight.deployment_settings' if 'RENDER_EXTERNAL_HOSTNAME' in os.environ else 'robson_insight.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE',settings_module )

application = get_asgi_application()
