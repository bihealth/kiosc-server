from django.urls import path

from . import views


app_name = "kioscadmin"


urlpatterns = [
    path(
        "overview",
        view=views.KioscAdminView.as_view(),
        name="overview",
    ),
]
