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
    return RailingFrame(rods=frame_rods)


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

    def test_evaluate_returns_score_based_on_incircle_uniformity(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test that evaluate() returns score based on incircle uniformity."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        fitness = evaluator.evaluate(simple_infill, simple_frame)

        # Simple infill has uniform holes, should get high score
        assert fitness > 0.9
        assert fitness <= 1.0

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

        # Empty infill has single hole, perfect uniformity
        assert fitness == 1.0

    def test_is_acceptable_with_empty_infill(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
    ) -> None:
        """Test is_acceptable() with empty infill arrangement."""
        evaluator = QualityEvaluator(quality_evaluator_params)
        empty_infill = RailingInfill(rods=[])

        acceptable = evaluator.is_acceptable(empty_infill, simple_frame)

        # Empty infill creates one large hole (the entire frame)
        # Should be acceptable if frame area < max_hole_area_cm2
        assert acceptable is True


class TestHoleIdentification:
    """Tests for hole identification using shapely.node() and polygonize()."""

    def test_identify_holes_with_simple_vertical_rods(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test hole identification with simple vertical rods."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        holes = evaluator._identify_holes(simple_infill, simple_frame)

        # 3 vertical rods in a 100x100 frame create 4 rectangular holes
        assert len(holes) == 4
        # Each hole should be a Polygon
        for hole in holes:
            assert isinstance(hole, Polygon)
            assert hole.is_valid

    def test_identify_holes_returns_correct_areas(
        self,
        quality_evaluator_params: QualityEvaluatorParameters,
        simple_frame: RailingFrame,
        simple_infill: RailingInfill,
    ) -> None:
        """Test that identified holes have correct areas."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        holes = evaluator._identify_holes(simple_infill, simple_frame)

        # 3 vertical rods at x=25, 50, 75 create 4 holes of width 25 each
        # Each hole: 25cm wide x 100cm tall = 2500 cm²
        expected_area = 2500.0
        for hole in holes:
            assert abs(hole.area - expected_area) < 1.0  # Allow small floating point error

    def test_identify_holes_with_crossing_rods(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test hole identification with crossing rods (different layers)."""
        # Create a 100x100 frame
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
        frame = RailingFrame(rods=frame_rods)

        # Create crossing rods: one vertical, one horizontal (different layers)
        infill_rods = [
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),  # Vertical
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
            Rod(
                geometry=LineString([(0, 50), (100, 50)]),  # Horizontal
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=2,
            ),
        ]
        infill = RailingInfill(rods=infill_rods)

        evaluator = QualityEvaluator(quality_evaluator_params)
        holes = evaluator._identify_holes(infill, frame)

        # Crossing rods create 4 quadrants
        assert len(holes) == 4
        # Each quadrant: 50cm x 50cm = 2500 cm²
        expected_area = 2500.0
        for hole in holes:
            assert isinstance(hole, Polygon)
            assert hole.is_valid
            assert abs(hole.area - expected_area) < 1.0

    def test_identify_holes_with_empty_infill(
        self, quality_evaluator_params: QualityEvaluatorParameters, simple_frame: RailingFrame
    ) -> None:
        """Test hole identification with no infill rods."""
        evaluator = QualityEvaluator(quality_evaluator_params)
        empty_infill = RailingInfill(rods=[])

        holes = evaluator._identify_holes(empty_infill, simple_frame)

        # No infill means one large hole (the entire frame)
        assert len(holes) == 1
        assert holes[0].area == pytest.approx(10000.0, rel=0.01)  # 100x100 = 10000

    def test_identify_holes_with_diagonal_rods(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test hole identification with diagonal rods."""
        # Create a 100x100 frame
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
        frame = RailingFrame(rods=frame_rods)

        # Create diagonal rods forming an X
        infill_rods = [
            Rod(
                geometry=LineString([(0, 0), (100, 100)]),  # Bottom-left to top-right
                start_cut_angle_deg=45.0,
                end_cut_angle_deg=45.0,
                weight_kg_m=0.3,
                layer=1,
            ),
            Rod(
                geometry=LineString([(100, 0), (0, 100)]),  # Bottom-right to top-left
                start_cut_angle_deg=-45.0,
                end_cut_angle_deg=-45.0,
                weight_kg_m=0.3,
                layer=2,
            ),
        ]
        infill = RailingInfill(rods=infill_rods)

        evaluator = QualityEvaluator(quality_evaluator_params)
        holes = evaluator._identify_holes(infill, frame)

        # X pattern creates 4 triangular holes
        assert len(holes) == 4
        for hole in holes:
            assert isinstance(hole, Polygon)
            assert hole.is_valid
            # Each triangle has area = (100 * 100) / 4 = 2500 cm²
            assert abs(hole.area - 2500.0) < 10.0  # Allow some tolerance for diagonal

    def test_is_acceptable_rejects_large_holes(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test that is_acceptable() rejects arrangements with holes exceeding max area."""
        # Create evaluator with small max hole area
        params = QualityEvaluatorParameters(
            max_hole_area_cm2=1000.0,  # Small max area
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        )
        evaluator = QualityEvaluator(params)

        # Create a 100x100 frame with one vertical rod
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
        frame = RailingFrame(rods=frame_rods)

        # One vertical rod creates two 50x100 = 5000 cm² holes (exceeds 1000 cm²)
        infill_rods = [
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ]
        infill = RailingInfill(rods=infill_rods)

        acceptable = evaluator.is_acceptable(infill, frame)

        # Should reject because holes are too large
        assert acceptable is False

    def test_is_acceptable_accepts_small_holes(
        self, quality_evaluator_params: QualityEvaluatorParameters, simple_frame: RailingFrame
    ) -> None:
        """Test that is_acceptable() accepts arrangements with holes within max area."""
        # Create evaluator with large max hole area
        params = QualityEvaluatorParameters(
            max_hole_area_cm2=10000.0,  # Large max area
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        )
        evaluator = QualityEvaluator(params)

        # 3 vertical rods create 4 holes of 2500 cm² each (all within limit)
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
        infill = RailingInfill(rods=infill_rods)

        acceptable = evaluator.is_acceptable(infill, simple_frame)

        # Should accept because all holes are within limit
        assert acceptable is True


class TestIncircleUniformity:
    """Tests for incircle uniformity criterion."""

    def test_calculate_incircle_radius_for_square(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test incircle radius calculation for a square."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create a 10x10 square
        square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

        radius = evaluator._calculate_incircle_radius(square)

        # For a square with side s, incircle radius = s/2
        # Area = 100, Perimeter = 40, r = 2*100/40 = 5.0
        assert abs(radius - 5.0) < 0.01

    def test_calculate_incircle_radius_for_circle(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test incircle radius calculation for a circle."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create a circle with radius 10 (approximate with many points)
        import math

        center_x, center_y = 50.0, 50.0
        radius_actual = 10.0
        num_points = 100
        points = [
            (
                center_x + radius_actual * math.cos(2 * math.pi * i / num_points),
                center_y + radius_actual * math.sin(2 * math.pi * i / num_points),
            )
            for i in range(num_points)
        ]
        circle = Polygon(points)

        radius = evaluator._calculate_incircle_radius(circle)

        # For a circle, the approximation should be very close to the actual radius
        assert abs(radius - radius_actual) < 0.5  # Allow some tolerance for approximation

    def test_calculate_incircle_radius_for_rectangle(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test incircle radius calculation for a rectangle."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create a 20x10 rectangle
        rectangle = Polygon([(0, 0), (20, 0), (20, 10), (0, 10)])

        radius = evaluator._calculate_incircle_radius(rectangle)

        # For a rectangle, the maximum inscribed circle has radius = half the shorter side
        # In this case: min(20, 10) / 2 = 5.0
        expected_radius = 5.0
        assert abs(radius - expected_radius) < 0.01

    def test_incircle_uniformity_with_identical_holes(
        self, quality_evaluator_params: QualityEvaluatorParameters, simple_frame: RailingFrame
    ) -> None:
        """Test that identical holes get perfect uniformity score."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create 3 vertical rods that divide frame into 4 equal rectangles
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
        infill = RailingInfill(rods=infill_rods)

        holes = evaluator._identify_holes(infill, simple_frame)
        score = evaluator._calculate_incircle_uniformity(holes)

        # All holes are identical 25x100 rectangles, should get perfect score
        assert score == pytest.approx(1.0, abs=0.01)

    def test_incircle_uniformity_with_varied_holes(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test that varied hole sizes get lower uniformity score."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create frame with non-uniform divisions
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
        frame = RailingFrame(rods=frame_rods)

        # Create rods at x=10 and x=90 (very uneven division: 10, 80, 10)
        infill_rods = [
            Rod(
                geometry=LineString([(10, 0), (10, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
            Rod(
                geometry=LineString([(90, 0), (90, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ]
        infill = RailingInfill(rods=infill_rods)

        holes = evaluator._identify_holes(infill, frame)
        score = evaluator._calculate_incircle_uniformity(holes)

        # Holes have very different sizes (10x100, 80x100, 10x100)
        # Should get lower score than uniform arrangement
        assert score < 0.9  # Not perfect
        assert score > 0.0  # But not zero

    def test_incircle_uniformity_with_single_hole(
        self, quality_evaluator_params: QualityEvaluatorParameters, simple_frame: RailingFrame
    ) -> None:
        """Test that single hole gets perfect uniformity score."""
        evaluator = QualityEvaluator(quality_evaluator_params)
        empty_infill = RailingInfill(rods=[])

        holes = evaluator._identify_holes(empty_infill, simple_frame)
        score = evaluator._calculate_incircle_uniformity(holes)

        # Single hole = perfect uniformity
        assert score == 1.0

    def test_incircle_uniformity_with_no_holes(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test that no holes gets perfect uniformity score."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Empty list of holes
        score = evaluator._calculate_incircle_uniformity([])

        # No holes = perfect uniformity
        assert score == 1.0

    def test_evaluate_uses_incircle_uniformity(
        self, quality_evaluator_params: QualityEvaluatorParameters, simple_frame: RailingFrame
    ) -> None:
        """Test that evaluate() now uses incircle uniformity criterion."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create uniform infill
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
        infill = RailingInfill(rods=infill_rods)

        fitness = evaluator.evaluate(infill, simple_frame)

        # Should get high score for uniform arrangement
        assert fitness > 0.9
        assert fitness <= 1.0

    def test_evaluate_with_non_uniform_arrangement(
        self, quality_evaluator_params: QualityEvaluatorParameters
    ) -> None:
        """Test that evaluate() gives lower score for non-uniform arrangement."""
        evaluator = QualityEvaluator(quality_evaluator_params)

        # Create frame
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
        frame = RailingFrame(rods=frame_rods)

        # Create non-uniform infill
        infill_rods = [
            Rod(
                geometry=LineString([(10, 0), (10, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
            Rod(
                geometry=LineString([(90, 0), (90, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
        ]
        infill = RailingInfill(rods=infill_rods)

        fitness = evaluator.evaluate(infill, frame)

        # Should get lower score for non-uniform arrangement
        assert fitness < 0.9
        assert fitness > 0.0
