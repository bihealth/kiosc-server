.. _administration_commands:

Commands
========

.. contents::

Create "Hello World" App
^^^^^^^^^^^^^^^^^^^^^^^^

*Usage:* ``python manage.py createtoyapp``

This command creates an example project with a toy app for testing purposes.
The idea is to give admins a way to check whether the installation has worked.
The command will create a top-level category (by default called "Hello
World"), a project within that category (by default called "Test"), and a
container with a Shiny app demo. The app is taken from the `Rocker project
<https://rocker-project.org/images/versioned/shiny.html>`__. If the project
or app already exist, the command has no effect.

By default, the app is created with public access for all viewers (see the
:ref:`introduction_roles` docs for more information about user roles).

*Options:*

- ``--category-name=<category name>``: name of the category to be created
- ``--project-name=<project name>``: name of the project to be created
- ``--app-name=<app name>``: name of the app to be created
- ``--private``: with this flag, the project will be visible only to the superuser

Remove Stopped Containers
^^^^^^^^^^^^^^^^^^^^^^^^^

*Usage:* ``python manage.py remove_stopped --remove``

This command removes all of the stopped containers.
To prevent accidentally deleting containers, the ``--remove``
parameter has to be provided. Omitting this parameter
only dry-runs the command.

Stop All Containers
^^^^^^^^^^^^^^^^^^^

*Usage:* ``python manage.py stop_all``

This command sets all containers to ``exited`` status, no
matter their current state.

Stop Unused Containers
^^^^^^^^^^^^^^^^^^^^^^

*Usage:* ``python manage.py stop_unused``

This command stops all containers that haven't been accessed
by the reverse proxy for a defined period of time (the parameter
can be set in the container object itself, but there is an upper
limit of 7 days).
