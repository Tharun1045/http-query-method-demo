#!/usr/bin/env bash
# examples/query_example.sh
# --------------------------------------------------------
# Demonstrates: QUERY /products  (RFC 10008)
# Filters are passed inside a JSON request body.
# QUERY is safe + idempotent, unlike POST.
# It is the semantically correct method for read-only
# searches that require a structured request body.
# --------------------------------------------------------

BASE_URL="http://localhost:8000"

echo "========================================"
echo "  Demo: QUERY /products  (RFC 10008)"
echo "  Filters: category=kitchen, max_price=50, min_rating=4.5, in_stock=true"
echo "========================================"

curl -s -X QUERY \
  "${BASE_URL}/products" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "category": "kitchen",
    "max_price": 50.0,
    "min_rating": 4.5,
    "in_stock": true
  }' | python -m json.tool

echo ""
echo "HTTP method used: QUERY (RFC 10008)"
echo "Filters location: JSON request body"
echo "Safe: true  |  Idempotent: true"
