from django.views.decorators.csrf import csrf_exempt
from django.urls import path, re_path

from . import views


urlpatterns = [
    path(
        '',
        view=csrf_exempt(views.KioscRegistryNotificationsView.as_view()),
        name='registry-notifications',
    ),
]
