import json
from flask import Blueprint, render_template, request, redirect, session, jsonify,url_for,flash
from .. import db
from ..models import Staff, WeightedVeggie, UnitPriceVeggie, PackVeggie,PremadeBox, Order, Customer,OrderItem,Item,Order,CreditCardPayment,DebitCardPayment
from datetime import datetime, timedelta
import pytz
from sqlalchemy.sql import func
from app.utility import hashing

staff_bp = Blueprint('staff_bp', __name__)

# 1. Staff login routing
@staff_bp.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        staff = Staff.query.filter_by(username=username).first()
        if staff:
            user_password = staff.password
            if hashing.check_value(user_password, password, salt='neal'):
               session['staff_id'] = staff.id
               session['staff_username'] = staff.username
               return redirect('/staff/dashboard')
            else:
                return "Incorrect password. Please try again."
        else:
            return "Invalid credentials. Please try again."
    return render_template('staff_login.html')

# 1. Staff logout route
@staff_bp.route('/staff/logout')
def staff_logout():
    session.pop('staff_id', None)
    session.pop('staff_username', None)
    return redirect(url_for('customer_bp.index'))

# Staff Dashboard
@staff_bp.route('/staff/dashboard')
def staff_dashboard():
    if 'staff_id' not in session:
        return redirect('/staff/login')
    return render_template('staff_dashboard.html')

#2. Check out all the veggie and pre-made boxes.
@staff_bp.route('/staff/items', methods=['GET'])
def view_items():
    # Fetch all items categorized by type
    weighted_veggies = WeightedVeggie.query.all()
    unit_price_veggies = UnitPriceVeggie.query.all()
    pack_veggies = PackVeggie.query.all()
    premade_boxes = PremadeBox.query.all()

    # Rendering the template and passing data
    return render_template('staff_items.html', 
                           weighted_veggies=weighted_veggies, 
                           unit_price_veggies=unit_price_veggies, 
                           pack_veggies=pack_veggies, 
                           premade_boxes=premade_boxes)

# 3. View all current orders
@staff_bp.route('/staff/current_orders', methods=['GET'])
def view_all_current_orders():
    # Fetch all orders that are currently 'Pending'
    current_orders = Order.query.filter(Order.status == 'Pending').all()

    # Create a dictionary to map each order to its items
    orders_with_items = []
    for order in current_orders:
        # Access the associated customer
        customer = order.customer  
        
        # Prepare the order data, including customer information
        order_data = {
            'order': order,
            'customer_name': f"{customer.first_name} {customer.last_name}",  # Customer's full name
            'items': []
        }

        # For each order, fetch the order items and their associated products
        for order_item in order.order_items:
            item_data = {
                'product_id': order_item.product_id,
                'description': order_item.product.description,  # description of product
                'quantity': order_item.quantity,
                'price': order_item.price
            }
            order_data['items'].append(item_data)

        orders_with_items.append(order_data)

    return render_template('staff_current_orders.html', orders_with_items=orders_with_items)

# 4. View all previous orders
@staff_bp.route('/staff/previous_orders', methods=['GET'])
def view_all_previous_orders():
    previous_orders = Order.query.filter(Order.status != 'Pending').all()
    
    # Calculate the total amount of each order
    for order in previous_orders:
        order.total_amount = sum(item.price * item.quantity for item in order.order_items)
    
    return render_template('staff_previous_orders.html', previous_orders=previous_orders)

