# Event & Conference Management System

## Overview

The **Event & Conference Management System** is a real-world backend application developed using **FastAPI**. It provides APIs for managing events, venues, halls, speakers, sessions, attendees, registrations, tickets, purchases, payments, bookings, check-ins, certificates, feedback, notifications, refunds, dashboards, reports, filtering, pagination, and security.

The project follows a modular architecture using separate **Models, Schemas, Repositories, Services, and Routes** without using an `app` folder.

---

## Technology Stack

* Python 3.10+
* FastAPI
* PostgreSQL
* SQLAlchemy ORM
* Pydantic
* JWT Authentication
* Passlib / Bcrypt
* Alembic
* Pytest
* Uvicorn
* CORS Middleware

---

## Project Structure

```text
event_conference_management/
│
├── main.py
├── database.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── models/
│   ├── user.py
│   ├── event.py
│   ├── venue.py
│   ├── hall.py
│   ├── speaker.py
│   ├── session.py
│   ├── attendee.py
│   ├── registration.py
│   ├── ticket.py
│   ├── purchase.py
│   ├── payment.py
│   ├── session_booking.py
│   ├── checkin.py
│   ├── certificate.py
│   ├── feedback.py
│   ├── refund.py
│   └── audit_log.py
│
├── schemas/
│   ├── user.py
│   ├── event.py
│   ├── venue.py
│   ├── hall.py
│   ├── speaker.py
│   ├── session.py
│   ├── attendee.py
│   ├── registration.py
│   ├── ticket.py
│   ├── purchase.py
│   ├── payment.py
│   ├── session_booking.py
│   ├── checkin.py
│   ├── certificate.py
│   ├── feedback.py
│   ├── refund.py
│   └── audit_log.py
│
├── repositories/
│   ├── user_repository.py
│   ├── event_repository.py
│   ├── venue_repository.py
│   ├── hall_repository.py
│   ├── speaker_repository.py
│   ├── session_repository.py
│   ├── registration_repository.py
│   ├── ticket_repository.py
│   ├── purchase_repository.py
│   ├── payment_repository.py
│   ├── refund_repository.py
│   └── audit_log_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── event_service.py
│   ├── venue_service.py
│   ├── hall_service.py
│   ├── speaker_service.py
│   ├── session_service.py
│   ├── registration_service.py
│   ├── ticket_service.py
│   ├── purchase_service.py
│   ├── payment_service.py
│   ├── refund_service.py
│   └── audit_log_service.py
│
├── routes/
│   ├── auth.py
│   ├── events.py
│   ├── venues.py
│   ├── speakers.py
│   ├── sessions.py
│   ├── registrations.py
│   ├── tickets.py
│   ├── purchases.py
│   ├── payments.py
│   ├── session_bookings.py
│   ├── checkins.py
│   ├── certificates.py
│   ├── feedback.py
│   ├── notifications.py
│   ├── refunds.py
│   ├── dashboard.py
│   ├── reports.py
│   └── audit_logs.py
│
├── utils/
│   ├── dependencies.py
│   ├── security.py
│   ├── exceptions.py
│   └── enums.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_events.py
│   ├── test_venues.py
│   ├── test_speakers.py
│   ├── test_sessions.py
│   ├── test_registrations.py
│   ├── test_tickets.py
│   ├── test_purchases.py
│   ├── test_payments.py
│   ├── test_session_bookings.py
│   ├── test_checkins.py
│   ├── test_certificates.py
│   ├── test_feedback.py
│   ├── test_filtering_pagination.py
│   ├── test_dashboard.py
│   ├── test_reports.py
│   ├── test_refunds.py
│   └── test_security_data_integrity.py
│
├── alembic/
└── docs/
```

---

# User Roles

The system supports the following roles:

* Admin
* Event Organizer
* Speaker
* Staff
* Attendee

Role-based authorization controls access to protected operations.

---

# Implemented Levels

## Level 1 – Authentication & Authorization

Implemented:

* User registration
* Login
* JWT access tokens
* JWT refresh tokens
* Current-user endpoint
* Password change
* Password hashing
* User activation/deactivation
* Role-based authorization

---

## Level 2 – Event Management

Implemented:

* Event creation
* Event retrieval
* Event update
* Event deletion
* Event status management
* Event type management
* Capacity validation
* Event date validation
* Registration period validation

---

## Level 3 – Venue & Hall Management

Implemented:

* Venue management
* Hall management
* Venue capacity validation
* Hall capacity validation
* Hall availability
* Venue and hall relationships

---

## Level 4 – Speaker Management

Implemented:

* Speaker CRUD
* Speaker information
* Speaker expertise
* Speaker company
* Speaker experience
* Speaker activation/deactivation
* Speaker assignment validation

