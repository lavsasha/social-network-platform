from functools import wraps
from flask import request, jsonify, current_app
import requests


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing or invalid'}), 401

        try:
            response = requests.get(
                f"{current_app.config['USER_SERVICE_URL']}/user-info",
                headers={'Authorization': token},
                timeout=5
            )

            if response.status_code != 200:
                return jsonify({'error': 'Invalid token'}), 401

            data = response.json()

            if not data.get('user_id'):
                return jsonify({'error': 'Invalid user info'}), 401

            return f(data['user_id'], *args, **kwargs)

        except requests.exceptions.RequestException:
            return jsonify({'error': 'Service unavailable'}), 503
        except Exception:
            return jsonify({'error': 'Internal server error'}), 500

    return decorated
