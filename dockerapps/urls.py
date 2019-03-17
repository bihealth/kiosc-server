from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import consumers
from . import views

app_name = "dockerapps"

urlpatterns = [
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/$",
        view=views.DockerAppListView.as_view(),
        name="dockerapp-list",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/create$",
        view=views.DockerAppCreateView.as_view(),
        name="dockerapp-create",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/$",
        view=views.DockerAppDetailView.as_view(),
        name="dockerapp-detail",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/update/$",
        view=views.DockerAppUpdateView.as_view(),
        name="dockerapp-update",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/changestate/$",
        view=views.DockerAppChangeStateView.as_view(),
        name="dockerapp-changestate",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/updatestates/$",
        view=views.DockerAppUpdateStateView.as_view(),
        name="dockerapp-updatestates",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/delete/$",
        view=views.DockerAppDeleteView.as_view(),
        name="dockerapp-delete",
    ),
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/run/$",
        view=views.DockerAppRunView.as_view(),
        name="dockerapp-run",
    ),
    # Proxy to embedded Docker / Shiny app.  NB: there is a "partner" websocket_urlpattern through Django Channels.
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/proxy/(?P<path>.*)$",
        view=csrf_exempt(views.DockerProxyView.as_view()),
        name="dockerapp-proxy",
    ),
]

websocket_urlpatterns = [
    url(
        r"^dockerapps/(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/proxy/(?P<path>.*)$",
        consumers.TunnelConsumer,
    )
]
