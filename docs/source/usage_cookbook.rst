.. _introduction_cookbook:

Cookbook
========

.. contents:: Contents
   :local:

Creating a project
------------------

After you log in, you should see the home page with the projects list. In Kiosc,
like in `SODAR <https://github.com/bihealth/sodar-server>`__, projects are
organized hierarchically in *categories*. A category is a directory that can
contain projects or other categories. If no project exists, you can create one
yourself within an existing category. Only an administrator with superuser
access can create top-level categories, by clicking on "Create Category" in the
left side menu.

To create a project, navigate to the desired category, then click on "Create
Project or Category" in the menu on the left side. The project page will show
you an overview of the containers, container templates, and files that belong to
this project. Initially, everything will be empty.

Accessing containers in a project
---------------------------------

If an administrator or another user have created a project, they may have given
you access to it. In Kiosc, users can have various roles in a project; check out
the :ref:`relevant documentation <introduction_roles>` for reference. If you are
a member of the project, you will be able to see the containers in that project.
Depending on your role, you may or may not be able to modify the containers,
stop them, and restart them, but you should always be able to access them. To
access the web app inside a container, browse to the project of interest, find
the container, and click on its title. You should see the container status page,
and if you click on the eye icon, you'll be redirected to the container's app.

.. image:: figures/introduction/cookbook/container_controls.png
  :alt: Container controls

The button with the eye icon also indicates the status of the container. If
they button is colored in gray and the eye is crossed-out, it means that the
container is not running. If the button is blue with an open eye, it means
that the container is running. Even if the container is not running, clicking
on the button will start it and redirect you to the web app. If you have the
appropriate role in the project, you will also see the :guilabel:`Controls`
button for changing the state of the container.

.. note::

    If the container needs to be started, it may take some time before it
    becomes available. When Kiosc says that the container is running, but
    you cannot access it, it means that the container is starting up. Please
    be patient and come back after several minutes. If, after one hour, the
    container is still inaccessible, report this to the project owner or the
    container developer.

Controlling containers
----------------------

A Docker container can be in different states, and this is reflected in Kiosc.

- **Initial**: The image was just downloaded and the container has not been
  started for the first time yet.
- **Running**: The container is running. Note that this does not mean that you
  can access the app, since the container may need some time to download data
  before starting the app.
- **Paused**: The processes inside the container are sleeping and do not consume
  resources, but can be restarted at any time.
- **Exited**: The container has been stopped by a user. It can be restarted at
  any time.
- **Terminated**: If the app is not accessed by anyone for a long time, it is
  stopped automatically. It can be restarted at any time. The inactivity timeout
  can be chosen when creating or updating the container.
- **Failed**: Something went wrong inside the container, you should report this
  error to the container's authors.

Controlling a container means changing its state, and your user needs to have
the appropriate permission to do so. In Kiosc, there are three places where
containers can be managed. One is the container detail page, as shown in the
figure above. To access that, navigate to the corresponding project from the
home page, then click on the container title.

.. image:: figures/introduction/cookbook/containers_overview.png
  :alt: Containers overview

The second place which allows you to control the containers is the project page.
There, you will find a section called :guilabel:`Containers overview` listing all the containers belonging to that project.
By clicking on the gear icon, you will access the controls menu.

.. image:: figures/introduction/cookbook/container_list_app.png
  :alt: Container list

Finally, clicking on the user menu at the top-right corner, you'll be able to access the :guilabel:`Container List` app.
There, you will find a view similar to the Containers overview, except that it will show all your container, regardless of the project they are in.

Creating a container for...
---------------------------

This section illustrates how to create containers. For concreteness, we describe
a few real-world use cases that, in our experience, occur often in practice.

If you want to create a container, navigate to the project where you want to
have it, and make sure you have a :ref:`role <introduction_roles>` that allows
you to create containers. Switch to the :guilabel:`Containers` app

.. image:: figures/apps/containers/menu.png
  :alt: Container app

and select :guilabel:`Create Container`. This will be the starting point
for the following tutorials.

.. image:: figures/apps/containers/overview_create.png
  :alt: Project overview

At this point you can simply fill out the form with the container details.
You'll need to know the repository where the container should be downloaded
from (typically `Docker Hub <https://hub.docker.com>`__, `GitHub Container
Registry <https://ghcr.io>`__, or a similar platform). You will also need to
know the port on which the app inside the container listens to; this should
be specified in the container's documentation. If you want, you can pass
environment variables to the app or customize the command to run. The following
subsections will describe in detail how to set up a container using specific
examples.

