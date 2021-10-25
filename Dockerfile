ARG bgpq4_version=0.0.6

FROM python:3.9-alpine as base

ARG virtual_env=/venv
ARG install_to=/srv/service
ARG build_deps=" \
    postgresql-dev \
    g++ \
    git \
    libffi-dev \
    libjpeg-turbo-dev \
    linux-headers \
    make \
    openssl-dev \
    curl \
    git \
    "
ARG run_deps=" \
    libgcc \
    postgresql-libs \
    "

# env to pass to sub images
ENV BUILD_DEPS=$build_deps
ENV RUN_DEPS=$run_deps
ENV IXCTL_HOME=$install_to
ENV VIRTUAL_ENV=$virtual_env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# build container
FROM ghcr.io/fullctl/fullctl-builder-alpine:prep-release as builder
ARG bgpq4_version

WORKDIR /build

# poetry install
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY Ctl/VERSION Ctl/


#### final image

FROM base as final

ARG uid=5002
ARG USER=fullctl

# extra settings file if needed
# TODO keep in until final production deploy
ARG COPY_SETTINGS_FILE=src/ixctl/settings/dev.py

# add dependencies
RUN apk add $RUN_DEPS

RUN adduser -Du $uid $USER

WORKDIR $IXCTL_HOME

COPY --from=builder "$VIRTUAL_ENV" "$VIRTUAL_ENV"

RUN mkdir -p etc locale media static
COPY Ctl/VERSION etc/
COPY docs/ docs

# XXX
# COPY ars_config/ /root/arouteserver

#RUN Ctl/docker/manage.sh collectstatic --no-input

RUN chown -R $USER:$USER locale media

#### entry point from final image, not tester
FROM final

#  XXX ARG USER=fullctl

COPY src/ main/
COPY Ctl/docker/entrypoint.sh .

RUN ln -s $IXCTL_HOME/entrypoint.sh /entrypoint
RUN ln -s /venv $IXCTL_HOME/venv

COPY Ctl/docker/django-uwsgi.ini etc/
COPY Ctl/docker/manage.sh /usr/bin/manage


#ENV UWSGI_SOCKET=127.0.0.1:6002

USER $USER

ENTRYPOINT ["/entrypoint"]
CMD ["runserver"]
