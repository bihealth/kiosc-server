"""Django command for stopping all containers."""
import docker.errors
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from bgjobs.models import BackgroundJob
from containers.models import Container, ContainerBackgroundJob, ACTION_STOP
from containers.statemachines import connect_docker
from kiosc.users.models import User
from containers.tasks import container_task


class Command(BaseCommand):
    """Implementation for stopping all containers."""

    #: Help message displayed on the command line.
    help = "Stop containers all containers."

    @transaction.atomic
    def handle(self, *args, **options):
        """Perform stopping all containers."""

        msg_fin = "Command successfully finished"
        cli = connect_docker()
        user = User.objects.get(username=settings.PROJECTROLES_DEFAULT_ADMIN)

        for container in Container.objects.all():
            if not container.container_id:
                continue

            # Check if container exists
            try:
                cli.inspect_container(container.container_id)

            except docker.errors.NotFound:
                continue

            else:
                bg_job = BackgroundJob.objects.create(
                    name="Stop container",
                    project=container.project,
                    job_type=ContainerBackgroundJob.spec_name,
                    user=user,
                )
                job = ContainerBackgroundJob.objects.create(
                    action=ACTION_STOP,
                    project=container.project,
                    container=container,
                    bg_job=bg_job,
                )

                container_task.apply_async(
                    kwargs={"job_id": job.id}, countdown=0.5
                )

                self.stdout.write(
                    self.style.NOTICE("{} stopped".format(container.title))
                )

        self.stdout.write(self.style.SUCCESS(msg_fin))
