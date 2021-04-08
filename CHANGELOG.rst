Kiosc Changelog
^^^^^^^^^^^^^^^

Changelog for the **Kiosc** Django app package.
Loosely follows the `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


HEAD (unreleased)
=================

Added
-----

- **General**
  - Initial commit based on SODAR core v0.9.1 (#16)
  - Strings are formatted using double quotes (#17)
- **Containers**
  - App itself (#17)
  - Models ``Container``, ``ContainerBackgroundJob`` and ``ContainerLogEntry`` (#17, #18)
  - Views/templates/urls for listing, creating, updating and deleting container objects and viewing its details (#18)
  - Permission rules for viewing, creating, editing and deleting container objects. (#18)
