.. _introduction_user_stories.rst:

User Stories
============

.. contents::

The Guest Accessing the Web Interface of a Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You are a guest of a project. You can list the containers
of the project, and access the details of each container. You can't
change the status of a container, except indirectly by viewing
a container that is not running. Probably you like to access
the web interface provided by the container.

To proceed, click on a project and then select the **Container** app.
This will display a list of all containers in the project. On the right-hand
side of each container is a button with an eye icon. The button might be
either gray-outlined with a crossed-out eye, or with a blue background
with an open eye. The crossed-out eye indicates that the container is
not running and this will also be reflected in the state. The blue open
eye indicates that the container is available. No matter the state,
clicking the icon will open the web interface provided by the container.
The difference is that in the crossed-out state Kiosc tries to start the
container before accessing the web interface which might take some time
while in the running state the web interface will be displayed immediately.


