.. _apps_containers_volumes:

Container Volumes
=================

Starting from v0.5.3, each container is given a persistent `Docker
volume <https://docs.docker.com/engine/storage/volumes/>`__ which can be used for
persistent storage. The volume is mounted at `/kiosc`, and the container can
read or write files in this path at will. The next time the container starts up,
the files will still be there.
