# MyCurrency – Backend API

A Django REST Framework backend for retrieving, storing, and converting currency exchange rates using a provider–adapter architecture.

---

## Features

- CRUD for currencies and providers  
- Provider activation and priority management  
- Currency conversion (single and multi-target)  
- Historical exchange rates (sync and async)  
- Provider fallback mechanism  
- Database caching for fetched rates  
- Modular adapter system to add new providers easily  
- Django admin UI for manual conversion  
- Swagger/OpenAPI documentation  
- Unit tests included

---

## Tech Stack

- **Python 3.11**
- **Django 5.2**
- **Django REST Framework**
- **drf-spectacular**
- **SQLite** (preloaded)

---

## Setup Instructions

### 1. Clone the project

git clone https://github.com/AdamAbidi/MyCurrency.git
cd MyCurrency


### 2. Install dependencies
pip install -r requirements.txt


### 3. Run the server
python manage.py runserver



## Admin Access
* URL: http://localhost:8000/admin/
* Username: admin
* Password: admin

Database already includes:
* Providers
* Currencies
* Exchange rates

Everything works out of the box.


## API Documentation
* http://localhost:8000/api/v1/docs/


## Main API Endpoints
Currencies

* GET /api/v1/currencies/

* POST /api/v1/currencies/

Providers

* POST /api/v1/providers/{id}/toggle/

* POST /api/v1/providers/{id}/set-priority/

Exchange Rates

* GET /api/v1/exchange-rates/convert/

* GET /api/v1/exchange-rates/convert-multi/

* GET /api/v1/exchange-rates/history/

* GET /api/v1/exchange-rates/history-async/



## Unit Tests
* python manage.py test


## Adding New Providers
1. Create a provider adapter class

2. Register it in the adapter registry

3. Add a provider record with the same adapter_key

No core service logic needs modification.



## Included in This Project

* Full Django source code
* Preloaded SQLite database
* Technical design document (PDF)
* Postman collection
* README.md
