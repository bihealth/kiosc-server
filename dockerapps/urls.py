from django.conf.urls import url
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
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/delete/$",
        view=views.DockerAppDeleteView.as_view(),
        name="dockerapp-delete",
    ),
    # Proxy to embedded Docker / Shiny app.
    url(
        regex=r"^(?P<project>[0-9a-f-]+)/dockerapps/(?P<dockerapp>[0-9a-f-]+)/proxy/(?P<path>.*)$",
        view=views.DockerProxyView.as_view(),
        name="dockerapp-proxy",
    ),
]
