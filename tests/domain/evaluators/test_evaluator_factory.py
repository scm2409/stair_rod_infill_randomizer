"""Tests for Evaluator Factory."""

import pytest

from railing_generator.domain.evaluators.evaluator_factory import EvaluatorFactory
from railing_generator.domain.evaluators.passthrough_evaluator import PassThroughEvaluator
from railing_generator.domain.evaluators.passthrough_evaluator_parameters import (
    PassThroughEvaluatorParameters,
)
from railing_generator.domain.evaluators.quality_evaluator import QualityEvaluator
from railing_generator.domain.evaluators.quality_evaluator_parameters import (
    QualityEvaluatorParameters,
)


class TestEvaluatorFactory:
    """Tests for EvaluatorFactory."""

    def test_create_passthrough_evaluator(self) -> None:
        """Test creating Pass-Through Evaluator from parameters."""
        params = PassThroughEvaluatorParameters()

        evaluator = EvaluatorFactory.create_evaluator(params)

        assert isinstance(evaluator, PassThroughEvaluator)
        assert evaluator.params == params

    def test_create_quality_evaluator(self) -> None:
        """Test creating Quality Evaluator from parameters."""
        params = QualityEvaluatorParameters(
            max_hole_area_cm2=10000.0,
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        )

        evaluator = EvaluatorFactory.create_evaluator(params)

        assert isinstance(evaluator, QualityEvaluator)
        assert evaluator.params == params

    def test_create_evaluator_with_invalid_type(self) -> None:
        """Test that factory raises error for unknown evaluator type."""
        from pydantic import BaseModel

        # Create a mock parameter class that doesn't match any known type
        class UnknownEvaluatorParameters(BaseModel):
            type: str = "unknown"

        params = UnknownEvaluatorParameters()

        with pytest.raises(ValueError, match="Unknown evaluator parameter type"):
            EvaluatorFactory.create_evaluator(params)  # type: ignore[arg-type]

    def test_factory_returns_correct_types(self) -> None:
        """Test that factory returns correct evaluator types for different parameters."""
        passthrough_params = PassThroughEvaluatorParameters()
        quality_params = QualityEvaluatorParameters(
            max_hole_area_cm2=5000.0,
            hole_uniformity_weight=0.3,
            incircle_uniformity_weight=0.2,
            angle_distribution_weight=0.2,
            anchor_spacing_horizontal_weight=0.15,
            anchor_spacing_vertical_weight=0.15,
        )

        passthrough_evaluator = EvaluatorFactory.create_evaluator(passthrough_params)
        quality_evaluator = EvaluatorFactory.create_evaluator(quality_params)

        # Verify types are different
        assert type(passthrough_evaluator) != type(quality_evaluator)
        assert isinstance(passthrough_evaluator, PassThroughEvaluator)
        assert isinstance(quality_evaluator, QualityEvaluator)
