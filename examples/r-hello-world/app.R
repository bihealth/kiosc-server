# https://dev.to/bettyes/make-your-code-shiny--598d

library(shiny)
library(ggplot2)
ui <- fluidPage(
 h1("Some iris data visualised"),br(),
  fluidRow(
    column(4,
        wellPanel(
          sliderInput("bin", "Binwidth:",
            min = 0.1, max = 1, value = 1)
    )),
    column(8,
      tabsetPanel(
        tabPanel("Plot",plotOutput("IrisPlot")),
        tabPanel("Summary",verbatimTextOutput("IrisSummary")),
        tabPanel("Table",tableOutput("IrisTable"))
    ))
 ),
 fluidRow(
    column(4,
      checkboxGroupInput("Species", label = "Select Species",
        choices = list("Iris setosa" = "setosa", 
          "iris versicolor" = "versicolor",
          "iris verginica" = "virginica"),
          selected = 1)),
    column(8,plotOutput("IrisPlot2"))
 )
)

   server <- function(input, output) {
     output$IrisPlot <- renderPlot({
        ggplot(iris)+geom_histogram(aes(Sepal.Length,     fill=Species),binwidth=input$bin, colour="white")+facet_wrap(~Species)
     })
 output$IrisSummary <- renderPrint({summary(iris)})
 output$IrisTable <-renderTable(iris)

output$IrisPlot2 <- renderPlot({
   ggplot(iris[iris$Species==input$Species,])+geom_point(aes(Sepal.Length,     Sepal.Width,color=Species))
 })
}

shinyApp(ui = ui, server = server)
