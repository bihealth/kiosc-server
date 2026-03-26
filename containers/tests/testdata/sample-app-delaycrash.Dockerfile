FROM alpine:latest

CMD ["/bin/sh", "-c", "sleep 10 && INEXISTING_COMMAND --should-fail"]
