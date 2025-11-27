# Simple static site Dockerfile for Cloud Run
FROM nginx:alpine
COPY simple_health_check.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
