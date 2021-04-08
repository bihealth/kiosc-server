from django.conf.urls import url

from . import views


app_name = "containers"


urlpatterns = [
    url(
        regex=r"^(?P<project>[0-9a-f-]+)$",
        view=views.ContainerListView.as_view(),
        name="container-list",
    ),
    url(
        regex=r"^detail/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerDetailView.as_view(),
        name="container-detail",
    ),
    url(
        regex=r"^create/(?P<project>[0-9a-f-]+)$",
        view=views.ContainerCreateView.as_view(),
        name="container-create",
    ),
    url(
        regex=r"^update/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerUpdateView.as_view(),
        name="container-update",
    ),
    url(
        regex=r"^delete/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerDeleteView.as_view(),
        name="container-delete",
    ),
]
