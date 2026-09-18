# Event & Conference Management System

## Overview

The **Event & Conference Management System** is a real-world backend application developed using **FastAPI**. It provides APIs for managing events, venues, halls, speakers, sessions, attendees, registrations, tickets, purchases, payments, bookings, check-ins, certificates, feedback, notifications, refunds, dashboards, reports, filtering, pagination, security, and data integrity.

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
├── schemas/
├── repositories/
├── services/
├── routes/
├── utils/
├── tests/
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
* Venue and hall relationships
* Hall availability

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
* Registration status management
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

* Background task notifications
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

### Pagination & Sorting

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

### JWT Authentication

* JWT access tokens
* JWT refresh tokens
* Token expiration
* Access-token type validation
* Invalid-token protection
* Inactive-user protection

### Role-Based Authorization

* Admin authorization
* Event Organizer authorization
* Staff authorization
* Attendee authorization
* Unauthorized role protection

### Password Hashing

* Bcrypt password hashing
* Secure password verification
* Plain-text passwords are not stored

### Foreign Keys

Database relationships use foreign keys to maintain referential integrity.

Examples:

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
AuditLog → User
```

### Unique Constraints

Unique constraints prevent duplicate records such as:

* User email
* Speaker email
* Payment transaction ID

### Database Transactions

SQLAlchemy database sessions are used to commit successful operations and roll back failed operations to prevent partial data changes.

### Global Exception Handling

Centralized handling is provided for common API errors including:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
422 Validation Error
```

### Audit Logs

Audit logging records important system actions.

Audit log information includes:

```text
User ID
Action
Resource Type
Resource ID
Description
IP Address
Created At
```

Admin users can access:

```text
GET /api/v1/audit-logs
```

### Soft Delete

User account deactivation is used as a soft-delete mechanism.

Inactive users cannot access protected operations while their historical database information remains available.

### CORS

CORS middleware is configured to support frontend communication.

Development origin:

```text
http://localhost:3000
```

### Input Validation

Pydantic validation is used for:

* Required fields
* String lengths
* Positive values
* Dates
* Registration periods
* Enum values
* Payment amounts
* Ratings
* Pagination parameters
* Request data

---

# API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

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

## Start the Server

```powershell
uvicorn main:app --reload
```

API:

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

---

# Test Results

The project has been tested progressively across the implemented assignment levels.

## Final Test Result

```text
385 passed
```

### Level-wise Test Results

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
Level 14  – Filtering & Pagination tests
Level 15  – 13 passed
Level 16  – 17 passed
Level 17  – Security & Data Integrity tests
```

### Overall

```text
========================================
        TEST SUITE RESULT
========================================

385 PASSED
0 FAILED

All implemented project tests passed successfully.
========================================
```

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

Define database tables, fields, constraints, and relationships.

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

* JWT authentication
* Password hashing
* Dependencies
* Exceptions
* Enumerations

---

# Main Workflow

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
Attend
      ↓
Submit Feedback
      ↓
Generate Certificate
      ↓
Cancellation / Refund
      ↓
Dashboard & Reports
      ↓
Audit & Security
```

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
* Database transactions
* Input validation
* Audit logging
* Soft deletion/deactivation
* CORS configuration
* Exception handling

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

Possible future improvements:

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
