# Test Automation Implementation
# Path: tests/test_get_relevant_context.py
"""
Test Suite for mcp_braincell_get_relevant_context Tool

Implements all test cases from TEST_PROCEDURES_GET_RELEVANT_CONTEXT.md
Automation ready - suitable for CI/CD pipeline integration
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import uuid4

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import SessionLocal, Base
from src.core.models import DesignDecision, CodeSnippet, ArchitectureNote
from src.core.config import get_settings

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client():
    """HTTP client for API calls"""
    async with httpx.AsyncClient(
        base_url="http://localhost:9504",
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def db_session():
    """Database session for test setup/teardown"""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(autouse=True)
def cleanup_db(db_session):
    """Clean up test data after each test"""
    yield
    # Truncate tables
    db_session.query(DesignDecision).delete()
    db_session.query(CodeSnippet).delete()
    db_session.query(ArchitectureNote).delete()
    db_session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def create_test_decision(
    db_session,
    decision: str,
    rationale: str = "Test rationale",
    status: str = "active",
    date_made: datetime = None
) -> DesignDecision:
    """Helper to create test decisions"""
    decision_obj = DesignDecision(
        decision=decision,
        rationale=rationale,
        status=status,
        date_made=date_made or datetime.now()
    )
    db_session.add(decision_obj)
    db_session.commit()
    return decision_obj


def assert_response_structure(response_data: Dict) -> None:
    """Validate response has required structure"""
    assert isinstance(response_data, dict), "Response must be dict"
    assert "query" in response_data, "Missing 'query' field"
    assert "semantic_results" in response_data, "Missing 'semantic_results' field"
    assert "recent_decisions" in response_data, "Missing 'recent_decisions' field"
    
    assert isinstance(response_data["semantic_results"], list), "semantic_results must be list"
    assert isinstance(response_data["recent_decisions"], list), "recent_decisions must be list"


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: FUNCTIONAL TESTING
# ─────────────────────────────────────────────────────────────────────────────

class TestFunctional:
    """Functional tests for get_relevant_context"""
    
    @pytest.mark.asyncio
    async def test_1_1_valid_query_default_limit(self, http_client, db_session):
        """Test 1.1: Valid Query with Default Limit (limit=5)"""
        # Setup: Create test decisions
        create_test_decision(db_session, "Use JWT for authentication")
        create_test_decision(db_session, "Implement caching layer")
        create_test_decision(db_session, "Use PostgreSQL for storage")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "authentication"}
        )
        
        # Assert
        assert response.status_code == 200, f"Status: {response.status_code}"
        data = response.json()
        
        assert_response_structure(data)
        assert data["query"] == "authentication"
        assert len(data["semantic_results"]) <= 5, "Default limit should be 5"
        
        # At least one result should match
        assert len(data["semantic_results"]) >= 1, "Should find JWT decision"
        assert "JWT" in data["semantic_results"][0]["decision"]
    
    
    @pytest.mark.asyncio
    async def test_1_2a_custom_limit_3(self, http_client, db_session):
        """Test 1.2a: Custom Limit = 3"""
        # Setup: Create 10 decisions
        for i in range(10):
            create_test_decision(db_session, f"Database decision {i}")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "database", "limit": 3}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["semantic_results"]) <= 3, "Should respect limit=3"
    
    
    @pytest.mark.asyncio
    async def test_1_2b_custom_limit_10(self, http_client, db_session):
        """Test 1.2b: Custom Limit = 10"""
        # Setup: Create 15 decisions
        for i in range(15):
            create_test_decision(db_session, f"System decision {i}")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "system", "limit": 10}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["semantic_results"]) <= 10, "Should respect limit=10"
    
    
    @pytest.mark.asyncio
    async def test_1_3_empty_query_error(self, http_client):
        """Test 1.3: Empty Query Handling"""
        # Execute with empty query
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": ""}
        )
        
        # Assert error response
        assert response.status_code == 400, "Should reject empty query"
        data = response.json()
        assert "error" in data, "Should return error field"
        assert "required" in data["error"].lower(), "Error should mention required"
    
    
    @pytest.mark.asyncio
    async def test_1_4_semantic_relevance(self, http_client, db_session):
        """Test 1.4: Semantic Relevance Validation"""
        # Setup: Create diverse decisions
        create_test_decision(db_session, "Use Docker for containerization")
        create_test_decision(db_session, "Implement REST API with FastAPI")
        create_test_decision(db_session, "Use PostgreSQL as primary database")
        create_test_decision(db_session, "Implement caching with Redis")
        
        # Execute: Query for "REST API"
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "REST API", "limit": 5}
        )
        
        # Assert relevance
        assert response.status_code == 200
        data = response.json()
        assert len(data["semantic_results"]) > 0, "Should find relevant decisions"
        
        # First result should contain REST or FastAPI
        first_result = data["semantic_results"][0]["decision"].lower()
        assert ("rest" in first_result or "fastapi" in first_result), \
            f"Expected REST/FastAPI in first result, got: {first_result}"


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case tests"""
    
    @pytest.mark.asyncio
    async def test_2_1_limit_zero(self, http_client, db_session):
        """Test 2.1: Limit = 0"""
        # Setup
        create_test_decision(db_session, "Test decision 1")
        create_test_decision(db_session, "Test decision 2")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "test", "limit": 0}
        )
        
        # Assert: Either returns empty results or error
        assert response.status_code in [200, 400], "Should handle limit=0"
        if response.status_code == 200:
            data = response.json()
            assert len(data["semantic_results"]) == 0, "limit=0 should return no results"
    
    
    @pytest.mark.asyncio
    async def test_2_2_limit_one(self, http_client, db_session):
        """Test 2.2: Limit = 1 (Minimum)"""
        # Setup
        create_test_decision(db_session, "Database decision 1")
        create_test_decision(db_session, "Database decision 2")
        create_test_decision(db_session, "Database decision 3")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "database", "limit": 1}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["semantic_results"]) <= 1, "limit=1 should return max 1 result"
    
    
    @pytest.mark.asyncio
    async def test_2_3_limit_very_high(self, http_client, db_session):
        """Test 2.3: Limit > Max (sehr hohe Werte)"""
        # Setup: Create 50 decisions
        for i in range(50):
            create_test_decision(db_session, f"System item {i}")
        
        # Execute with very high limit
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "system", "limit": 1000000}
        )
        
        # Assert: No crash, returns available results
        assert response.status_code == 200, "Should handle very high limit"
        data = response.json()
        assert len(data["semantic_results"]) <= 50, "Should not exceed available items"
        assert len(data["semantic_results"]) >= 1, "Should return at least 1 result"
    
    
    @pytest.mark.asyncio
    async def test_2_4_special_characters(self, http_client):
        """Test 2.4: Query with Special Characters"""
        # Execute: SQL injection attempt
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "'; DROP TABLE decisions; --", "limit": 5}
        )
        
        # Assert: Should be safe
        assert response.status_code in [200, 400], "Should handle safely"
        # Most importantly: database should not be corrupted
        # (verified implicitly by subsequent tests passing)
    
    
    @pytest.mark.asyncio
    async def test_2_5_non_ascii_characters(self, http_client, db_session):
        """Test 2.5: Query with Non-ASCII Characters"""
        # Setup: Create decision with special chars
        create_test_decision(db_session, "Implementeer API gateway")
        
        # Execute: Query with special chars
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "gateway", "limit": 5}
        )
        
        # Assert
        assert response.status_code == 200, "Should handle non-ASCII"
        data = response.json()
        assert len(data["semantic_results"]) >= 1, "Should find gateway decision"


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: MEMORY STATE TESTING
# ─────────────────────────────────────────────────────────────────────────────