---

## Level 5 – Session Management

Implemented:

* Session creation
* Session retrieval
* Session update
* Session deletion
* Event/session relationships
* Speaker/session relationships
* Hall/session relationships
* Session timing validation
* Speaker conflict validation
* Hall conflict validation

---

## Level 6 – Attendee Registration

Implemented:

* Attendee registration
* Event registration
* Registration status
* Duplicate registration prevention
* Capacity validation
* Registration period validation
* Registration cancellation

---

## Level 7 – Tickets

Implemented:

* Standard tickets
* VIP tickets
* Early Bird tickets
* Student tickets
* Ticket quantity management
* Available quantity management
* Ticket sale periods
* Ticket validation

---

## Level 8 – Purchase & Payment

Implemented:

* Ticket purchase
* Purchase calculation
* Discount
* Tax
* Total amount
* Payment creation
* Payment status
* Payment methods
* Transaction ID validation
* Duplicate payment prevention
* Payment amount validation
* Successful payment registration confirmation
* Failed payment handling

---

## Level 9 – Session Booking

Implemented:

* Session seat booking
* Attendee session booking
* Booking cancellation
* Session capacity validation
* Duplicate booking prevention
* Confirmed attendee validation

---

## Level 10 – Check-In

Implemented:

* Attendee check-in
* Check-out
* Check-in method
* Attendance history
* Duplicate check-in prevention
* Confirmed attendee validation

---

## Level 11 – Certificates

Implemented:

* Certificate generation
* Certificate number
* Certificate type
* Certificate status
* Certificate issue date
* Attendance requirement
* Certificate retrieval

---

## Level 12 – Event Feedback & Ratings

Implemented:

* Event feedback
* Speaker ratings
* Session feedback
* Rating validation from 1 to 5
* Checked-in attendee validation
* Duplicate session feedback prevention

---

## Level 13 – Notifications

Implemented:

* Background task based notifications
* Registration notifications
* Payment notifications
* Reminder notifications
* Cancellation notifications
* Ticket notifications
* Certificate notifications

---

## Level 14 – Search, Filtering & Pagination

Implemented filtering for:

### Events

* Event type
* City
* Date range
* Status
* Available capacity

### Sessions

* Speaker
* Event
* Session type
* Date

### Registrations

* Event
* Registration status
* Registration date

### Payments

* Payment status
* Payment method
* Date range

### Pagination

Supported parameters:

```text
page
limit
sort_by
sort_order
```

---

## Level 15 – Dashboards & Reports

Implemented:

* Admin dashboard
* Organizer dashboard
* Registration reports
* Event revenue reports
* Ticket sales reports
* Attendance reports
* Speaker rating reports
* Session popularity reports
* Role-based report access
* Organizer event restrictions

---

## Level 16 – Cancellation & Refund

Implemented:

* Registration cancellation
* Purchase/payment refund processing
* Refund status
* Refund amount
* Cancellation reason
* Refund validation
* Authorization checks
* Refund history

---

# Level 17 – Security & Data Integrity

Implemented:

## JWT Authentication

The system uses JWT-based authentication.

Access tokens contain:

```text
sub
type
exp
```

The API verifies:

* Token validity
* Token type
* User ID
* Token expiration
* User account status

---

## Role-Based Authorization

Protected operations verify the authenticated user's role.

Example roles:

```text
Admin
Event Organizer
Speaker
Staff
Attendee
```

Unauthorized roles receive an HTTP `403 Forbidden` response.

---

## Password Hashing

Passwords are hashed using Bcrypt before being stored in the database.

The application never stores passwords as plain text.

Password verification is performed against the stored password hash during authentication.

---

## Foreign Keys

Database relationships use foreign keys to maintain referential integrity.

Examples include:

```text
Event → User
Hall → Venue
Session → Event
Session → Speaker
Session → Hall
Registration → Attendee
Registration → Event
Payment → Purchase
Refund → Payment
Refund → Purchase
AuditLog → User
```

---

## Unique Constraints

Unique constraints are used where duplicate data must be prevented.

Examples include:

* User email
* Speaker email
* Payment transaction ID

Duplicate records are rejected instead of creating inconsistent data.

---

## Database Transactions

Database operations use SQLAlchemy sessions and transaction handling to ensure that changes are committed successfully or rolled back when an operation fails.

This helps prevent partially completed operations.

---

## Global Exception Handling

The project provides centralized exception helpers for common API errors:

```text
401 Unauthorized
403 Forbidden
404 Not Found
400 Bad Request
```

Validation errors are also handled through FastAPI/Pydantic validation.

---

## Audit Logs

