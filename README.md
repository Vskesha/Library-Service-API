# Library-Service-API
Library where you can borrow books and pay for your borrowings using cash, depending on how many days it takes you to read the book

## Problems solved

In a local library, all book tracking and payments are handled manually. There's no way to check inventory, no online payment support, and no system to track overdue returns. This project solves those problems by implementing a fully functional REST API that:

- Manages book inventory
- Handles user borrowings
- Processes payments via Stripe
- Sends notifications via Telegram
- Supports admin and user roles
- Requires no frontend — fully browsable via 

## 🚀 Technologies Used

- Python 3.11
- Django 5.2.6
- Django REST Framework
- PostgreSQL
- Stripe API
- Telegram Bot API
- Celery
- Docker
- Coverage
- Swagger documentation

## ⚙️ Installation

```
git clone https://github.com/your-username/library-service-api.git
cd library-service-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## 🐳 Docker setup

```
docker-compose up --build
```

## 🔐 Authentication

Use these tokens in headers:

## 📑 API Documentation

Swagger (link will be inserted later)

Documentation is auto-generated via drf-yasg. Custom actions include inline descriptions.

## 🧪 Testing & Coverage

will add when completed

## 🛡 Library Rules

Cannot borrow if book inventory is 0

Cannot borrow if user has pending payments

Cannot return a book twice

Fine is calculated for overdue returns:
    fine = overdue_days * daily_fee * FINE_MULTIPLIER
