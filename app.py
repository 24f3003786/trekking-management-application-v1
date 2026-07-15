from flask import Flask, render_template, url_for, request, redirect, flash , session
from models import db, User, Trek, Booking, Staff_Profile
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime
from functools import wraps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'Vidhya@123'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# --------------------------------- Chart Helper ---------------------------------

CHART_COLORS = {
    "Open":      "#198754",  # bootstrap success green
    "Started":   "#ffc107",  # warning yellow
    "Completed": "#6c757d",  # secondary grey
    "Closed":    "#212529",  # dark
    "Booked":    "#0d6efd",  # primary blue
    "Cancelled": "#dc3545",  # danger red
    "Pending":   "#ffc107",
    "Paid":      "#198754",
    "Refunded":  "#6c757d",
}

def make_status_chart(counts, title, filename):

    if not counts or sum(counts.values()) == 0:
        return None

    labels = list(counts.keys())
    values = list(counts.values())
    colors = [CHART_COLORS.get(label, "#0d6efd") for label in labels]
    os.makedirs("static", exist_ok=True)


    plt.figure(figsize=(5, 3))
    plt.bar(labels, values, color=colors)
    plt.title(title)
    plt.ylabel("Count")

    for spine in plt.gca().spines.values():
        spine.set_edgecolor("#dee2e6")

    plt.tight_layout()

    save_path = os.path.join("static", filename)
    plt.savefig(save_path)
    plt.close()

    return f"/static/{filename}"


