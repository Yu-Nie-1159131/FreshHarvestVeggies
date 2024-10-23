from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprint
    from .routes.customer_routes import customer_bp
    from .routes.staff_routes import staff_bp

    app.register_blueprint(customer_bp)
    app.register_blueprint(staff_bp)

    return app
