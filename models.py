from flask_sqlalchemy import SQLAlchemy
from datetime import date
from sqlalchemy import UniqueConstraint

db=SQLAlchemy()

class User(db.Model): 
    __tablename__ = "user"
    id = db.Column(db.Integer  , primary_key = True)
    name = db.Column(db.String() , nullable=False)
    email=db.Column(db.String(), unique = True , nullable=False )
    password = db.Column(db.String() , nullable=False)
    phone = db.Column(db.String(15))
    role = db.Column(db.String(), nullable=False , default='trekker')
    #role = db.Column(db.Enum('admin', 'trek_staff', 'trekker', name = 'user_roles'), nullable=False)
    is_blacklisted = db.Column(db.Boolean , nullable= False , default = False)

    # relationship
    bookings = db.relationship( "Booking" ,backref = "user",lazy=True) # One User -> Many Bookings
    staff_profile = db.relationship("Staff_Profile",backref = "user",uselist=False,lazy=True)

class Trek(db.Model):
    __tablename__ = "trek"
    id = db.Column(db.Integer  , primary_key = True)
    trek_name = db.Column(db.String() , nullable = False)
    location = db.Column(db.String(100),nullable=False)
    difficulty = db.Column(db.String(20),nullable=False)
    duration = db.Column(db.Integer,nullable=False)
    available_slots = db.Column(db.Integer,nullable=False)
    trek_status = db.Column(db.String(20),nullable=False,default = "pending")
    #trek_status = db.Column(db.Enum('pending', 'approved', 'Open' , 'Closed' , 'Completed' , name = 'trek_status'), nullable=False)
    start_date = db.Column(db.Date,nullable=False)
    end_date = db.Column(db.Date,nullable=False)
    description = db.Column(db.Text)

    # Relationship 
    staff_id = db.Column(db.Integer,db.ForeignKey("staff_profile.id"), nullable = True)
    bookings = db.relationship("Booking",backref = "trek",lazy=True) # One Trek -> Many Bookings

class Booking(db.Model):
    __tablename__ = "booking"
    id = db.Column(db.Integer  , primary_key = True)
    #booking_date = db.Column(db.Date,nullable=False)
    booking_date = db.Column(db.Date, default=date.today)
    booking_status = db.Column(db.String(20),nullable=False,default = "booked")
    #booking_status = db.Column(db.Enum('Booked', 'Cancelled','Completed' , name = 'booking_status'), nullable = False)
    payment_status = db.Column(db.String(20),nullable=False,default="pending")
    #payment_status = db.Column(db.Enum('pending', 'paid','refunded' , name = 'payment_status'), nullable = False)

    # Relationship
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"), nullable=False) # many     
    trek_id = db.Column(db.Integer,db.ForeignKey("trek.id") , nullable=False)

    # Constraint for Unique bookings
    __table_args__ = (db.UniqueConstraint('user_id','trek_id',name='unique_user_trek'),)

class Staff_Profile(db.Model):
    __tablename__ = "staff_profile"
    id = db.Column(db.Integer  , primary_key = True)
    # name = db.Column(db.String() , nullable=False)
    # email = db.Column(db.String(), unique = True , nullable=False )
    # password = db.Column(db.String() , nullable=False)
    # phone = db.Column(db.String(15))
    description = db.Column(db.Text)
    approved = db.Column(db.Boolean,nullable=False,default=False)

    # Realtionship
    user_id = db.Column(db.Integer , db.ForeignKey("user.id"), unique=True, nullable=False) # One User -> One Staff_Profile
    treks = db.relationship("Trek", backref="staff", lazy=True) # One Staff Profile -> Many Treks
        
    

# Relationships

# User ↔ Booking --- One User -> Many Bookings

# user.bookings
# booking.user

# Trek ↔ Booking --- One Trek -> Many Bookings

# trek.bookings
# booking.trek

# Staff_Profile ↔ Trek --- One Staff Profile -> Many Treks

# staff_profile.treks
# trek.staff

# User ↔ Staff_Profile --- One User -> One Staff_Profile

# user.staff_profile
# staff_profile.user