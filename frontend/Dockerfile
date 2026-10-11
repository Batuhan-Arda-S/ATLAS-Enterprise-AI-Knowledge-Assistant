FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build


FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

RUN mkdir -p /var/cache/nginx /var/run \
    && chown -R nginx:nginx /var/cache/nginx /var/run /usr/share/nginx/html \
    && sed -i 's#pid        /run/nginx.pid;#pid /tmp/nginx.pid;#; /^user  nginx;$/d' /etc/nginx/nginx.conf

USER nginx

EXPOSE 8080

CMD ["nginx","-g","daemon off;"]
