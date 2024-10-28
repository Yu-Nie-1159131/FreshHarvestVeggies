import logging
from app import db
from app.models import PackVeggie, UnitPriceVeggie, WeightedVeggie, PremadeBox,Item, Veggie
logger = logging.getLogger(__name__)

def test_login(client):
    logger.info("Starting login test")
    
    # Test login success - follow redirect
    response = client.post('/login', data={
        'username': 'jdoe',
        'password': 'test002'
    })
    assert response.status_code == 302  # Expected redirect status code
    assert response.location == '/dashboard'  # Verify redirect target

    # Test login failure - wrong password
    response = client.post('/login', data={
        'username': 'jdoe',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200  # Login failure should stay on the login page
    assert b"Incorrect password" in response.data
    
    # Test login failure - wrong username and password
    response = client.post('/login', data={
        'username': 'wrongusername',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200  
    assert b"Invalid credentials" in response.data
    

def test_available_items(client, app):
    with app.app_context():
        # Create PackVeggie test data
        pack_veggie = PackVeggie(
            description='Fresh Carrots Pack',
            price=10.0,
            weight_per_kilo=0.5,
            price_per_pack=10.0,
            num_of_packs=20,
            veg_name='Carrots'
        )
        
        # Create UnitPriceVeggie test data
        unit_veggie = UnitPriceVeggie(
            description='Fresh Lettuce',
            price=2.0,
            weight_per_kilo=0.3,
            price_per_unit=2.0,
            quantity=50
        )
        
        # Create WeightedVeggie test data
        weight_veggie = WeightedVeggie(
            description='Fresh Potatoes',
            price=5.0,
            weight_per_kilo=1.0,
            weight=75.0
        )
        
        # Create PremadeBox test data
        premade_box = PremadeBox(
            description='Weekly Veggie Box',
            price=20.0,
            box_size='Large',
            num_of_boxes=15
        )
        
        # Add to database
        db_items = [pack_veggie, unit_veggie, weight_veggie, premade_box]
        for item in db_items:
            db.session.add(item)
        db.session.commit()

        # Test route access
        response = client.get('/available_items')
        assert response.status_code == 200
        
        
        
        # Check the response content
        response_data = response.data.decode('utf-8')

        # Check PackVeggie data
        assert 'Carrots' in response_data
        assert '10.0' in response_data
        assert '20' in response_data  # num_of_packs

        # Check UnitPriceVeggie data
        assert 'Fresh Lettuce' in response_data
        assert '2.0' in response_data
        assert '50' in response_data  # quantity

        # Check the WeightedVeggie data
        assert 'Fresh Potatoes' in response_data
        assert '5.0' in response_data
        assert '75.0' in response_data  # weight

        # Check PremadeBox data
        assert 'Weekly Veggie Box' in response_data
        assert '20.0' in response_data
        assert 'Large' in response_data
        assert '15' in response_data  # num_of_boxes

def test_available_items_empty(client, app):
    """Test the situation when there is no product"""
    with app.app_context():
        response = client.get('/available_items')
        assert response.status_code == 200
        response_data = response.data.decode('utf-8')
        assert 'No' in response_data 

def test_available_items_quantities(client, app):
    """Test whether products with quantity 0 are displayed"""
    with app.app_context():
        # Create a product with a quantity of 0
        empty_pack = PackVeggie(
            description='Out of Stock Pack',
            price=10.0,
            weight_per_kilo=0.5,
            price_per_pack=10.0,
            num_of_packs=0,
            veg_name='Out of Stock'
        )
        
        db.session.add(empty_pack)
        db.session.commit()

        response = client.get('/available_items')
        assert response.status_code == 200

def test_veggie_inheritance(app):
    """Test whether the inheritance relationship is correct"""
    with app.app_context():
       # Create test data
        pack_veggie = PackVeggie(
            description='Test Pack',
            price=10.0,
            weight_per_kilo=0.5,
            price_per_pack=10.0,
            num_of_packs=20,
            veg_name='Test Veg'
        )
        
        db.session.add(pack_veggie)
        db.session.commit()

        # Test inheritance relationship
        # Query by Item
        item = Item.query.first()
        assert item is not None
        assert item.price == 10.0

        # Query via Veggie
        veggie = Veggie.query.first()
        assert veggie is not None
        assert veggie.weight_per_kilo == 0.5

        # Query via PackVeggie
        pack = PackVeggie.query.first()
        assert pack is not None
        assert pack.veg_name == 'Test Veg'