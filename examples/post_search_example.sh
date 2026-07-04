#!/bin/bash

# POST search example for http-query-method-demo
# This script sends a POST request containing search filters in the JSON request body.
# This is a common workaround in REST APIs to bypass URL length limitations of GET.

echo ">>> POST /products/search with JSON body"
echo "Sending request..."
echo "--------------------------------------------------"
curl -X POST "http://localhost:8000/products/search" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "category": "electronics",
    "max_price": 100.0,
    "in_stock": true
  }' \
  -w "\n\nHTTP Response Code: %{http_code}\n"
echo "--------------------------------------------------"
