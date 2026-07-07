from flask import Flask, render_template, url_for, request, redirect, flash , session
from models import db, User, Trek, Booking, Staff_Profile
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'Vidhya@123'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def create_admin():
    if not User.query.filter_by(role="admin").first():
        admin = User(name="Admin", email='admin@example.com',
                     password=generate_password_hash("admin@123"),
                     phone="9999999999", role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully")
    else:
        print("Admin already exists")


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

        
        if user.role == "admin":
            #session['role'] = user.role
            #session['user_id'] = user.id
            return redirect(url_for("admin_dashboard"))
        elif user.role == "trekker":
            #session['role'] = user.role
            #session['user_id'] = user.id
            return redirect(url_for("trekker_dashboard",user_id=user.id))
        elif user.role == "trek_staff":
            if user.staff_profile.approved:
                #session['role'] = user.role
                #session['user_id'] = user.id
                return redirect(url_for("trek_staff_dashboard"))
            else:
                flash("Waiting for Admin Approval", "warning")
                return redirect(url_for("login"))

    return render_template("login.html")


# --------------------------------- Logout ---------------------------------

@app.route("/logout")
def logout():
    #session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# --------------------------------- Admin Dashboard ---------------------------------

@app.route("/admin/dashboard")
def admin_dashboard():
    total_treks     = Trek.query.count()
    total_users     = User.query.filter_by(role="trekker").count()
    total_staff     = Staff_Profile.query.filter_by(approved=True).count()
    total_bookings  = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()

    return render_template("admin_dashboard.html",
                           total_treks=total_treks,
                           total_users=total_users,
                           total_staff=total_staff,
                           total_bookings=total_bookings,
                           recent_bookings=recent_bookings)


# --------------------------------- Admin Trek Management ---------------------------------

@app.route("/admin/treks")
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


@app.route("/admin/trek/add", methods=["GET", "POST"])
def add_trek():
    approved_staff = Staff_Profile.query.filter_by(approved=True).all()
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
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":
        trek.trek_name = request.form.get("trek_name")
        trek.location = request.form.get("location")
        trek.difficulty = request.form.get("difficulty")
        trek.duration = int(request.form.get("duration"))
        trek.available_slots = int(request.form.get("available_slots"))
        trek.trek_status = request.form.get("status")
        trek.description = request.form.get("description")
        trek.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        trek.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()

        staff_id = request.form.get("staff_id")
        trek.staff_id = int(staff_id) if staff_id else None

        db.session.commit()
        flash(f"Trek '{trek.trek_name}' updated successfully.", "success")
        return redirect(url_for("admin_treks"))

    approved_staff = Staff_Profile.query.filter_by(approved=True).all()
    return render_template("admin_edit_trek.html", trek=trek, approved_staff=approved_staff)

@app.route("/admin/trek/delete/<int:trek_id>")
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek_id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash(f"Trek '{trek.trek_name}' deleted.", "warning")
    return redirect(url_for("admin_treks"))


# --------------------------------- Admin Staff Management ---------------------------------

@app.route("/admin/staff")
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
def approve_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    staff.approved = True
    db.session.commit()
    flash(f"{staff.user.name} approved.", "success")
    return redirect(url_for("admin_staff", tab="pending"))


@app.route("/admin/reject_staff/<int:staff_id>", methods=["POST"])
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
def blacklist_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    staff.user.is_blacklisted = True
    db.session.commit()
    flash(f"{staff.user.name} blacklisted.", "danger")
    return redirect(url_for("admin_staff", tab="approved"))


@app.route("/admin/unblacklist_staff/<int:staff_id>")
def unblacklist_staff(staff_id):
    staff = Staff_Profile.query.get_or_404(staff_id)
    staff.user.is_blacklisted = False
    db.session.commit()
    flash(f"{staff.user.name} unblacklisted.", "success")
    return redirect(url_for("admin_staff", tab="blacklisted"))


# --------------------------------- Admin User Management ---------------------------------

@app.route("/admin/users")
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
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = True
    db.session.commit()
    flash(f"{user.name} blacklisted.", "warning")
    return redirect(url_for("admin_users", tab="active"))


@app.route("/admin/unblacklist_user/<int:user_id>")
def unblacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = False
    db.session.commit()
    flash(f"{user.name} unblacklisted.", "success")
    return redirect(url_for("admin_users", tab="blacklisted"))


# --------------------------------- Admin Booking Management ---------------------------------

@app.route("/admin/bookings")
def admin_bookings():
    active_tab   = request.args.get("tab", "booked")
    search_query = request.args.get("search", "")

    def filter_bookings(status):
        q = Booking.query.filter_by(booking_status=status)
        if search_query:
            q = q.join(User).filter(User.name.ilike(f"%{search_query}%"))
        return q.all()

    return render_template("admin_bookings.html",
                           active_tab=active_tab,
                           search_query=search_query,
                           booked=filter_bookings("booked"),
                           cancelled=filter_bookings("cancelled"),
                           completed=filter_bookings("completed"))


# --------------------------------- Trek Staff Dashboard (placeholder) ---------------------------------

@app.route("/trek_staff/dashboard")
def trek_staff_dashboard():
    return "Trek Staff dashboard coming soon"


# --------------------------------- Trekker Dashboard ---------------------------------

@app.route("/trekker/dashboard/<int:user_id>")
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
def trekker_bookings(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id, booking_status="Booked").all()
    return render_template("trekker_bookings.html", user=user, bookings=bookings)


@app.route("/trekker/book/<int:trek_id>/<int:user_id>")
def trekker_booking(trek_id, user_id):
    trek = Trek.query.get_or_404(trek_id)
    user = User.query.get_or_404(user_id)

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
def trekker_cancel_booking(booking_id, user_id):
    booking = Booking.query.get_or_404(booking_id)

    booking.booking_status = "cancelled"
    booking.trek.available_slots += 1

    db.session.commit()
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for("trekker_bookings", user_id=user_id))

@app.route("/trekker/trek/details/<int:trek_id>/<int:user_id>")
def trekker_trek_details(trek_id, user_id):
    trek = Trek.query.get_or_404(trek_id)
    booking = Booking.query.filter_by(trek_id=trek_id, user_id=user_id).first()
    return render_template("trekker_booking_details.html", trek=trek, booking=booking, user_id=user_id)


# --------------------------------- Trekker History ---------------------------------

@app.route("/trekker/history/<int:user_id>")
def trekker_history(user_id):
    user = User.query.get_or_404(user_id)
    history = Booking.query.filter_by(user_id=user_id, booking_status="completed").all()
    return render_template("trekker_history.html", user=user, history=history)



# ----------------------------------------------------------------------------------------------------

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == "__main__":
    app.run(debug=True)
