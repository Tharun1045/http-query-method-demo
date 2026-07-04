#!/bin/bash

# QUERY example for http-query-method-demo
# This script sends a native HTTP QUERY request (RFC 9458) with filters in the request body.
# This is the modern standard way to perform safe, idempotent read-only lookups with body parameters.

echo ">>> QUERY /products with JSON body"
echo "Sending request..."
echo "--------------------------------------------------"
curl -X QUERY "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "category": "kitchen",
    "max_price": 50.0,
    "min_rating": 4.5,
    "in_stock": true
  }' \
  -w "\n\nHTTP Response Code: %{http_code}\n"
echo "--------------------------------------------------"
