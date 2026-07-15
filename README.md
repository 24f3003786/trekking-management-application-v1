# Trekking Management Application

A role-based web application for managing trekking activities, built as part of the Modern Application Development 1 (MAD1) course project.

---

## Overview

The Trekking Management Application allows three types of users — **Admin**, **Trek Staff**, and **Trekkers** — to interact with the system based on their roles. Admin manages treks and users, Trek Staff coordinates assigned treks, and Trekkers can browse, book, and track their trekking experiences.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | Jinja2, HTML5, Bootstrap 5 |
| Database | SQLite (via SQLAlchemy ORM) |
| Charts | Matplotlib |
| Auth | Flask Session |

> JavaScript was **not** used for any core functionality, as per project requirements.

---

## Features

### Admin
- Pre-existing superuser (no registration required)
- Dashboard with total treks, users, staff, and bookings
- Create, edit, and delete treks
- Approve or reject trek staff registration requests
- Assign staff to treks
- View all bookings (searchable by user name or trek name)
- Blacklist / unblacklist users and staff
- Bar charts for trek status and booking status breakdown

### Trek Staff
- Self-registration with admin approval workflow
- Dashboard showing assigned treks and participant counts
- Update available slots and trek status (Open → Started → Completed)
- View participant list per trek
- Trek status locks once Completed or Closed

### Trekker
- Self-registration and login
- Browse available (Open) treks with filters for location and difficulty
- Book treks, view booking status, and cancel active bookings
- Simulated payment with card form (frontend + backend validation)
- View trekking history with booking status chart
- Edit profile (name, phone, password)

### Additional Features
- Session-based authentication with role guards and IDOR protection
- Trek lifecycle cascade: status changes propagate to all active bookings
- Refund logic: cancelling a paid booking auto-marks payment as Refunded
- Blacklist cascade: blacklisting staff auto-unassigns them from active treks
- Slot locking: admin cannot over-remove slots; staff capped at existing capacity
- Landing page with navigation for unauthenticated users

---

## Project Structure

```
trekking-management-application-v1/
├── app.py                  # All routes, decorators, and chart helper
├── models.py               # SQLAlchemy models (User, Trek, Booking, Staff_Profile)
├── static/
│   └── style.css           # Custom styles
├── templates/
│   ├── index.html                  # Landing page
│   ├── login.html
│   ├── register_choice.html
│   ├── register_trekker.html
│   ├── register_trek_staff.html
│   ├── admin_dashboard.html
│   ├── admin_treks.html
│   ├── admin_add_trek.html
│   ├── admin_edit_trek.html
│   ├── admin_staff.html
│   ├── admin_users.html
│   ├── admin_bookings.html
│   ├── trek_staff_dashboard.html
│   ├── staff_manage_trek.html
│   ├── trek_staff_profile.html
│   ├── trekker_dashboard.html
│   ├── trekker_bookings.html
│   ├── trekker_booking_details.html
│   ├── trekker_history.html
│   ├── trekker_profile.html
│   └── trekker_pay.html
└── instance/
    └── trekking.db         # Auto-created on first run
```

---

## Database Models

| Model | Key Fields |
|---|---|
| `User` | id, name, email, password, phone, role, is_blacklisted |
| `Trek` | id, trek_name, location, difficulty, duration, available_slots, trek_status, start_date, end_date, staff_id |
| `Booking` | id, user_id, trek_id, booking_date, booking_status, payment_status |
| `Staff_Profile` | id, user_id, description, approved |

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip

### Steps

```bash
# 1. Clone or extract the project folder
cd trekking-management-application-v1

# 2. Install dependencies
pip install flask flask-sqlalchemy werkzeug matplotlib

# 3. Run the application
python app.py
```

The app will be available at `http://127.0.0.1:5000`

> The database and admin user are created automatically on first run.  
> No manual database setup is required.

---

## Default Admin Credentials

| Field | Value |
|---|---|
| Email | admin@example.com |
| Password | 1234 |

---

## Trek Status Lifecycle

```
Open → Started → Completed
         ↓
       Closed  (admin only — trek withdrawn before completion)
```

When a trek's status changes, all active bookings cascade automatically:
- `Open → Started`: all `Booked` bookings → `Started`
- `Started → Completed`: all `Booked`/`Started` bookings → `Completed`

---

## Booking Status Lifecycle

```
Booked → Started → Completed
   ↓
Cancelled (only while still "Booked"; refund auto-applied if Paid)
```

---

## Payment Flow

Payment is simulated (no real gateway). The card form validates:
- Card number: 13–19 digits (spaces ignored)
- Expiry: MM/YY format, valid month, not expired
- CVV: 3–4 digits

Validation runs both client-side (HTML5 `pattern=`) and server-side.

---

## Security

- **Session-based auth**: `session['user_id']` and `session['role']` set only after all login checks pass
- **Role guards**: `@role_required("admin")` / `@role_required("trekker")` / `@role_required("trek_staff")` on every protected route
- **IDOR protection**: URL `<user_id>` is validated against `session['user_id']` — a logged-in trekker cannot access another trekker's pages by editing the URL
- **Blacklist enforcement**: blacklisted users cannot log in and are redirected with an error

---

## Charts

Generated using **Matplotlib** (server-side, saved as PNG to `static/`):

| Page | Chart |
|---|---|
| Admin Dashboard | Treks by Status + Bookings by Status |
| Trekker History | My Bookings by Status |

Charts only render when there is data to display.

---

## License

This project was built for academic purposes as part of the MAD1 course.

