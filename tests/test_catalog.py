"""
Tests for specialty catalog.
"""

import pytest

from src.catalog import (
    get_catalog,
    get_specialty_by_id,
    get_specialty_ids,
    validate_specialty_ids,
    get_generalist_ids,
)


def test_catalog_integrity():
    """Test that catalog is well-formed."""
    catalog = get_catalog()

    assert len(catalog) > 0, "Catalog should not be empty"

    # Check all IDs are unique
    ids = [spec.id for spec in catalog]
    assert len(ids) == len(set(ids)), "Specialty IDs must be unique"

    # Check all have required fields
    for spec in catalog:
        assert spec.id, "Specialty must have ID"
        assert spec.display_name, "Specialty must have display name"
        assert spec.type in ["generalist", "medical", "surgical"], f"Invalid type: {spec.type}"
        assert 0.0 <= spec.emergency_weight <= 1.0
        assert 0.0 <= spec.pediatric_weight <= 1.0
        assert 0.0 <= spec.adult_weight <= 1.0
        assert 0.0 <= spec.procedural_signal <= 1.0


def test_get_specialty_by_id():
    """Test specialty lookup by ID."""
    # Valid ID
    cardiology = get_specialty_by_id("cardiology")
    assert cardiology is not None
    assert cardiology.id == "cardiology"
    assert cardiology.display_name == "Cardiology"

    # Invalid ID
    invalid = get_specialty_by_id("nonexistent_specialty")
    assert invalid is None


def test_get_specialty_ids():
    """Test getting all specialty IDs."""
    ids = get_specialty_ids()

    assert len(ids) > 0
    assert "cardiology" in ids
    assert "emergency_medicine" in ids
    assert "neurology" in ids


def test_validate_specialty_ids():
    """Test specialty ID validation."""
    # Valid IDs
    is_valid, invalid = validate_specialty_ids(["cardiology", "neurology"])
    assert is_valid
    assert len(invalid) == 0

    # Invalid IDs
    is_valid, invalid = validate_specialty_ids(["cardiology", "fake_specialty"])
    assert not is_valid
    assert "fake_specialty" in invalid

    # Mixed
    is_valid, invalid = validate_specialty_ids(["cardiology", "fake1", "neurology", "fake2"])
    assert not is_valid
    assert len(invalid) == 2
    assert "fake1" in invalid
    assert "fake2" in invalid


def test_get_generalist_ids():
    """Test getting generalist specialty IDs."""
    generalist_ids = get_generalist_ids()

    assert len(generalist_ids) == 3
    assert "emergency_medicine" in generalist_ids
    assert "pediatrics" in generalist_ids
    assert "family_internal_medicine" in generalist_ids


def test_catalog_coverage():
    """Test that catalog has expected specialties."""
    ids = get_specialty_ids()

    # Check for key specialties
    expected = [
        "emergency_medicine",
        "pediatrics",
        "family_internal_medicine",
        "cardiology",
        "neurology",
        "pulmonology",
        "gastroenterology",
        "general_surgery",
        "orthopedic_surgery",
    ]

    for spec_id in expected:
        assert spec_id in ids, f"Expected specialty {spec_id} not in catalog"