After the creation of the container you will be redirected the details of the
container. The state will be set to ``initial`` which indicates that there
is the container object but no actual Docker container (yet). You can find
the operations menu (cog icon) on the top right of the details page. Open the
dropdown menu by clicking the cog icon and select **Start**, or click
the crossed-out eye icon to start and access the container directly.

Shiny
^^^^^

.. image:: figures/introduction/cookbook/proxy_shiny.png
  :alt: Shiny proxy

*For this tutorial we provide you with a pre-built*
`Docker image with a Shiny application <https://github.com/bihealth/kiosc-example-shiny/>`_.
*Use the linked repository as a base to create your own Docker image.*

This example sets up a simple `Shiny <https://shiny.posit.co/>`__
application loading the popular `Iris dataset
<https://www.rdocumentation.org/packages/datasets/versions/3.6.2/topics/iris>`__.
The data set is loaded by setting the ``dataset`` variable in the environment.
Fill out the following fields and click :guilabel:`Create`:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``ghcr.io/bihealth/kioscshinytest``
**Tag**             ``latest``
**Container Port**  ``8080``
**Environment**     ``{"title": "Kiosc Shiny App example", "dataset": "iris"}``
==================  ==================================================================

The **Environment** field should contain a `JSON object literal
<https://www.w3schools.com/js/js_json_objects.asp>`_, which corresponds to a
Python dictionary with the exception that only double quotes are allowed, or
nothing.

The value in the **Environment** field will be transformed and passed to the
environment of the container. In the above example, the Docker container will
hold two environment variables. Imagine that inside the container the following
lines will be performed upon start::

    $ export title="Kiosc Shiny App example"
    $ export dataset=iris

Dash
^^^^

.. image:: figures/introduction/cookbook/proxy_dash.png
  :alt: Dash proxy

*For this tutorial we provide you with a pre-built*
`Docker image with a Dash application <https://github.com/bihealth/kiosc-example-dash/>`_.
*Use the linked repository as a base to create your own Docker image.*

In this example we are running a `Dash <https://dash.plotly.com/>`__
application. As we are behind a reverse proxy, the Dash application needs
some tweaks to make it load all scripts and stylesheets into the container
when started. The Dash application was extended by accepting an environmental
variable named ``PUBLIC_URL_PREFIX``, and for this to work, you have to set up
this environment variable and set it to the value ``__KIOSC_URL_PREFIX__``.
This acts as a place holder that is substituted with the path to the container
how it is known to the outside. Fill out the following fields and click
:guilabel:`Create`:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``ghcr.io/bihealth/kiosc-example-dash``
**Tag**             ``main-0``
**Container Port**  ``8050``
**Environment**     ``{"PUBLIC_URL_PREFIX": "__KIOSC_URL_PREFIX__"}``
==================  ==================================================================

The **Environment** field should contain a `JSON object literal
<https://www.w3schools.com/js/js_json_objects.asp>`_, which corresponds to a
Python dictionary with the exception that only double quotes are allowed, or
nothing.

The value in the **Environment** field will be transformed and passed to the
environment of the container. In the above example, the Docker container will
hold two environment variables. Imagine that inside the container the following
lines will be performed upon start::

    $ export PUBLIC_URL_PREFIX=containers/proxy/abcdef123...

seaPiper
^^^^^^^^

.. image:: figures/introduction/cookbook/proxy_seapiper.png
  :alt: seaPiper proxy

*For this tutorial we provide you with a pre-built*
`Docker image with a seaPiper application <https://github.com/bihealth/kiosc-seapiper-demo/>`_.
*Use the linked repository as a base to create your own Docker image.*

`seaPiper <https://bihealth.github.io/seaPiper/>`__ is an exploratory data
analysis app based on Shiny. Fill out the following fields and click **Create**:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``ghcr.io/bihealth/kiosc-seapiper-demo``
**Tag**             ``latest``
**Container Port**  ``8080``
==================  ==================================================================

CELLxGENE
^^^^^^^^^

.. image:: figures/introduction/cookbook/proxy_cellxgene.png
  :alt: CELLxGENE proxy

