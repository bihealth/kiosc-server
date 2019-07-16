from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import consumers
from . import views

app_name = "dockerapps"

urlpatterns = [
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image/$",
        view=views.DockerImageListView.as_view(),
        name="image-list",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image/create$",
        view=views.DockerImageCreateView.as_view(),
        name="image-create",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image/(?P<image>[0-9a-f-]+)/$",
        view=views.DockerImageDetailView.as_view(),
        name="image-detail",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image/(?P<image>[0-9a-f-]+)/update/$",
        view=views.DockerImageUpdateView.as_view(),
        name="image-update",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image/(?P<image>[0-9a-f-]+)/delete/$",
        view=views.DockerImageDeleteView.as_view(),
        name="image-delete",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image/(?P<image>[0-9a-f-]+)/control/$",
        view=views.DockerImageJobControlView.as_view(),
        name="image-control",
    ),
    # Background job views
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/image-job/(?P<job>[0-9a-f-]+)/$",
        view=views.ImageBackgroundJobDetailView.as_view(),
        name="image-job-detail",
    ),
    # Proxy to embedded Docker / Shiny app.  NB: there is a "partner" websocket_urlpattern through Django Channels.
    url(
        regex=(
            r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<image>[0-9a-f-]+)/proxy/"
            "(?P<container>[0-9a-f-]+)/(?P<path>.*)$"
        ),
        view=csrf_exempt(views.DockerProxyView.as_view()),
        name="container-proxy",
    ),
]

websocket_urlpatterns = [
    url(
        (
            r"^dockerapps/(?P<project>[0-9a-f-]+)/dockerapps/(?P<image>[0-9a-f-]+)/proxy/"
            "(?P<container>[0-9a-f-]+)/(?P<path>.*)$"
        ),
        consumers.TunnelConsumer,
    )
]
