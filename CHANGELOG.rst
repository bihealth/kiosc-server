Kiosc Changelog
^^^^^^^^^^^^^^^

Changelog for the **Kiosc** Django app package.
Loosely follows the `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


Head (unreleased)
=================

General
-------

- Added manual (#97, #99)
- Migrated to SODAR core v0.10.5 (#97)
- Fixed menu notches display bug (#97)
- Added user story to documentation for a guest user that wants to view the web interface provided by the container (#103)

Kioscadmin
----------

- Added view for overall container and Docker information (#37)
- Added commands ``stop_unused``, ``remove_stopped`` and ``stop_all`` (#37)
- Moved container maintenance tasks from ``Container`` app to ``Kioscadmin`` app (#37)
- Added tests for commands, views and tasks (#108)
- Added documentation (#109)


v0.3.0 (2021-09-15)
===================

Container
---------

- Added REST API view for creating/listing a container (#40)
- Added REST API view for starting/stopping a container (#41)
- Added REST API view for deleting a container (#42)
- Migrated to SODAR core v0.10.4


v0.2.0 (2021-08-09)
===================

General
-------

- Switched to Docker deployment
- Added site-wide apps to menu (#30)
- Migrated to SODAR core v0.10.3
- Celery production settings which prevented workers from receiving jobs
- UI improvements (#81)
- Added setting ``KIOSC_DOCKER_MAX_INACTIVITY`` to set maximal inactivity timespan (#62)
- Replacing ``gunicorn`` with ``daphne``
- Enabled websockets via channels in daphne

Containertemplates
------------------

- Added app itself (#29)
- ``ContainerTemplates`` model (#29)
- Views for creating/updating/deleting and viewing details of ``ContainerTemplate`` (#29)
- Permissions for ``ContainerTemplate`` views (#29)
- View for duplicate a ``ContainerTemplate`` (#30)
- Renamed ``ProjectApp`` to ``SiteApp`` (#30)
- Removed ``project`` field from ``ContainerTemplates`` model (#30)
- ``ContainerTemplateProject`` model (#31)
- Views for creating/updating/deleting/duplicating and viewing details of ``ContainerTemplateProject`` (#31)
- Permissions for ``ContainerTemplateSite`` views (#31)
- ``ProjectApp`` re-introduced living alongside ``SiteApp`` (#31)
- Renamed ``ContainerTemplate`` model to ``ContainerTemplateSite`` (#31)
- View and forms to copy site-wide and project-wide container template (#32)
- Added optional foreign key ``containertemplatesite`` to ``ContainerTemplateProject`` model (#32)
- Added AJAX view to get values of a site- or project-wide containertemplate (#33)
- Added field ``inactivity_threshold`` to ``ContainerTemplateBase`` model to adjust inactivity timespan X (#62)
- Removed ``environment_secret_keys`` field from ``ContainerTemplateBase`` model as they should not be allowed in templates (#83)
- Updated detail page concerning links between site- and project-wide templates (#85)

Containers
----------

- Changed internal naming of URLs (#30)
- Field ``environment`` now optional (#31)
- Fixed setting the environment variables in the container (#32)
- Fixed bug in parsing of docker log date (#32)
- Starting and restarting a container now removes old container and creates a new one (#72)
- Detail page now allows for managing the container (#72)
- Extended container logs with stack trace in case of unknown error
- Added ``ContainerActionLock`` model to throttle actions performed on a container (#75)
- Accepting ``__KIOSC_URL_PREFIX__`` in the ``environment`` field, being replaced by the reverse proxy url
- Added fuctionality to copy values from a site- or project-wide containertemplate to the container form (#33)
- Added title and description to ``Container`` model (#81)
- Delete action added that stops and deletes Docker containers and not just the container database object (#63)
- Adjusted proxy lobby view to start containers asynchronously (#62)
- Added more checks and differientated error messages to proxy view (#62)
- Added periodic task running once a day to stop running containers when not accessed for timespan X (#62)
- Added field ``inactivity_threshold`` to ``Container`` model to adjust inactivity timespan X (#62)
- Fixed environment secret key feature that still showed the values of the secret keys (#83)
- Fixed bug in statemachine that prevented users from deleteing failed containers
- Updated detail page concerning links to templates (#85)


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
