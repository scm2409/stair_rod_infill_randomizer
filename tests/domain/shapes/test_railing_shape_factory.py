"""Tests for RailingShapeFactory."""

import pytest

from railing_generator.domain.shapes.railing_shape_factory import RailingShapeFactory
from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShape,
    RectangularRailingShapeParameters,
)
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShape,
    StaircaseRailingShapeParameters,
)


class TestRailingShapeFactory:
    """Test suite for RailingShapeFactory."""

    def test_create_staircase_shape(self) -> None:
        """Test creating a staircase shape from factory."""
        # Arrange
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act
        shape = RailingShapeFactory.create_shape("staircase", params)

        # Assert
        assert isinstance(shape, StaircaseRailingShape)
        assert shape.params == params

    def test_create_shape_with_unknown_type(self) -> None:
        """Test that creating a shape with unknown type raises ValueError."""
        # Arrange
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown shape type: 'invalid'"):
            RailingShapeFactory.create_shape("invalid", params)

    def test_create_shape_with_mismatched_parameters(self) -> None:
        """Test that creating a shape with wrong parameter type raises ValueError."""
        # Arrange - Create a mock parameter class that's not StaircaseRailingShapeParameters
        from pydantic import BaseModel

        class WrongParameters(BaseModel):
            """Mock wrong parameter type."""

            some_field: float = 1.0

        params = WrongParameters()

        # Act & Assert
        with pytest.raises(ValueError, match="requires StaircaseRailingShapeParameters"):
            RailingShapeFactory.create_shape("staircase", params)  # type: ignore[arg-type]

    def test_create_rectangular_shape(self) -> None:
        """Test creating a rectangular shape from factory."""
        # Arrange
        params = RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act
        shape = RailingShapeFactory.create_shape("rectangular", params)

        # Assert
        assert isinstance(shape, RectangularRailingShape)
        assert shape.params == params

    def test_create_rectangular_shape_with_mismatched_parameters(self) -> None:
        """Test that creating rectangular shape with wrong parameter type raises ValueError."""
        # Arrange - Use staircase parameters for rectangular shape
        params = StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="requires RectangularRailingShapeParameters"):
            RailingShapeFactory.create_shape("rectangular", params)

    def test_get_available_shape_types(self) -> None:
        """Test getting list of available shape types."""
        # Act
        types = RailingShapeFactory.get_available_shape_types()

        # Assert
        assert isinstance(types, list)
        assert "staircase" in types
        assert "rectangular" in types
        assert len(types) >= 2  # At least staircase and rectangular should be available

    def test_create_shape_with_registered_but_unhandled_type(self) -> None:
        """Test that factory raises error for registered but unhandled shape types."""
        # Arrange - Temporarily add a shape type to registry without handling it
        from pydantic import BaseModel

        class MockShape:
            """Mock shape class."""

            def __init__(self, params: BaseModel):
                pass

        # Save original registry
        original_registry = RailingShapeFactory._SHAPE_REGISTRY.copy()

        try:
            # Add mock shape to registry
            RailingShapeFactory._SHAPE_REGISTRY["mock"] = MockShape  # type: ignore[assignment]

            params = StaircaseRailingShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=280.0,
                stair_height_cm=280.0,
                num_steps=10,
                frame_weight_per_meter_kg_m=0.5,
            )

            # Act & Assert
            with pytest.raises(ValueError, match="Unhandled shape type: 'mock'"):
                RailingShapeFactory.create_shape("mock", params)

        finally:
            # Restore original registry
            RailingShapeFactory._SHAPE_REGISTRY = original_registry
