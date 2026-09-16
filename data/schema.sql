DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_date TIMESTAMP,
    status TEXT NOT NULL
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    category_id INTEGER REFERENCES categories(category_id),
    name TEXT NOT NULL,
    base_price REAL NOT NULL,
    cost_price REAL NOT NULL,
    is_discontinued INTEGER DEFAULT 0
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id),
    order_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    discount_amount REAL DEFAULT 0.00,
    shipping_cost REAL DEFAULT 0.00,
    total_amount REAL NOT NULL
);

CREATE TABLE order_items (
    item_id TEXT PRIMARY KEY,
    order_id TEXT REFERENCES orders(order_id),
    product_id TEXT REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL
);