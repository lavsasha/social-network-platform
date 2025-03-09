from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
app.config['JWT_SECRET'] = 'your-secret-key'
USER_SERVICE_URL = "http://user_service:5000"


@app.route('/register', methods=['POST'])
def register():
    try:
        response = requests.post(f"{USER_SERVICE_URL}/register", json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"message": "Internal server error"}), 500
    except ValueError:
        return jsonify({"message": "Internal server error"}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        response = requests.post(f"{USER_SERVICE_URL}/login", json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"message": "Internal server error"}), 500
    except ValueError:
        return jsonify({"message": "Internal server error"}), 500


@app.route('/profile', methods=['GET'])
def get_profile():
    try:
        response = requests.get(f"{USER_SERVICE_URL}/profile", headers=request.headers)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"message": "Internal server error"}), 500
    except ValueError:
        return jsonify({"message": "Internal server error"}), 500


@app.route('/profile', methods=['PUT'])
def update_profile():
    try:
        response = requests.put(f"{USER_SERVICE_URL}/profile", headers=request.headers, json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException:
        return jsonify({"message": "Internal server error"}), 500
    except ValueError:
        return jsonify({"message": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
