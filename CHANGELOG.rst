Kiosc Changelog
^^^^^^^^^^^^^^^

Changelog for the **Kiosc** Django app package.
Loosely follows the `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


HEAD (unreleased)
=================

Added
-----

- **Container**
  - ``process`` field to ``ContainerLogEntry`` to reflect which process writes to the logs (#26)
  - ``date_docker_log`` field to ``ContainerLogEntry`` to represent the time of the Docker log entry (#26)
  - ``ContainerLogEntryManager`` to allow ordering by date of log or date of Docker log (#26)
  - Permission to view logs (#26)
  - Task to pull docker logs and the current status (#26)
  - Periodic task pulling docker log and status (#26)

Changed
-------


v0.1.2 (2021-04-27)
===================

Added
-----

- **Container**
  - Logging with timeline for views and tasks (#24)
  - Container-centric logging (#25)


v0.1.1 (2021-04-23)
===================

Added
-----

- **General**
  - urllib3-mock 0.3.3 dependency (#21)
- **Container**
  - Tests for views (#21)
  - Tests for permissions (#21)
  - Tests f0r forms (#21)
  - Tests for models (#23)
  - Tests for tasks (#22)


v0.1.0 (2021-04-15)
===================

Added
-----

- **General**
  - Initial commit based on SODAR core v0.9.1 (#16)
  - Strings are formatted using double quotes (#17)
  - Docker 5.0.0 dependency (#19)
  - Logo and color scheme (#20)
  - Revproxy 0.10.0 dependency (#20)
- **Containers**
  - App itself (#17)
  - Models ``Container``, ``ContainerBackgroundJob`` and ``ContainerLogEntry`` (#17, #18)
  - Views/templates/urls for listing, creating, updating and deleting container objects and viewing its details (#18)
  - Permission rules for viewing, creating, editing and deleting container objects (#18)
  - Task to pull an image and start and stop a container (#19)
  - Views to start and stop a container (#19)
  - Activated Celery support (#19)
  - Reverse proxy with view and url (#20)

Changed
^^^^^^^

- **General**
  - Upgrade to Django v3.1.7 (#47)
  - Upgrade to SODAR core pre-v0.10.0 (#47)
  - Bumped Celery version to 5.0.5 (#19)
