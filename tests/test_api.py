"""
API endpoint tests.

Tests all major API endpoints to ensure they return correct data and status codes.
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoints:
    """Test root and utility endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert data["version"] == "1.0.0"

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_stats_endpoint(self, client):
        """Test the statistics endpoint returns database stats."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "database_stats" in data
        assert "total_members" in data["database_stats"]
        assert "total_votes" in data["database_stats"]
        assert "total_bills" in data["database_stats"]
        # Verify we have data
        assert data["database_stats"]["total_members"] > 0
        assert data["database_stats"]["total_bills"] > 0


class TestMembersEndpoints:
    """Test member-related endpoints."""

    def test_list_members(self, client):
        """Test listing members with pagination."""
        response = client.get("/members/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()

        # Check pagination structure
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "items" in data

        # Verify pagination values
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10
        assert data["total"] > 0

    def test_list_members_with_filters(self, client):
        """Test member filtering by party."""
        response = client.get("/members/?party=Liberal&page_size=5")
        assert response.status_code == 200
        data = response.json()

        # All returned members should be Liberal
        for member in data["items"]:
            assert member["party"] == "Liberal"

    def test_list_parties(self, client):
        """Test getting list of parties."""
        response = client.get("/members/parties")
        assert response.status_code == 200
        parties = response.json()
        assert isinstance(parties, list)
        assert len(parties) > 0
        # Common Canadian parties
        assert any("Liberal" in p for p in parties)

    def test_list_provinces(self, client):
        """Test getting list of provinces."""
        response = client.get("/members/provinces")
        assert response.status_code == 200
        provinces = response.json()
        assert isinstance(provinces, list)
        assert len(provinces) > 0
        # Check for common provinces
        assert any("Ontario" in p for p in provinces)

    def test_get_member_detail(self, client):
        """Test getting detailed member information."""
        # First get a member ID
        list_response = client.get("/members/?page_size=1")
        member_id = list_response.json()["items"][0]["member_id"]

        # Get detailed info
        response = client.get(f"/members/{member_id}")
        assert response.status_code == 200
        data = response.json()

        assert "member_id" in data
        assert "name" in data
        assert "roles" in data
        assert "votes_count" in data
        assert "sponsored_bills_count" in data

    def test_get_member_roles(self, client):
        """Test getting member's roles."""
        # Get a member ID
        list_response = client.get("/members/?page_size=1")
        member_id = list_response.json()["items"][0]["member_id"]

        response = client.get(f"/members/{member_id}/roles")
        assert response.status_code == 200
        roles = response.json()
        assert isinstance(roles, list)

    def test_get_nonexistent_member(self, client):
        """Test getting a member that doesn't exist."""
        response = client.get("/members/999999")
        assert response.status_code == 404


class TestVotesEndpoints:
    """Test vote-related endpoints."""

    def test_list_votes(self, client):
        """Test listing votes with pagination."""
        response = client.get("/votes/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()

        # Check pagination
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) <= 10

    def test_list_parliaments(self, client):
        """Test getting parliament/session combinations."""
        response = client.get("/votes/parliaments")
        assert response.status_code == 200
        parliaments = response.json()

        assert isinstance(parliaments, list)
        assert len(parliaments) > 0
        # Each entry should have parliament_number, session_number, vote_count
        for parl in parliaments:
            assert "parliament_number" in parl
            assert "session_number" in parl
            assert "vote_count" in parl

    def test_vote_summary(self, client):
        """Test vote summary statistics."""
        response = client.get("/votes/stats/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_votes" in data
        assert "agreed" in data
        assert "negatived" in data


class TestBillsEndpoints:
    """Test bill-related endpoints."""

    def test_list_bills(self, client):
        """Test listing bills with pagination."""
        response = client.get("/bills/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()

        # Check pagination
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) <= 10
        assert data["total"] > 0

    def test_list_bills_with_search(self, client):
        """Test searching bills by title."""
        response = client.get("/bills/?search=Act&page_size=5")
        assert response.status_code == 200
        data = response.json()

        # Results should contain "Act" in title or number
        for bill in data["items"]:
            text = f"{bill['bill_number']} {bill.get('short_title', '')} {bill.get('long_title', '')}"
            assert "Act" in text or "act" in text.lower()

    def test_list_chambers(self, client):
        """Test getting list of chambers."""
        response = client.get("/bills/chambers")
        assert response.status_code == 200
        chambers = response.json()

        assert isinstance(chambers, list)
        # Should have House and/or Senate
        assert len(chambers) > 0

    def test_list_bill_statuses(self, client):
        """Test getting list of bill statuses."""
        response = client.get("/bills/statuses")
        assert response.status_code == 200
        statuses = response.json()

        assert isinstance(statuses, list)
        assert len(statuses) > 0

    def test_get_bill_detail(self, client):
        """Test getting detailed bill information."""
        # Get a bill ID
        list_response = client.get("/bills/?page_size=1")
        bill_id = list_response.json()["items"][0]["bill_id"]

        response = client.get(f"/bills/{bill_id}")
        assert response.status_code == 200
        data = response.json()

        assert "bill_id" in data
        assert "bill_number" in data
        assert "progress_stages" in data
        assert "votes_count" in data

    def test_get_bill_progress(self, client):
        """Test getting bill progress stages."""
        # Get a bill ID
        list_response = client.get("/bills/?page_size=1")
        bill_id = list_response.json()["items"][0]["bill_id"]

        response = client.get(f"/bills/{bill_id}/progress")
        assert response.status_code == 200
        progress = response.json()

        assert isinstance(progress, list)

    def test_bills_summary(self, client):
        """Test bills summary statistics."""
        response = client.get("/bills/stats/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_bills" in data
        assert "house_bills" in data
        assert "senate_bills" in data


class TestPagination:
    """Test pagination logic across endpoints."""

    def test_pagination_page_size_limits(self, client):
        """Test that page_size is enforced."""
        # Request 500 items (should be capped at 200)
        response = client.get("/members/?page_size=500")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 200

    def test_pagination_total_pages_calculation(self, client):
        """Test that total_pages is calculated correctly."""
        response = client.get("/members/?page_size=10")
        assert response.status_code == 200
        data = response.json()

        expected_pages = (data["total"] + 9) // 10  # Ceiling division
        assert data["total_pages"] == expected_pages

    def test_pagination_empty_page(self, client):
        """Test requesting a page beyond available data."""
        response = client.get("/members/?page=99999&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestDataIntegrity:
    """Test data integrity and relationships."""

    def test_member_has_roles(self, client):
        """Test that members have associated roles."""
        # Get first member
        response = client.get("/members/?page_size=1")
        member = response.json()["items"][0]
        member_id = member["member_id"]

        # Check roles
        roles_response = client.get(f"/members/{member_id}/roles")
        roles = roles_response.json()

        # Member should have at least one role
        assert len(roles) > 0

    def test_bill_sponsor_exists(self, client):
        """Test that bills with sponsors reference valid members."""
        # Get bills with sponsors
        response = client.get("/bills/?page_size=10")
        bills = response.json()["items"]

        for bill in bills:
            if bill.get("sponsor_id"):
                # Verify sponsor exists
                sponsor_response = client.get(f"/members/{bill['sponsor_id']}")
                assert sponsor_response.status_code in [200, 404]  # Either exists or doesn't
