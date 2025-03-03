from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.String(36), primary_key=True)
    role_id = db.Column(db.String(36), db.ForeignKey('user_role.role_id'), nullable=False)
    login = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    role = db.relationship('UserRole', backref='users')


class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    profile_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    avatar_url = db.Column(db.String(200))
    about_me = db.Column(db.Text)
    city = db.Column(db.String(80))
    education = db.Column(db.String(80))
    interests = db.Column(db.String(200))
    date_of_birth = db.Column(db.DateTime)
    phone_number = db.Column(db.String(20))


class UserRole(db.Model):
    __tablename__ = 'user_role'
    role_id = db.Column(db.String(36), primary_key=True)
    role_name = db.Column(db.String(80), nullable=False)
    role_description = db.Column(db.Text)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
