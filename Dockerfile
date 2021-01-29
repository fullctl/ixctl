FROM python:3.7-alpine as base

ARG virtual_env=/venv
ARG install_to=/srv/ixctl
ARG build_deps=" \
    postgresql-dev \
    g++ \
    libffi-dev \
    libjpeg-turbo-dev \
    linux-headers \
    make \
    openssl-dev \
    "
ARG run_deps=" \
    postgresql-libs \
    "
# env to pass to sub images
ENV BUILD_DEPS=$build_deps
ENV RUN_DEPS=$run_deps
ENV IXCTL_HOME=$install_to
ENV VIRTUAL_ENV=$virtual_env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV POETRY_VERSION=1.1.4


# build container
FROM base as builder

RUN apk --update --no-cache add $BUILD_DEPS

# create venv
RUN pip install -U pip

# pipenv install
# RUN pip install -U pipenv

# poetry install
RUN pip install "poetry==$POETRY_VERSION"
RUN python3 -m venv "$VIRTUAL_ENV"

WORKDIR /build

# PipFile install
# COPY Pipfile* ./
# RUN pipenv install --dev --ignore-pipfile

# individual files here instead of COPY . . for caching
COPY pyproject.toml poetry.lock ./

RUN . "$VIRTUAL_ENV"/bin/activate && poetry install --no-root --no-dev

COPY Ctl/VERSION Ctl/

#### final image

FROM base as final

ARG uid=5002
ARG USER=acctsvc

# extra settings file if needed
# TODO keep in until final production deploy
ARG COPY_SETTINGS_FILE=src/ixctl/settings/dev.py

# add dependencies
RUN apk add $RUN_DEPS

RUN adduser -Du $uid $USER

WORKDIR $IXCTL_HOME
# This stays the same
COPY --from=builder "$VIRTUAL_ENV" "$VIRTUAL_ENV"



RUN mkdir -p etc locale media static
COPY Ctl/VERSION etc/
COPY docs/ docs

RUN chown -R $USER:$USER locale media

#### entry point from final image, not tester
FROM final

COPY src/ main/
COPY Ctl/docker/entrypoint.sh .

RUN . "$VIRTUAL_ENV"/bin/activate

RUN ln -s $IXCTL_HOME/entrypoint.sh /entrypoint
RUN ln -s /venv $IXCTL_HOME/venv

COPY Ctl/docker/django-uwsgi.ini etc/
COPY Ctl/docker/manage.sh /usr/bin/manage


ENV UWSGI_SOCKET=127.0.0.1:6002

USER $USER

ENTRYPOINT ["/entrypoint"]
CMD ["runserver", "127.0.0.1:8000"]
