FROM alpine:latest

CMD ["sh", "-c", "for s in `seq 1 10000`; do echo $s; sleep .2; done"]
