from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rides = db.relationship('Ride', backref='creator', lazy=True)
    CIN = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(100), nullable=False)

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    departure = db.Column(db.String(200), nullable=False)
    departure_coordinates = db.Column(db.String(100))
    destination = db.Column(db.String(200), nullable=False)
    destination_coordinates = db.Column(db.String(100))
    departure_time = db.Column(db.DateTime, nullable=False)
    trip_type = db.Column(db.String(50))
    return_time = db.Column(db.DateTime)
    return_destination = db.Column(db.String(200))
    return_destination_coordinates = db.Column(db.String(100))
    preferred_gender = db.Column(db.String(50))
    preferred_music = db.Column(db.String(50))
    smoking_preference = db.Column(db.String(50))
    talkative_preference = db.Column(db.String(50))
    pets_allowed = db.Column(db.String(50))
    air_conditioning = db.Column(db.String(50))
    children_allowed = db.Column(db.String(50))
    carte_grise = db.Column(db.String(100))
    car_type = db.Column(db.String(100))
    car_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    Finished = db.Column(db.Boolean, default=False)  # This is automatically set to False by default


class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    departure=db.Column(db.String(200), nullable=False)
    departure_coordinates = db.Column(db.String(100))
    destination = db.Column(db.String(200), nullable=False)
    destination_coordinates = db.Column(db.String(100))
    departure_time = db.Column(db.DateTime, nullable=False)
    trip_type = db.Column(db.String(50))
    return_time = db.Column(db.DateTime)
    return_destination = db.Column(db.String(200))
    return_destination_coordinates = db.Column(db.String(100))
    preferred_gender = db.Column(db.String(50))
    preferred_music = db.Column(db.String(50))
    smoking_preference = db.Column(db.String(50))
    talkative_preference = db.Column(db.String(50))
    pets_allowed = db.Column(db.String(50))
    air_conditioning = db.Column(db.String(50))
    children_allowed = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
class Satisfaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=True)
    comments = db.Column(db.Text, nullable=False, default='')

    def __repr__(self):
        return f'<Satisfaction {self.id}>'
    