# 5. Update order status
@staff_bp.route('/staff/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status not in ['Pending', 'Completed', 'Cancelled']:
        flash('Invalid status selected.', 'error')
        return redirect(url_for('staff_bp.view_all_current_orders'))

    # Update the order status
    order.status = new_status
    db.session.commit()
    
    flash(f'Order {order_id} status updated to {new_status}.', 'success')
    return redirect(url_for('staff_bp.view_all_current_orders'))

# 6. View all customers 
@staff_bp.route('/staff/customers', methods=['GET'])
def get_all_customers():
    customers = Customer.query.all()  # Query all customers
    customer_list = []

    for customer in customers:
        customer_data = {
            'custID': customer.id,
            'username': customer.username,
            'firstName': customer.first_name,
            'lastName': customer.last_name,
            'custAddress': customer.cust_address,
            'maxOwing': customer.max_owing,
            'custBalance': customer.balance,
            'listOfOrders': [order.id for order in customer.orders],
        }
        customer_list.append(customer_data)

    return render_template('staff_customer_list.html', customers=customer_list)  # 渲染客户列表模板

# 7. View details of a specific customer
@staff_bp.route('/staff/customer/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    customer = Customer.query.get(customer_id)  # Query customers by customer ID
    if customer is None:
        return "Customer not found", 404

    # Fetch orders for the customer and gather details
    order_details = []
    for order in customer.orders:
        order_info = {
            'order_id': order.id,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),  # Format the order date
            'status': order.status,
            'total_amount': order.total_amount,
            'items': [
                {
                    'product_id': item.product_id,
                    'description': item.product.description,  # Access the product description
                    'quantity': item.quantity,
                    'price': item.price
                } for item in order.order_items  # Change this to order.order_items
            ]
        }
        order_details.append(order_info)

    customer_data = {
        'custID': customer.id,
        'username': customer.username,
        'firstName': customer.first_name,
        'lastName': customer.last_name,
        'custAddress': customer.cust_address,
        'maxOwing': customer.max_owing,
        'custBalance': customer.balance,
        'listOfOrders': order_details,  # Pass detailed order info
    }

    return render_template('staff_customer_detail.html', customer=customer_data)  # Render the customer details template


# 8. Generate total sales for a week, month, and year
@staff_bp.route('/staff/sales_summary', methods=['GET'])
def get_sales_summary():
    # Get the current date
    nz_timezone = pytz.timezone('Pacific/Auckland')
    now = datetime.now(nz_timezone)

    # Calculate sales for a week
    week_start = now - timedelta(days=7)
    week_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date >= week_start).scalar() or 0.0

    # Calculate sales for a month
    month_start = now - timedelta(days=30)
    month_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date >= month_start).scalar() or 0.0

    # Calculate sales for one year
    year_start = now - timedelta(days=365)
    year_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date >= year_start).scalar() or 0.0

    # Pass the sales amount to the template
    return render_template('staff_sales_summary.html', week_sales=week_sales, month_sales=month_sales, year_sales=year_sales)

# 9. Check out the most popular items
@staff_bp.route('/staff/popular_items', methods=['GET'])
def get_popular_items():
    # Query the most popular products
    popular_items = (
        db.session.query(Item.description, func.sum(OrderItem.quantity).label('total_quantity'))
        .join(OrderItem, OrderItem.product_id == Item.id)
        .group_by(Item.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)  # Get the top 10 most popular products
        .all()
    )

    return render_template('staff_popular_items.html', popular_items=popular_items)

