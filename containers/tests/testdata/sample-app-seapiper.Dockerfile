FROM ghcr.io/bihealth/seapiper:0.6.9

COPY seapiper-entrypoint.R .

ENTRYPOINT ["Rscript", "--vanilla", "seapiper-entrypoint.R"]
