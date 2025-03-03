from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
USER_SERVICE_URL = "http://user_service:5000"


@app.route('/register', methods=['POST'])
def register():
    try:
        logging.debug(f"Register request data: {request.json}")
        response = requests.post(f"{USER_SERVICE_URL}/register", json=request.json)
        logging.debug(f"Register response status code: {response.status_code}")
        logging.debug(f"Register response content: {response.content}")
        response_data = response.json()
        return jsonify(response_data), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Request to user_service failed: {e}")
        return jsonify({"message": "Internal server error"}), 500

    except ValueError:
        logging.error("Failed to parse JSON response from user_service")
        return jsonify({"message": "Internal server error"}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        logging.debug(f"Login request data: {request.json}")
        response = requests.post(f"{USER_SERVICE_URL}/login", json=request.json)
        logging.debug(f"Login response status code: {response.status_code}")
        logging.debug(f"Login response content: {response.content}")
        response_data = response.json()
        return jsonify(response_data), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Request to user_service failed: {e}")
        return jsonify({"message": "Internal server error"}), 500

    except ValueError:
        logging.error("Failed to parse JSON response from user_service")
        return jsonify({"message": "Internal server error"}), 500


@app.route('/profile', methods=['GET'])
def get_profile():
    try:
        logging.debug(f"Get profile request headers: {request.headers}")
        response = requests.get(f"{USER_SERVICE_URL}/profile", headers=request.headers)
        logging.debug(f"Get profile response status code: {response.status_code}")
        logging.debug(f"Get profile response content: {response.content}")
        response_data = response.json()
        return jsonify(response_data), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Request to user_service failed: {e}")
        return jsonify({"message": "Internal server error"}), 500

    except ValueError:
        logging.error("Failed to parse JSON response from user_service")
        return jsonify({"message": "Internal server error"}), 500


@app.route('/profile', methods=['PUT'])
def update_profile():
    try:
        logging.debug(f"Update profile request headers: {request.headers}")
        logging.debug(f"Update profile request data: {request.json}")
        response = requests.put(f"{USER_SERVICE_URL}/profile", headers=request.headers, json=request.json)

        logging.debug(f"Update profile response status code: {response.status_code}")
        logging.debug(f"Update profile response content: {response.content}")
        response_data = response.json()
        return jsonify(response_data), response.status_code

    except requests.exceptions.RequestException as e:
        logging.error(f"Request to user_service failed: {e}")
        return jsonify({"message": "Internal server error"}), 500

    except ValueError:
        logging.error("Failed to parse JSON response from user_service")
        return jsonify({"message": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
