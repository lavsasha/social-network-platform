from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import time
import uuid
from .models import db, User, UserProfile, UserRole
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db/user_db'
app.config['JWT_SECRET'] = 'your-secret-key'
db.init_app(app)

with app.app_context():
    time.sleep(10)
    db.create_all()


def generate_jwt(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')


def decode_jwt(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(login=data['login']).first():
        return jsonify({"message": "Login is already taken."}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email is already registered."}), 400
    user_id = str(uuid.uuid4())
    role_id = str(uuid.uuid4())
    user_role = UserRole(
        role_id=role_id,
        role_name='user',
        role_description='Regular user',
        assigned_at=func.now()
    )
    hashed_password = generate_password_hash(data['password'], method='scrypt')
    new_user = User(
        user_id=user_id,
        role_id=role_id,
        login=data['login'],
        email=data['email'],
        hashed_password=hashed_password,
        first_name=data.get('first_name'),
        last_name=data.get('last_name')
    )
    db.session.add(user_role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully."}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(login=data['login']).first()
    if user and check_password_hash(user.hashed_password, data['password']):
        token = generate_jwt(user.user_id)
        return jsonify({"token": token}), 200
    return jsonify({"message": "Invalid credentials"}), 401


@app.route('/profile', methods=['GET'])
def get_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    payload = decode_jwt(token)
    if not payload:
        return jsonify({"message": "Invalid or expired token"}), 401
    user = User.query.get(payload['user_id'])
    if user:
        return jsonify({
            "login": user.login,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.role_name,
            "profile": {
                "avatar_url": user.profile.avatar_url if user.profile else None,
                "about_me": user.profile.about_me if user.profile else None,
                "city": user.profile.city if user.profile else None,
                "education": user.profile.education if user.profile else None,
                "interests": user.profile.interests if user.profile else None,
                "date_of_birth": user.profile.date_of_birth.isoformat() if user.profile and user.profile.date_of_birth else None,
                "phone_number": user.profile.phone_number if user.profile else None
            }
        }), 200
    return jsonify({"message": "User not found"}), 404


@app.route('/profile', methods=['PUT'])
def update_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    payload = decode_jwt(token)
    if not payload:
        return jsonify({"message": "Invalid or expired token"}), 401
    user = User.query.get(payload['user_id'])
    if user:
        data = request.json
        if 'login' in data or 'password' in data:
            return jsonify({"message": "Updating login or password is not allowed"}), 400
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'profile' in data:
            profile_data = data['profile']
            if not user.profile:
                user.profile = UserProfile(profile_id=str(uuid.uuid4()), user_id=user.user_id)
            if 'avatar_url' in profile_data:
                user.profile.avatar_url = profile_data['avatar_url']
            if 'about_me' in profile_data:
                user.profile.about_me = profile_data['about_me']
            if 'city' in profile_data:
                user.profile.city = profile_data['city']
            if 'education' in profile_data:
                user.profile.education = profile_data['education']
            if 'interests' in profile_data:
                user.profile.interests = profile_data['interests']
            if 'date_of_birth' in profile_data:
                user.profile.date_of_birth = datetime.datetime.fromisoformat(profile_data['date_of_birth'])
            if 'phone_number' in profile_data:
                user.profile.phone_number = profile_data['phone_number']
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    return jsonify({"message": "User not found"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
