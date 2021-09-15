from bgjobs.models import BackgroundJob
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from projectroles.plugins import get_backend_api
from projectroles.views_api import SODARAPIGenericProjectMixin
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    DestroyAPIView,
)
from rest_framework.views import APIView

from containers.models import (
    Container,
    ContainerBackgroundJob,
    ACTION_START,
    ACTION_STOP,
    PROCESS_OBJECT,
    PROCESS_ACTION,
    STATE_INITIAL,
    STATE_DELETED,
    ACTION_DELETE,
)
from containers.serializers import ContainerSerializer
from containers.tasks import container_task
from containers.views import CELERY_SUBMIT_COUNTDOWN


APP_NAME = "containers"


class ContainerListAPIView(
    SODARAPIGenericProjectMixin,
    ListAPIView,
):

    serializer_class = ContainerSerializer
    permission_required = "containers.view_container"

    def get_queryset(self):
        return Container.objects.filter(project=self.get_project())


class ContainerDetailAPIView(
    SODARAPIGenericProjectMixin,
    RetrieveAPIView,
):

    serializer_class = ContainerSerializer
    lookup_url_kwarg = "container"
    lookup_field = "sodar_uuid"
    permission_required = "containers.view_container"


class ContainerCreateAPIView(
    SODARAPIGenericProjectMixin,
    CreateAPIView,
):

    serializer_class = ContainerSerializer
    permission_required = "containers.create_container"

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            # Add container log entry
            container = Container.objects.get(
                sodar_uuid=response.data.get("sodar_uuid")
            )
            container.log_entries.create(
                text="Created [API]",
                process=PROCESS_OBJECT,
                user=self.request.user,
            )
            return response

        except IntegrityError as e:
            return JsonResponse(
                {"error": f"Bad Request (400) - {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ContainerDeleteAPIView(
    SODARAPIGenericProjectMixin,
    DestroyAPIView,
):

    serializer_class = ContainerSerializer
    lookup_url_kwarg = "container"
    lookup_field = "sodar_uuid"
    permission_required = "containers.delete_container"

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        timeline = get_backend_api("timeline_backend")
        container = Container.objects.get(sodar_uuid=kwargs.get("container"))
        project = self.get_project()

        bg_job = BackgroundJob.objects.create(
            name="Delete container",
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_DELETE,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Add container log entry
        container.log_entries.create(
            text="Delete [API]",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # No async task
        container_task(job_id=job.id)
        container.refresh_from_db()

        if container.state not in (STATE_INITIAL, STATE_DELETED):
            # Add timeline event
            if timeline:
                timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=request.user,
                    event_name="delete_container",
                    description=f"deleting of {container.get_display_name()} failed",
                    status_type="FAILED",
                )

            return JsonResponse(
                {
                    "message": f"Failed deleting container {container.get_display_name()}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Add timeline event
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name="delete_container",
                description=f"deleted {container.get_display_name()}",
                status_type="OK",
            )

        return super().delete(request, *args, **kwargs)


class ContainerStartAPIView(
    SODARAPIGenericProjectMixin,
    APIView,
):

    serializer_class = ContainerSerializer
    lookup_url_kwarg = "container"
    lookup_field = "sodar_uuid"
    permission_required = "containers.start_container"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = Container.objects.get(sodar_uuid=kwargs.get("container"))

        bg_job = BackgroundJob.objects.create(
            name="Start container",
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_START,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Add container log entry
        container.log_entries.create(
            text="Start [API]",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return JsonResponse(
            {"message": "container starting job submitted"},
            status=status.HTTP_200_OK,
        )


class ContainerStopAPIView(
    SODARAPIGenericProjectMixin,
    APIView,
):

    serializer_class = ContainerSerializer
    lookup_url_kwarg = "container"
    lookup_field = "sodar_uuid"
    permission_required = "containers.stop_container"

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        project = self.get_project()
        container = Container.objects.get(sodar_uuid=kwargs.get("container"))

        bg_job = BackgroundJob.objects.create(
            name="Stop container",
            project=project,
            job_type=ContainerBackgroundJob.spec_name,
            user=request.user,
        )
        job = ContainerBackgroundJob.objects.create(
            action=ACTION_STOP,
            project=project,
            container=container,
            bg_job=bg_job,
        )

        # Add container log entry
        container.log_entries.create(
            text="Stop [API]",
            process=PROCESS_ACTION,
            user=request.user,
        )

        # Schedule task
        container_task.apply_async(
            kwargs={"job_id": job.id}, countdown=CELERY_SUBMIT_COUNTDOWN
        )

        return JsonResponse(
            {"message": "container stopping job submitted"},
            status=status.HTTP_200_OK,
        )
