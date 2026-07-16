FROM ghcr.io/cirruslabs/flutter:3.44.6 AS build

WORKDIR /app
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get
COPY . .

ARG API_BASE_URL
ARG META_APP_ID
ARG META_API_VERSION=v23.0
ARG META_REDIRECT_URI
RUN flutter build web --release \
    --dart-define=API_BASE_URL=${API_BASE_URL} \
    --dart-define=META_APP_ID=${META_APP_ID} \
    --dart-define=META_API_VERSION=${META_API_VERSION} \
    --dart-define=META_REDIRECT_URI=${META_REDIRECT_URI}

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build/web /usr/share/nginx/html
EXPOSE 8080
