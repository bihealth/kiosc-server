from django.conf.urls import url

from . import views


app_name = "containertemplates"


urlpatterns = [
    url(
        regex=r"^(?P<project>[0-9a-f-]+)$",
        view=views.ContainerTemplateListView.as_view(),
        name="list",
    ),
    url(
        regex=r"^detail/(?P<containertemplate>[0-9a-f-]+)$",
        view=views.ContainerTemplateDetailView.as_view(),
        name="detail",
    ),
    url(
        regex=r"^create/(?P<project>[0-9a-f-]+)$",
        view=views.ContainerTemplateCreateView.as_view(),
        name="create",
    ),
    url(
        regex=r"^update/(?P<containertemplate>[0-9a-f-]+)$",
        view=views.ContainerTemplateUpdateView.as_view(),
        name="update",
    ),
    url(
        regex=r"^delete/(?P<containertemplate>[0-9a-f-]+)$",
        view=views.ContainerTemplateDeleteView.as_view(),
        name="delete",
    ),
]
