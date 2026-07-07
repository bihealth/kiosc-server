.. _apps_registry:

Registry
========

.. versionadded:: 0.6.0
    The registry Django app interfaces with a custom registry hosted behind Kiosc.
    It has two functions: acting as a proxy to the registry and triggering events
    based on events concerning the registry. In practice, it allows Kiosc to act as
    a Docker registry to which users can push their images, after authenticating
    with their own Kiosc credentials. When a new Docker image is pushed to a
    project, the corresponding container object is created.

Pushing an image to the Kiosc registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Kiosc acts as a regular Docker registry to which you can authenticate, push
images, and pull images using standard Docker clients. First, you will need to
authenticate to the registry using your user's name and password. Access through
Single Sign-On (SSO) is not supported yet. To be concrete, let's assume that a
Kiosc instance with custom registry is available at the url ``kiosc.acme.org``,
to which you have access as a user called ``alice``. For this tutorial, we also
assume that you use the ``docker`` command line tool from a Linux terminal. The
first time, you can authenticate to the registry by running

.. code-block:: bash

    docker login kiosc.acme.org

You will be prompted to enter you username (``alice``, or, possibly,
``alice@SOMEDOMAIN`` if your instance uses LDAP with multiple domains) and
password. The credentials will be cached to a file in your home directory, but
you can optionally configure a keyring or password manager. If everything went
well, you will see a "Login Succeeded" message.

Before pushing your image, you need to tag it with the appropriate registry and
project information. You can do so either when you build the image, by supplying
the ``-t <tag>`` command line option, or afterwards, with the ``docker image
tag`` command. The image tag must follow this scheme::

    <kiosc url>/<project uuid>/<image name>:<image version>

For example, suppose that you just built an image called ``seaPiper:v6.1``. If you run

.. code-block:: bash

    docker image ls

you should see a line similar to the following::

    seaPiper:v6.1                            a8cde0290af1       12.9MB         3.85MB

At this point you can tag the image. Each image must be tagged with the
project ID to which it belongs, and your user must have a role with sufficient
permissions to create containers in that project. For example, suppose
that alice is the owner of a project titled "RNASeq Pipelines" with ID
``4850f861-571e-4416-ae48-65a23012490e`` (the project ID can be found by looking
at the URL when browsing the project detail page from the Kiosc web interface).
Then, you would tag the image as follows::

    docker image tag seaPiper:v6.1 kiosc.acme.org/4850f861-571e-4416-ae48-65a23012490e/seaPiper:v6.1

The image name and version can be changed, the important parts are the registry
name and the project ID.

After tagging the image, you can finally push it to Kiosc::

    docker push kiosc.acme.org/4850f861-571e-4416-ae48-65a23012490e/seaPiper:v6.1

You should see progress bars for the various layers being uploaded, and finally
a success message.

Automatic creation of container objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Under the hood, the registry notices when an image is pushed, and informs
the Kiosc web server. This is implemented through `registry notifications
<https://distribution.github.io/distribution/about/notifications/>`__, with
Kiosc itself as an endpoint.

Thus, when an image is pushed, the corresponding container object is created
automatically in the appropriate project. This is why you need to tag the image
with the project ID (as well as for security reasons: you shouldn't be able to
overwrite images belonging to other users). The title of the new container will
be the image name and version.

After pushing the image, go to the Kiosc web interface and browse to your
project. You should see the new container, which in principle can be started
immediately. However, since Kiosc is not able to infer the container's
configuration, you should double check by clicking on the "Update container"
button and modifying any values as appropriate. For example, you may need to
set the container port, command, and/or environment variables. Note that the
"repository" field reads ``<project uuid>/<image name>``.

Re-using containers from the Kiosc registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once a container is in the Kiosc registry, it can be used in Kiosc, but
only from the project it was tagged with. The container object should be
automatically created when you push the image to the registry, but you can
re-use a container from the registry by using a special convention for the
"repository" field when you create a new container object in the Kiosc web
interface: write the repository as ``<project uuid>/<image name>``, and the
image will be pulled from the Kiosc private registry. Note that the container
must be in the project for which it's tagged.
