# Equipment Rental Management (ERM)

A small Flask REST API for tracking equipment, renters, and rentals. Data is
stored **in memory** (plain Python objects, no database) and is reset every
time the app restarts — this project is meant to run before you've covered
databases.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The app runs at `http://127.0.0.1:5000`.

> **macOS:** the AirPlay Receiver uses port 5000. Turn it off in
> System Settings → General → AirDrop & Handoff before starting the app.

## Run with Docker

**Prerequisites:** [Docker Desktop](https://docs.docker.com/get-docker/)
(Windows/macOS) or Docker Engine (Linux). Check it with `docker --version`.

From this folder (`equipment-rental-management/`, where the `Dockerfile` is):

```bash
docker build -t cisc327-a4 .                 # build the image
docker run --rm -p 5000:5000 cisc327-a4      # run it (Ctrl+C to stop)
```

The container serves the app on port **5000**, so open
`http://127.0.0.1:5000/` the same as when running locally. To run it in the
background instead:

```bash
docker run --rm -d --name cisc327-a4 -p 5000:5000 cisc327-a4
docker stop cisc327-a4                       # stop (and remove) it
```

**Data does not persist.** The container runs the same in-memory app, so all
equipment, renters, and rentals are lost when the container stops. Every new
container starts empty.

## Web UI

Open `http://127.0.0.1:5000/` in a browser for a basic HTML front end (plain
forms and tables, no JavaScript) to add/delete equipment and renters, and
check equipment in/out:

| Page | Path |
|---|---|
| Home | `/` |
| Equipment | `/ui/equipment` |
| Renters | `/ui/renters` |
| Rentals | `/ui/rentals` |

This UI is separate from the JSON API below — it's there so you can see the
app working without a REST client, and calls the same in-memory store.

## Entities

- **Equipment**: `id, name, category, total_units, available_units`
- **Renter**: `id, name, email, membership_date`
- **Rental**: `id, equipment_id, renter_id, rental_date, due_date, return_date`

## JSON API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/equipment` | List all equipment |
| POST | `/equipment` | Add an equipment item |
| GET | `/equipment/<id>` | Get one equipment item |
| PUT | `/equipment/<id>` | Update an equipment item |
| DELETE | `/equipment/<id>` | Delete an equipment item |
| PATCH | `/equipment/<id>/status` | Mark equipment in or out of service (`is_available`) |
| GET | `/equipment/<id>/availability` | Get an item's availability summary |
| GET | `/renters` | List all renters |
| POST | `/renters` | Create a renter |
| GET | `/renters/<id>` | Get one renter |
| PUT | `/renters/<id>` | Update a renter |
| DELETE | `/renters/<id>` | Delete a renter |
| POST | `/rentals` | Check out equipment (`equipment_id`, `renter_id`); returns 400 if the item is out of service |
| PUT | `/rentals/<id>/return` | Return rented equipment |
| GET | `/rentals?renter_id=&equipment_id=&renter_name=&item_name=` | Look up rentals; all filters are optional, and names match partially and ignore case |

## Tests

```bash
pytest
```

### End-to-end (browser) tests

The Playwright tests in `tests/e2e/` drive a real browser against a running
copy of the app over HTTP, either local or in Docker.

```bash
pip install -r requirements.txt
python -m playwright install chromium

# Terminal 1: start the app, either locally or in Docker
python run.py                                # or: docker run --rm -p 5000:5000 cisc327-a4

# Terminal 2: run the tests (--headed shows the browser)
python -m pytest tests/e2e -v --headed
```

Each test creates its own data, so the tests don't need a fresh server and can
run in any order. They target `http://127.0.0.1:5000` by default; set
`E2E_BASE_URL` to use another address. If no app is running, the E2E tests are
skipped, so a plain `pytest` (as in CI) still runs only the unit tests.
