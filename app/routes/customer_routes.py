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
    payment_method = request.form.get('payment_method')
    delivery_method = request.form.get('delivery_method')
    delivery_distance = request.form.get('distance')

    # Check if a delivery distance is provided and can be converted to a float
    if delivery_distance:
        try:
            delivery_distance = float(delivery_distance)
        except ValueError:
            flash('Invalid delivery distance.', 'error')
            return redirect(url_for('customer_bp.available_items'))
    else:
        delivery_distance = 0.0  # Default value

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

    # Get current customer
    customer = Customer.query.get(customer_id)
    if not customer:
        flash('Customer not found.', 'error')
        return redirect(url_for('customer_bp.available_items'))

    try:
        total_amount = 0.0
        discount_rate = 1.0  # Default discount

        # Check customer type and process order limits
        if isinstance(customer, CorporateCustomer):
            if customer.min_balance < customer.max_credit:
                flash('Your balance is lower than the allowed credit limit. Cannot place an order.', 'error')
                return redirect(url_for('customer_bp.available_items'))
            discount_rate = 0.9  # Corporate customers get a 10% discount
        else:
            if customer.balance > 100:
                flash('You owe more than $100. Cannot place an order.', 'error')
                return redirect(url_for('customer_bp.available_items'))

        # Create new order
        new_order = Order(customer_id=customer_id)
        db.session.add(new_order)
        db.session.flush()  # Ensure order ID is available

        # Process order items and update inventory
        for item in items:
            product_id = item['product_id']
            quantity = float(item['quantity'])  # Ensure quantity is a float
            product = None

            # Differentiate product types and find corresponding products
            if item['type'] == 'pack_veggie':
                product = PackVeggie.query.get(product_id)
                if product.num_of_packs >= quantity:  # Ensure enough stock
                    product.num_of_packs -= quantity  # Deduct stock
                else:
                    flash(f'Not enough packs of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))
            elif item['type'] == 'unit_price_veggie':
                product = UnitPriceVeggie.query.get(product_id)
                if product.quantity >= quantity:  # Ensure enough stock
                    product.quantity -= quantity  # Deduct stock
                else:
                    flash(f'Not enough quantity of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))
            elif item['type'] == 'weighted_veggie':
                product = WeightedVeggie.query.get(product_id)
                if product.weight >= quantity:  # Ensure enough stock
                    product.weight -= quantity  # Deduct stock
                else:
                    flash(f'Not enough weight of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))
            elif item['type'] == 'premade_box':
                product = PremadeBox.query.get(product_id)
                if product.num_of_boxes >= quantity:  # Ensure enough stock
                    product.num_of_boxes -= quantity  # Deduct stock
                else:
                    flash(f'Not enough boxes of {product.description} available.', 'error')
                    return redirect(url_for('customer_bp.available_items'))

            # If product found, add to order
            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price * discount_rate  # Apply discount
                )
                db.session.add(order_item)

                # Calculate total amount
                total_amount += product.price * quantity * discount_rate

        # Handle delivery charges
        if delivery_method == 'delivery':
            if delivery_distance > 20:
                flash('Delivery is only available within 20 km.', 'error')
                return redirect(url_for('customer_bp.available_items'))
            total_amount += 10.00  # Fixed fee

        # Update total amount in order
        new_order.total_amount = total_amount

        # Handle payment
        payment = None  # Initialize payment variable
        if payment_method == 'Credit Card':
            payment = CreditCardPayment(
                payment_date=datetime.now(),
                amount=total_amount,
                card_type=request.form.get('card_type'),
                payment_type=payment_method,
                card_expiry_date=request.form.get('expiry_date')
            )
        elif payment_method == 'Debit Card':
            payment = DebitCardPayment(
                payment_date=datetime.now(),
                amount=total_amount,
                debit_card_number=request.form.get('debit_card_number'),
                payment_type=payment_method,
                bank_name=request.form.get('bank_name')
            )
        elif payment_method == 'Account Payment':
            # Charge to account
            customer.balance += total_amount
            db.session.commit()  # Update balance
        else:
            flash('Invalid payment method.', 'error')
            return redirect(url_for('customer_bp.available_items'))

        # Save payment record and commit inventory changes (only if payment method is not Account Payment)
        if payment:
            db.session.add(payment)

        db.session.commit()

        flash('Order placed successfully!', 'success')  # Success message
        return redirect(url_for('customer_bp.available_items'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Failed to place order. Details: ' + str(e), 'error')
        return redirect(url_for('customer_bp.available_items'))




#4. View the current order details.
#5. If the order has not been fulfilled, you can cancel the current order.
@customer_bp.route('/current_order', methods=['GET', 'POST'])
def current_order():
    if 'customer_id' not in session:
        return redirect('/login')

    customer_id = session['customer_id']
    
    # Query current orders
    current_order = Order.query.filter_by(customer_id=customer_id, status='Pending').order_by(Order.id.desc()).first()
    
    if request.method == 'POST':
        # Cancel order
        if current_order:
            try:
                current_order.status = 'Cancelled'
                db.session.commit()
                return render_template('customer_current_order.html', order=None, message='Order has been cancelled.')
            except Exception as e:
                db.session.rollback()
                return render_template('customer_current_order.html', order=current_order, message='Failed to cancel the order: ' + str(e))

    if current_order is None:
        return render_template('customer_current_order.html', message='No current orders found.')

    # Query order items with corresponding item descriptions
    order_items = (
        db.session.query(OrderItem, Item)
        .join(Item, OrderItem.product_id == Item.id)
        .filter(OrderItem.order_id == current_order.id)
        .all()
    )

    # Pass the items with descriptions to the template
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
        # 获取表单数据
        customer_type = request.form['customer_type']
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        address = request.form['address']
        max_owing = request.form['max_owing']
        
        # 企业客户的额外字段
        min_balance = request.form.get('min_balance')
        max_credit = request.form.get('max_credit')
        discount_rate = 0.9

        # 检查用户名是否已存在
        existing_customer = Customer.query.filter_by(username=username).first()
        if existing_customer:
            flash('Username already exists, please choose a different one.', 'error')
            return redirect(url_for('customer_bp.register'))

        # 加密密码
        hashed_password = hashing.hash_value(password, salt='neal')

        try:
            # 根据客户类型创建私人客户或企业客户
            if customer_type == 'private':
                new_customer = Customer(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    cust_address=address,
                    max_owing=max_owing,
                    balance=0  # 初始余额为0
                )
            elif customer_type == 'corporate':
                new_customer = CorporateCustomer(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    cust_address=address,
                    max_owing=max_owing,
                    balance=0,  # 初始余额为0
                    min_balance=min_balance,
                    max_credit=max_credit,
                    discount_rate=discount_rate
                )

            # 保存到数据库
            db.session.add(new_customer)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('customer_bp.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('customer_bp.register'))

    return render_template('customer_register.html')
