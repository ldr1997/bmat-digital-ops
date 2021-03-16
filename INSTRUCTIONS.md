# User Manual for Server

## I. Running the Server

> NOTE: Make sure you have Docker installed.

### 1. Run with `docker-compose`:

```bash
docker-compose up -d
```

This will load up a Python container (ver 3.9) and install the necessarily dependencies using `pipenv`.


### 2. Migrate

```bash
docker exec -it <container_name> python manage.py migrate
```

> NOTE: Look for the container name using `docker container ls`.

### 3. Create a Superuser

In order to access the Admin page, you will need superuser access:

```bash
docker exec -it <container_name> python manage.py createsuperuser
```

It will ask you to input a username, email, and password.

## II. Loading Data Into the Server

The sample data provided is located in [`data/`](data/).

A loading script ([`dsrs/management/commands/load.py`](dsrs/management/commands/load.py)) reads the contents of each file, parses territory and currency codes, applies currency conversion, and loads the data onto the built-in database of this server. This script automatically loads DSR data if its `status` field is `"failed"`, or if it doesn't exist in the DSR table.

There are **two** ways to access this script:

### 1. Django Management

```bash
docker exec -it <container_name> python manage.py load
```

### 2. Admin Page

Under [`http://localhost:8000/admin/dsrs/dsr/`](http://localhost:8000/admin/dsrs/dsr/), click the "**Reload DSRs**" button. More info about the Admin page is detailed below.

## III. API Endpoints

The API endpoints provided are specified in [`openapi.md`](openapi.md). There are 3 endpoints:

1. `GET /dsrs/` - List all DSRs in the repository in JSON format.
2. `GET /dsrs/{id}` - Display details of the DSR with ID number `{id}`.
3.  `GET /resources/percentile/{number}` - Get the TOP percentile by revenue for `{number}`%. The query contents for this are the ff:
    - `territory` - Territory code. ES, FR..
    - `period_start` - Datetime of the starting date of the associated DSRs
    - `period_end` - Datetime of the ending date of the associated DSRs.

### Testing API Endpoints

The built-in Django testing framework was used to test possible scenarios of each API endpoint.

To run the tests, simply run:

```bash
docker exec -it <container_name> python manage.py test
```

> NOTE: To run the tests in verbose mode, append "`-v 2`" to the command.

## IV. Managing Data

The data can be accessed in the Admin page ([`http://localhost:8000/admin`](http://localhost:8000/admin)). You may view, edit, create, and delete objects thanks to Django's built-in admin capabilities.

Some additional functionality was added to the DSR page at [`http://localhost:8000/admin/dsrs/dsr/`](http://localhost:8000/admin/dsrs/dsr/).

### 1. Loading DSR Data

As mentioned above, the Admin has the ability to re-scan and reload DSR data by clicking on the "**Reload DSRs**" button.

### 2. Viewing DSR Contents

To view the resources listed under a certain DSR, click on the "**View DSR**" field located on the rightmost column of the entry. This will redirect you to the Resources page, however the entries here are filtered to only show those under the chosen DSR.

Each resource here can be edited indivitually by clicking on its `dsp_id`.

### 3. Deleting DSRs

The admin can delete a DSR along with all of its contents by clicking on the "**Delete**" button (next to "**View DSR**"). This will also delete all resources linked to that DSR.

> NOTE: If a resource is linked to multiple DSRs, it will stay in the database until all DSRs linked to it are also removed.