def create_admin():
    if not User.query.filter_by(role="admin").first():
        admin = User(name="Admin", email='admin@example.com',
                     password=generate_password_hash("1234"),
                     phone="9999999999", role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully")
    else:
        print("Admin already exists")


# --------------------------------- Access-Control Decorators ---------------------------------

def _redirect_to_own_area():
    """Where to send someone who tried to access a page they shouldn't."""
    role = session.get('role')
    user_id = session.get('user_id')
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "trekker" and user_id:
        return redirect(url_for("trekker_dashboard", user_id=user_id))
    elif role == "trek_staff" and user_id:
        return redirect(url_for("trek_staff_dashboard", user_id=user_id))
    return redirect(url_for("login"))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        
        if 'user_id' in kwargs and kwargs['user_id'] != session['user_id']:
            flash("You don't have access to that page.", "warning")
            return _redirect_to_own_area()

        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Restricts a route to one or more roles (e.g. role_required('admin'))."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if session.get('role') not in roles:
                flash("You don't have access to that page.", "warning")
                return _redirect_to_own_area()
            return f(*args, **kwargs)
        return wrapper
    return decorator


# --------------------------------- Controllers ---------------------------------

@app.route("/")
def home():
    return render_template('index.html')


# --------------------------------- Register Choice ---------------------------------

@app.route("/register-choice")
def register_choice():
    return render_template("register_choice.html")


# --------------------------------- Registration ---------------------------------

@app.route("/register/trekker", methods=["GET", "POST"])
def register_trekker():
    if request.method == "POST":
        name     = request.form.get('name')
        email    = request.form.get('email')
        password = request.form.get('password')
        phone    = request.form.get("phone")

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register_trekker"))

        new_user = User(name=name, email=email,
                        password=generate_password_hash(password),
                        phone=phone, role="trekker")
        db.session.add(new_user)
        db.session.commit()
        flash("Registration Successful. Please Login.", "success")
        return redirect(url_for("login"))

    return render_template("register_trekker.html")


@app.route("/register/trek_staff", methods=["GET", "POST"])
def register_trek_staff():
    if request.method == "POST":
        name        = request.form.get('name')
        email       = request.form.get('email')
        password    = request.form.get('password')
        phone       = request.form.get("phone")
        description = request.form.get("description")

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register_trek_staff"))

        new_user = User(name=name, email=email,
                        password=generate_password_hash(password),
                        phone=phone, role="trek_staff")
        db.session.add(new_user)
        db.session.flush()

        new_staff = Staff_Profile(description=description,
                                  user_id=new_user.id, approved=False)
        db.session.add(new_staff)
        db.session.commit()
        flash("Registration Successful. Please Login.", "success")
        return redirect(url_for("login"))

    return render_template("register_trek_staff.html")


# --------------------------------- Login ---------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Invalid Credentials", "danger")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Invalid Credentials", "danger")
            return redirect(url_for("login"))

        if not check_password_hash(user.password, password):
            flash("Invalid Credentials", "danger")
            return redirect(url_for("login"))

        if user.is_blacklisted:
            flash("Account Blacklisted", "danger")
            return redirect(url_for("login"))
        session.clear()

        if user.role == "admin":
            session['role'] = user.role
            session['user_id'] = user.id
            return redirect(url_for("admin_dashboard"))
        elif user.role == "trekker":
            session['role'] = user.role
            session['user_id'] = user.id
            return redirect(url_for("trekker_dashboard",user_id=user.id))
        elif user.role == "trek_staff":
            if user.staff_profile.approved:
                session['role'] = user.role
                session['user_id'] = user.id
                return redirect(url_for("trek_staff_dashboard",user_id=user.id))
            else:
                flash("Waiting for Admin Approval", "warning")
                return redirect(url_for("login"))

    return render_template("login.html")


# --------------------------------- Logout ---------------------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# --------------------------------- Admin Dashboard ---------------------------------

@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    total_treks     = Trek.query.count()
    total_users     = User.query.filter_by(role="trekker").count()
    total_staff     = Staff_Profile.query.filter_by(approved=True).count()
    total_bookings  = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()

    
    trek_status_counts = dict(
        db.session.query(Trek.trek_status, db.func.count(Trek.id))
                  .group_by(Trek.trek_status).all()
    )
    
    for status in ("Open", "Started", "Completed", "Closed"):
        trek_status_counts.setdefault(status, 0)

    booking_status_counts = dict(
        db.session.query(Booking.booking_status, db.func.count(Booking.id))
                  .group_by(Booking.booking_status).all()
    )
    for status in ("Booked", "Started", "Cancelled", "Completed"):
        booking_status_counts.setdefault(status, 0)

    trek_chart = make_status_chart(trek_status_counts, "Treks by Status", "chart_admin_treks.png")
    booking_chart = make_status_chart(booking_status_counts, "Bookings by Status", "chart_admin_bookings.png")

    return render_template("admin_dashboard.html",
                           total_treks=total_treks,
                           total_users=total_users,
                           total_staff=total_staff,
                           total_bookings=total_bookings,
                           recent_bookings=recent_bookings,
                           trek_chart=trek_chart,
                           booking_chart=booking_chart)


# --------------------------------- Admin Trek Management ---------------------------------

@app.route("/admin/treks")
@role_required("admin")
def admin_treks():
    search_query = request.args.get("search", "").strip()
    search_field = request.args.get("search_field", "trek_name")

    if search_query:
        column = getattr(Trek, search_field)
        treks = Trek.query.filter(column.ilike(f"%{search_query}%")).all()
    else:
        treks = Trek.query.all()

    return render_template("admin_treks.html", treks=treks,
                            search_query=search_query, search_field=search_field)

def start_trek(trek):

    trek.trek_status = "Started"
    for booking in trek.bookings:
        if booking.booking_status == "Booked":
            booking.booking_status = "Started"

def complete_trek(trek):
    
    trek.trek_status = "Completed"
    for booking in trek.bookings:
        if booking.booking_status in ("Booked", "Started"):
            booking.booking_status = "Completed"


@app.route("/admin/trek/add", methods=["GET", "POST"])
@role_required("admin")
def add_trek():
    approved_staff = (Staff_Profile.query
                  .filter_by(approved=True)
                  .join(User)
                  .filter(User.is_blacklisted == False)
                  .all())
    if request.method == "POST":
        trek_name = request.form.get("trek_name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        duration = request.form.get("duration")
        available_slots = request.form.get("available_slots")
        trek_status = request.form.get("status")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        description = request.form.get("description")
        staff_id = request.form.get("staff_id")

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        duration = int(duration)
        available_slots = int(available_slots)
        staff_id = int(staff_id) if staff_id else None

        new_trek = Trek(
            trek_name=trek_name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            available_slots=available_slots,
            trek_status=trek_status,
            start_date=start_date,
            end_date=end_date,
            description=description,
            staff_id=staff_id
        )
        db.session.add(new_trek)
        db.session.commit()
        flash(f"Trek '{trek_name}' created successfully.", "success")
        return redirect(url_for("admin_treks"))
    return render_template("admin_add_trek.html", approved_staff=approved_staff)

@app.route("/admin/trek/edit/<int:trek_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    is_locked = trek.trek_status in ("Completed", "Closed")

    if request.method == "POST":
        trek.trek_name = request.form.get("trek_name")
        trek.location = request.form.get("location")
        trek.difficulty = request.form.get("difficulty")
        trek.duration = int(request.form.get("duration"))
        trek.description = request.form.get("description")
        trek.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        trek.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()

        staff_id = request.form.get("staff_id")
        trek.staff_id = int(staff_id) if staff_id else None

        if not is_locked:
            submitted_slots = int(request.form.get("available_slots"))
            if submitted_slots < 0:
                flash("Available slots cannot be negative.", "danger")
                return redirect(url_for("edit_trek", trek_id=trek_id))
            trek.available_slots = submitted_slots

            new_status = request.form.get("status")
            if new_status == "Completed":
                complete_trek(trek)
            elif new_status == "Started":
                start_trek(trek)
            else:
                trek.trek_status = new_status

        db.session.commit()
        flash(f"Trek '{trek.trek_name}' updated successfully.", "success")
        return redirect(url_for("admin_treks"))

    approved_staff = (Staff_Profile.query
                  .filter_by(approved=True)
                  .join(User)
                  .filter(User.is_blacklisted == False)
                  .all())
    return render_template("admin_edit_trek.html", trek=trek, approved_staff=approved_staff, is_locked=is_locked)

@app.route("/admin/trek/delete/<int:trek_id>")
@role_required("admin")
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek_id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash(f"Trek '{trek.trek_name}' deleted.", "warning")
    return redirect(url_for("admin_treks"))


# --------------------------------- Admin Staff Management ---------------------------------

@app.route("/admin/staff")
@role_required("admin")
def admin_staff():
    active_tab = request.args.get("tab", "pending")
    search_query = request.args.get("search", "").strip()

    pending_query = (Staff_Profile.query
                     .filter_by(approved=False)
                     .join(User)
                     .filter(User.is_blacklisted == False))

    approved_query = (Staff_Profile.query
                      .filter_by(approved=True)
                      .join(User)
                      .filter(User.is_blacklisted == False))

    blacklisted_query = (Staff_Profile.query
                         .join(User)
                         .filter(User.is_blacklisted == True))

    if search_query:
        pending_query = pending_query.filter(
            or_(User.name.ilike(f"%{search_query}%"), User.email.ilike(f"%{search_query}%"))
        )
        approved_query = approved_query.filter(
            or_(User.name.ilike(f"%{search_query}%"), User.email.ilike(f"%{search_query}%"))
        )
        blacklisted_query = blacklisted_query.filter(
            or_(User.name.ilike(f"%{search_query}%"), User.email.ilike(f"%{search_query}%"))
        )

    pending_staff = pending_query.all()
    approved_staff = approved_query.all()
    blacklisted_staff = blacklisted_query.all()

    return render_template("admin_staff.html",
                           active_tab=active_tab,
                           search_query=search_query,
                           pending_staff=pending_staff,
                           approved_staff=approved_staff,
                           blacklisted_staff=blacklisted_staff)

@app.route("/admin/approve_staff/<int:staff_id>", methods=["POST"])
@role_required("admin")
def approve_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    staff.approved = True
    db.session.commit()
    flash(f"{staff.user.name} approved.", "success")
    return redirect(url_for("admin_staff", tab="pending"))


@app.route("/admin/reject_staff/<int:staff_id>", methods=["POST"])
@role_required("admin")
def reject_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    user  = staff.user
    db.session.delete(staff)
    db.session.flush()
    db.session.delete(user)
    db.session.commit()
    flash("Staff application rejected.", "warning")
    return redirect(url_for("admin_staff", tab="pending"))


@app.route("/admin/blacklist_staff/<int:staff_id>")
@role_required("admin")
def blacklist_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    staff.user.is_blacklisted = True
    unassigned_count = 0
    for trek in staff.treks:
        if trek.trek_status in ("Open", "Started"):
            trek.staff_id = None
            unassigned_count += 1

    db.session.commit()

    msg = f"{staff.user.name} blacklisted."
    if unassigned_count:
        msg += f" {unassigned_count} active trek(s) unassigned."
    flash(msg, "danger")
    return redirect(url_for("admin_staff", tab="approved"))


@app.route("/admin/unblacklist_staff/<int:staff_id>")
@role_required("admin")
def unblacklist_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    staff.user.is_blacklisted = False
    db.session.commit()
    flash(f"{staff.user.name} unblacklisted.", "success")
    return redirect(url_for("admin_staff", tab="blacklisted"))


# --------------------------------- Admin User Management ---------------------------------

@app.route("/admin/users")
@role_required("admin")
def admin_users():
    active_tab   = request.args.get("tab", "active")
    search_query = request.args.get("search", "")

    active_q      = User.query.filter_by(role="trekker", is_blacklisted=False)
    blacklisted_q = User.query.filter_by(role="trekker", is_blacklisted=True)

    if search_query:
        f = or_(User.name.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"))
        active_q      = active_q.filter(f)
        blacklisted_q = blacklisted_q.filter(f)

    return render_template("admin_users.html",
                           active_tab=active_tab,
                           search_query=search_query,
                           active_users=active_q.all(),
                           blacklisted_users=blacklisted_q.all())


@app.route("/admin/blacklist_user/<int:user_id>")
@role_required("admin")
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = True
    db.session.commit()
    flash(f"{user.name} blacklisted.", "warning")
    return redirect(url_for("admin_users", tab="active"))


@app.route("/admin/unblacklist_user/<int:user_id>")
@role_required("admin")
def unblacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = False
    db.session.commit()
    flash(f"{user.name} unblacklisted.", "success")
    return redirect(url_for("admin_users", tab="blacklisted"))


# --------------------------------- Admin Booking Management ---------------------------------

@app.route("/admin/bookings")
@role_required("admin")
def admin_bookings():
    active_tab   = request.args.get("tab", "booked")
    search_query = request.args.get("search", "")

    def filter_bookings(statuses):
        q = Booking.query.filter(Booking.booking_status.in_(statuses))
        if search_query:
            q = q.join(User).join(Trek).filter(or_(User.name.ilike(f"%{search_query}%") , Trek.trek_name.ilike(f"%{search_query}%")))
        return q.all()

    return render_template("admin_bookings.html",
                       active_tab=active_tab,
                       search_query=search_query,
                       booked=filter_bookings(["Booked", "Started"]),
                       cancelled=filter_bookings(["Cancelled"]),
                       completed=filter_bookings(["Completed"]))


# --------------------------------- Trek Staff Dashboard ---------------------------------

@app.route("/trek_staff/dashboard/<int:user_id>")
@role_required("trek_staff")
@login_required
def trek_staff_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    staff_profile = user.staff_profile

    assigned_treks = staff_profile.treks

    trek_counts = {}
    for trek in assigned_treks:
        trek_counts[trek.id] = Booking.query.filter(
            Booking.trek_id == trek.id,
            Booking.booking_status.in_(["Booked", "Started", "Completed"])
        ).count()

    total_participants = sum(trek_counts.values())
    open_treks_count = sum(1 for trek in assigned_treks if trek.trek_status == "Open")

    return render_template(
        "trek_staff_dashboard.html",
        user=user,
        treks=assigned_treks,
        trek_counts=trek_counts,
        total_participants=total_participants,
        open_treks_count=open_treks_count)

@app.route("/trek_staff/trek/manage/<int:trek_id>/<int:user_id>", methods=["GET", "POST"])
@role_required("trek_staff")
@login_required
def staff_manage_trek(trek_id, user_id):
    trek = Trek.query.get_or_404(trek_id)
    user = User.query.get_or_404(user_id)

    if trek.staff_id != user.staff_profile.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("trek_staff_dashboard", user_id=user_id))

    consumed_count = Booking.query.filter(
        Booking.trek_id == trek_id,
        Booking.booking_status.in_(["Booked", "Started", "Completed"])
    ).count()

    is_locked = trek.trek_status in ("Completed", "Closed")

    if request.method == "POST":
        if is_locked:
            flash("This trek is locked and can no longer be updated.", "warning")
            return redirect(url_for("staff_manage_trek", trek_id=trek_id, user_id=user_id))

        total_slots_before = trek.available_slots + consumed_count
        submitted_slots = int(request.form.get("available_slots"))
        if submitted_slots < 0 or submitted_slots > total_slots_before:
            flash(f"Available slots must be between 0 and {total_slots_before}.", "danger")
            return redirect(url_for("staff_manage_trek", trek_id=trek_id, user_id=user_id))

        trek.available_slots = submitted_slots
        new_status = request.form.get("status")

        if new_status == "Completed":
            complete_trek(trek)
        elif new_status == "Started":
            start_trek(trek)
        else:
            trek.trek_status = new_status

        db.session.commit()
        flash(f"Trek '{trek.trek_name}' updated successfully.", "success")
        return redirect(url_for("staff_manage_trek", trek_id=trek_id, user_id=user_id))

    bookings = Booking.query.filter_by(trek_id=trek_id).all()

    total_slots = trek.available_slots + consumed_count

    return render_template(
        "staff_manage_trek.html",
        trek=trek,
        user=user,
        bookings=bookings,
        total_slots=total_slots,
        is_locked=is_locked
    )

# --------------------------------- Trek Staff Profile ---------------------------------

@app.route("/trek_staff/profile/<int:user_id>", methods=["GET", "POST"])
@role_required("trek_staff")
@login_required
def staff_profile(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.name = request.form.get("name")
        user.phone = request.form.get("phone")

        new_password = request.form.get("password")
        if new_password:
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("staff_profile", user_id=user_id))

    return render_template("trek_staff_profile.html", user=user)

# --------------------------------- Trekker Dashboard ---------------------------------

@app.route("/trekker/dashboard/<int:user_id>")
@role_required("trekker")
@login_required
def trekker_dashboard(user_id):
    user = User.query.get_or_404(user_id)

    location = request.args.get("location", "").strip()
    difficulty = request.args.get("difficulty", "").strip()

    treks_query = Trek.query.filter_by(trek_status="Open")

    if location:
        treks_query = treks_query.filter(Trek.location == location)
    if difficulty:
        treks_query = treks_query.filter(Trek.difficulty == difficulty)

    treks = treks_query.all()

    all_locations = [row[0] for row in db.session.query(Trek.location).distinct().all()]
    all_difficulties = [row[0] for row in db.session.query(Trek.difficulty).distinct().all()]

    recent_bookings = (Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).limit(3).all())
    return render_template("trekker_dashboard.html", user=user,
                           treks=treks, location=location, difficulty=difficulty,
                           all_locations=all_locations, all_difficulties=all_difficulties,
                           recent_bookings=recent_bookings)

# --------------------------------- Trekker Bookings ---------------------------------

@app.route("/trekker/bookings/<int:user_id>")
@role_required("trekker")
@login_required
def trekker_bookings(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter( Booking.user_id == user_id, Booking.booking_status.in_(["Booked", "Started"])).all()
    return render_template("trekker_bookings.html", user=user, bookings=bookings)


@app.route("/trekker/book/<int:trek_id>/<int:user_id>")
@role_required("trekker")
@login_required
def trekker_booking(trek_id, user_id):
    trek = Trek.query.get_or_404(trek_id)
    user = User.query.get_or_404(user_id)

    if trek.trek_status != "Open":
        flash("This trek is no longer accepting bookings.", "danger")
        return redirect(url_for("trekker_dashboard", user_id=user_id))

    existing = Booking.query.filter_by(trek_id=trek_id, user_id=user_id).first()
    if existing:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for("trekker_dashboard", user_id=user_id))

    if trek.available_slots <= 0:
        flash("No slots available for this trek.", "danger")
        return redirect(url_for("trekker_dashboard", user_id=user_id))

    new_booking = Booking(user_id=user_id, trek_id=trek_id)
    trek.available_slots -= 1

    db.session.add(new_booking)
    db.session.commit()

    flash(f"Successfully booked '{trek.trek_name}'.", "success")
    return redirect(url_for("trekker_dashboard", user_id=user_id))


@app.route("/trekker/cancel/<int:booking_id>/<int:user_id>")
@role_required("trekker")
@login_required
def trekker_cancel_booking(booking_id, user_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.booking_status != "Booked":
        flash("This booking can no longer be cancelled.", "warning")
        return redirect(url_for("trekker_bookings", user_id=user_id))

    booking.booking_status = "Cancelled"
    booking.trek.available_slots += 1

    if booking.payment_status == "Paid":
        booking.payment_status = "Refunded"

    db.session.commit()
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for("trekker_bookings", user_id=user_id))

@app.route("/trekker/trek/details/<int:trek_id>/<int:user_id>")
@role_required("trekker")
@login_required
def trekker_trek_details(trek_id, user_id):
    trek = Trek.query.get_or_404(trek_id)
    booking = Booking.query.filter_by(trek_id=trek_id, user_id=user_id).first()
    return render_template("trekker_booking_details.html", trek=trek, booking=booking, user_id=user_id)

# --------------------------------- Trekker Payment ---------------------------------

@app.route("/trekker/profile/<int:user_id>", methods=["GET", "POST"])
@role_required("trekker")
@login_required
def trekker_profile(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.name = request.form.get("name")
        user.phone = request.form.get("phone")

        new_password = request.form.get("password")
        if new_password:
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("trekker_profile", user_id=user_id))

    return render_template("trekker_profile.html", user=user)

# --------------------------------- Trekker History ---------------------------------

@app.route("/trekker/history/<int:user_id>")
@role_required("trekker")
@login_required
def trekker_history(user_id):
    user = User.query.get_or_404(user_id)
    history = Booking.query.filter_by(user_id=user_id, booking_status="Completed").all()

    all_bookings = Booking.query.filter_by(user_id=user_id).all()
    status_counts = {"Booked": 0, "Started": 0, "Completed": 0, "Cancelled": 0}
    for b in all_bookings:
        if b.booking_status in status_counts:
            status_counts[b.booking_status] += 1
    booking_chart = make_status_chart(status_counts, "My Bookings by Status", f"chart_trekker_{user_id}.png")

    return render_template("trekker_history.html", user=user, history=history, booking_chart=booking_chart)


# --------------------------------- Trekker Profile ---------------------------------

@app.route("/trekker/pay/<int:booking_id>/<int:user_id>", methods=["GET", "POST"])
@role_required("trekker")
@login_required
def trekker_pay(booking_id, user_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.booking_status not in ("Booked", "Started"):
        flash("This booking is not active — payment can no longer be made.", "warning")
        return redirect(url_for("trekker_bookings", user_id=user_id))

    if booking.payment_status != "Pending":
        flash("This booking is already paid or refunded.", "warning")
        return redirect(url_for("trekker_bookings", user_id=user_id))

    if request.method == "POST":
   
        card_number = request.form.get("card_number", "").replace(" ", "")
        expiry = request.form.get("expiry", "").strip()
        cvv = request.form.get("cvv", "").strip()

        errors = []
        if not card_number.isdigit() or not (13 <= len(card_number) <= 19):
            errors.append("Card number must be 13 to 19 digits.")

 
        if len(expiry) != 5 or expiry[2] != "/" or not (expiry[:2].isdigit() and expiry[3:].isdigit()):
            errors.append("Expiry must be in MM/YY format.")
        else:
            month = int(expiry[:2])
            year = 2000 + int(expiry[3:])
            today = datetime.today().date()
            if not (1 <= month <= 12):
                errors.append("Expiry month must be between 01 and 12.")
            elif (year, month) < (today.year, today.month):
                errors.append("This card has expired.")

      
        if not cvv.isdigit() or not (3 <= len(cvv) <= 4):
            errors.append("CVV must be 3 or 4 digits.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("trekker_pay", booking_id=booking_id, user_id=user_id))

      
        booking.payment_status = "Paid"
        db.session.commit()
        flash(f"Payment for '{booking.trek.trek_name}' completed successfully.", "success")
        return redirect(url_for("trekker_bookings", user_id=user_id))

    return render_template("trekker_pay.html", booking=booking, user_id=user_id)


# ----------------------------------------------------------------------------------------------------

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == "__main__":
    app.run(debug=True)
