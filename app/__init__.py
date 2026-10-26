from flask import Flask, jsonify

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

    return app
