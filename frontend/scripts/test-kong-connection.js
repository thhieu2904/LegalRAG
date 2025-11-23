/**
 * Test Kong Gateway Connection
 *
 * This script tests the connection from frontend to backend services via Kong Gateway
 * Run: node scripts/test-kong-connection.js
 */

const KONG_BASE_URL = 'http://localhost:8000';

async function testEndpoint(endpoint, method = 'GET', body = null) {
  console.log(`\n📡 Testing: ${method} ${endpoint}`);

  try {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${KONG_BASE_URL}${endpoint}`, options);
    const data = await response.json();

    if (response.ok) {
      console.log(`✅ SUCCESS (${response.status})`);
      console.log('Response:', JSON.stringify(data, null, 2));
      return { success: true, data };
    } else {
      console.log(`❌ FAILED (${response.status})`);
      console.log('Error:', JSON.stringify(data, null, 2));
      return { success: false, error: data };
    }
  } catch (error) {
    console.log(`❌ ERROR: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  console.log('🚀 Testing Kong Gateway Connection');
  console.log('='.repeat(60));

  const results = [];

  // Test 1: Query Service Health
  console.log('\n📋 Test 1: Query Service Health Check');
  const queryHealth = await testEndpoint('/query/health', 'GET');
  results.push({ name: 'Query Health', ...queryHealth });

  // Test 2: Admin Service Health
  console.log('\n📋 Test 2: Admin Service Health Check');
  const adminHealth = await testEndpoint('/admin/health', 'GET');
  results.push({ name: 'Admin Health', ...adminHealth });

  // Test 3: Query Service - Search
  console.log('\n📋 Test 3: Query Service - Search Documents');
  const searchRequest = {
    question: 'Điều kiện tốt nghiệp là gì?',
    top_k: 3,
    threshold: 0.7,
    filters: {
      ma_khoa: 'CNTT',
    },
  };
  const search = await testEndpoint('/query/search', 'POST', searchRequest);
  results.push({ name: 'Query Search', ...search });

  // Test 4: Query Service - Chat (RAG)
  console.log('\n📋 Test 4: Query Service - Chat with RAG');
  const chatRequest = {
    question: 'Lập trình hướng đối tượng là gì?',
    history: [],
    top_k: 5,
    threshold: 0.7,
    filters: {},
  };
  const chat = await testEndpoint('/query/chat', 'POST', chatRequest);
  results.push({ name: 'Query Chat', ...chat });

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(60));

  const passed = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;

  console.log(`\n✅ Passed: ${passed}/${results.length}`);
  console.log(`❌ Failed: ${failed}/${results.length}`);

  results.forEach((result) => {
    const icon = result.success ? '✅' : '❌';
    console.log(`${icon} ${result.name}`);
  });

  if (failed === 0) {
    console.log('\n🎉 All tests passed! Kong Gateway is working correctly.');
  } else {
    console.log('\n⚠️  Some tests failed. Check the logs above for details.');
    console.log('\n💡 Make sure:');
    console.log('   1. Kong Gateway is running: docker-compose up kong-gateway');
    console.log('   2. Backend services are running: docker-compose up');
    console.log('   3. Services are healthy: docker-compose ps');
  }
}

// Run tests
runTests().catch(console.error);
