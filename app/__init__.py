from flask import Flask, jsonify
from pymongo.errors import PyMongoError

from .config import JWT_SECRET, JWT_EXPIRES_MINUTES
from .database import connect

TEST_SECRET = "test-secret-key-used-only-by-the-automated-tests"
MIN_SECRET_LENGTH = 32


def create_app(testing=False):
    secret = JWT_SECRET
    if testing and not secret:
        secret = TEST_SECRET
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            "JWT_SECRET is missing or too short. Add a line like JWT_SECRET=<64 random characters> "
            "to your .env file. Generate one with: "
            'python -c "import secrets; print(secrets.token_hex(32))"'
        )

    app = Flask(__name__)
    app.config["JWT_SECRET"] = secret
    app.config["JWT_EXPIRES_MINUTES"] = JWT_EXPIRES_MINUTES
    app.config["PASSWORD_HASH_METHOD"] = "pbkdf2:sha256:1000" if testing else "pbkdf2:sha256"
    connect(app, testing)

    from .routes import api
    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(PyMongoError)
    def database_error(e):
        return jsonify({"error": "Database error, please try again later"}), 503

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
