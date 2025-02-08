FROM nginx:latest

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y openssl && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /etc/nginx/ssl
RUN openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
        -out /etc/nginx/ssl/nginx-selfsigned.crt \
        -keyout /etc/nginx/ssl/nginx-selfsigned.key \
        -subj "/C=CH/ST=Lausanne/L=Lausanne/O=42School/CN=localhost"

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d