.. _administration_periodic_tasks:

Periodic Tasks
==============

The user has no influence on periodic tasks, but
the periodic tasks in return influence the user experience.

They are designed to keep the Docker containers consistent
with the information the user enters into the web interface,
and to fetch logs and information from the Docker containers.

.. contents::

Get logs and status from Docker container
-----------------------------------------

*Runs every 30 seconds.*

This task fetches the logs that are provided by the Docker
container, which includes logs from whatever runs inside of the
Docker container. It also sets the Docker container status
in the container database object, which means that the Docker
container can change without the users intention (e.g. in case
the Docker container exists unexpectedly).

Synchronize Docker container state with last user action
--------------------------------------------------------

*Runs every minute.*

This task synchronizes the last user action performed on the
container with the actual Docker container status if and only
if this information differs. For example, if the Docker container
exited for whatever reason but the last user action was to start
the container, the task tries to run the Docker container.

Stop inactive containers
------------------------

*Runs every day at 1:11am.*

This task stops inactive containers that were not accessed by the
proxy for a defined period of time. This can be set by the user
for each container individually, but there is maximum of 7 days.
If the user omits the setting, it defaults to the 7 days maximum.

Synchronize with upstream SODAR instance (if configured)
--------------------------------------------------------

*Runs every five minutes.*

This task synchronizes the projects and users with the upstream
SODAR instance. Only if this site is in target mode.