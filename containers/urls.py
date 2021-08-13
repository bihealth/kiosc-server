from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views, consumers, views_api

app_name = "containers"


ui_urlpatterns = [
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

api_urlpatterns = [
    url(
        regex=r"^api/(?P<project>[0-9a-f-]+)$",
        view=views_api.ContainerListAPIView.as_view(),
        name="api-list",
    ),
    url(
        regex=r"^api/detail/(?P<container>[0-9a-f-]+)$",
        view=views_api.ContainerDetailAPIView.as_view(),
        name="api-detail",
    ),
    url(
        regex=r"^api/create/(?P<project>[0-9a-f-]+)$",
        view=views_api.ContainerCreateAPIView.as_view(),
        name="api-create",
    ),
    url(
        regex=r"^api/delete/(?P<container>[0-9a-f-]+)$",
        view=views_api.ContainerDeleteAPIView.as_view(),
        name="api-delete",
    ),
    url(
        regex=r"^api/start/(?P<container>[0-9a-f-]+)$",
        view=views_api.ContainerStartAPIView.as_view(),
        name="api-start",
    ),
    url(
        regex=r"^api/stop/(?P<container>[0-9a-f-]+)$",
        view=views_api.ContainerStopAPIView.as_view(),
        name="api-stop",
    ),
]

websocket_urlpatterns = [
    url(
        (r"^containers/proxy/(?P<container>[0-9a-f-]+)/(?P<path>.*)$"),
        consumers.TunnelConsumer,
    )
]

urlpatterns = ui_urlpatterns + api_urlpatterns
