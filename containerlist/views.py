from django.views.generic import ListView

from containers.models import Container
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
)


class ContainerListView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ListView,
):
    """View for Container List app."""

    permission_required = "containerlist.view"
    template_name = "containerlist/containerlist.html"
    model = Container
