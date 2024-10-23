from . import db
from datetime import datetime
from sqlalchemy import Enum

# Person class as the base class for all people (customers and employees)
class Person(db.Model):
    __tablename__ = 'person'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)

# The Customer class inherits Person
class Customer(Person):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    cust_address = db.Column(db.String(255), nullable=False)
    max_owing = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    orders = db.relationship('Order', back_populates='customer')

# CorporateCustomer Class
class CorporateCustomer(Customer):
    __tablename__ = 'corporate_customer'
    id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    min_balance = db.Column(db.Float, nullable=False)
    max_credit = db.Column(db.Float, nullable=False)
    discount_rate = db.Column(db.Float, nullable=False)

# Employee class inherits Person
class Staff(Person):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    dept_name = db.Column(db.String(255), nullable=False)
    date_joined = db.Column(db.Date, nullable=False)

# Order Class
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(Enum('Pending', 'Completed', 'Cancelled', name='order_status'), default='Pending', nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = db.relationship('Customer', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order')
    payments = db.relationship('Payment', back_populates='order')

# Product class as base class
class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

# Veggie class inherits Item
class Veggie(Item):
    __tablename__ = 'veggie'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    weight_per_kilo = db.Column(db.Float, nullable=False)

# PackVeggie class, inherited from Veggie
class PackVeggie(Veggie):
    __tablename__ = 'pack_veggie'
    id = db.Column(db.Integer, db.ForeignKey('veggie.id'), primary_key=True)
    price_per_pack = db.Column(db.Float, nullable=False)
    num_of_packs = db.Column(db.Integer, nullable=False)
    veg_name = db.Column(db.String(255), nullable=False)

# UnitPriceVeggie class, inherited from Veggie
class UnitPriceVeggie(Veggie):
    __tablename__ = 'unit_price_veggie'
    id = db.Column(db.Integer, db.ForeignKey('veggie.id'), primary_key=True)
    price_per_unit = db.Column(db.Float, nullable=False)  # Price per unit
    quantity = db.Column(db.Integer, nullable=False)

# WeightedVeggie class, inherited from Veggie
class WeightedVeggie(Veggie):
    __tablename__ = 'weighted_veggie'
    id = db.Column(db.Integer, db.ForeignKey('veggie.id'), primary_key=True)
    weight = db.Column(db.Float, nullable=False)  # Actual weight of vegetables

# PremadeBox class inherits Item
class PremadeBox(Item):
    __tablename__ = 'premade_box'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    box_size = db.Column(db.String(255), nullable=False)
    num_of_boxes = db.Column(db.Integer, nullable=False)

# Order Item Class
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # 每项产品的单价
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Item')

# Payment class as base class
class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(Enum('Credit Card', 'Debit Card', 'Account Balance', name='payment_type'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))

    order = db.relationship('Order', back_populates='payments')

# CreditCardPayment Class
class CreditCardPayment(Payment):
    __tablename__ = 'credit_card_payment'
    id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    card_type = db.Column(db.String(50), nullable=False)
    card_expiry_date = db.Column(db.Date, nullable=False)

# DebitCardPayment Class
class DebitCardPayment(Payment):
    __tablename__ = 'debit_card_payment'
    id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    debit_card_number = db.Column(db.String(50), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
