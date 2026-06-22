# Scalable Product Browsing API

A high-performance FastAPI backend designed to handle real-time product browsing and filtering over large datasets (200,000+ items) using optimized cursor pagination.

## Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** Serverless PostgreSQL (Neon Cloud)
- **Database Driver:** Psycopg2

## Architectural Choices & Optimizations

1. **Database Selection (PostgreSQL)**
   - Used PostgreSQL for robust relational indexing mechanisms, ideal for performing composite tracking queries across complex attributes over large datasets.

2. **Cursor-Based Pagination (Keyset Pagination)**
   - Implemented Keyset Cursor pagination over traditional `LIMIT/OFFSET` offsets. This perfectly handles real-time constraints: if items are inserted dynamically at the head of the table while a user reads down the page, the pagination anchor remains entirely static relative to the specific record sequence state. It completely eliminates data shifting and duplicate items.
   - It maintains an O(1) lookup performance boundary via B-tree index traversal, preventing system degradation on high page lookups.

3. **High-Performance Seeding Script**
   - Utilized Python’s `psycopg2.extras.execute_batch` functionality rather than individual looped iterations. This processed and seeded all 200,000 entities in bulk blocks of 10,000, minimizing network handshakes down to seconds.

4. **Composite Indexing Optimization**
   - Implemented a specialized compound operational index:
     `CREATE INDEX idx_products_pagination ON products (category, created_at DESC, id DESC);`
   - This ordering allows the query planner to completely avoid an explicit sort phase when combining filtering parameters with chronological display rules.