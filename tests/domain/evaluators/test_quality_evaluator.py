"""Tests for Quality Evaluator."""

import pytest
from shapely.geometry import LineString, Polygon

from railing_generator.domain.evaluators.quality_evaluator import QualityEvaluator
from railing_generator.domain.evaluators.quality_evaluator_criteria_defaults import (
    QualityEvaluatorCriteriaDefaults,
)
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod


@pytest.fixture
def quality_evaluator_params() -> QualityEvaluatorParameters:
    """Create Quality Evaluator parameters for testing."""
    return QualityEvaluatorParameters(
        max_hole_area_cm2=10000.0,
        hole_uniformity_weight=0.3,
        incircle_uniformity_weight=0.2,
        angle_distribution_weight=0.2,
        anchor_spacing_horizontal_weight=0.15,
        anchor_spacing_vertical_weight=0.15,
    )


@pytest.fixture
def simple_frame() -> RailingFrame:
    """Create a simple rectangular frame for testing."""
    # Create a 100cm x 100cm rectangular frame
    frame_rods = [
        Rod(
            geometry=LineString([(0, 0), (100, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 0), (100, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 100), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 100), (0, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]
    boundary = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    return RailingFrame(rods=frame_rods, boundary=boundary)


@pytest.fixture
def simple_infill() -> RailingInfill:
    """Create a simple infill arrangement for testing."""
    infill_rods = [
        Rod(
            geometry=LineString([(25, 0), (25, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(50, 0), (50, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(75, 0), (75, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        ),
    ]
    return RailingInfill(rods=infill_rods)


class TestQualityEvaluatorParameters:
    """Tests for QualityEvaluatorParameters."""

    def test_create_with_valid_parameters(self) -> None:
        """Test creating parameters with valid values."""
        params = QualityEvaluatorParameters(
            max_hole_area_cm2=5000.0,
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        )

        assert params.type == "quality"
        assert params.max_hole_area_cm2 == 5000.0
        assert params.hole_uniformity_weight == 0.3
        assert params.incircle_uniformity_weight == 0.2
        assert params.angle_distribution_weight == 0.2
        assert params.anchor_spacing_horizontal_weight == 0.15
        assert params.anchor_spacing_vertical_weight == 0.15

    def test_type_discriminator_is_quality(self) -> None:
        """Test that type discriminator is always 'quality'."""
        params = QualityEvaluatorParameters(
            max_hole_area_cm2=10000.0,
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        )

        assert params.type == "quality"

    def test_from_defaults(self) -> None:
        """Test creating parameters from defaults."""
        criteria = QualityEvaluatorCriteriaDefaults()
        params = QualityEvaluatorParameters.from_defaults(
            max_hole_area_cm2=8000.0, criteria=criteria
        )

        assert params.max_hole_area_cm2 == 8000.0
        assert params.hole_uniformity_weight == criteria.hole_uniformity_weight
        assert params.incircle_uniformity_weight == criteria.incircle_uniformity_weight
        assert params.angle_distribution_weight == criteria.angle_distribution_weight
        assert params.anchor_spacing_horizontal_weight == criteria.anchor_spacing_horizontal_weight
        assert params.anchor_spacing_vertical_weight == criteria.anchor_spacing_vertical_weight

    def test_invalid_max_hole_area(self) -> None:
        """Test that negative max hole area is rejected."""
        with pytest.raises(ValueError):
            QualityEvaluatorParameters(
                max_hole_area_cm2=-100.0,
                hole_uniformity_weight=0.3,
                incircle_uniformity_weight=0.2,
                angle_distribution_weight=0.2,
                anchor_spacing_horizontal_weight=0.15,
                anchor_spacing_vertical_weight=0.15,
            )

    def test_invalid_weight_out_of_range(self) -> None:
        """Test that weights outside [0, 1] are rejected."""
        with pytest.raises(ValueError):
            QualityEvaluatorParameters(
                max_hole_area_cm2=10000.0,
                hole_uniformity_weight=1.5,  # Invalid: > 1.0
                incircle_uniformity_weight=0.2,
                angle_distribution_weight=0.2,
                anchor_spacing_horizontal_weight=0.15,
                anchor_spacing_vertical_weight=0.15,
            )


class TestQualityEvaluatorCriteriaDefaults:
    """Tests for QualityEvaluatorCriteriaDefaults."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        defaults = QualityEvaluatorCriteriaDefaults()

        assert defaults.hole_uniformity_weight == 0.3
        assert defaults.incircle_uniformity_weight == 0.2
        assert defaults.angle_distribution_weight == 0.2
        assert defaults.anchor_spacing_horizontal_weight == 0.15
        assert defaults.anchor_spacing_vertical_weight == 0.15

    def test_weights_sum_to_one(self) -> None:
        """Test that default weights sum to approximately 1.0."""
        defaults = QualityEvaluatorCriteriaDefaults()

        total = (
            defaults.hole_uniformity_weight
            + defaults.incircle_uniformity_weight
            + defaults.angle_distribution_weight
            + defaults.anchor_spacing_horizontal_weight
            + defaults.anchor_spacing_vertical_weight
        )

        assert abs(total - 1.0) < 0.01  # Allow small floating point error


class TestQualityEvaluator:
    """Tests for QualityEvaluator."""

    def test_initialization(self, quality_evaluator_params: QualityEvaluatorParameters) -> None:
        """Test that evaluator initializes correctly."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        assert evaluator.params == quality_evaluator_params

    def test_evaluate_returns_dummy_score(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test that evaluate() returns dummy score of 0.5."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        fitness = evaluator.evaluate(simple_infill, simple_frame)

        # Dummy implementation should return 0.5
        assert fitness == 0.5

    def test_evaluate_returns_float(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test that evaluate() returns a float value."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        fitness = evaluator.evaluate(simple_infill, simple_frame)

        assert isinstance(fitness, float)

    def test_is_acceptable_returns_dummy_true(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test that is_acceptable() returns dummy value of True."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        acceptable = evaluator.is_acceptable(simple_infill, simple_frame)

        # Dummy implementation should always return True
        assert acceptable is True

    def test_is_acceptable_returns_bool(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test that is_acceptable() returns a boolean value."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        acceptable = evaluator.is_acceptable(simple_infill, simple_frame)

        assert isinstance(acceptable, bool)

    def test_evaluate_with_empty_infill(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
    ) -> None:
        """Test evaluate() with empty infill arrangement."""
        evaluator = QualityEvaluator(quality_evaluator_params)
        empty_infill = RailingInfill(rods=[])

        fitness = evaluator.evaluate(empty_infill, simple_frame)

        # Should still return dummy score
        assert fitness == 0.5

    def test_is_acceptable_with_empty_infill(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
    ) -> None:
        """Test is_acceptable() with empty infill arrangement."""
        evaluator = QualityEvaluator(quality_evaluator_params)
        empty_infill = RailingInfill(rods=[])

        acceptable = evaluator.is_acceptable(empty_infill, simple_frame)

        # Should still return dummy True
        assert acceptable is True