This example takes a publicly available container and passes a command
that is run when starting the container. In this case, the `CELLxGENE
<https://cellxgene.cziscience.com/>`__ application is started immediately
when running the container. The data is loaded by passing the data URL to the
command. Fill out the following fields and click **Create**:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``quay.io/biocontainers/cellxgene``
**Tag**             ``1.0.0--pyhdfd78af_0``
**Container Port**  ``8050``
**Command**         ``cellxgene launch https://cellxgene-example-data.czi.technology/pbmc3k.h5ad -p 8050 --host 0.0.0.0 --verbose``
==================  ==================================================================

CELLxGENE (using the files app)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: figures/introduction/cookbook/proxy_cellxgene.png
  :alt: CELLxGENE proxy

This example is the same as above but using a file uploaded to Kiosc.
A command to copy-and-paste can't be provided as the link to the file
depend on the UUID that is randomly created. To get the file into Kiosc,
download the file from the official server and upload it to Kiosc:

1. Download `example data <https://cellxgene-example-data.czi.technology/pbmc3k.h5ad>`_.
2. Go to a Kiosc project and select the :ref:`Small Files app <apps_filesfolders>`.
3. Upload the ``pbmc3k.h5ad`` file. It is now available during container creation.

Now continue with the container creation. To make use of the uploaded file, when
inserting the command, place the cursor at the mentioned position in the command,
select the file and click :guilabel:`Insert`.

.. image:: figures/introduction/cookbook/file_insert.png
  :alt: Insert file

This will place a link at the cursor position.

.. image:: figures/introduction/cookbook/file_inserted.png
  :alt: Inserted file

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``quay.io/biocontainers/cellxgene``
**Tag**             ``1.0.0--pyhdfd78af_0``
**Container Port**  ``8050``
**Command**         ``cellxgene launch <PLACE_CURSOR_HERE_BEFORE_INSERTING_FILE> -p 8050 --host 0.0.0.0 --verbose``
**Files**           ``/pbmc3k.h5ad``
==================  ==================================================================

ScElvis
^^^^^^^

.. image:: figures/introduction/cookbook/proxy_scelvis.png
  :alt: ScElvis proxy

This example sets up the `ScElvis
<https://scelvis.readthedocs.io/en/latest/>`__, a single cell visualization tool
based on Dash. For this to work, you have to set up two environment variables,
``SCELVIS_URL_PREFIX`` helps the application alter the URL path to load scripts
and style sheets into the container and ``SCELIVS_DATA_URL`` sets the data that
is to be loaded into the container. Fill out the following fields and click
:guilabel:`Create`:

==================  ==================================================================
**Title**           *Set a unique title that helps you identify the container easily.*
**Repository**      ``ghcr.io/bihealth/scelvis``
**Tag**             ``v0.8.6``
**Container Port**  ``8050``
**Environment**     ``{"SCELVIS_URL_PREFIX": "__KIOSC_URL_PREFIX__", "SCELVIS_DATA_SOURCES": "https://cellxgene-example-data.czi.technology/pbmc3k.h5ad"}``
**Command**         ``scelvis run``
==================  ==================================================================

The **Environment** field should contain a `JSON object literal <https://www.w3schools.com/js/js_json_objects.asp>`_,
which corresponds to a Python dictionary with the exception that only double quotes are allowed, or nothing.

The value in the **Environment** field will be transformed and passed to the environment of
the container. In the above example, the Docker container will hold two environment variables.
Imagine that inside the container the following lines will be performed upon start::

    $ export SCELVIS_URL_PREFIX=containers/proxy/abcdef123...
    $ export SCELVIS_DATA_SOURCES=https://cellxgene-example-data.czi.technology/pbmc3k.h5ad

In addition to the user defined variables, the ``title``, ``description`` and
``container_port`` are also exposed as environment variables to the Docker container
(as ``TITLE``, ``DESCRIPTION`` and ``CONTAINER_PORT`` respectively)::

    $ export TITLE="Some unique title"
    $ export DESCRIPTION="Some description"
    $ export CONTAINER_PORT=8050

Jupyter Notebooks
^^^^^^^^^^^^^^^^^

.. versionadded:: 0.6.2

.. image:: figures/introduction/cookbook/proxy_jupyter.png
   :alt: Jupyter notebook proxy

`Jupyter notebooks <https://jupyter.org/>`__ are interactive reports
that combine code, equations, narrative text, and visualizations. Due to
the limitations outlined below, we recommend to always try and export
the notebook to HTML if possible (check out the `relevant docuementation
<https://jupyterlab.readthedocs.io/en/stable/user/export.html>`__), since
serving a static HTML file on Kiosc is trivial and safe. If your notebook uses
interactive widgets, or for some reason cannot be rendered to HTML, you can
still publish it on Kiosc, but you should be aware of the limitations.

