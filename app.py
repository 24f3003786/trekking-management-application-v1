from flask import Flask, render_template, url_for, request, redirect, flash
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
            return redirect(url_for("trekker_dashboard"))
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


# -------------------------------------------------------------------------------

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == "__main__":
    app.run(debug=True)
