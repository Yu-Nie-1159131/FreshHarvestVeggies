from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # First load the default configuration
    app.config.from_object('config.Config')
    
    # If a test configuration is provided, it overrides the default configuration
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprint
    from .routes.customer_routes import customer_bp
    from .routes.staff_routes import staff_bp

    app.register_blueprint(customer_bp)
    app.register_blueprint(staff_bp)

    return app