.. _introduction_docker:

Basic Docker concepts for beginners
===================================

This chapter is meant to provide a quick introduction to Docker and Docker
Compose so that you can start using Kiosc right away even if you are not
familiar with container technologies. If you have already mastered these topics,
feel free to skip to the next chapter.

Docker containers and images
----------------------------

`Docker <https://www.docker.com>`__ is a program that allows running
applications and their dependencies in a controlled and isolated environment.
It is useful to strictly control the application and has a number of advantages
over installing the application directly:

- Avoid accidentally deleting important files from your computer;
- Running different versions of the same program at the same time;
- Making sure that the application cannot interfere with your own programs or
  other Docker applications;
- Packaging an application and all its dependencies in a single object that can
  be shared and directly run on any computer.

Docker calls these isolated application *containers*. They are similar to a
virtual machine, except that they are much more lightweight since they share
most of the operating system with the host machine. Before running a container,
the application and all the files it requires (including software libraries)
must be packaged into a single object, which Docker calls *images*. An image
is a package (think of it as a ZIP archive) which contains everything that
is necessary to run the app. The Docker program is able to create and run a
container from the image; thus, a container is simply an isolated application
running on your machine, while an image is the package that contains the files
needed by the application.

If you have some knowledge of Linux and can run commands at the terminal, the
following snippet shows how you can run a Docker container (assuming that
Docker is already installed). It will run a demo container that just prints
a "hello world" message. If the image is not available locally, it will be
downloaded first.

.. code-block:: bash

    docker run hello-world

Expert Docker wizards can create images by writing text files which specify all
the files that are part of the application. Regular users can then download
these images on their computer and run the applications as containers. This
is precisely what Kiosc does behind the scenes: it downloads existing images
and orchestrates the containers. The advantage of Kiosc is that we can do
it from a simple web interface without knowing anything about Docker or web
administration.

Further reading
^^^^^^^^^^^^^^^

- `<https://docs.docker.com/get-started/>`__

Docker Compose
--------------

In order to install and administer a Kiosc instance, a basic knowledge of
``docker compose`` is required. This section gives an introduction to this
topic.

Many applications rely on other applications to function properly. For
example, a web service may require a data base, in addition to the main app.
In principle, you could create a container that contains both the app and the
data base, but in practice it's more convenient to run two separate containers
and allow them to communicate. Normally, each container would be isolated from
the others and from the host machine, but the Docker program is also able to
run two or more containers at the same time, in a way that they can share
some resources and communicate with each other. Docker Compose simplifies
this process. The application developers can write a file, typically called
`docker-compose.yml`, which specifies all the containers that need to run at the
same time and how they should interact. You, as the user, can simply download
the `docker-compose.yml` file and run::

    docker compose up

This will instruct Docker to download all the images and start all the
containers necessary for the application. Finally, you can simply use the
application. If it is a web application, as in the case of Kiosc, you should
be able to access it from your browser by connecting to a specific port (the
application developer must tell you how to do it exactly).

Further reading
^^^^^^^^^^^^^^^

- `<https://docs.docker.com/compose/gettingstarted/>`__

Docker registries
-----------------

A Docker image can be either built from scratch or downloaded from a registry.
Thus, a registry is a storage space from which Docker images are downloaded.
The most popular registry is `Docker Hub <hub.docker.com>`__, which hosts the
official Docker images for many projects, including the *hello-world* in the
example above. By default, ``docker run <image name>`` will download the image
from Docker hub if it's not already available locally. If you want to use an
image from a different registry, you can do so by specifying the registry name
along with the image, for example ``docker run quay.io/<image name>`` will use
quay.io instead of Docker Hub.

Some registries require authentication. Running ``docker login <registry name>``
will prompt you to enter your credentials, which will be stored in a file in
your home directory so that you won't have to enter them every time.

If you build your own Docker image and want to make it available to others,
you can upload it to a registry with the ``docker push <image name>`` command.
Normally, before you can push an image, you must have an account on the registry
and you need to tag the image in a special way which depends on the registry.
In general, the steps to push an image to a registry are as follows::

    # Log in to the registry (only the first time)
    docker login <registry name>
    # Tag the image with the registry name
    docker image tag <existing image name> <registry name>/<image name>
    # Push the image
    docker push <registry name>/<image name>

Starting from v0.6.0, Kiosc hosts its own Docker registry, so you can store your
images privately. Head to the :ref:`custom registry chapter <apps_registry>` to
learn how to use the Kiosc registry.

Further reading
^^^^^^^^^^^^^^^

- `<https://docs.docker.com/get-started/introduction/build-and-push-first-image/>`__

Conclusion
----------

Now that you are familiar with Docker, you can proceed with the
:ref:`installation of Kiosc <introduction_installation>`.
