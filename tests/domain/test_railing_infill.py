"""Tests for RailingInfill class."""

import pytest
from shapely.geometry import LineString
from railing_generator.domain.rod import Rod
from railing_generator.domain.railing_infill import RailingInfill


@pytest.fixture
def sample_rods() -> list[Rod]:
    """Create sample infill rods for testing."""
    return [
        Rod(
            geometry=LineString([(0, 0), (0, 100)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=1,
        ),
        Rod(
            geometry=LineString([(50, 0), (50, 100)]),
            start_cut_angle_deg=15,
            end_cut_angle_deg=-15,
            weight_kg_m=0.5,
            layer=1,
        ),
        Rod(
            geometry=LineString([(100, 0), (100, 100)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=2,
        ),
    ]


def test_railing_infill_creation(sample_rods: list[Rod]) -> None:
    """Test creating a RailingInfill instance."""
    infill = RailingInfill(rods=sample_rods)

    assert infill.rods == sample_rods
    assert infill.fitness_score is None
    assert infill.iteration_count is None
    assert infill.duration_sec is None


def test_railing_infill_with_metadata(sample_rods: list[Rod]) -> None:
    """Test creating a RailingInfill with optional metadata."""
    infill = RailingInfill(
        rods=sample_rods, fitness_score=0.85, iteration_count=42, duration_sec=12.5
    )

    assert infill.rods == sample_rods
    assert infill.fitness_score == 0.85
    assert infill.iteration_count == 42
    assert infill.duration_sec == 12.5


def test_railing_infill_rod_count(sample_rods: list[Rod]) -> None:
    """Test rod_count computed property."""
    infill = RailingInfill(rods=sample_rods)
    assert infill.rod_count == 3


def test_railing_infill_rod_count_empty() -> None:
    """Test rod_count with empty rods list."""
    infill = RailingInfill(rods=[])
    assert infill.rod_count == 0


def test_railing_infill_total_length(sample_rods: list[Rod]) -> None:
    """Test total_length_cm computed property."""
    infill = RailingInfill(rods=sample_rods)
    # Each rod is 100cm long, 3 rods total
    assert infill.total_length_cm == pytest.approx(300.0, rel=1e-6)


def test_railing_infill_total_weight(sample_rods: list[Rod]) -> None:
    """Test total_weight_kg computed property."""
    infill = RailingInfill(rods=sample_rods)
    # Each rod: 100cm * 0.5 kg/m = 1.0m * 0.5 kg/m = 0.5 kg
    # 3 rods * 0.5 kg = 1.5 kg
    assert infill.total_weight_kg == pytest.approx(1.5, rel=1e-6)


def test_railing_infill_immutable(sample_rods: list[Rod]) -> None:
    """Test that RailingInfill is immutable (frozen)."""
    infill = RailingInfill(rods=sample_rods)

    with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
        infill.fitness_score = 0.9  # type: ignore[misc,unused-ignore]


def test_railing_infill_serialization(sample_rods: list[Rod]) -> None:
    """Test serialization of RailingInfill."""
    infill = RailingInfill(
        rods=sample_rods, fitness_score=0.85, iteration_count=42, duration_sec=12.5
    )

    # Test model_dump
    data = infill.model_dump()
    assert "rods" in data
    assert data["fitness_score"] == 0.85
    assert data["iteration_count"] == 42
    assert data["duration_sec"] == 12.5
    assert data["rod_count"] == 3
    assert data["total_length_cm"] == pytest.approx(300.0, rel=1e-6)
    assert data["total_weight_kg"] == pytest.approx(1.5, rel=1e-6)


def test_railing_infill_validation_negative_iteration() -> None:
    """Test validation rejects negative iteration count."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        RailingInfill(rods=[], iteration_count=-1)


def test_railing_infill_validation_negative_duration() -> None:
    """Test validation rejects negative duration."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        RailingInfill(rods=[], duration_sec=-1.0)
