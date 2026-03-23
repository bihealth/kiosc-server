.. _introduction_overview:

.. image:: figures/introduction/overview/logo.png
  :align: center
  :alt: Kiosc Logo

Overview
========

General Idea
------------

In many data analysis projects it is convenient to visualize the results through an interactive web app or dashboard.
These interactive reports can then be shared with customers, collaborators, or the general public.
When projects and users start growing, creating and publishing these apps can become cumbersome.
Kiosc provides an easy way to orchestrate web apps, organize them into projects, and regulate access control.
Users can select docker containers packaging apps like `Plotly Dash <https://dash.plotly.com/>`__, `Shiny <https://shiny.posit.co/>`__, or `Quarto <https://quarto.org/docs/dashboards/>`__, and configure them to display the results of their analysis.
Kiosc runs the containers with the appropriate network configuration and acts as a proxy to the web services running inside the containers.
Using and managing Kiosc doesn't require being experts in either docker or network administration, while still scaling up to a large number of containers and users.

Users can authenticate in Kiosc through LDAP, OIDC, or local accounts created by the administrator.
Then, they create projects, sub-projects, and docker containers within the projects.
Kiosc offers functionality to create, configure, manage and control Docker containers from existing Docker images, allowing to customize the environment variable and the entrypoint command of the container.
Furthermore, Kiosc gives access to the web services running within the containers by acting as a reverse proxy and allowing access to the containers only for authorized users (public access is also an option).
Technically, Kiosc can be used to pull and start any Docker image, however, one would not benefit much from that as Kiosc is specifically designed for running interactive Docker containers hosting a web server.

A key question is how can users upload their own data in the containerized app.
At this time, Kiosc doesn't enforce a specific method, but there are several possibilities.
If the container supports it, users can pass environment variables or command-line flags pointing to the location of the data.
Alternatively, users can override the entrypoint command of the container with a custom script that downloads the data and then starts the web service.
Another possibility is to create a completely custom docker image that bundles the required data together with the web app, although this is not recommended.
Finally, users can upload small files (< 2GB) directly into Kiosc through the "Small Files" app (see :ref:`introduction_interface`).

.. At this time, Kiosc doesn't support mounting remote filesystems, but this functionality is being considered.

A typical workflow scheme is then as follows:

1. The user logs into Kiosc, navigates to a project, and adds a preconfigured docker container, which is downloaded on demand if necessary
2. Kiosc launches the container, which is expected to contain or download the user's data and spin up a web server
3. Kiosc establishes a reverse proxy to dispatch the user requests to the appropriate container
4. Authorized users can browse the container's web server from the Kiosc interface
5. Authorized users can stop, pause, restart, or delete containers, as well as checking their health status and logs

SODAR Universe
--------------

Kiosc is based on the `SODAR Core <https://github.com/bihealth/sodar-core>`__ framework and can be linked to an upstream SODAR instance to receive projects, users and role assignments.
Docker containers will only be shared with users who have access to the corresponding project.

.. Technical Description
.. ---------------------

.. - Docker environment
.. - Technical description of networks
.. - Reverse proxy
