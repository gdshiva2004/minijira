from flask import Flask, jsonify

from .config import Config
from .database import init_db
from .errors import ApiError


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    init_db(app)

    from .routes import api

    app.register_blueprint(api)

    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_405(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_500(_):
        return jsonify({"error": "Internal server error"}), 500

    return app
