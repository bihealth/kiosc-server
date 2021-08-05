from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views, consumers

app_name = "containers"


urlpatterns = [
    url(
        regex=r"^(?P<project>[0-9a-f-]+)$",
        view=views.ContainerListView.as_view(),
        name="list",
    ),
    url(
        regex=r"^detail/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerDetailView.as_view(),
        name="detail",
    ),
    url(
        regex=r"^create/(?P<project>[0-9a-f-]+)$",
        view=views.ContainerCreateView.as_view(),
        name="create",
    ),
    url(
        regex=r"^update/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerUpdateView.as_view(),
        name="update",
    ),
    url(
        regex=r"^delete/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerDeleteView.as_view(),
        name="delete",
    ),
    url(
        regex=r"^start/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerStartView.as_view(),
        name="start",
    ),
    url(
        regex=r"^stop/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerStopView.as_view(),
        name="stop",
    ),
    url(
        regex=r"^pause/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerPauseView.as_view(),
        name="pause",
    ),
    url(
        regex=r"^unpause/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerUnpauseView.as_view(),
        name="unpause",
    ),
    url(
        regex=r"^restart/(?P<container>[0-9a-f-]+)$",
        view=views.ContainerRestartView.as_view(),
        name="restart",
    ),
    url(
        regex=r"^proxy/(?P<container>[0-9a-f-]+)/(?P<path>.*)$",
        view=csrf_exempt(views.ReverseProxyView.as_view()),
        name="proxy",
    ),
    url(
        regex=r"^proxy/lobby/(?P<container>[0-9a-f-]+)/(?P<path>.*)$",
        view=views.ContainerProxyLobbyView.as_view(),
        name="proxy-lobby",
    ),
]

websocket_urlpatterns = [
    url(
        (r"^containers/proxy/(?P<container>[0-9a-f-]+)/(?P<path>.*)$"),
        consumers.TunnelConsumer,
    )
]
