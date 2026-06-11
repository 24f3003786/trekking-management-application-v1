from flask import Flask , render_template , url_for , request , redirect
from models import db , User , Trek , Booking , Staff_Profile
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///trekking.db'
app.config['SECRET_KEY']='Vidhya@123'

db.init_app(app)

def create_admin():
    if not User.query.filter_by(role = "admin").first():
        admin = User(name= "Admin" , email='admin@example.com', password = generate_password_hash("admin@123"), phone="9999999999",role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully")
    else:
        print("Admin already exists")
        

with app.app_context():
    db.create_all()
    create_admin()

if __name__=="__main__":
    app.run(debug=True)