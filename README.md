# FreshHarvestVeggies Order Management System
An online order management system for Fresh Harvest Veggies, built with Flask and SQLAlchemy. This system manages customer accounts, orders, and inventory, with both staff and customer interfaces.

# Table of Contents
Installation
Configuration
Deployment
Usage
Test Credentials

# Installation

## Requirements
Python 3.10+
MySQL (or compatible database)

### Step 1: Clone the Repository
bash
Copy code
git clone https://github.com/Yu-Nie-1159131/FreshHarvestVeggies.git
cd FreshHarvestVeggies

### Step 2: Create and Activate a Virtual Environment
#### On Windows:

bash
Copy code
python -m venv myenv
myenv\Scripts\activate

#### On macOS/Linux:

bash
python3 -m venv myenv
source myenv/bin/activate

### Step 3: Install Requirements

bash
pip install -r requirements.txt

# Configuration
## Database Setup
1. Create a MySQL database for your project.

2. Update the database URI in config.py with your MySQL database details:

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/db_name'

3. Run the database migrations to set up tables:

bash

flask db upgrade

# Usage
Start the server: After setting up and deploying the server, you can access the application at http://localhost:5000.

You can use : ( python run.py ) to start the server

Endpoints include:
/customer: For finishing customer functions.
/staff: For finishing staff functions.

# Test Credentials
## Customer:

### balance: 100
Username: btaylor
Password: test002

### balance: 0
Username: jdoe
Password: test002

### balance: 201
Username: asmith
Password: test002

## Cooperate Customer

Username: corporate_user
password: test002

## staff:

Username: staff_user
Password: test002
