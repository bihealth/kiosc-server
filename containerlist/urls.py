from django.urls import path

from . import views


app_name = 'containerlist'


urlpatterns = [
    path(
        '',
        view=views.ContainerSiteListView.as_view(),
        name='overview',
    ),
]
