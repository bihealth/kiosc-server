.. _introduction_overview:

Overview
========

.. image:: figures/introduction/overview/logo.png
  :alt: Logo

General Idea
------------

Kiosc was developed to share analysis results with customers
and collaborators that are best displayed using an app – an interactive
client-side tool that is based on a webserver. The idea was to bundle the
webserver in a custom-build Docker image with an application of
choice.  Upon starting, the container loads the data by setting the
environment variables or passing a parameter to the command when starting
the Docker container.

Kiosc takes the role of providing functionality to create, configure,
manage and control Docker containers from such Docker images, allowing to
set up the environment variables or the start command of the container, and
to give access to the web interface of the container using a reverse proxy.
Technically, Kiosc can be used to pull and start any Docker image, however,
one would not benefit from that as it is specifically designed for Docker
images hosting a web server.

A typical workflow scheme is then as follows:

1. Kiosc launches a previously configured docker container
2. The container downloads and initializes necessary data objects and starts a web server on a
   specified port serving the preconfigured app
3. Kiosc allows the access to the webserver via reverse proxy.
4. Users can navigate to the app served by the container from the Kiosc
   entry page.

SODAR Universe
--------------

Kiosc is based on the SODAR core framework and be linked to an upstream SODAR instance
to receive projects, users and role assignments. Based on the project information,
Docker containers can be created from available Docker images and shared with collaborators
and customers.

Technical Description
---------------------

- Docker environment
- Technical description of networks
- Reverse proxy
