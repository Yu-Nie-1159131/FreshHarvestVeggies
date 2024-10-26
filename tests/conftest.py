import os
import sys
import pytest
import logging

# Set the log file path to the project root directory
log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_debug.log')

#Configure logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import Customer
from app.utility import hashing

@pytest.fixture
def app():
    logger.info("Setting up test app")
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        db.create_all()
        
        # Log the password hash creation process
        password_hash = hashing.hash_value('test002', salt='neal')
        logger.debug(f"Created password hash: {password_hash}")
        
        test_customer = Customer(
            username='jdoe',
            password=password_hash,
            first_name='John',
            last_name='Doe',
            cust_address='123 Test St, Test City',
            max_owing=1000.0,
            balance=0.0
        )
        
        db.session.add(test_customer)
        db.session.commit()       
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()