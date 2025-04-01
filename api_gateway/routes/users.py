from flask import Blueprint, request, jsonify, current_app
import requests

users_bp = Blueprint('users', __name__)


@users_bp.route('/register', methods=['POST'])
def register():
    try:
        response = requests.post(
            f"{current_app.config['USER_SERVICE_URL']}/register",
            json=request.json
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': str(e.response.json())}), e.response.status_code
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503


@users_bp.route('/login', methods=['POST'])
def login():
    try:
        response = requests.post(
            f"{current_app.config['USER_SERVICE_URL']}/login",
            json=request.json,
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': str(e.response.json())}), e.response.status_code
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503


@users_bp.route('/profile', methods=['GET'])
def get_profile():
    try:
        response = requests.get(
            f"{current_app.config['USER_SERVICE_URL']}/profile",
            headers=request.headers,
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': str(e.response.json())}), e.response.status_code
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503


@users_bp.route('/profile', methods=['PUT'])
def update_profile():
    try:
        response = requests.put(
            f"{current_app.config['USER_SERVICE_URL']}/profile",
            headers=request.headers,
            json=request.json,
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': str(e.response.json())}), e.response.status_code
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503

@users_bp.route('/user-info', methods=['GET'])
def get_user_info():
    try:
        response = requests.get(
            f"{current_app.config['USER_SERVICE_URL']}/user-info",
            headers=request.headers,
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': str(e.response.json())}), e.response.status_code
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503


@users_bp.route('/health', methods=['GET'])
def health():
    try:
        response = requests.get(
            f"{current_app.config['USER_SERVICE_URL']}/health",
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({'error': 'User service unavailable'}), 503
