#!/bin/bash

# LegalRAG System Health Check & Validation Script
# Tests all services and validates the entire architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  LegalRAG Microservices - Health Check Script${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

# Configuration
SERVICES=(
  "storage-service:8001"
  "identifill-service:8002"
  "vector-service:8003"
  "embedding-service:8004"
  "query-service:8005"
  "llm-service:8006"
  "admin-service:8007"
)

INFRASTRUCTURE=(
  "postgres-vector:5432"
  "minio:9000"
)

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
check_service() {
  local service=$1
  local port=$2
  
  echo -n "Checking ${service}... "
  
  if curl -s -f http://localhost:${port}/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((TESTS_PASSED++))
    return 0
  else
    echo -e "${RED}✗${NC}"
    ((TESTS_FAILED++))
    return 1
  fi
}

check_container() {
  local container=$1
  
  echo -n "Container ${container}... "
  
  if docker inspect ${container} > /dev/null 2>&1; then
    local status=$(docker inspect -f '{{.State.Status}}' ${container})
    if [ "$status" = "running" ]; then
      echo -e "${GREEN}✓ (running)${NC}"
      ((TESTS_PASSED++))
      return 0
    else
      echo -e "${RED}✗ (${status})${NC}"
      ((TESTS_FAILED++))
      return 1
    fi
  else
    echo -e "${RED}✗ (not found)${NC}"
    ((TESTS_FAILED++))
    return 1
  fi
}

test_endpoint() {
  local name=$1
  local method=$2
  local endpoint=$3
  local data=$4
  
  echo -n "Testing ${name}... "
  
  if [ -z "$data" ]; then
    if curl -s -f -X ${method} ${endpoint} > /dev/null 2>&1; then
      echo -e "${GREEN}✓${NC}"
      ((TESTS_PASSED++))
      return 0
    else
      echo -e "${RED}✗${NC}"
      ((TESTS_FAILED++))
      return 1
    fi
  else
    if curl -s -f -X ${method} \
      -H "Content-Type: application/json" \
      -d "${data}" \
      ${endpoint} > /dev/null 2>&1; then
      echo -e "${GREEN}✓${NC}"
      ((TESTS_PASSED++))
      return 0
    else
      echo -e "${RED}✗${NC}"
      ((TESTS_FAILED++))
      return 1
    fi
  fi
}

# ============================================
# 1. Check Docker & Compose
# ============================================
echo -e "${YELLOW}1. System Dependencies${NC}"
echo "═════════════════════════════════════"

echo -n "Docker... "
if command -v docker &> /dev/null; then
  echo -e "${GREEN}✓ $(docker --version)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

echo -n "Docker Compose... "
if command -v docker-compose &> /dev/null; then
  echo -e "${GREEN}✓ $(docker-compose --version)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

echo -n "curl... "
if command -v curl &> /dev/null; then
  echo -e "${GREEN}✓${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

# ============================================
# 2. Check Containers Running
# ============================================
echo -e "\n${YELLOW}2. Container Status${NC}"
echo "═════════════════════════════════════"

CONTAINERS=(
  "legalrag-minio"
  "legalrag-postgres"
  "legalrag-storage"
  "legalrag-vector"
  "legalrag-embedding"
  "legalrag-llm"
  "legalrag-query"
  "legalrag-admin"
  "legalrag-identifill"
  "legalrag-frontend"
)

for container in "${CONTAINERS[@]}"; do
  check_container "$container" || true
done

# ============================================
# 3. Check Service Health
# ============================================
echo -e "\n${YELLOW}3. Service Health${NC}"
echo "═════════════════════════════════════"

for service_port in "${SERVICES[@]}"; do
  IFS=':' read -r service port <<< "$service_port"
  check_service "$service" "$port" || true
done

# ============================================
# 4. Database Connectivity
# ============================================
echo -e "\n${YELLOW}4. Database Connectivity${NC}"
echo "═════════════════════════════════════"

echo -n "PostgreSQL... "
if pg_isready -h localhost -p 5432 -U legalrag > /dev/null 2>&1; then
  echo -e "${GREEN}✓${NC}"
  ((TESTS_PASSED++))
  
  # Check tables
  echo -n "  - documents table... "
  if psql -h localhost -U legalrag -d legalrag -c "\dt documents" 2>/dev/null | grep -q documents; then
    echo -e "${GREEN}✓${NC}"
    ((TESTS_PASSED++))
  else
    echo -e "${RED}✗${NC}"
    ((TESTS_FAILED++))
  fi
  
  echo -n "  - chunks table... "
  if psql -h localhost -U legalrag -d legalrag -c "\dt chunks" 2>/dev/null | grep -q chunks; then
    echo -e "${GREEN}✓${NC}"
    ((TESTS_PASSED++))
  else
    echo -e "${RED}✗${NC}"
    ((TESTS_FAILED++))
  fi
  
  echo -n "  - Vector count... "
  count=$(psql -h localhost -U legalrag -d legalrag -tc "SELECT COUNT(*) FROM chunks;" 2>/dev/null | tr -d ' ')
  echo -e "${GREEN}✓ (${count} vectors)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

