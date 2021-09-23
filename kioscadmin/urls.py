from django.conf.urls import url

from . import views


app_name = "kioscadmin"


urlpatterns = [
    url(
        regex=r"^overview$",
        view=views.KioscAdminView.as_view(),
        name="overview",
    ),
]
