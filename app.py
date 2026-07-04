"""
HTTP QUERY Method Demo - app.py
================================
Demonstrates the difference between:
  - GET  /products            (filters in URL query string)
  - POST /products/search     (filters in JSON request body - common workaround)
  - QUERY /products           (filters in JSON request body - RFC 10008)

Zero external dependencies. Uses only Python's built-in http.server module.
Run with: python app.py
"""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


# ---------------------------------------------------------------------------
# In-memory product dataset
# ---------------------------------------------------------------------------
# This represents a simple product catalog. In a real application this would
# come from a database, but for this demo we keep it in memory to stay
# dependency-free.
PRODUCTS = [
    {
        "id": 1,
        "name": "Python Crash Course",
        "category": "book",
        "price": 29.99,
        "rating": 4.8,
        "in_stock": True,
    },
    {
        "id": 2,
        "name": "Clean Code",
        "category": "book",
        "price": 35.50,
        "rating": 4.7,
        "in_stock": True,
    },
    {
        "id": 3,
        "name": "Design Patterns",
        "category": "book",
        "price": 54.99,
        "rating": 4.5,
        "in_stock": False,
    },
    {
        "id": 4,
        "name": "Wireless Mouse",
        "category": "electronics",
        "price": 19.99,
        "rating": 4.2,
        "in_stock": True,
    },
    {
        "id": 5,
        "name": "Mechanical Keyboard",
        "category": "electronics",
        "price": 89.99,
        "rating": 4.6,
        "in_stock": True,
    },
    {
        "id": 6,
        "name": "Noise Cancelling Headphones",
        "category": "electronics",
        "price": 149.99,
        "rating": 4.9,
        "in_stock": False,
    },
    {
        "id": 7,
        "name": "Cotton T-Shirt",
        "category": "clothing",
        "price": 15.00,
        "rating": 3.9,
        "in_stock": True,
    },
    {
        "id": 8,
        "name": "Denim Jacket",
        "category": "clothing",
        "price": 59.99,
        "rating": 4.1,
        "in_stock": True,
    },
    {
        "id": 9,
        "name": "Leather Boots",
        "category": "clothing",
        "price": 120.00,
        "rating": 4.4,
        "in_stock": False,
    },
    {
        "id": 10,
        "name": "Chef's Knife",
        "category": "kitchen",
        "price": 45.00,
        "rating": 4.6,
        "in_stock": True,
    },
    {
        "id": 11,
        "name": "Cast Iron Skillet",
        "category": "kitchen",
        "price": 39.99,
        "rating": 4.7,
        "in_stock": True,
    },
]