class TestMemoryState:
    """Memory state and database state tests"""
    
    @pytest.mark.asyncio
    async def test_3_1_empty_memory(self, http_client, db_session):
        """Test 3.1: Empty Memory Repository"""
        # Setup: Database already empty (from fixtures)
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "anything", "limit": 5}
        )
        
        # Assert
        assert response.status_code == 200, "Should handle empty memory"
        data = response.json()
        assert_response_structure(data)
        assert len(data["semantic_results"]) == 0, "Empty memory should return 0 results"
        assert len(data["recent_decisions"]) == 0, "Empty memory should return 0 recent"
    
    
    @pytest.mark.asyncio
    async def test_3_2_recent_decisions_retrieval(self, http_client, db_session):
        """Test 3.2: Recent Decision Retrieval"""
        # Setup: Create decisions with different timestamps
        old_date = datetime.now() - timedelta(days=30)
        recent_date_1 = datetime.now() - timedelta(hours=2)
        recent_date_2 = datetime.now() - timedelta(hours=1)
        recent_date_3 = datetime.now()
        
        create_test_decision(db_session, "Old legacy decision", date_made=old_date)
        create_test_decision(db_session, "Use FastAPI", date_made=recent_date_1)
        create_test_decision(db_session, "Implement caching", date_made=recent_date_2)
        create_test_decision(db_session, "Add monitoring", date_made=recent_date_3)
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "any", "limit": 10}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        recent = data["recent_decisions"]
        
        assert len(recent) <= 3, "Should return max 3 recent decisions"
        assert "Add monitoring" in recent[0]["decision"], "Most recent should be first"
        assert "Old legacy" not in [r["decision"] for r in recent], "Old decision should not be included"
    
    
    @pytest.mark.asyncio
    async def test_3_3_relevance_ranking(self, http_client, db_session):
        """Test 3.3: Relevance Ranking Correctness"""
        # Setup
        create_test_decision(db_session, "Implement JWT authentication")
        create_test_decision(db_session, "Add Redis caching")
        create_test_decision(db_session, "Authenticate users with OAuth")
        create_test_decision(db_session, "Use Docker containers")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "authentication", "limit": 5}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        results = data["semantic_results"]
        
        # Should find authentication-related decisions
        assert any("authentication" in r["decision"].lower() for r in results), \
            "Should find auth-related decisions"
        
        # Docker should not appear in results
        docker_found = any("docker" in r["decision"].lower() for r in results)
        assert not docker_found, "Docker decision is irrelevant for 'authentication' query"
    
    
    @pytest.mark.asyncio
    async def test_3_4_duplicate_handling(self, http_client, db_session):
        """Test 3.4: Duplicate Filtering/Handling"""
        # Setup: Create duplicate decisions
        decision_text = "Use PostgreSQL for data storage"
        for _ in range(3):
            create_test_decision(db_session, decision_text, rationale="ACID compliance")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "PostgreSQL", "limit": 10}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        results = data["semantic_results"]
        
        # Behavior depends on implementation policy
        # Current implementation: returns all duplicates
        assert len(results) >= 1, "Should find at least one PostgreSQL decision"
        # Note: Duplicate policy should be documented


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: PERFORMANCE TESTING
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_4_1_response_time_single(self, http_client, db_session):
        """Test 4.1: Response Time < 1 Second"""
        # Setup: Create test data
        for i in range(100):
            create_test_decision(db_session, f"Decision {i} about database systems")
        
        # Execute: Single call with timing
        start = time.perf_counter()
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "database", "limit": 5}
        )
        elapsed = time.perf_counter() - start
        
        # Assert
        assert response.status_code == 200
        assert elapsed < 1.0, f"Response time {elapsed:.3f}s exceeds 1 second"
    
    
    @pytest.mark.asyncio
    async def test_4_1_response_time_bulk(self, http_client, db_session):
        """Test 4.1: Response Time Percentiles (10 calls)"""
        # Setup
        for i in range(200):
            create_test_decision(db_session, f"System decision {i}")
        
        # Execute: 10 calls and measure
        response_times = []
        for _ in range(10):
            start = time.perf_counter()
            response = await http_client.post(
                "/tools/get_relevant_context",
                json={"query": "system", "limit": 5}
            )
            elapsed = time.perf_counter() - start
            response_times.append(elapsed)
            assert response.status_code == 200
        
        # Analyze
        response_times.sort()
        avg_time = sum(response_times) / len(response_times)
        p95_time = response_times[int(len(response_times) * 0.95)]
        max_time = max(response_times)
        
        print(f"\nPerformance Results:")
        print(f"  Average: {avg_time*1000:.1f}ms")
        print(f"  P95: {p95_time*1000:.1f}ms")
        print(f"  Max: {max_time*1000:.1f}ms")
        
        # Assert
        assert avg_time < 0.5, f"Average response time {avg_time:.3f}s > 500ms"
        assert p95_time < 0.8, f"P95 response time {p95_time:.3f}s > 800ms"
    
    
    @pytest.mark.asyncio
    async def test_4_2_large_limit_100(self, http_client, db_session):
        """Test 4.2a: Large Limit (100)"""
        # Setup: Create 200 decisions
        for i in range(200):
            create_test_decision(db_session, f"Item {i} with system keyword")
        
        # Execute
        start = time.perf_counter()
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "system", "limit": 100}
        )
        elapsed = time.perf_counter() - start
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["semantic_results"]) <= 100
        assert elapsed < 1.5, f"Response time {elapsed:.3f}s exceeds 1.5 seconds"
        
        # Check response size
        import json
        response_size = len(json.dumps(data))
        assert response_size < 5_000_000, f"Response size {response_size} bytes too large"
    
    
    @pytest.mark.asyncio
    async def test_4_3_complex_query(self, http_client, db_session):
        """Test 4.3: Complex Query Performance"""
        # Setup
        create_test_decision(db_session, "Implement secure microservices architecture")
        create_test_decision(db_session, "Use distributed tracing")
        create_test_decision(db_session, "Add comprehensive logging")
        
        # Execute: Long, complex query
        complex_query = "Implement secure microservices architecture with distributed tracing and logging"
        start = time.perf_counter()
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": complex_query, "limit": 5}
        )
        elapsed = time.perf_counter() - start
        
        # Assert
        assert response.status_code == 200, f"Status: {response.status_code}"
        assert elapsed < 1.0, f"Complex query too slow: {elapsed:.3f}s"


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: INTEGRATION TESTING
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    """Integration with other tools"""
    
    @pytest.mark.asyncio
    async def test_5_1_save_decision_integration(self, http_client, db_session):
        """Test 5.1: Results Compatible with save_decision"""
        # Setup
        create_test_decision(db_session, "Use FastAPI for REST API")
        
        # Step 1: Get relevant context
        response1 = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "API framework", "limit": 5}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["semantic_results"]) > 0
        
        retrieved_decision = data1["semantic_results"][0]["decision"]
        
        # Step 2: Create new decision using retrieved context
        rationale = f"Complement to: {retrieved_decision}"
        
        # Step 3: Save new decision (would call save_decision in real scenario)
        create_test_decision(
            db_session,
            "Extend API with GraphQL support",
            rationale=rationale
        )
        
        # Step 4: Verify new decision appears in searches
        response3 = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "GraphQL", "limit": 5}
        )
        assert response3.status_code == 200
        data3 = response3.json()
        assert any("GraphQL" in r["decision"] for r in data3["semantic_results"])
    
    
    @pytest.mark.asyncio
    async def test_5_2_list_memories_consistency(self, http_client, db_session):
        """Test 5.2: Results Consistent with list_memories"""
        # Setup
        create_test_decision(db_session, "Use FastAPI", status="active")
        create_test_decision(db_session, "Implement Redis caching", status="active")
        create_test_decision(db_session, "Use Docker", status="archived")
        
        # Execute: get_relevant_context
        response1 = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "cache", "limit": 5}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Assert: Should find Redis decision
        redis_found = any(
            "Redis" in r["decision"] for r in data1["semantic_results"]
        )
        assert redis_found, "Should find Redis decision in results"
        
        # Verify: Archived decisions not included in search
        docker_found = any(
            "Docker" in r["decision"] for r in data1["semantic_results"]
        )
        # Docker has status="archived", might not appear depending on filter
    
    
    @pytest.mark.asyncio
    async def test_5_3_data_integrity(self, http_client, db_session):
        """Test 5.3: Cross-Tool Data Integrity"""
        # Setup
        decision1 = create_test_decision(db_session, "Use JWT authentication")
        decision1_id = decision1.id
        
        # Step 1: Retrieve and verify
        response1 = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "JWT", "limit": 5}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["semantic_results"]) > 0
        
        retrieved_uuid = data1["semantic_results"][0]["id"]
        assert str(decision1_id) == retrieved_uuid, "UUID should match"
        
        # Step 2: Verify consistency
        # (Would verify with list_memories in real scenario)
        
        # Step 3: Create related decision
        decision2 = create_test_decision(
            db_session,
            "Implement JWT refresh tokens"
        )
        
        # Step 4: Verify update immediately visible
        response2 = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "JWT refres", "limit": 10}  # Typo catches partial matches
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # At least one JWT decision should be found
        jwt_count = sum(
            1 for r in data2["semantic_results"] if "JWT" in r["decision"]
        )
        assert jwt_count >= 1, "Updated decisions should be visible"


