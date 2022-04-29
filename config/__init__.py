# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

# TODO: Uncomment if your site uses celery and bgjobs

from .celery import app as celery_app
from . import monkey_patches
import asgiref


__all__ = ("celery_app",)


asgiref.sync.sync_to_async = monkey_patches.patch_sync_to_async
