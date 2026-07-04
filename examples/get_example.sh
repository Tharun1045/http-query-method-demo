#!/bin/bash

# GET example for http-query-method-demo
# This script sends a standard GET request. Filters are passed in the URL query parameters.

echo ">>> GET /products?category=book&max_price=50"
echo "Sending request..."
echo "--------------------------------------------------"
curl -X GET "http://localhost:8000/products?category=book&max_price=50" \
  -H "Accept: application/json" \
  -w "\n\nHTTP Response Code: %{http_code}\n"
echo "--------------------------------------------------"
