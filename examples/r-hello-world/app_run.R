# https://dev.to/bettyes/my-first-shiny-docker-image-1jp7

require(shiny) #loads shiny package
shiny::runApp("app.R", launch.browser = FALSE, port = 8080, host = "0.0.0.0") #runs shiny app in port 8080 localhost