*The resources of the Kiosc server are limited and shared with other users.*
In particular, you should avoid running notebooks that require a large amount
of RAM or run very long computations. Instead, use an HPC cluster to process
the data, export the final results to a file, and only run lightweight
visualizations tasks in the notebook.

*Anyone who has access to the notebook can execute arbitrary code.* The notebook
runs in an isolated environment, but security vulnerabilities must be taken into
account. Therefore, only share the notebook with people you trust, and never
make it publicly available.

*Containers are killed after a period of inactivity.* In Kiosc, if nobody
accesses the container for a few days (7 by default), the container will be
terminated, so that all computations in the notebook may be lost.

If you understand and accept these limitations, here is how to set up a Jupyter
container for Kiosc. At this time, we do not provide a stock Docker container
for Jupyter, as each notebook may have different requirements for environments
and data, and we are still figuring out the most common use cases. Thus, you
will have to write a custom Dockerfile (please reach out to your friendly
neighborhood Kiosc admin for help). Here is a template Dockerfile that uses a
conda environment and copies the data file directly inside the Docker image.
This is not recommended when the data is large, as it leads to heavy containers.

.. code-block:: dockerfile

    # Use a miniconda base image
    FROM continuumio/miniconda3:24.9.2-0

    # Set the default base_url for Jupyter
    ENV JUPYTER_BASE_URL=""

    # Create a regular user and work under the /app directory
    # (running the notebook as root is not recommended)
    RUN useradd -r -m -d /app jupyter
    USER jupyter
    WORKDIR /app

    # Import the conda environment from a yaml file
    # (assuming that you previously ran `conda env export > environment.yaml`)
    COPY ./environment.yaml ./
    RUN conda env create -f environment.yaml -n my_conda_env

    # Add the data and notebook files to the image
    COPY ./my_data_file.tsv ./
    COPY ./my_notebook.ipynb ./

    # Run CMD from the default conda environment
    ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "my_conda_env"]

    # Configure the exposed port
    EXPOSE ["8888"]

    # Run Jupyter with the appropriate arguments for Kiosc
    # (replace `my_notebook.ipynb` with the path to your notebook)
    CMD [ \
        "/bin/bash", "-c", \
        "jupyter notebook \
            --ip=0.0.0.0 \
            --port=8888 \
            --no-browser \
            --ServerApp.base_url=$JUPYTER_BASE_URL \
            --ServerApp.allow_origin='*' \
            --ServerApp.allow_remote_access=true \
            --ServerApp.allow_unauthenticated_access=true \
            --ServerApp.disable_check_xsrf=true \
            --ServerApp.token='' \
            --ServerApp.trust_xheaders=true" \
    ]

Your mileage may vary, but this should be a reasonable starting point. Note
that the command line flags for the jupyter notebook command are all required.
``$JUPYTER_BASE_URL`` is an environment variable which stands for the full
path of the proxy to the container. This is needed because the Jupyter server
uses absolute paths for its redirects and static files. Using the environment
variable lets Jupyter know the correct URL at which it should listen. After
building the container, you can push it to the Kiosc registry (see the commands
below). A container will be automatically created in Kiosc with your container's
name as title. To build and push the container you can use these commands, after
replacing the values between ``<angle brackets>`` with appropriate values.

.. code-block:: bash

    # Build the container
    docker buildx build -t <kiosc url>/<project uuid>/<image name>:<image version>

    # Push it to Kiosc
    docker login <kiosc_url>
    docker push <kiosc url>/<project uuid>/<image name>:<image version>

You can of course also create the container manually, if you push your image to
a different container registry available on the internet. After creating the
container in Kiosc, you must click on "Update container" and modify, at a minimum,
the fields in thefollowing table:

==================  ==================================================================
**Container Port**  ``8888``
**Container Path**  ``__KIOSC_URL_PREFIX__/notebooks/my_notebook.ipynb``
**Environment**     ``{"JUPYTER_BASE_URL": "__KIOSC_URL_PREFIX__"``
==================  ==================================================================

Do not replace ``__KIOSC_URL_PREFIX__``: it is a special string that tells the
Kiosc proxy to forward the full absolute path to this container, instead of the
relative one.