# ---------------------------------------------------------------------------
# Filter helper
# ---------------------------------------------------------------------------
def filter_products(filters):
    """
    Apply optional filter criteria to the product list.

    Supported filters:
        category   (str)   - Exact match, case-insensitive.
        max_price  (float) - Return products where price <= max_price.
        min_rating (float) - Return products where rating >= min_rating.
        in_stock   (bool)  - True = only in-stock, False = only out-of-stock.

    'filters' may come from parse_qs() (values are lists of strings) or from
    json.loads() (values are native Python types). This function handles both.
    """
    results = PRODUCTS.copy()

    # ---- category ---------------------------------------------------------
    category = filters.get("category")
    if category is not None:
        # parse_qs returns lists; json body returns a plain string
        if isinstance(category, list):
            category = category[0] if category else None
        if category:
            results = [
                p for p in results
                if p["category"].lower() == category.lower()
            ]

    # ---- max_price --------------------------------------------------------
    max_price = filters.get("max_price")
    if max_price is not None:
        if isinstance(max_price, list):
            max_price = max_price[0] if max_price else None
        if max_price is not None:
            try:
                max_price_val = float(max_price)
                results = [p for p in results if p["price"] <= max_price_val]
            except (ValueError, TypeError):
                pass  # ignore bad values; do not crash

    # ---- min_rating -------------------------------------------------------
    min_rating = filters.get("min_rating")
    if min_rating is not None:
        if isinstance(min_rating, list):
            min_rating = min_rating[0] if min_rating else None
        if min_rating is not None:
            try:
                min_rating_val = float(min_rating)
                results = [p for p in results if p["rating"] >= min_rating_val]
            except (ValueError, TypeError):
                pass

    # ---- in_stock ---------------------------------------------------------
    in_stock = filters.get("in_stock")
    if in_stock is not None:
        if isinstance(in_stock, list):
            in_stock = in_stock[0] if in_stock else None
        if isinstance(in_stock, bool):
            # Came from JSON body – already a proper boolean
            results = [p for p in results if p["in_stock"] == in_stock]
        elif isinstance(in_stock, str):
            # Came from URL query string – convert manually
            if in_stock.lower() in ("true", "1"):
                results = [p for p in results if p["in_stock"] is True]
            elif in_stock.lower() in ("false", "0"):
                results = [p for p in results if p["in_stock"] is False]

    return results


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------
class DemoHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler.

    Supports GET, POST, QUERY, and OPTIONS.

    Key concepts demonstrated:
      - GET   : read-only, filters in URL (classic approach).
      - POST  : body accepted, but semantically "unsafe" per HTTP spec.
      - QUERY : body accepted AND semantically safe + idempotent (RFC 10008).
    """

    # Silence the default per-request console logging for a cleaner demo.
    # Remove this override if you want to see request logs.
    def log_message(self, format, *args):  # noqa: A002
        pass

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _set_common_headers(self):
        """
        Write the shared headers that every response should include.

        Allow         - Lists all HTTP methods this server supports.
        Accept-Query  - Declares the media type accepted for QUERY bodies
                        (defined in RFC 10008).
        CORS headers  - Allow browser clients and tools to call this API.
        """
        self.send_header("Allow", "GET, POST, QUERY, OPTIONS")
        self.send_header("Accept-Query", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, QUERY, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status_code, data):
        """Serialize 'data' to JSON and send it as an HTTP response."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._set_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        """
        Read the request body and parse it as JSON.
        Returns (parsed_dict, error_response_or_None).
        """
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8")), None
        except json.JSONDecodeError as exc:
            return None, {"error": "Bad Request", "message": f"Invalid JSON: {exc}"}

    # ------------------------------------------------------------------
    # OPTIONS – CORS preflight
    # ------------------------------------------------------------------
    def do_OPTIONS(self):
        """
        Respond to browser CORS preflight requests.

        Browsers send OPTIONS before any cross-origin request that uses a
        non-simple method (QUERY is non-simple) or a custom Content-Type.
        Returning 204 + CORS headers tells the browser the actual request
        is allowed.
        """
        self.send_response(204)
        self._set_common_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # GET /products
    # ------------------------------------------------------------------
    def do_GET(self):
        """
        Classic read-only search via URL query parameters.

        Example:
            GET /products?category=book&max_price=50

        Strengths:
            - Universally supported by every HTTP client, library and CDN.
            - Responses can be cached based on the URL alone.
            - Bookmarkable and shareable.

        Limitations:
            - URL length is capped (~2 KB in many browsers/proxies).
            - Complex filters must be URL-encoded, which can be messy.
            - Sensitive filter values appear in server access logs.
        """
        t_start = time.perf_counter()

        parsed = urlparse(self.path)
        if parsed.path != "/products":
            self._send_json(404, {"error": "Not Found", "message": "Use GET /products"})
            return

        # parse_qs returns {"key": ["value"]} – a list for every key.
        query_params = parse_qs(parsed.query)

        # Build a cleaner dict for the response (collapse single-item lists).
        filters_display = {
            k: (v[0] if len(v) == 1 else v)
            for k, v in query_params.items()
        }

        results = filter_products(query_params)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 4)

        self._send_json(200, {
            "method": "GET",
            "use_case": (
                "Simple read-only search. Filters are passed in the URL "
                "query string. Best for short, non-sensitive filters."
            ),
            "safe": True,
            "idempotent": True,
            "processing_time_ms": elapsed_ms,
            "filters_applied": filters_display,
            "results_count": len(results),
            "products": results,
        })

    # ------------------------------------------------------------------
    # POST /products/search
    # ------------------------------------------------------------------
    def do_POST(self):
        """
        Common workaround: search filters sent inside a JSON request body.

        Example:
            POST /products/search
            Content-Type: application/json
            { "category": "electronics", "max_price": 100, "in_stock": true }

        Why teams use this:
            - No URL-length limit; works for very complex payloads.
            - Sensitive filters stay out of access logs.
            - Supported by every client library.

        The trade-off:
            - HTTP defines POST as *unsafe* and *non-idempotent*.
            - CDNs / reverse proxies will not cache POST responses by default.
            - Automated clients (e.g., web crawlers) will not retry POST on
              network failure.

        This is a pragmatic and widely-accepted workaround, but it is
        semantically imprecise. QUERY (RFC 10008) is the correct solution.
        """
        t_start = time.perf_counter()

        if self.path != "/products/search":
            self._send_json(
                404,
                {"error": "Not Found", "message": "Use POST /products/search"},
            )
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(
                400,
                {"error": "Bad Request", "message": "A JSON body is required."},
            )
            return

        filters, err = self._read_json_body()
        if err:
            self._send_json(400, err)
            return

        results = filter_products(filters)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 4)

        self._send_json(200, {
            "method": "POST",
            "use_case": (
                "Common workaround for complex search with a JSON body. "
                "Works well in practice, but POST is semantically unsafe "
                "and non-idempotent, which limits automatic caching and retries."
            ),
            "safe": False,       # HTTP spec: POST may modify state
            "idempotent": False,  # HTTP spec: repeating POST is not guaranteed safe
            "processing_time_ms": elapsed_ms,
            "filters_applied": filters,
            "results_count": len(results),
            "products": results,
        })

    # ------------------------------------------------------------------
    # QUERY /products  (RFC 10008)
    # ------------------------------------------------------------------
    def do_QUERY(self):
        """
        RFC 10008 – The HTTP QUERY method.

        Combines the best of GET and POST for search:
          - Accepts a structured request body (no URL-length limit).
          - Declared as *safe*  (read-only, will not modify server state).
          - Declared as *idempotent* (can be retried safely by clients).
          - Cacheable in principle (keyed on URL + request body hash).

        Example:
            QUERY /products
            Content-Type: application/json
            { "category": "kitchen", "max_price": 50, "in_stock": true }

        Note:
            QUERY solves an API *design* problem, not a database *performance*
            problem. The processing_time_ms in the response will be virtually
            identical to GET or POST for the same query.

        Content-Type Validation:
            RFC 10008 requires the body to carry an explicit media type.
            We accept only application/json and return 415 otherwise.
        """
        t_start = time.perf_counter()

        if self.path != "/products":
            self._send_json(
                404,
                {"error": "Not Found", "message": "Use QUERY /products"},
            )
            return

        # Validate Content-Type – QUERY requires an explicit body media type.
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            self._send_json(
                415,
                {
                    "error": "Unsupported Media Type",
                    "message": (
                        "QUERY /products requires the header "
                        "'Content-Type: application/json'."
                    ),
                },
            )
            return

        filters, err = self._read_json_body()
        if err:
            self._send_json(400, err)
            return

        results = filter_products(filters)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 4)

        self._send_json(200, {
            "method": "QUERY",
            "use_case": (
                "RFC 10008 – Read-only search with a structured request body. "
                "Safe and idempotent by definition; cacheable by intermediaries."
            ),
            "safe": True,        # QUERY explicitly does not modify state
            "idempotent": True,  # Repeating the same QUERY is always safe
            "processing_time_ms": elapsed_ms,
            "filters_applied": filters,
            "results_count": len(results),
            "products": results,
        })


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------
def run(port=8000):
    """Start the demo HTTP server on localhost:{port}."""
    httpd = HTTPServer(("", port), DemoHTTPRequestHandler)
    base = f"http://localhost:{port}"
    print("=" * 52)
    print("  HTTP QUERY Method Demo  –  RFC 10008")
    print("=" * 52)
    print(f"  Server  : {base}")
    print(f"  GET     : {base}/products?category=book&max_price=50")
    print(f"  POST    : {base}/products/search   (JSON body)")
    print(f"  QUERY   : {base}/products           (JSON body, RFC 10008)")
    print("=" * 52)
    print("  Press Ctrl+C to stop.")
    print()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()


if __name__ == "__main__":
    run()
