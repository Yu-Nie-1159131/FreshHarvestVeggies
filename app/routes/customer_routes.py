from datetime import datetime
import pytz
from flask import Blueprint, render_template, request, redirect, session, jsonify,flash,url_for
from .. import db
from sqlalchemy.exc import SQLAlchemyError
from ..models import CorporateCustomer, Customer, Veggie, Order, OrderItem, Payment, CreditCardPayment, DebitCardPayment,PremadeBox,Item,PackVeggie,UnitPriceVeggie,WeightedVeggie
from app.utility import hashing

customer_bp = Blueprint('customer_bp', __name__)


@customer_bp.route('/')
@customer_bp.route('/home')
@customer_bp.route('/index')
def index():
    return render_template('index.html')

# 1. Customer login routing
@customer_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        customer = Customer.query.filter_by(username=username).first()
        if customer:
            user_password = customer.password
            if hashing.check_value(user_password, password, salt='neal'):
               session['customer_id'] = customer.id
               session['customer_username'] = customer.username
               return redirect('/dashboard')
            else:
               return "Incorrect password. Please try again."
        else:
            return "Invalid credentials. Please try again."
    return render_template('customer_login.html')

@customer_bp.route('/dashboard', methods=['GET'])
def member_dashboard():
    if 'customer_id' not in session:
        return redirect('/login')
    customer_id = session['customer_id']
    customer_name = session['customer_username']
    
    return render_template('customer_dashboard.html', customer_name=customer_name)
    
# 1. Client logout route
@customer_bp.route('/logout')
def logout():
    session.pop('customer_id', None)
    session.pop('username', None)
    return redirect(url_for('customer_bp.index'))

# 2. Check out the available vegetables and pre-made boxes
@customer_bp.route('/available_items', methods=['GET'])
def available_items():
    # Query available vegetables
    pack_veggies = PackVeggie.query.all()
    unit_price_veggies = UnitPriceVeggie.query.all()
    weight_veggies = WeightedVeggie.query.all()
    
    # Query available prefab boxes
    premade_boxes = PremadeBox.query.all()

    return render_template('customer_available_items.html', pack_veggies=pack_veggies,unit_price_veggies=unit_price_veggies,weight_veggies = weight_veggies, premade_boxes=premade_boxes)

# 3. Place an order for vegetables and pre-made boxes. Pre-made boxes need to be assembled according to size. At checkout, pay for the items using a credit or debit card or have the amount charged to their account.
@customer_bp.route('/order_page')
def order_page():
    if 'customer_id' not in session:
        return redirect('/login')
    # Query all available vegetables and pre-made boxes
    pack_veggies = PackVeggie.query.all()
    unit_price_veggies = UnitPriceVeggie.query.all()
    weighted_veggies = WeightedVeggie.query.all()
    
    return render_template('customer_order_page.html', 
                           pack_veggies=pack_veggies, 
                           unit_price_veggies=unit_price_veggies,
                           weighted_veggies=weighted_veggies)
    
