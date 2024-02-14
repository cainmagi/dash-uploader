ARG BASE_IMAGE=nikolaik/python-nodejs:python3.9-nodejs21-slim
FROM $BASE_IMAGE

# Set configs
ARG INSTALL_MODE=default
# The following args are temporary but necessary during the deployment.
# Do not change them.
ARG DEBIAN_FRONTEND=noninteractive

# Force the user to be root
USER root

WORKDIR /app
COPY ./docker/install* /app/
COPY ./assets /app/assets
COPY ./dash_uploader /app/dash_uploader
COPY ./devscripts /app/devscripts
COPY ./docs /app/docs
COPY ./tests /app/tests
COPY ./*.* /app/
COPY ./NAMESPACE /app/NAMESPACE

# Install dependencies
RUN bash /app/install.sh $INSTALL_MODE

COPY ./docker/entrypoint.sh /app/

ENTRYPOINT ["/bin/bash", "--login", "/app/entrypoint.sh"]
CMD [""]
