# IXCTL

## Quickstart

To get a local repo and change into the directory:
```sh
git clone git@github.com:20c/ixctl
cd ixctl
```
Ixctl is containerized with Docker. First we want to copy the example environment file:
```sh
cp Ctl/dev/example.env Ctl/dev/.env
```
Any of the env variables can be changed, and you should set your own secret key. If you change any of the Postgres variables, you also must configure the Postgres service in the `docker-compose.yml` file to match your changes. Then you can launch the app via: 
```sh
Ctl/dev/compose.sh build
Ctl/dev/compose.sh up
```
The compose script will automatically perform migrations. If you're starting up the app for the first time, you will want to `ssh` into the django Docker container and run a few additional commands (Do this **without** the services currently running. The best way to stop the Docker containers is `Ctl/dev/compose.sh down`).
```sh
Ctl/dev/run.sh /bin/sh
cd main
manage createsuperuser
manage createcachetable
manage ixctl_peeringdb_sync
```

## Notable env variables

- `SECRET_KEY`
- `DATABASE_HOST`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`

## Routeserver config generation

Routeserver configs are generated using [https://github.com/pierky/arouteserver](arouteserver)

Pipenv will have installed all the necessary libraries, but you still need to run the
initial setup for it.

```sh
Ctl/dev/run.sh /bin/sh
arouteserver setup
```

Afterwards you can run the following command regenerate the routeserver config for any ixctl routeserver entries that have outdated configs.

```sh
cd main
python manage.py ixctl_rsconf_generate
```

(optionally) add a cron job that does this every minute

```sh
* * * * * python manage.py ixctl_rsconf_generate
```

## API Key auth

### Method 1: HTTP Header

```
Authorization: bearer {key}
```

```
curl -X GET https://localhost/api/20c/ix/ -H "Authorization: bearer {key}"
```

### Method 2: URI parameter

```
?key={key}
```

## Generate openapi schema

```sh
python manage.py generateschema > django_ixctl/static/ixctl/openapi.yaml
cp django_ixctl/static/ixctl/openapi.yaml ../docs/openapi.yaml
```
