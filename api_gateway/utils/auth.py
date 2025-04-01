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
                headers={'Authorization': token}
            )
            response.raise_for_status()
            data = response.json()

            if 'user_id' not in data:
                return jsonify({'error': 'User info does not contain user_id'}), 401

            user_id = data['user_id']
            return f(user_id, *args, **kwargs)

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return jsonify({'error': 'Invalid or expired token'}), 401
            return jsonify({'error': f'User service error: {str(e)}'}), 500
        except requests.exceptions.RequestException as e:
            return jsonify({'error': 'User service unavailable'}), 503
        except KeyError as e:
            return jsonify({'error': f'Invalid user info response: missing {str(e)}'}), 401
        except Exception as e:
            current_app.logger.error(f'Unexpected error in token_required: {repr(e)}', exc_info=True)
            return jsonify({'error': 'Invalid token'}), 401

    return decorated
