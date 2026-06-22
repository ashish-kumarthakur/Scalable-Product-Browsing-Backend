from fastapi import FastAPI, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
import base64
from datetime import datetime
from typing import Optional

app = FastAPI(title="Scalable Product Browsing API")

DB_URI = "postgresql://neondb_owner:npg_cnY3dDHhV8rB@ep-jolly-bonus-ao3sp39f.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DB_URI, cursor_factory=RealDictCursor)

# Helper Function: Safely decode the cursor string sent by frontend
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
    limit: int = Query(default=10, le=100, description="Number of items per page"),
    category: Optional[str] = Query(default=None, description="Filter products by category"),
    cursor: Optional[str] = Query(default=None, description="Base64 encoded pagination token")
):
    conn = get_db_connection()
    cursor_db = conn.cursor()
    
    # Base SQL Query using the optimal index sorting orders
    query = "SELECT id, name, category, price, created_at FROM products"
    conditions = []
    params = []
    
    # 1. Apply category filtering if requested
    if category:
        conditions.append("category = %s")
        params.append(category)
        
    # 2. Apply Keyset Cursor Pagination filter if cursor exists
    if cursor:
        cursor_time, cursor_id = decode_cursor(cursor)
        # Keyset Pagination logic: Find items OLDER than cursor time.
        # If times are identical, use the unique ID as the deterministic tie-breaker.
        conditions.append("(created_at < %s OR (created_at = %s AND id < %s))")
        params.extend([cursor_time, cursor_time, cursor_id])
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    # Standard continuous sorting matching our database index exactly
    query += " ORDER BY category ASC, created_at DESC, id DESC LIMIT %s;" if category else " ORDER BY created_at DESC, id DESC LIMIT %s;"
    params.append(limit)
    
    # Execute query
    cursor_db.execute(query, params)
    products = cursor_db.fetchall()
    
    cursor_db.close()
    conn.close()
    
    # 3. Generate the token for the next page if items remain
    next_cursor = None
    if len(products) == limit:
        last_item = products[-1]
        next_cursor = encode_cursor(last_item['created_at'], last_item['id'])
        
    return {
        "results": products,
        "next_cursor": next_cursor
    }