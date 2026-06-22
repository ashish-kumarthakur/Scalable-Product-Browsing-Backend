import psycopg2
from psycopg2.extras import execute_batch
import random
import datetime

import os
DATABASE_URL = os.getenv("DATABASE_URL")
CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Beauty"]
PRODUCT_NAMES = ["Pro", "Ultra", "Classic", "Premium", "Elite", "Smart", "Eco"]

def generate_mock_products(count=200000):
    print(f"Generating {count} products in memory...")
    data = []
    base_time = datetime.datetime.now()
    
    for i in range(count):
        # Stagger timestamps to simulate logical creation history
        created_at = base_time - datetime.timedelta(seconds=i)
        
        category = random.choice(CATEGORIES)
        name = f"{random.choice(PRODUCT_NAMES)} {category[:-1] if category.endswith('s') else category} {i}"
        price = round(random.uniform(10.0, 1000.0), 2)
        
        # Matches schema structure: name, category, price, created_at, updated_at
        data.append((name, category, price, created_at, created_at))
        
    return data

def seed_database():
    print("Connecting to the database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Clearing old records from the table...")
    cursor.execute("TRUNCATE TABLE products RESTART IDENTITY;")
    
    # Generate the dataset
    products_data = generate_mock_products(200000)
    
    # Optimized batch insertion query
    query = """
        INSERT INTO products (name, category, price, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    print("Inserting data into database in batches...")
    batch_size = 10000
    
    for i in range(0, len(products_data), batch_size):
        batch = products_data[i:i+batch_size]
        execute_batch(cursor, query, batch)
        print(f"Successfully inserted rows {i} to {i+len(batch)}.")
        
    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 200,000 Products successfully inserted into the database!")

if __name__ == "__main__":
    seed_database()