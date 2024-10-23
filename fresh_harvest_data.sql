-- pasword is test002
-- Insert into person table
INSERT INTO person (username, first_name, last_name, password)
VALUES 
('jdoe', 'John', 'Doe', '7731ebed82a2a739d0762e2cb6781f7bb7bc5919ddbc15a546a36bb9b5fb1e3e'),
('asmith', 'Alice', 'Smith', '7731ebed82a2a739d0762e2cb6781f7bb7bc5919ddbc15a546a36bb9b5fb1e3e'),
('btaylor', 'Bob', 'Taylor', '7731ebed82a2a739d0762e2cb6781f7bb7bc5919ddbc15a546a36bb9b5fb1e3e'),
('corporate_user', 'Corporate', 'User', '7731ebed82a2a739d0762e2cb6781f7bb7bc5919ddbc15a546a36bb9b5fb1e3e'),
('staff_user', 'Staff', 'User', '7731ebed82a2a739d0762e2cb6781f7bb7bc5919ddbc15a546a36bb9b5fb1e3e');


-- Insert into customer table
INSERT INTO customer (id, cust_address, max_owing, balance)
VALUES 
(1, '123 Main St', 1000.00, 0),
(2, '456 Oak St', 500.00, 50.00),
(3, '789 Pine St', 1500.00, 30.00),
(4, 'Corporate Address', 10000.00, 0);


-- Insert into corporate_customer table
INSERT INTO corporate_customer (id, min_balance, max_credit, discount_rate)
VALUES 
(4, 10000.00, 5000.00, 0.9);  


-- Insert into staff table
INSERT INTO staff (id, dept_name, date_joined)
VALUES 
(5, 'Sales', '2020-06-01'); 


-- Items
-- Step 1: 插入数据到 item 表
INSERT INTO item (description, price) VALUES 
('Carrot Pack', 5.00), 
('Tomato by Unit', 0.80), 
('Potato by Weight', 2.50), 
('Premade Box - Large', 20.00);

-- Step 2: 插入数据到 veggie 表
INSERT INTO veggie (id, weight_per_kilo) VALUES 
(1, 1.5), -- Carrot Pack
(2, 0.5), -- Tomato by Unit
(3, 2.0); -- Potato by Weight

-- Step 3: 插入数据到 pack_veggie 表 (继承自 veggie)
INSERT INTO pack_veggie (id, price_per_pack, num_of_packs, veg_name) VALUES 
(1, 5.00, 10, 'Carrot Pack');

-- Step 4: 插入数据到 unit_price_veggie 表 (继承自 veggie)
INSERT INTO unit_price_veggie (id, price_per_unit, quantity) VALUES 
(2, 0.80, 50); -- Tomato by Unit

-- Step 5: 插入数据到 weighted_veggie 表 (继承自 veggie)
INSERT INTO weighted_veggie (id, weight) VALUES 
(3, 20.0); -- Potato by Weight

-- Step 6: 插入数据到 premade_box 表 (继承自 item)
INSERT INTO premade_box (id, box_size, num_of_boxes) VALUES 
(4, 'Large', 5); -- Premade Box - Large
