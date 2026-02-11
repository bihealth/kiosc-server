"""Django command for removing stopped containers."""

from django.core.management.base import BaseCommand
from django.db import transaction

from bgjobs.models import BackgroundJob
from django.conf import settings
from containers.models import (
    Container,
    STATE_EXITED,
    ContainerBackgroundJob,
    ACTION_DELETE,
    PROCESS_ACTION,
)
from containers.statemachines import connect_docker
from containers.tasks import container_task
from kiosc.users.models import User
from projectroles.plugins import PluginAPI


plugin_api = PluginAPI()


class Command(BaseCommand):
    """Implementation for removing stopped containers."""

    #: Help message displayed on the command line.
    help = "Remove stopped containers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--remove",
            help="Activate this flag to perform the removal",
            action="store_true",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Perform removing stopped containers."""

        if options["remove"]:
            msg_fin = "Command successfully finished"

        else:
            msg_fin = "Command successfully finished (dry-run)"

        cli = connect_docker()
        user = User.objects.filter(
            username=settings.PROJECTROLES_DEFAULT_ADMIN
        ).first()

        for container in Container.objects.filter(state=STATE_EXITED):
            if container.container_id:
                timeline = plugin_api.get_backend_api("timeline_backend")
                container_info = cli.inspect_container(container.container_id)
                state = container_info.get("State", {}).get("Status")
                project = container.project

                # Double check if state is really EXITED
                if not state == STATE_EXITED:
                    continue

                if options["remove"]:
                    bg_job = BackgroundJob.objects.create(
                        name="Delete container",
                        project=project,
                        job_type=ContainerBackgroundJob.spec_name,
                        user=user,
                    )
                    job = ContainerBackgroundJob.objects.create(
                        action=ACTION_DELETE,
                        project=project,
                        container=container,
                        bg_job=bg_job,
                    )

                    # Add container log entry
                    container.log_entries.create(
                        text="Delete",
                        process=PROCESS_ACTION,
                        user=user,
                    )

                    container_task(job_id=job.id)

                    # Add timeline event
                    if timeline:
                        timeline.add_event(
                            project=project,
                            app_name="kioscadmin",
                            user=user,
                            event_name="delete_container",
                            description=f"deleted {container.get_display_name()}",
                            status_type=timeline.TL_STATUS_OK,
                        )

                    container.delete()

                    self.stdout.write(
                        self.style.NOTICE("{} removed".format(container.title))
                    )

                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            "{} would be removed".format(container.title)
                        )
                    )

        self.stdout.write(self.style.SUCCESS(msg_fin))
