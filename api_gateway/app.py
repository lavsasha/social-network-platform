from flask import Flask
from routes.posts import posts_bp
from routes.users import users_bp
from routes.statistics import statistics_bp
import os

app = Flask(__name__)

app.config.update({
    'USER_SERVICE_URL': os.getenv('USER_SERVICE_URL', 'http://user_service:5000'),
    'POST_SERVICE_HOST': os.getenv('POST_SERVICE_HOST', 'post_service'),
    'POST_SERVICE_PORT': os.getenv('POST_SERVICE_PORT', '50051'),
    'STATISTIC_SERVICE_HOST': os.getenv('STATISTIC_SERVICE_HOST', 'statistic_service'),
    'STATISTIC_SERVICE_PORT': os.getenv('STATISTIC_SERVICE_PORT', '50052')
})

app.config['JWT_SECRET'] = '12345678'
app.config['JSON_SORT_KEYS'] = False

app.register_blueprint(users_bp, url_prefix='/api/v1')
app.register_blueprint(posts_bp, url_prefix='/api/v1')
app.register_blueprint(statistics_bp, url_prefix='/api/v1')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
