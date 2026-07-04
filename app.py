import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# In-memory product dataset representing a hypothetical online store.
# This data will be filtered based on request parameters/body.
PRODUCTS = [
    {"id": 1, "name": "Python Crash Course", "category": "book", "price": 29.99, "rating": 4.8, "in_stock": True},
    {"id": 2, "name": "Clean Code", "category": "book", "price": 35.50, "rating": 4.7, "in_stock": True},
    {"id": 3, "name": "Design Patterns", "category": "book", "price": 54.99, "rating": 4.5, "in_stock": False},
    {"id": 4, "name": "Wireless Mouse", "category": "electronics", "price": 19.99, "rating": 4.2, "in_stock": True},
    {"id": 5, "name": "Mechanical Keyboard", "category": "electronics", "price": 89.99, "rating": 4.6, "in_stock": True},
    {"id": 6, "name": "Noise Cancelling Headphones", "category": "electronics", "price": 149.99, "rating": 4.9, "in_stock": False},
    {"id": 7, "name": "Cotton T-Shirt", "category": "clothing", "price": 15.00, "rating": 3.9, "in_stock": True},
    {"id": 8, "name": "Denim Jacket", "category": "clothing", "price": 59.99, "rating": 4.1, "in_stock": True},
    {"id": 9, "name": "Leather Boots", "category": "clothing", "price": 120.00, "rating": 4.4, "in_stock": False},
    {"id": 10, "name": "Chef's Knife", "category": "kitchen", "price": 45.00, "rating": 4.6, "in_stock": True},
    {"id": 11, "name": "Cast Iron Skillet", "category": "kitchen", "price": 39.99, "rating": 4.7, "in_stock": True},
]

def filter_products(filters):
    """
    Applies criteria to filter the list of products.
    Supports category (exact matching), max_price, min_rating, and in_stock.
    """
    results = PRODUCTS.copy()

    # Filter by Category (case-insensitive check)
    category = filters.get("category")
    if category is not None:
        if isinstance(category, list):
            category = category[0] if category else None
        if category:
            results = [p for p in results if p["category"].lower() == category.lower()]

    # Filter by Maximum Price (less than or equal to)
    max_price = filters.get("max_price")
    if max_price is not None:
        if isinstance(max_price, list):
            max_price = max_price[0] if max_price else None
        if max_price:
            try:
                max_price_val = float(max_price)
                results = [p for p in results if p["price"] <= max_price_val]
            except ValueError:
                pass  # Ignore invalid float values gracefully

    # Filter by Minimum Rating (greater than or equal to)
    min_rating = filters.get("min_rating")
    if min_rating is not None:
        if isinstance(min_rating, list):
            min_rating = min_rating[0] if min_rating else None
        if min_rating:
            try:
                min_rating_val = float(min_rating)
                results = [p for p in results if p["rating"] >= min_rating_val]
            except ValueError:
                pass  # Ignore invalid float values gracefully

    # Filter by In-Stock Status (boolean check)
    in_stock = filters.get("in_stock")
    if in_stock is not None:
        if isinstance(in_stock, list):
            in_stock = in_stock[0] if in_stock else None
        
        # Convert string (from URL query string) or handle native bool (from JSON)
        if isinstance(in_stock, bool):
            results = [p for p in results if p["in_stock"] == in_stock]
        elif isinstance(in_stock, str):
            in_stock_str = in_stock.lower()
            if in_stock_str in ("true", "1"):
                results = [p for p in results if p["in_stock"] is True]
            elif in_stock_str in ("false", "0"):
                results = [p for p in results if p["in_stock"] is False]

    return results

class DemoHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    A custom handler inheriting from Python's standard BaseHTTPRequestHandler.
    We implement support for GET, POST, and the new QUERY HTTP method.
    """

    def send_cors_headers(self):
        """
        Helper to append default CORS headers.
        Since HTTP QUERY is a non-standard/new HTTP method, web browsers will trigger
        a CORS preflight check (OPTIONS request) if it is called cross-origin.
        """
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, QUERY, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json_response(self, status_code, data):
        """
        Helper method to serialize a dictionary and send a JSON HTTP response.
        """
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        """
        Handle OPTIONS preflight requests which are triggered by browser applications
        performing CORS verification, especially for newer HTTP methods like QUERY.
        """
        self.send_response(204)  # 204 No Content is typical for OPTIONS
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """
        Endpoint: GET /products
        Filters are read from the URL query string (e.g. ?category=book&max_price=50).
        This is the classic way to request read-only data, but it is limited by URL length
        limits, URL character encoding rules, and potential security issues with sensitive data in URL logs.
        """
        start_time = time.perf_counter()

        parsed_url = urlparse(self.path)
        
        # Route path check
        if parsed_url.path != "/products":
            self.send_json_response(404, {"error": "Not Found", "message": "Try GET /products"})
            return

        # Extract filters from the URL query string
        query_params = parse_qs(parsed_url.query)
        
        # Clean query parameters for output representation (collapsing lists where possible)
        clean_filters = {}
        for k, v in query_params.items():
            clean_filters[k] = v[0] if len(v) == 1 else v

        # Apply filtering logic
        filtered_products = filter_products(query_params)

        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000

        # Construct final payload
        payload = {
            "method": "GET",
            "use_case": "Simple read operation using URL query parameters.",
            "safe": True,
            "idempotent": True,
            "processing_time_ms": round(processing_time_ms, 4),
            "filters_applied": clean_filters,
            "results_count": len(filtered_products),
            "products": filtered_products
        }
        self.send_json_response(200, payload)

    def do_POST(self):
        """
        Endpoint: POST /products/search
        Filters are read from a JSON request body.
        POST is safe to send large request bodies, but POST is historically defined as *unsafe*
        and *non-idempotent*. Using POST for queries is a popular workaround, but breaks semantic API design.
        """
        start_time = time.perf_counter()

        if self.path != "/products/search":
            self.send_json_response(404, {"error": "Not Found", "message": "Try POST /products/search"})
            return

        # Read JSON body content
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_json_response(400, {"error": "Bad Request", "message": "POST search requires a JSON request body."})
            return

        body = self.rfile.read(content_length)
        try:
            filters = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json_response(400, {"error": "Bad Request", "message": "Failed to parse body JSON."})
            return

        # Apply filtering
        filtered_products = filter_products(filters)

        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000

        # Construct response payload
        payload = {
            "method": "POST",
            "use_case": "Common workaround for sending complex queries inside a request body.",
            "safe": False,        # POST is semantically unsafe (assumed to mutate state)
            "idempotent": False,  # POST is semantically non-idempotent
            "processing_time_ms": round(processing_time_ms, 4),
            "filters_applied": filters,
            "results_count": len(filtered_products),
            "products": filtered_products
        }
        self.send_json_response(200, payload)

    def do_QUERY(self):
        """
        Endpoint: QUERY /products
        Filters are read from a JSON request body.
        The QUERY method (RFC 9458) is designed specifically for this: safe, idempotent read-only requests
        that require a request body to pass complex, structured query inputs.
        """
        start_time = time.perf_counter()

        if self.path != "/products":
            self.send_json_response(404, {"error": "Not Found", "message": "Try QUERY /products"})
            return

        # Read JSON body content
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        
        filters = {}
        if body:
            try:
                filters = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_json_response(400, {"error": "Bad Request", "message": "Failed to parse body JSON."})
                return

        # Apply filtering
        filtered_products = filter_products(filters)

        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000

        # Construct response payload showing off QUERY properties
        payload = {
            "method": "QUERY",
            "use_case": "Read-only lookup using a request body without changing server state.",
            "safe": True,        # QUERY is semantically safe (does not alter resources)
            "idempotent": True,  # QUERY is semantically idempotent (can be repeated with same result)
            "processing_time_ms": round(processing_time_ms, 4),
            "filters_applied": filters,
            "results_count": len(filtered_products),
            "products": filtered_products
        }
        self.send_json_response(200, payload)

def run(server_class=HTTPServer, handler_class=DemoHTTPRequestHandler, port=8000):
    """
    Start the local Python HTTP server.
    """
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"=== HTTP QUERY Method Demo Server Starting ===")
    print(f"Server is running on: http://localhost:{port}")
    print(f"API endpoints available:")
    print(f"  - GET   http://localhost:{port}/products (Filters in URL query parameters)")
    print(f"  - POST  http://localhost:{port}/products/search (Filters in JSON body)")
    print(f"  - QUERY http://localhost:{port}/products (Filters in JSON body - RFC 9458)")
    print(f"Press Ctrl+C to stop the server.")
    print(f"=============================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
