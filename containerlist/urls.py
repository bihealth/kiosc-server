from django.urls import path

from . import views


app_name = "containerlist"


urlpatterns = [
    path(
        "",
        view=views.ContainerListView.as_view(),
        name="overview",
    ),
]