echo -n "MinIO... "
if curl -s -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
  echo -e "${GREEN}✓${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

# ============================================
# 5. API Endpoint Tests
# ============================================
echo -e "\n${YELLOW}5. API Endpoint Tests${NC}"
echo "═════════════════════════════════════"

# Storage
test_endpoint "Storage /health" "GET" "http://localhost:8001/health" "" || true

# Vector
test_endpoint "Vector /count" "GET" "http://localhost:8003/count" "" || true

# Embedding
test_endpoint "Embedding /embed" "POST" "http://localhost:8004/embed" \
  '{"text": "test"}' || true

# Query
test_endpoint "Query /health" "GET" "http://localhost:8005/health" "" || true

# LLM
test_endpoint "LLM /health" "GET" "http://localhost:8006/health" "" || true

# Admin
test_endpoint "Admin /documents" "GET" "http://localhost:8007/documents" "" || true

# ============================================
# 6. Service Dependencies
# ============================================
echo -e "\n${YELLOW}6. Service Dependencies${NC}"
echo "═════════════════════════════════════"

echo -n "Query → Embedding... "
health=$(curl -s http://localhost:8005/health 2>/dev/null | grep -q "embedding.*ok" && echo "ok" || echo "fail")
if [ "$health" = "ok" ]; then
  echo -e "${GREEN}✓${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

echo -n "Admin → Storage... "
curl -s http://localhost:8007/health | grep -q "storage" && echo -e "${GREEN}✓${NC}" && ((TESTS_PASSED++)) || (echo -e "${RED}✗${NC}" && ((TESTS_FAILED++)))

echo -n "Admin → Vector... "
curl -s http://localhost:8007/health | grep -q "vector" && echo -e "${GREEN}✓${NC}" && ((TESTS_PASSED++)) || (echo -e "${RED}✗${NC}" && ((TESTS_FAILED++)))

# ============================================
# 7. Functional Tests
# ============================================
echo -e "\n${YELLOW}7. Functional Tests${NC}"
echo "═════════════════════════════════════"

# Create test file
TEST_FILE="/tmp/legal_test.txt"
echo "Vietnamese Legal Document Test
Luật Dân sự năm 2015
Điều 1: Quyền cơ bản của công dân" > "$TEST_FILE"

echo -n "Functional: Upload document... "
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8007/upload -F "file=@$TEST_FILE")
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$DOCUMENT_ID" ]; then
  echo -e "${GREEN}✓ (${DOCUMENT_ID:0:8}...)${NC}"
  ((TESTS_PASSED++))
  
  # Test query with document
  echo -n "Functional: Query with document... "
  QUERY_RESPONSE=$(curl -s -X POST http://localhost:8005/query \
    -H "Content-Type: application/json" \
    -d '{"question": "Quyền cơ bản là gì?", "top_k": 5}')
  
  if echo "$QUERY_RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✓${NC}"
    ((TESTS_PASSED++))
  else
    echo -e "${RED}✗${NC}"
    ((TESTS_FAILED++))
  fi
else
  echo -e "${RED}✗${NC}"
  ((TESTS_FAILED++))
fi

# Cleanup
rm -f "$TEST_FILE"

# ============================================
# 8. Performance Metrics
# ============================================
echo -e "\n${YELLOW}8. Performance Metrics${NC}"
echo "═════════════════════════════════════"

echo -n "Query response time... "
START=$(date +%s%N)
curl -s -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "top_k": 5}' > /dev/null
END=$(date +%s%N)
DURATION=$((($END - $START) / 1000000))
echo -e "${GREEN}${DURATION}ms${NC}"

echo -n "Embedding response time... "
START=$(date +%s%N)
curl -s -X POST http://localhost:8004/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}' > /dev/null
END=$(date +%s%N)
DURATION=$((($END - $START) / 1000000))
echo -e "${GREEN}${DURATION}ms${NC}"

# ============================================
# 9. Summary
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
PASS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL" | bc 2>/dev/null || echo "N/A")

echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo -e "Total:  ${BLUE}${TOTAL}${NC}"
echo -e "Pass Rate: ${PASS_RATE}%"

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "\n${GREEN}✓ All checks passed! System is healthy.${NC}"
  exit 0
else
  echo -e "\n${RED}✗ Some checks failed. See above for details.${NC}"
  exit 1
fi