@staff_bp.route('/staff/submit_order', methods=['GET', 'POST'])
def submit_order():
    if request.method == 'GET':
        customers = Customer.query.all()
        pack_veggies = PackVeggie.query.all()
        unit_price_veggies = UnitPriceVeggie.query.all()
        weight_veggies = WeightedVeggie.query.all()
        premade_boxes = PremadeBox.query.all()
        
        return render_template('staff_create_new_order.html', 
                               customers=customers, 
                               pack_veggies=pack_veggies, 
                               unit_price_veggies=unit_price_veggies, 
                               weight_veggies=weight_veggies, 
                               premade_boxes=premade_boxes)

    elif request.method == 'POST':
        customer_id = request.form.get('customer_id')
        
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
          return redirect(url_for('staff_bp.submit_order'))
        # Create an order object
        new_order = Order(customer_id=customer_id, status='Pending', total_amount=0)
        db.session.add(new_order)
        db.session.flush()  # Ensure order ID is available

        total_amount = 0  # Initialize total_amount
        # Process items based on their types
        for item in items:
            item_type = item['type']
            product_id = item['product_id']
            quantity = item['quantity']

            # Process the item according to its type
            if item_type == 'pack_veggie':
                veggie = PackVeggie.query.get(product_id)
                if veggie and veggie.num_of_packs >= int(quantity):
                    veggie.num_of_packs -= int(quantity)
                    order_item = OrderItem(order_id=new_order.id,product_id=product_id, quantity=int(quantity), price=veggie.price_per_pack)
                    db.session.add(order_item)
                    total_amount += veggie.price_per_pack * int(quantity)

            elif item_type == 'unit_price_veggie':
                veggie = UnitPriceVeggie.query.get(product_id)
                if veggie and veggie.quantity >= int(quantity):
                    veggie.quantity -= int(quantity)
                    order_item = OrderItem(order_id=new_order.id,product_id=product_id, quantity=int(quantity), price=veggie.price_per_unit)
                    db.session.add(order_item)
                    total_amount += veggie.price_per_unit * int(quantity)

            elif item_type == 'weighted_veggie':
                veggie = WeightedVeggie.query.get(product_id)
                if veggie and veggie.weight >= float(quantity):
                    veggie.weight -= float(quantity)
                    order_item = OrderItem(order_id=new_order.id,product_id=product_id, quantity=float(quantity), price=veggie.price_per_kg)
                    db.session.add(order_item)
                    total_amount += veggie.price_per_kg * float(quantity)

            elif item_type == 'premade_box':
                box = PremadeBox.query.get(product_id)
                if box and box.num_of_boxes >= int(quantity):
                    box.num_of_boxes -= int(quantity)
                    order_item = OrderItem(order_id=new_order.id,product_id=product_id, quantity=int(quantity), price=box.price)
                    db.session.add(order_item)
                    total_amount += box.price * int(quantity)

        # Set the total amount for the order
        new_order.total_amount = total_amount
        db.session.add(new_order)  # Add the order to the session
        db.session.commit()  # Commit the session

        # Redirect or render a new page to display the order details
        return redirect(url_for('staff_bp.staff_dashboard'))




# Display the payment page
@staff_bp.route('/staff/payment/<int:order_id>', methods=['GET'])
def payment_page(order_id):
    order = Order.query.get(order_id)
    if not order:
        return "Order not found", 404

    return render_template('staff_process_payment.html', order=order)


# Processing Payments
@staff_bp.route('/staff/process_payment/<int:order_id>', methods=['POST'])
def process_payment(order_id):
    order = Order.query.get(order_id)
    if not order:
        return "Order not found", 404

    payment_method = request.form.get('payment_method')
    total_amount = order.total_amount

    if payment_method == 'Credit Card':
        # Create a CreditCardPayment object
        payment = CreditCardPayment(
            payment_date=datetime.now(),
            amount=total_amount,
            card_type=request.form.get('card_type'),  # Make sure there is card_type in the form
            payment_type=payment_method,  
            card_expiry_date=request.form.get('expiry_date')  
        )
        db.session.add(payment)

    elif payment_method == 'Debit Card':
        # Create a DebitCardPayment object
        payment = DebitCardPayment(
            payment_date=datetime.now(),
            amount=total_amount,
            debit_card_number=request.form.get('debit_card_number'),  
            payment_type=payment_method,  
            bank_name=request.form.get('bank_name')  
        )
        db.session.add(payment)

    elif payment_method == 'Account Payment':
       # If it is an account payment, update the customer balance
        customer = Customer.query.get(order.customer_id)
        customer.balance += total_amount  # Balance increases
        payment_type = payment_method 

    else:
        return "Invalid payment method", 400

    # Submit the changes and update the order status to completed
    order.status = 'Completed'
    db.session.commit()

    return redirect(url_for('staff_bp.view_all_current_orders'))

