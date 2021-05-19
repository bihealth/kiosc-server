from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

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
    url(
        regex=r"^start/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerStartView.as_view(),
        name="container-start",
    ),
    url(
        regex=r"^stop/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerStopView.as_view(),
        name="container-stop",
    ),
    url(
        regex=r"^pause/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerPauseView.as_view(),
        name="container-pause",
    ),
    url(
        regex=r"^unpause/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerUnpauseView.as_view(),
        name="container-unpause",
    ),
    url(
        regex=r"^restart/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerRestartView.as_view(),
        name="container-restart",
    ),
    url(
        regex=r"^proxy/(?P<container>[0-9a-f-]+)/(?P<path>.*)$",
        view=csrf_exempt(views.ReverseProxyView.as_view()),
        name="proxy",
    ),
]
