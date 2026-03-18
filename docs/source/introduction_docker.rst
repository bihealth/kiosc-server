.. _introduction_docker:

Basic Docker concepts for beginners
===================================

This chapter is meant to provide a quick introduction to docker and docker compose so that you can start using Kiosc right away even if you are not familiar with container technologies.
If you have already mastered these topics, feel free to skip to the next chapter.

Docker
------

Docker is a program that allows you to isolate certain applications so that they will still run in your machine, but they won't have access to any of your files or resources unless explicitly provided.
It is useful to strictly control the application and has a number of advantages over installing the application directly:

- Avoid accidentally deleting important files from your computer
- Running different versions of the same program at the same time
- Making sure that the application cannot interfere with your own programs or other docker applications
- Packaging an application and all its dependencies in a single object that can be shared and directly run on any computer

Docker calls these isolated application *containers*.
They are similar to a virtual machine, except that they are much more lightweight since they share most of the operating system with the host machine.
Before running a container, the application and all the files it requires (including software libraries) must be packaged into a single object, which docker calls *images*. 
An image is a package (think of it as a ZIP archive) which contains everything that is necessary to run the app.
The image can be shared and distributed to different computers.
The docker program is able to create and run a container from the image; thus, a container is simply an isolated application running on your machine, while an image is the package that contains the files needed by the application.

If you have some knowledge of Linux and can run commands at the terminal, the following snippet shows how you can run a docker container (assuming that docker is already installed).
It will run a demo container that just prints a "hello world" message.
If the image is not available locally, it will be downloaded first.

    $ docker run hello-world

Expert docker wizards can create images by writing text files which specify all the files that are part of the application.
Regular users can then download these images on their computer and run the applications as containers.
This is precisely what Kiosc does behind the scenes: it downloads existing images and orchestrates the containers.
The advantage of Kiosc is that we can do it from a simple web interface without knowing anything about docker or web administration.

Further reading
^^^^^^^^^^^^^^^

- `<https://docs.docker.com/get-started/>`__

Docker compose
--------------

In order to install and administer a Kiosc instance, a basic knowledge of ``docker compose`` is required.
This section gives an introduction to this topic.

Many applications rely on other applications to function properly.
For example, a web service may require a data base, in addition to the main app.
In principle, you could create a container that contains both the app and the data base, but in practice it's more convenient to run two separate containers and allow them to communicate.
Normally, each container would be isolated from the others and from the host machine, but the docker program is also able to run two or more containers at the same time, in a way that they can share some resources and communicate with each other.
Docker compose simplifies this process.
The application developers can write a file, typically called `docker-compose.yml`, which specifies all the containers that need to run at the same time and how they should interact.
You, as the user, can simply download the `docker-compose.yml` file and run::

    docker compose up

This will instruct docker to download all the images and start all the containers necessary for the application.
Finally, you can simply use the application.
If it is a web application, as in the case of Kiosc, you should be able to access it from your browser by connecting to a specific port (the application developer must tell you how to do it exactly).

Further reading
^^^^^^^^^^^^^^^

- `<https://docs.docker.com/compose/gettingstarted/>`__

Conclusion
----------

Now that you are familiar with docker, you can proceed with the :ref:`installation of Kiosc <introduction_installation>`.
