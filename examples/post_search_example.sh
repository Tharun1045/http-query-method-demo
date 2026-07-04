#!/usr/bin/env bash
# examples/post_search_example.sh
# --------------------------------------------------------
# Demonstrates: POST /products/search
# Filters are passed inside a JSON request body.
# This is the widely-used workaround when GET URL params
# are too limited for complex queries.
# --------------------------------------------------------

BASE_URL="http://localhost:8000"

echo "========================================"
echo "  Demo: POST /products/search"
echo "  Filters: category=electronics, max_price=100, in_stock=true"
echo "========================================"

curl -s -X POST \
  "${BASE_URL}/products/search" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "category": "electronics",
    "max_price": 100.0,
    "in_stock": true
  }' | python -m json.tool

echo ""
echo "HTTP method used: POST"
echo "Filters location: JSON request body"
