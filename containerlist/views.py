from django.views.generic import ListView

from containers.models import Container
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
)


class ContainerSiteListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ListView,
):
    """View for Container List app."""

    permission_required = "containerlist.view"
    template_name = "containerlist/containerlist.html"
    model = Container

    def get_queryset(self):
        res = []
        for container in Container.objects.all():
            if self.request.user.has_perm('containers.view_container', container.project):
                res.append(container)

        return res

