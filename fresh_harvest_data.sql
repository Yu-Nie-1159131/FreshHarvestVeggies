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
(2, '456 Oak St', 500.00, 201.00),
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
INSERT INTO item (description, price) VALUES 
('Carrot Pack', 5.00), 
('Tomato by Unit', 0.80), 
('Potato by Weight', 2.50), 
('Premade Box - Middle', 20.00),
('Lettuce Pack', 4.50), 
('Cucumber by Unit', 1.00), 
('Pumpkin by Weight', 1.80), 
('Premade Box - Small', 15.00),
('Broccoli Pack', 6.00),
('Eggplant by Unit', 1.50),
('Zucchini by Weight', 2.20),
('Premade Box - Large', 30.00);

-- Veggie class
INSERT INTO veggie (id, weight_per_kilo) VALUES 
(1, 1.5),  -- Carrot Pack
(2, 0.5),  -- Tomato by Unit
(3, 2.0),  -- Potato by Weight
(5, 1.2),  -- Lettuce Pack
(6, 0.6),  -- Cucumber by Unit
(7, 3.0),  -- Pumpkin by Weight
(9, 1.0),  -- Broccoli Pack
(10, 0.8), -- Eggplant by Unit
(11, 2.5); -- Zucchini by Weight

-- PackVeggie class, ensure ids correspond to veggie ids
INSERT INTO pack_veggie (id, price_per_pack, num_of_packs, veg_name) VALUES 
(1, 5.00, 10, 'Carrot Pack'),  -- This corresponds to id=1 in veggie
(5, 4.50, 15, 'Lettuce Pack'),  -- This corresponds to id=5 in veggie
(9, 6.00, 20, 'Broccoli Pack'); -- This corresponds to id=9 in veggie

-- Other categories
INSERT INTO unit_price_veggie (id, price_per_unit, quantity) VALUES 
(2, 0.80, 50), -- Tomato by Unit
(6, 1.00, 100), -- Cucumber by Unit
(10, 1.50, 60);  -- Eggplant by Unit

INSERT INTO weighted_veggie (id, weight) VALUES 
(3, 20.0),  -- Potato by Weight
(7, 50.0),  -- Pumpkin by Weight
(11, 30.0);  -- Zucchini by Weight

INSERT INTO premade_box (id, box_size, num_of_boxes) VALUES 
(4, 'Middle', 5),    -- Premade Box - Middle
(8, 'Small', 8),     -- Premade Box - Small
(12, 'Large', 3);    -- Premade Box - Large

