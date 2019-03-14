# https://dev.to/bettyes/my-first-shiny-docker-image-1jp7
#build an image on top of the base image for r version 3.5.1 from [rocker] (https://hub.docker.com/r/rocker/r-ver/~/dockerfile/)
FROM rocker/r-ver:3.5.1 
#install necessary libraries
RUN R -e "install.packages(c('ggplot2','shiny'))"

#copy the current folder into the path of the app
COPY . /usr/local/src/app
#set working directory to the app
WORKDIR /usr/local/src/app

#set the unix commands to run the app
CMD ["Rscript","app_run.R"]
