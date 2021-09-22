.. _introduction_overview:

Overview
========

General Idea
------------

Kiosc was developed to share analysis results with customers
and collaborators that are best displayed using an interactive
tool that is based on a webserver. The idea was to bundle the
webserver in a custom build Docker image with an application of
choice, and upon starting, the container loads the data by setting the
environment variables or passing a parameter to the command when starting
the Docker container. Kiosc now takes the roll of providing functionality to create
and control Docker containers from such Docker images, to set the
environment variables or the start command of the container, and to
give access to the web interface of the container using a reverse proxy.
Technically, Kiosc can be used to pull and start any Docker image, however,
one would not benefit from that as it is specifically designed for
Docker images hosting a web server.

SODAR Universe
--------------

Kiosc is based on the SODAR core framework and be linked to an upstream SODAR instance
to receive projects, users and role assignments. Based on the project information,
Docker container can be created from available Docker images and shared with collaborators
and customers.

Technical Description
---------------------

- Docker environment
- Technical description of networks
- Reverse proxy