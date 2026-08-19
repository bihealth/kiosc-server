#!/usr/bin/env -S Rscript --vanilla

library(seaPiper)

example_dir <- system.file("extdata/example_pipeline", package="Rseasnap")
config_file <- file.path(example_dir, "DE_config.yaml")
pip <- Rseasnap::load_de_pipeline(config_file=config_file)
spd <- seapiperdata_from_rseasnap(pip)
app <- seapiper(spd)
shiny::runApp(app, host="0.0.0.0", port=8080)
