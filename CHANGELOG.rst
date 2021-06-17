Kiosc Changelog
^^^^^^^^^^^^^^^

Changelog for the **Kiosc** Django app package.
Loosely follows the `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


HEAD (unreleased)
=================

Added
-----

- **General**
  - Docker deployment
- **ContainerTemplates**
  - App itself (#29)
  - ``ContainerTemplates`` model (#29)
  - Views for creating/updating/deleting and viewing details of ``ContainerTemplates`` (#29)
  - Permissions for ``ContainerTemplates`` views (#29)


v0.1.3 (2021-06-09)
===================

Added
-----

- **Containers**
  - ``process`` field to ``ContainerLogEntry`` to reflect which process writes to the logs (#26)
  - ``date_docker_log`` field to ``ContainerLogEntry`` to represent the time of the Docker log entry (#26)
  - ``ContainerLogEntryManager`` to allow ordering by date of log or date of Docker log (#26)
  - Permission to view logs (#26)
  - Task to pull docker logs and the current status (#26)
  - Periodic task pulling docker log and status (#26)
  - ``restart``, ``pause`` and ``unpause`` action (#27)
  - python-statemachine v0.8.0 dependency (#27)
  - Statemachine for controlling flow of a container (#27)
  - Switch class for coordinating actions with the statemachine (#27)
  - ``date_last_status_update`` field to ``Container`` model to store the date of the last status update (#59)
  - ``max_retries`` field to ``Container`` model to set number of maximum retries to match the expected Docker container state (#59)
  - ``get_repos_full()`` method to ``Container`` model (#59)
  - ``retries`` field to ``ContainerBackgroundJob`` model to count retries of matching the expected Docker container state (#59)
  - ``sync_container_state_with_last_user_action`` task, running periodically (#59)
  - ``is_project_guest`` permission to proxy rule (#28)
  - ``ContainerProxyLobbyView`` called when viewing a container not in state ``running`` (#28)

Changed
-------

- **General**
  - Bumped github workflow Ubuntu version to 20.04 (#28)
- **Containers**
  - Purpose of ``timeout`` field in ``Container`` model (#59)
  - Output of ``__str__`` and ``__repr`` of ``Container`` model (#59)
  - Refined mocking of Docker API (#59)
  - Updating a container triggers a restart if in state ``running`` or ``paused`` (#28)

Removed
-------

- **Containers**
  - ``timeout_exceeded`` field in ``Container`` model (#59)


v0.1.2 (2021-04-27)
===================

Added
-----

- **Containers**
  - Logging with timeline for views and tasks (#24)
  - Container-centric logging (#25)


v0.1.1 (2021-04-23)
===================

Added
-----

- **General**
  - urllib3-mock 0.3.3 dependency (#21)
- **Containers**
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
-------

- **General**
  - Upgrade to Django v3.1.7 (#47)
  - Upgrade to SODAR core pre-v0.10.0 (#47)
  - Bumped Celery version to 5.0.5 (#19)
