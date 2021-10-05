.. _administration_commands:

Commands
========

.. contents::

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
