.. _manual_main:

Welcome to the Kiosc documentation!
========================================

Kiosc is a web application to control Docker containers that run a webserver.

It was conceived to facilitate presenting analysis results interactively (but is not limited to that)
by running Docker images that are constricting any application that offers a web interface.
Any image can be loaded, and Kiosc manages the access to the web interface of the application.

What Kiosc is and what it is not
--------------------------------

Kiosc is a web interface for

- loading Docker images and creating containers from it,
- controlling the state of Docker containers,
- controlling access to containers based on the user management provided by SODAR,
- providing access to the app running in a container.

Kiosc is NOT

- a tool to create Docker images,
- for running Docker images without webserver (you can do that, but you won't benefit from it),
- for directly loading or sharing data (this has to be managed by the Docker image).

.. note::

   You can find the official version of this documentation at
   `readthedocs.io <https://kiosc.readthedocs.io/en/latest/>`_.
   If you view these files on GitHub, beware that their renderer does not
   render the ReStructuredText files correctly and content may be missing.

.. toctree::
    :maxdepth: 2
    :caption: Introduction
    :name: introduction
    :hidden:
    :titlesonly:

    introduction_overview
    introduction_installation

.. toctree::
    :maxdepth: 2
    :caption: Apps
    :name: apps
    :hidden:
    :titlesonly:

    apps_containers
    apps_containertemplates

.. toctree::
    :maxdepth: 2
    :caption: Administration
    :name: administration
    :hidden:
    :titlesonly:

    administration_periodic_tasks

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
