from django.conf.urls import url

from . import views


app_name = "containertemplates"


urlpatterns = [
    url(
        regex=r"^site$",
        view=views.ContainerTemplateSiteListView.as_view(),
        name="site-list",
    ),
    url(
        regex=r"^site/detail/(?P<containertemplatesite>[0-9a-f-]+)$",
        view=views.ContainerTemplateSiteDetailView.as_view(),
        name="site-detail",
    ),
    url(
        regex=r"^site/create$",
        view=views.ContainerTemplateSiteCreateView.as_view(),
        name="site-create",
    ),
    url(
        regex=r"^site/update/(?P<containertemplatesite>[0-9a-f-]+)$",
        view=views.ContainerTemplateSiteUpdateView.as_view(),
        name="site-update",
    ),
    url(
        regex=r"^site/delete/(?P<containertemplatesite>[0-9a-f-]+)$",
        view=views.ContainerTemplateSiteDeleteView.as_view(),
        name="site-delete",
    ),
    url(
        regex=r"^site/duplicate/(?P<containertemplatesite>[0-9a-f-]+)$",
        view=views.ContainerTemplateSiteDuplicateView.as_view(),
        name="site-duplicate",
    ),
    url(
        regex=r"^project/(?P<project>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectListView.as_view(),
        name="project-list",
    ),
    url(
        regex=r"^project/detail/(?P<containertemplateproject>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectDetailView.as_view(),
        name="project-detail",
    ),
    url(
        regex=r"^project/create/(?P<project>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectCreateView.as_view(),
        name="project-create",
    ),
    url(
        regex=r"^project/update/(?P<containertemplateproject>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectUpdateView.as_view(),
        name="project-update",
    ),
    url(
        regex=r"^project/delete/(?P<containertemplateproject>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectDeleteView.as_view(),
        name="project-delete",
    ),
    url(
        regex=r"^project/duplicate/(?P<containertemplateproject>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectDuplicateView.as_view(),
        name="project-duplicate",
    ),
    url(
        regex=r"^project/copy/(?P<project>[0-9a-f-]+)$",
        view=views.ContainerTemplateProjectCopyView.as_view(),
        name="project-copy",
    ),
    # Ajax views
    url(
        regex=r"^ajax/get-containertemplate$",
        view=views.ContainerTemplateSelectorApiView.as_view(),
        name="ajax-get-containertemplate",
    ),
]
