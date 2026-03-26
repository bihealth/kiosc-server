FROM nginx:latest

RUN echo "<h1>Hello World</h1>" > /usr/share/nginx/html/index.html

ENTRYPOINT ["/bin/sh", "-c", "sleep 10 && /docker-entrypoint.sh nginx -g 'daemon off;'"]
