from flask import Blueprint, render_template, request, redirect, session, jsonify,url_for,flash
from .. import db
from ..models import Staff, WeightedVeggie, UnitPriceVeggie, PackVeggie,PremadeBox, Order, Customer,OrderItem,Item,Order
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
                'description': order_item.product.description,  # Assuming the product has a description
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