from flask import Flask, jsonify
from pymongo.errors import PyMongoError

from .database import connect


def create_app(testing=False):
    app = Flask(__name__)
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
