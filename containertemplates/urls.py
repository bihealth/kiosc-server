from django.urls import path

from . import views


app_name = "containertemplates"


urlpatterns = [
    path(
        "site",
        view=views.ContainerTemplateSiteListView.as_view(),
        name="site-list",
    ),
    path(
        "site/detail/<uuid:containertemplatesite>",
        view=views.ContainerTemplateSiteDetailView.as_view(),
        name="site-detail",
    ),
    path(
        "site/create",
        view=views.ContainerTemplateSiteCreateView.as_view(),
        name="site-create",
    ),
    path(
        "site/update/<uuid:containertemplatesite>",
        view=views.ContainerTemplateSiteUpdateView.as_view(),
        name="site-update",
    ),
    path(
        "site/delete/<uuid:containertemplatesite>",
        view=views.ContainerTemplateSiteDeleteView.as_view(),
        name="site-delete",
    ),
    path(
        "site/duplicate/<uuid:containertemplatesite>",
        view=views.ContainerTemplateSiteDuplicateView.as_view(),
        name="site-duplicate",
    ),
    path(
        "project/<uuid:project>",
        view=views.ContainerTemplateProjectListView.as_view(),
        name="project-list",
    ),
    path(
        "project/detail/<uuid:containertemplateproject>",
        view=views.ContainerTemplateProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "project/create/<uuid:project>",
        view=views.ContainerTemplateProjectCreateView.as_view(),
        name="project-create",
    ),
    path(
        "project/update/<uuid:containertemplateproject>",
        view=views.ContainerTemplateProjectUpdateView.as_view(),
        name="project-update",
    ),
    path(
        "project/delete/<uuid:containertemplateproject>",
        view=views.ContainerTemplateProjectDeleteView.as_view(),
        name="project-delete",
    ),
    path(
        "project/duplicate/<uuid:containertemplateproject>",
        view=views.ContainerTemplateProjectDuplicateView.as_view(),
        name="project-duplicate",
    ),
    path(
        "project/copy/<uuid:project>",
        view=views.ContainerTemplateProjectCopyView.as_view(),
        name="project-copy",
    ),
    # Ajax views
    path(
        "ajax/get-containertemplate",
        view=views.ContainerTemplateSelectorApiView.as_view(),
        name="ajax-get-containertemplate",
    ),
]
