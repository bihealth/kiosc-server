from projectroles.plugins import ProjectAppPluginPoint

from .models import DockerApp
from .urls import urlpatterns


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    name = "dockerapps"
    title = "Dockerized Apps"
    urls = urlpatterns

    icon = "rocket"

    entry_point_url_id = "dockerapps:dockerapp-list"

    description = "Management of Docker Apps"

    #: Required permission for accessing the app
    app_permission = "dockerapps"

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ["dockerapps"]

    #: Search results template
    search_template = "dockerapps/_search_results.html"

    #: App card template for the project details page
    details_template = "dockerapps/_details_card.html"

    #: App card title for the project details page
    details_title = "Docker Apps"

    #: Position in plugin ordering
    plugin_ordering = 10

    def search(self, search_term, user, search_type=None, keywords=None):
        """
        Return app items based on a search term, user, optional type and optional keywords

        :param search_term: String
        :param user: User object for user initiating the search
        :param search_type: String
        :param keywords: List (optional)
        :return: Dict
        """
        items = []

        if not search_type:
            dockerapps = DockerApp.objects.find(search_term, keywords)
            items = list(dockerapps)
            items.sort(key=lambda x: x.name.lower())
        elif search_type == "dockerapps":
            items = DockerApp.objects.find(search_term, keywords)

        return {"all": {"title": "Docker Apps", "search_types": ["dockerapps"], "items": items}}

    def get_object_link(self, model_str, uuid):
        """
        Return URL for referring to a object used by the app, along with a
        label to be shown to the user for linking.
        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: Dict or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)

        if isinstance(obj, DockerApp):
            return {"url": obj.get_absolute_url(), "label": obj.title}

        return None
