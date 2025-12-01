"""Tests for InfillEditOperation model."""

from datetime import datetime

import pytest
from shapely.geometry import LineString

from railing_generator.domain.infill_edit_operation import InfillEditOperation
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


class TestInfillEditOperation:
    """Tests for InfillEditOperation model."""

    @pytest.fixture
    def sample_rod(self) -> Rod:
        """Create a sample rod for testing."""
        return Rod(
            geometry=LineString([(0, 0), (10, 10)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )

    @pytest.fixture
    def previous_infill(self, sample_rod: Rod) -> RailingInfill:
        """Create a sample previous infill state."""
        return RailingInfill(
            rods=[sample_rod],
            fitness_score=0.72,
            iteration_count=100,
            duration_sec=5.0,
        )

    @pytest.fixture
    def new_infill(self) -> RailingInfill:
        """Create a sample new infill state."""
        new_rod = Rod(
            geometry=LineString([(0, 0), (15, 15)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )
        return RailingInfill(
            rods=[new_rod],
            fitness_score=0.78,
            iteration_count=100,
            duration_sec=5.0,
        )

    def test_create_operation(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test creating an edit operation."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=0.72,
            new_fitness_score=0.78,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.previous_infill == previous_infill
        assert operation.new_infill == new_infill
        assert operation.previous_fitness_score == 0.72
        assert operation.new_fitness_score == 0.78
        assert operation.source_anchor_index == 0
        assert operation.target_anchor_index == 5
        assert operation.rod_index == 0
        assert isinstance(operation.timestamp, datetime)

    def test_operation_is_immutable(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test that operation is immutable (frozen)."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
            operation.rod_index = 10  # type: ignore[misc]

    def test_fitness_change_with_scores(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change property with valid scores."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=0.72,
            new_fitness_score=0.78,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.fitness_change == pytest.approx(0.06)

    def test_fitness_change_without_previous_score(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change returns None when previous score is None."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=None,
            new_fitness_score=0.78,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.fitness_change is None

    def test_fitness_change_without_new_score(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change returns None when new score is None."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=0.72,
            new_fitness_score=None,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.fitness_change is None

    def test_fitness_change_percent_with_scores(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change_percent property with valid scores."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=0.72,
            new_fitness_score=0.78,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        # (0.78 - 0.72) / 0.72 * 100 = 8.33...%
        assert operation.fitness_change_percent == pytest.approx(8.333, rel=0.01)

    def test_fitness_change_percent_without_scores(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change_percent returns None when scores are None."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=None,
            new_fitness_score=None,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.fitness_change_percent is None

    def test_fitness_change_percent_with_zero_previous(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change_percent returns None when previous score is zero."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=0.0,
            new_fitness_score=0.78,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.fitness_change_percent is None

    def test_negative_fitness_change(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test fitness_change with negative change (quality decreased)."""
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            previous_fitness_score=0.80,
            new_fitness_score=0.70,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
        )

        assert operation.fitness_change == pytest.approx(-0.10)
        assert operation.fitness_change_percent == pytest.approx(-12.5)

    def test_custom_timestamp(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test creating operation with custom timestamp."""
        custom_time = datetime(2025, 1, 15, 10, 30, 0)
        operation = InfillEditOperation(
            previous_infill=previous_infill,
            new_infill=new_infill,
            source_anchor_index=0,
            target_anchor_index=5,
            rod_index=0,
            timestamp=custom_time,
        )

        assert operation.timestamp == custom_time

    def test_invalid_negative_anchor_index(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test that negative anchor indices are rejected."""
        with pytest.raises(ValueError):
            InfillEditOperation(
                previous_infill=previous_infill,
                new_infill=new_infill,
                source_anchor_index=-1,
                target_anchor_index=5,
                rod_index=0,
            )

    def test_invalid_negative_rod_index(
        self, previous_infill: RailingInfill, new_infill: RailingInfill
    ) -> None:
        """Test that negative rod index is rejected."""
        with pytest.raises(ValueError):
            InfillEditOperation(
                previous_infill=previous_infill,
                new_infill=new_infill,
                source_anchor_index=0,
                target_anchor_index=5,
                rod_index=-1,
            )
