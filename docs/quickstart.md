# IXCTL

## Quickstart

Ixctl requires `pipenv` to manage the python environment

```sh
pip install pipenv
```

```sh
git clone git@github.com:20c/ixctl
cd ixctl
pipenv install --dev
pipenv shell
cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py createcachetable
python manage.py ixctl_peeringdb_sync
python manage.py runserver 0.0.0.0:8000
```

## Notable env variables

- `SECRET_KEY`
- `DATABASE_ENGINE`
- `DATABASE_HOST`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`

## Routeserver config generation

Routeserver configs are generated using [https://github.com/pierky/arouteserver](arouteserver)

Pipenv will have installed all the necessary libraries, but you still need to run the
initial setup for it.

```sh
arouteserver setup
```

Afterwards you can run the following command regenerate the routeserver config for any ixctl routeserver entries that have outdated configs.

```sh
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
```
