#!/usr/bin/env bash
# examples/get_example.sh
# --------------------------------------------------------
# Demonstrates: GET /products
# Filters are passed as URL query parameters.
# --------------------------------------------------------

BASE_URL="http://localhost:8000"

echo "========================================"
echo "  Demo: GET /products"
echo "  Filters: category=book, max_price=50"
echo "========================================"

curl -s -X GET \
  "${BASE_URL}/products?category=book&max_price=50" \
  -H "Accept: application/json" | python -m json.tool

echo ""
echo "HTTP method used: GET"
echo "Filters location: URL query string"
