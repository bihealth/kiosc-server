.. _introduction_cookbook:

Cookbook
========

.. contents::

Guest accessing the web interface of a container
------------------------------------------------

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

Create a container running (a) ...
----------------------------------

To create a container switch to the **Containers** app and
select **Create Container**. This will be the starting point
for the following tutorials.

After the creation of the container you will be redirected
the details of the container. The state will be set to
``initial`` which indicates that there is the container object
but no actual Docker container (yet). You can find the operations menu (cog icon)
on the top right of the details page. Open the dropdown
menu by clicking the cog icon and select **Start**, or click
the crossed-out eye icon to start and access the container directly.

Shiny application (using environment variables)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*For this tutorial we provide you with a pre-build*
`Docker image with a Shiny application <https://github.com/bihealth/kiosc-example-shiny/>`_.
*Use the linked repository as a base to create your own Docker image.*

In this example application you can learn how environment variables are set.
Fill out the following fields and click **Create**:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``ghcr.io/bihealth/kioscshinytest``
**Tag**             ``latest``
**Container Port**  ``8080``
**Environment**     ``{"title": "Kiosc Shiny App example", "dataset": "iris"}``
==================  ==================================================================

The **Environment** field should contain a `JSON object literal <https://www.w3schools.com/js/js_json_objects.asp>`_,
which corresponds to a Python dictionary with the exception that only double quotes are allowed, or nothing.

The value in the **Environment** field will be transformed and passed to the environment of
the container. In the above example, the Docker container will hold two environment variables.
Imagine that inside the container the following lines will be performed upon start::

    $ export title="Kiosc Shiny App example"
    $ export dataset=iris

The data is loaded into the container by setting the environmental variable ``dataset``.

Dash Application
^^^^^^^^^^^^^^^^

*For this tutorial we provide you with a pre-build*
`Docker image with a Dash application <https://github.com/bihealth/kiosc-example-dash/>`_.
*Use the linked repository as a base to create your own Docker image.*

Fill out the following fields and click **Create**:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``ghcr.io/bihealth/kiosc-example-dash``
**Tag**             ``master``
**Container Port**  ``8050``
==================  ==================================================================

cellxgene (using a command)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this example application you can learn how the command is used.
Fill out the following fields and click **Create**:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``quay.io/biocontainers/cellxgene``
**Tag**             ``0.16.7--py_0``
**Container Port**  ``8050``
**Command**         ``cellxgene launch https://cellxgene-example-data.czi.technology/pbmc3k.h5ad -p 8050 --host 0.0.0.0 --verbose``
==================  ==================================================================

This example takes a publicly available container and passes a command that is run
when starting the container. In this case, the cellxgene application is started
immediately when running the container. The data is loaded by passing the data
URL to the command.