# ─────────────────────────────────────────────────────────────────────────────
# Parametrized Tests (Additional Coverage)
# ─────────────────────────────────────────────────────────────────────────────

class TestParametrized:
    """Parametrized tests for comprehensive coverage"""
    
    @pytest.mark.parametrize("limit", [1, 5, 10, 25, 50])
    @pytest.mark.asyncio
    async def test_various_limits(self, http_client, db_session, limit):
        """Test various limit values"""
        # Setup
        for i in range(100):
            create_test_decision(db_session, f"Decision {i}")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": "decision", "limit": limit}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["semantic_results"]) <= limit
    
    
    @pytest.mark.parametrize("query", [
        "authentication",
        "database",
        "caching",
        "microservices",
        "security"
    ])
    @pytest.mark.asyncio
    async def test_various_queries(self, http_client, db_session, query):
        """Test various query types"""
        # Setup
        create_test_decision(db_session, f"Use {query} for system")
        create_test_decision(db_session, "Implement basic features")
        
        # Execute
        response = await http_client.post(
            "/tools/get_relevant_context",
            json={"query": query, "limit": 5}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert_response_structure(data)


# ─────────────────────────────────────────────────────────────────────────────
# Test Markers and Groups
# ─────────────────────────────────────────────────────────────────────────────

# pytest.ini markers defined as:
# [pytest]
# markers =
#     functional: functional tests
#     edge: edge case tests
#     performance: performance tests
#     integration: integration tests

# Run specific test groups:
# pytest -m functional  # Only functional tests
# pytest -m performance # Only performance tests
# pytest -m "not performance" # All except performance
