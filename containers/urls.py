from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from . import views, consumers, views_api

app_name = "containers"


ui_urlpatterns = [
    path(
        "<uuid:project>",
        view=views.ContainerListView.as_view(),
        name="list",
    ),
    path(
        "detail/<uuid:container>",
        view=views.ContainerDetailView.as_view(),
        name="detail",
    ),
    path(
        "create/<uuid:project>",
        view=views.ContainerCreateView.as_view(),
        name="create",
    ),
    path(
        "update/<uuid:container>",
        view=views.ContainerUpdateView.as_view(),
        name="update",
    ),
    path(
        "delete/<uuid:container>",
        view=views.ContainerDeleteView.as_view(),
        name="delete",
    ),
    path(
        "start/<uuid:container>",
        view=views.ContainerStartView.as_view(),
        name="start",
    ),
    path(
        "stop/<uuid:container>",
        view=views.ContainerStopView.as_view(),
        name="stop",
    ),
    path(
        "pause/<uuid:container>",
        view=views.ContainerPauseView.as_view(),
        name="pause",
    ),
    path(
        "unpause/<uuid:container>",
        view=views.ContainerUnpauseView.as_view(),
        name="unpause",
    ),
    path(
        "restart/<uuid:container>",
        view=views.ContainerRestartView.as_view(),
        name="restart",
    ),
    re_path(
        r"^proxy/(?P<container>[0-9a-f-]+)/(?P<path>.*)$",
        view=csrf_exempt(views.ReverseProxyView.as_view()),
        name="proxy",
    ),
    path(
        "proxy/lobby/<uuid:container>",
        view=views.ContainerProxyLobbyView.as_view(),
        name="proxy-lobby",
    ),
    path(
        "file/serve/<uuid:file>/<str:filename>",
        view=views.FileServeView.as_view(),
        name="file-serve",
    ),
    # Ajax views
    path(
        "ajax/get-dynamic-details/<uuid:container>",
        view=views.ContainerGetDynamicDetailsApiView.as_view(),
        name="ajax-get-dynamic-details",
    ),
]

api_urlpatterns = [
    path(
        "api/<uuid:project>",
        view=views_api.ContainerListAPIView.as_view(),
        name="api-list",
    ),
    path(
        "api/detail/<uuid:container>",
        view=views_api.ContainerDetailAPIView.as_view(),
        name="api-detail",
    ),
    path(
        "api/create/<uuid:project>",
        view=views_api.ContainerCreateAPIView.as_view(),
        name="api-create",
    ),
    path(
        "api/delete/<uuid:container>",
        view=views_api.ContainerDeleteAPIView.as_view(),
        name="api-delete",
    ),
    path(
        "api/start/<uuid:container>",
        view=views_api.ContainerStartAPIView.as_view(),
        name="api-start",
    ),
    path(
        "api/stop/<uuid:container>",
        view=views_api.ContainerStopAPIView.as_view(),
        name="api-stop",
    ),
]

websocket_urlpatterns = [
    re_path(
        r"^containers/proxy/(?P<container>[0-9a-f-]+)/(?P<path>.*)$",
        consumers.TunnelConsumer.as_asgi(),
    )
]

urlpatterns = ui_urlpatterns + api_urlpatterns