@customer_bp.route('/place_order', methods=['POST'])
def place_order():
    if 'customer_id' not in session:
        return redirect('/login')

    customer_id = session['customer_id']
    delivery_method = request.form.get('delivery_method')
    delivery_distance = request.form.get('distance')

   # Verify delivery distance
    if delivery_distance:
        try:
            delivery_distance = float(delivery_distance)
        except ValueError:
            flash('Invalid delivery distance.', 'error')
            return redirect(url_for('customer_bp.available_items'))
    else:
        delivery_distance = 0.0  # Default distance

    items = []

    # Get all fields starting with 'items['
    for key in request.form.keys():
        if key.startswith('items['):
            index = key[key.index('[') + 1:key.index(']')]
            item_type = request.form.get(f'items[{index}][type]')
            product_id = request.form.get(f'items[{index}][product_id]')
            quantity = request.form.get(f'items[{index}][quantity]')
            if quantity and float(quantity) > 0:  # Ensure quantity is greater than 0
               existing_item = next((item for item in items if item['product_id'] == product_id), None)
               if not existing_item:
                     items.append({
                        'type': item_type,
                        'product_id': product_id,
                        'quantity': quantity
                    })

    if not items:
        flash('No items in the order.', 'error')
        return redirect(url_for('customer_bp.available_items'))

    # Getting current customer
    customer = Customer.query.get(customer_id)
    if not customer:
        flash('Customer not found.', 'error')
        return redirect(url_for('customer_bp.available_items'))

    try:
        total_amount = 0.0
        discount_rate = 1.0  # Default rate

        # Check customer type and process order restrictions
        co_Customer = db.session.query(CorporateCustomer).filter(CorporateCustomer.id == customer_id).first()
        if co_Customer is not None:
            if co_Customer.min_balance < co_Customer.max_credit:
                flash('Your balance is lower than the allowed credit limit. Cannot place an order.', 'error')
                return redirect(url_for('customer_bp.available_items'))
            discount_rate = 0.9  # 10% discount for corporate customers
        else:
            if customer.balance < 0:
                flash('Your balance is not enough. Cannot place an order.', 'error')
                return redirect(url_for('customer_bp.available_items'))

        # Create a new order
        new_order = Order(customer_id=customer_id)
        db.session.add(new_order)
        db.session.flush()  # Ensure the order ID is available

        # Process order items and update inventory
        for item in items:
            product_id = item['product_id']
            quantity = float(item['quantity'])
            product = None

            if item['type'] == 'pack_veggie':
                product = PackVeggie.query.get(product_id)
                if product.num_of_packs >= quantity:
                    product.num_of_packs -= quantity
                else:
                    flash(f'Not enough packs of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))
            elif item['type'] == 'unit_price_veggie':
                product = UnitPriceVeggie.query.get(product_id)
                if product.quantity >= quantity:
                    product.quantity -= quantity
                else:
                    flash(f'Not enough quantity of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))
            elif item['type'] == 'weighted_veggie':
                product = WeightedVeggie.query.get(product_id)
                if product.weight >= quantity:
                    product.weight -= quantity
                else:
                    flash(f'Not enough weight of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))
            elif item['type'] == 'premade_box':
                product = PremadeBox.query.get(product_id)
                if product.num_of_boxes >= quantity:
                    product.num_of_boxes -= quantity
                else:
                    flash(f'Not enough boxes of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))

            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price * discount_rate  # Applying Discounts
                )
                db.session.add(order_item)
                total_amount += product.price * quantity * discount_rate

        # Handling shipping costs
        if delivery_method == 'delivery':
            if delivery_distance > 20:
                flash('Delivery is only available within 20 km.', 'error')
                return redirect(url_for('customer_bp.available_items'))
            total_amount += 10.00  # Fixed delivery fee
        
        # if customer order more items than max owning, then return an error
        if co_Customer is None and total_amount > customer.max_owing:
            flash('Your order amount is over your max owning. Cannot place an order.', 'error')
            return redirect(url_for('customer_bp.available_items'))
        new_order.total_amount = total_amount
        db.session.commit()

        # Save the order ID for payment processing
        session['order_id'] = new_order.id
        flash('Order placed successfully! Please proceed to payment.', 'success')
        return redirect(url_for('customer_bp.available_items'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Failed to place order. Details: ' + str(e), 'error')
        return redirect(url_for('customer_bp.available_items'))


@customer_bp.route('/process_payment/<int:order_id>', methods=['GET', 'POST'])
def process_payment(order_id):
    # Check if the customer is logged in
    if 'customer_id' not in session:
        return redirect('/login')

    # Retrieve the current order by order ID
    order = Order.query.get(order_id)
    if not order:
        return "Order not found", 404

    # If the order is not found, redirect to available items
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('customer_bp.available_items'))

    # Handle the POST request when the form is submitted
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')

        try:
            payment = None
            total_amount = order.total_amount

            # Handle credit card payment
            if payment_method == 'Credit Card':
                payment = CreditCardPayment(
                    payment_date=datetime.now(),
                    amount=total_amount,
                    card_type=request.form.get('card_type'),
                    payment_type=payment_method,
                    card_expiry_date=request.form.get('expiry_date')
                )
            # Handle debit card payment
            elif payment_method == 'Debit Card':
                payment = DebitCardPayment(
                    payment_date=datetime.now(),
                    amount=total_amount,
                    debit_card_number=request.form.get('debit_card_number'),
                    payment_type=payment_method,
                    bank_name=request.form.get('bank_name')
                )
            # Handle account payment
            elif payment_method == 'Account Payment':
                customer = Customer.query.get(order.customer_id)
                co_Customer = db.session.query(CorporateCustomer).filter(CorporateCustomer.id == order.customer_id).first()
                if co_Customer is not None:  # Check if customer is a CorporateCustomer
                    if co_Customer.min_balance  >=  co_Customer.max_credit:  # Check if balance is enough for CorporateCustomer
                        co_Customer.min_balance -= total_amount  # Deduct from min_balance
                    else:
                        flash('Insufficient balance for Account Payment.', 'error')
                        return redirect(url_for('customer_bp.process_payment', order_id=order_id))
                else:
                    if customer.balance < -100:  # For regular customers, check if balance is below -100
                        customer.balance -= total_amount  # Deduct from balance
                        db.session.commit()  # Update balance in the database
                    else:
                        flash('Insufficient balance for Account Payment.', 'error')
                        return redirect(url_for('customer_bp.process_payment', order_id=order_id))
            else:
                flash('Invalid payment method.', 'error')
                return redirect(url_for('customer_bp.process_payment', order_id=order_id))

            # Add the payment record to the session
            if payment:
                db.session.add(payment)

            # Mark the order as completed
            order.status = 'Completed'
            db.session.commit()

            flash('Payment successful and order completed!', 'success')
            return redirect(url_for('customer_bp.available_items'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Payment failed. Details: ' + str(e), 'error')
            return redirect(url_for('customer_bp.process_payment', order_id=order_id))

    # Render the payment page
    return render_template('customer_process_payment.html', order=order)







#4. View the current order details.
#5. If the order has not been fulfilled, you can cancel the current order.
@customer_bp.route('/current_order', methods=['GET', 'POST'])
def current_order():
    if 'customer_id' not in session:
        return redirect('/login')

    customer_id = session['customer_id']
    
    # Query the current order
    current_order = Order.query.filter_by(customer_id=customer_id, status='Pending').order_by(Order.id.desc()).first()
    
    if request.method == 'POST':
        # Check if the order exists
        if current_order:
            try:
                # Get the order items associated with the current order
                order_items = db.session.query(OrderItem).filter(OrderItem.order_id == current_order.id).all()

                for order_item in order_items:
                    
                    weightedV = db.session.query(WeightedVeggie).filter(WeightedVeggie.id == order_item.product_id).first()
                    packV = db.session.query(PackVeggie).filter(PackVeggie.id == order_item.product_id).first()
                    premadeBox = db.session.query(PremadeBox).filter(PremadeBox.id == order_item.product_id).first()
                    unitPriceV = db.session.query(UnitPriceVeggie).filter(UnitPriceVeggie.id == order_item.product_id).first()

                    # Restore the inventory based on the item type
                    if weightedV is not None:
                        weightedV.weight += order_item.quantity  # Restore weight
                    if packV is not None:
                        packV.num_of_packs += order_item.quantity  # Restore number of packs
                    if unitPriceV is not None:
                        unitPriceV.quantity += order_item.quantity  # Restore quantity
                    if premadeBox is not None:
                        premadeBox.num_of_boxes += order_item.quantity  # Restore number of boxes

                # Cancel the order
                current_order.status = 'Cancelled'

                # Commit changes
                db.session.commit()

                return render_template('customer_current_order.html', order=None, message='Order has been cancelled, and the stock has been updated.')
            except Exception as e:
                db.session.rollback()
                return render_template('customer_current_order.html', order=current_order, message='Failed to cancel the order: ' + str(e))

    if current_order is None:
        return render_template('customer_current_order.html', message='No current orders found.')

    # Query order items and corresponding product descriptions
    order_items = (
        db.session.query(OrderItem, Item)
        .join(Item, OrderItem.product_id == Item.id)
        .filter(OrderItem.order_id == current_order.id)
        .all()
    )

    # Pass order and product description to the template
    return render_template('customer_current_order.html', order=current_order, items=order_items)

#6. View previous order details.
@customer_bp.route('/previous_orders', methods=['GET'])
def previous_orders():
    if 'customer_id' not in session:
        return redirect('/login')

    customer_id = session['customer_id']
    
    # Query all completed orders
    latest_order = Order.query.filter_by(customer_id=customer_id, status='Pending').order_by(Order.id.desc()).first()
    previous_orders = Order.query.filter(Order.customer_id == customer_id, Order.id != latest_order.id).all() if latest_order else Order.query.filter_by(customer_id=customer_id).all()

    if not previous_orders:
        return render_template('customer_previous_orders.html', message='No previous orders found.')

    # Create a dictionary to hold order items and their corresponding descriptions
    order_items_map = {}
    
    for order in previous_orders:
        # Query the items for each order
        order_items = (
            db.session.query(OrderItem, Item)
            .join(Item, OrderItem.product_id == Item.id)
            .filter(OrderItem.order_id == order.id)
            .all()
        )
        order_items_map[order.id] = order_items

    return render_template('customer_previous_orders.html', orders=previous_orders, order_items_map=order_items_map)


#7. View their own details.
@customer_bp.route('/view_profile', methods=['GET'])
def view_profile():
    if 'customer_id' not in session:
        return redirect('/login')

    customer_id = session['customer_id']
    
    # Query customer information
    customer = Customer.query.get(customer_id)
    
    if customer is None:
        return render_template('customer_view_profile.html', message='Customer not found.')

    return render_template('customer_view_profile.html', customer=customer)

@customer_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        customer_type = request.form['customer_type']
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        address = request.form['address']
        balance = request.form['balance']
        
        # Additional fields for enterprise customers
        min_balance = request.form.get('min_balance')
        max_credit = request.form.get('max_credit')
        discount_rate = 0.9

        # Check if the username already exists
        existing_customer = Customer.query.filter_by(username=username).first()
        if existing_customer:
            flash('Username already exists, please choose a different one.', 'error')
            return redirect(url_for('customer_bp.register'))

        # Encrypted password
        hashed_password = hashing.hash_value(password, salt='neal')

        try:
            # Create private customers or corporate customers based on customer type
            if customer_type == 'private':
                new_customer = Customer(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    cust_address=address,
                    max_owing=100, # Initial max owning is 0
                    balance=balance  
                )
            elif customer_type == 'corporate':
                new_customer = CorporateCustomer(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    cust_address=address,
                    max_owing=100, # Initial max owning is 0
                    balance=balance,  
                    min_balance=min_balance,
                    max_credit=max_credit,
                    discount_rate=discount_rate
                )

            # Save to database
            db.session.add(new_customer)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('customer_bp.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('customer_bp.register'))

    return render_template('customer_register.html')
