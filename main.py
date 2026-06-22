from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import base64
from datetime import datetime
from typing import Optional
import os

app = FastAPI(title="Scalable Product Browsing API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def decode_cursor(cursor_str: str):
    try:
        decoded = base64.b64decode(cursor_str.encode()).decode()
        timestamp_str, last_id = decoded.split("||")
        timestamp = datetime.fromisoformat(timestamp_str)
        return timestamp, int(last_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cursor string provided.")

# Helper Function: Encode the last item's values to make a cursor string
def encode_cursor(timestamp: datetime, last_id: int) -> str:
    cursor_str = f"{timestamp.isoformat()}||{last_id}"
    return base64.b64encode(cursor_str.encode()).decode()

@app.get("/api/products")
def get_products(
    search: Optional[str] = Query(default=None, description="Search products by name"),
    category: Optional[str] = Query(default=None, description="Filter products by category"),
    limit: int = Query(default=10, le=100, description="Number of items per page"),
    offset: int = Query(default=0, description="Number of items to skip")
):
    connection = get_db_connection()
    cursor_db = connection.cursor()
    
    # Base SQL Query
    base_query = "SELECT id, name, category, price, created_at FROM products WHERE 1=1"
    query_parameters = []
    
    # 1. Search Filter
    if search:
        base_query += " AND name ILIKE %s"
        query_parameters.append(f"%{search}%")
        
    # 2. Category Filter
    if category:
        base_query += " AND category = %s"
        query_parameters.append(category)
        
    # 3. Sorting & Pagination
    base_query += " ORDER BY id DESC LIMIT %s OFFSET %s"
    query_parameters.append(limit)
    query_parameters.append(offset)
    
    # Execute query to get products
    cursor_db.execute(base_query, tuple(query_parameters))
    products_list = cursor_db.fetchall()
    

    
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
    
    cursor_db.close()
    connection.close()
    
    return {
        "total": total_products_count,
        "limit": limit,
        "offset": offset,
        "results": products_list
    }
