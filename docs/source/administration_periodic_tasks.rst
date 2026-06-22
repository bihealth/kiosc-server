.. _administration_periodic_tasks:

Periodic Tasks
==============

The user has no influence on periodic tasks, but
the periodic tasks in return influence the user experience.

They are designed to keep the Docker containers consistent
with the information the user enters into the web interface.

.. contents::

Get status from Docker container
--------------------------------

*Runs every 30 seconds.*

The state of a Docker container can change without the users intention (e.g. in
case the Docker container exists unexpectedly). This task polls the status of
all containers from the Docker daemon and updates the corresponding database
objects.

Stop inactive containers
------------------------

*Runs every day at 1:11am.*

This task stops inactive containers that were not accessed by the
proxy for a defined period of time. This can be set by the user
for each container individually, but there is maximum of 7 days.
If the user omits the setting, it defaults to the 7 days maximum.

Remove zombie containers
------------------------

*Runs every hour on the half hour (i.e., at 00:30, 01:30, 02:30, and so on).*

Occasionally, it happens that Kiosc loses track of a Docker container. The
container still exists, but it cannot be reached by Kiosc. We refer to such
containers as "zombies", and this tasks takes care of cleaning them up.

Synchronize with upstream SODAR instance (if configured)
--------------------------------------------------------

*Runs every five minutes.*

This task synchronizes the projects and users with the upstream
SODAR instance. Only if this site is in target mode.
