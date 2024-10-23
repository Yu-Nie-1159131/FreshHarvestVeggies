-- Create database
DROP DATABASE IF EXISTS fresh_harvest_db;
CREATE DATABASE IF NOT EXISTS fresh_harvest_db;
USE fresh_harvest_db;

-- Create person table
CREATE TABLE person (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create customer table, inheriting from person table
CREATE TABLE customer (
    id INT PRIMARY KEY,
    cust_address VARCHAR(255) NOT NULL,
    max_owing FLOAT NOT NULL,
    balance FLOAT DEFAULT 0.0 NOT NULL,
    FOREIGN KEY (id) REFERENCES person(id)
);

-- Create corporate_customer table, inheriting from customer table
CREATE TABLE corporate_customer (
    id INT PRIMARY KEY,
    min_balance FLOAT NOT NULL,
    max_credit FLOAT NOT NULL,
    discount_rate FLOAT NOT NULL,
    FOREIGN KEY (id) REFERENCES customer(id)
);

-- Create staff table, inheriting from person table
CREATE TABLE staff (
    id INT PRIMARY KEY,
    dept_name VARCHAR(255) NOT NULL,
    date_joined DATE NOT NULL,
    FOREIGN KEY (id) REFERENCES person(id)
);

-- Create orders table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_date DATE NOT NULL,
    status VARCHAR(255) NOT NULL,
    customer_id INT,
    total_amount FLOAT,
    FOREIGN KEY (customer_id) REFERENCES customer(id)
);

-- Create the Item table as a base class
CREATE TABLE item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL
);

-- Create Veggie table, inheriting from Item
CREATE TABLE veggie (
    id INT PRIMARY KEY,
    weight_per_kilo FLOAT NOT NULL,
    FOREIGN KEY (id) REFERENCES Item(id)
);

-- Create PackVeggie table, inherited from Veggie
CREATE TABLE pack_veggie (
    id INT PRIMARY KEY,
    price_per_pack FLOAT NOT NULL,
    num_of_packs INT NOT NULL,
    veg_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (id) REFERENCES Veggie(id)
);

-- Create the UnitPriceVeggie table, inheriting from Veggie
CREATE TABLE unit_price_veggie (
    id INT PRIMARY KEY,
    price_per_unit FLOAT NOT NULL, -- Indicates the price per unit
    quantity INT NOT NULL,
    FOREIGN KEY (id) REFERENCES Veggie(id)
);

-- Create the WeightedVeggie table, inherited from Veggie
CREATE TABLE Weighted_veggie (
    id INT PRIMARY KEY,
    weight FLOAT NOT NULL, -- Indicates the actual weight of the vegetables
    FOREIGN KEY (id) REFERENCES Veggie(id)
);

-- Create premade_box table, inheriting from item table
CREATE TABLE premade_box (
    id INT PRIMARY KEY,
    box_size VARCHAR(255) NOT NULL,
    num_of_boxes INT NOT NULL,
    FOREIGN KEY (id) REFERENCES item(id)
);

-- Create order_items table
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity FLOAT NOT NULL, -- including wweight for weighted veggies
    price FLOAT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES item(id)
);

-- Create payment table
CREATE TABLE payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount FLOAT NOT NULL,
    payment_type ENUM('Credit Card', 'Debit Card', 'Account Balance') NOT NULL,
    order_id INT,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Create credit_card_payment table, inheriting from payment table
CREATE TABLE credit_card_payment (
    id INT PRIMARY KEY,
    card_type VARCHAR(255) NOT NULL,
    card_expiry_date DATE NOT NULL,
    FOREIGN KEY (id) REFERENCES payment(id)
);

-- Create debit_card_payment table, inheriting from payment table
CREATE TABLE debit_card_payment (
    id INT PRIMARY KEY,
    debit_card_number VARCHAR(255) NOT NULL,
    bank_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (id) REFERENCES payment(id)
);