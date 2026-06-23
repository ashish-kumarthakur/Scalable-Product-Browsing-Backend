import os
import base64
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Scalable Product Browsing API")

# CORS Middleware Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database URL Connection Link
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Helper Function
def encode_cursor(created_at: datetime, product_id: int) -> str:
    timestamp_str = created_at.isoformat()
    cursor_str = f"{timestamp_str},{product_id}"
    return base64.b64encode(cursor_str.encode('utf-8')).decode('utf-8')

# Helper Function
def decode_cursor(cursor_str: str):
    decoded = base64.b64decode(cursor_str.encode('utf-8')).decode('utf-8')
    timestamp_str, product_id = decoded.split(',')
    return datetime.fromisoformat(timestamp_str), int(product_id)

@app.get("/api/products")
def get_products(
    search: Optional[str] = Query(None, description="Search products by name"),
    category: Optional[str] = Query(None, description="Filter products by category"),
    limit: int = Query(12, le=100, description="Number of items per page"),
    cursor: Optional[str] = Query(None, description="Base64 cursor for next page")
):
    connection = get_db_connection()
    cursor_db = connection.cursor()

    # 1. Base Query
    base_query = "SELECT id, name, category, price, created_at FROM products WHERE 1=1"
    query_parameters = []

    # 2. Search Filter 
    if search:
        base_query += " AND name ILIKE %s"
        query_parameters.append(f"%{search}%")

    # 3. Category Filter
    if category:
        base_query += " AND category = %s"
        query_parameters.append(category)

    # 4. Total Count Query 
    count_query = "SELECT COUNT(*) AS total_count FROM products WHERE 1=1"
    count_parameters = []
    if search:
        count_query += " AND name ILIKE %s"
        count_parameters.append(f"%{search}%")
    if category:
        count_query += " AND category = %s"
        count_parameters.append(category)

    cursor_db.execute(count_query, tuple(count_parameters))
    total_products_count = cursor_db.fetchone()['total_count']

    # 5. Cursor Pagination Logic (Failsafe dynamic injection)
    if cursor:
        try:
            _, last_id = decode_cursor(cursor)
            base_query += " AND id < %s"
            query_parameters.append(last_id)
        except Exception:
            cursor_db.close()
            connection.close()
            raise HTTPException(status_code=400, detail="Invalid cursor format string.")

    # 6. Fast Sorting & Limit
    base_query += " ORDER BY id DESC LIMIT %s"
    query_parameters.append(limit)

    # Main Query Execute karein
    cursor_db.execute(base_query, tuple(query_parameters))
    products_list = cursor_db.fetchall()

    cursor_db.close()
    connection.close()

    # 7. Next Page cursor calculation
    next_cursor = None
    if products_list and len(products_list) == limit:
        last_item = products_list[-1]
        next_cursor = encode_cursor(last_item['created_at'], last_item['id'])

    return {
        "total": total_products_count,
        "limit": limit,
        "next_cursor": next_cursor,
        "results": products_list
    }