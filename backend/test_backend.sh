#!/bin/bash

echo "Testing Backend API"
echo "==================="

# Health check
echo -e "\n1. Health Check:"
curl http://localhost:5000/health

# Register user
echo -e "\n\n2. Register Assessor:"
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "assessor@example.com",
    "password": "password123",
    "name": "Test Assessor",
    "role": "ASSESSOR"
  }'

# Get claims statistics
echo -e "\n\n3. Get Statistics:"
curl http://localhost:5000/api/claims/stats/summary

echo -e "\n\n✅ Backend API tests complete!"
