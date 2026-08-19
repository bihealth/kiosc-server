# Use a miniconda base image
FROM continuumio/miniconda3:24.9.2-0

ENV JUPYTER_BASE_URL=""

# Create a regular user and work under the /app directory
# (running the notebook as root is not recommended)
RUN useradd -r -m -d /app jupyter
USER jupyter
WORKDIR /app

# Import the conda environment from a yaml file
# (assuming that you previously ran `conda env export > my_conda_env.yaml`)
COPY ./my_conda_env.yaml ./
RUN conda env create -f my_conda_env.yaml -n my_conda_env

# Add the data and notebook files to the image
COPY ./my_data_file.tsv ./
COPY ./my_notebook.ipynb ./

# Run CMD from the default conda environment
# (replace `my_conda_env` with the name of your environment)
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "my_conda_env"]

# Configure the exposed port
EXPOSE 8888

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
        --ServerApp.trust_xheaders=true \
        my_notebook.ipynb" \
]