Audit logging was added to track important system actions.

Audit logs contain information such as:

```text
User ID
Action
Resource Type
Resource ID
Description
IP Address
Created At
```

The API endpoint is:

```text
GET /api/v1/audit-logs
```

Audit logs can be viewed by an authenticated Admin.

---

## Soft Delete

User account deactivation is used to prevent inactive users from accessing protected APIs while retaining their database records.

Inactive users cannot authenticate successfully against protected operations.

This preserves historical data instead of physically removing the user record.

---

## CORS

CORS middleware is configured to allow frontend applications to communicate with the FastAPI backend.

Configured development origin:

```text
http://localhost:3000
```

---

## Input Validation

Pydantic validation is used throughout the API.

Validation includes:

* Required fields
* String length
* Positive capacity
* Valid dates
* Registration periods
* Valid enum values
* Payment amounts
* Rating range
* Pagination values
* Invalid request data

Invalid input returns an appropriate validation response.

---

# API Documentation

After starting the server, Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

ReDoc is available at:

```text
http://127.0.0.1:8000/redoc
```

---

# Running the Project

## Activate Virtual Environment

PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## Start the Server

```powershell
uvicorn main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

---

# Database Migration

Create a migration:

```powershell
alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```powershell
alembic upgrade head
```

Check current migration:

```powershell
alembic current
```

View migration history:

```powershell
alembic history
```

---

# Testing

The project uses **Pytest** for automated testing.

Run all tests:

```powershell
pytest -q
```

Run a specific test file:

```powershell
python -m pytest tests/test_security_data_integrity.py -v -s
```

Run Level 14 filtering tests:

```powershell
python -m pytest tests/test_filtering_pagination.py -v -s
```

Run Level 16 refund tests:

```powershell
python -m pytest tests/test_refunds.py -v -s
```

---

# Test Status

The project has been tested progressively across the implemented assignment levels.

### Completed Test Results

```text
Level 1   – 15 passed
Level 2   – 15 passed
Level 3   – 11 passed
Level 4   – 15 passed
Level 5   – 20 passed
Level 6   – 16 passed
Level 7   – 19 passed
Level 8   – 35 passed
Level 9   – 22 passed
Level 10  – 34 passed
Level 11  – 33 passed
Level 12  – 18 passed
Level 15  – 13 passed
Level 16  – 17 passed
```

The Level 14 filtering and pagination test suite contains:

```text
23 tests
22 passed
```

The remaining Level 14 city-response issue was identified and addressed by exposing the event city through the existing Event → Session → Hall → Venue relationship rather than adding an unnecessary `city` database column.

---

# Architecture

The project follows a layered architecture:

```text
Client
   ↓
Routes
   ↓
Services
   ↓
Repositories
   ↓
SQLAlchemy Models
   ↓
PostgreSQL
```

### Models

Define database tables and relationships.

### Schemas

Validate request and response data using Pydantic.

### Routes

Define API endpoints and HTTP behavior.

### Services

Contain business logic and validation.

### Repositories

Handle database queries and persistence.

### Utils

Contain reusable functionality such as:

* Authentication
* JWT
* Password hashing
* Dependencies
* Exceptions
* Enumerations

---

# Security Features

The application provides:

* JWT authentication
* Access and refresh tokens
* Bcrypt password hashing
* Role-based authorization
* Active/inactive user protection
* Foreign key constraints
* Unique constraints
* Input validation
* Database transaction handling
* Audit logging
* Soft deletion/deactivation
* CORS configuration
* Centralized exception handling

---

# Main Workflow

The complete event management workflow is:

```text
Register User
      ↓
Login
      ↓
Create Event
      ↓
Create Venue
      ↓
Create Hall
      ↓
Add Speaker
      ↓
Create Session
      ↓
Open Registration
      ↓
Register Attendee
      ↓
Create Ticket
      ↓
Purchase Ticket
      ↓
Payment
      ↓
Book Session
      ↓
Check-In
      ↓
Attend Session/Event
      ↓
Submit Feedback
      ↓
Generate Certificate
      ↓
Dashboard & Reports
```

---

# Environment Variables

Sensitive configuration should be stored in `.env`.

Example:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5433/event_conference_management
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_NAME=Event & Conference Management System
APP_VERSION=1.0.0
```

Do not commit the actual `.env` file or secret keys to GitHub.

---

# Future Enhancements

Possible future improvements include:

* Celery
* Redis
* Email notifications
* QR-code based check-in
* PDF certificate generation
* Excel reports
* WebSocket live updates
* Docker deployment
* API versioning
* Advanced database indexing
* Performance optimization
* Automated deployment

---

# Author

**Srikanth Bethamcharla**
