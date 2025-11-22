"""Tests for RailingProjectModel."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject
from shapely.geometry import LineString

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.railing_shape_parameters import RailingShapeParameters


class MockShapeParameters(RailingShapeParameters):
    """Mock shape parameters for testing."""

    value: float = 10.0


class MockInfillGeneratorParameters(InfillGeneratorParameters):
    """Mock infill generator parameters for testing."""

    value: float = 10.0


@pytest.fixture
def model() -> RailingProjectModel:
    """Create a RailingProjectModel instance for testing."""
    return RailingProjectModel()


@pytest.fixture
def sample_frame() -> RailingFrame:
    """Create a sample RailingFrame for testing."""
    # Create a simple rectangular frame
    rods = [
        Rod(
            geometry=LineString([(0, 0), (0, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 100), (100, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 100), (100, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 0), (0, 0)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]
    return RailingFrame(rods=rods)


@pytest.fixture
def sample_infill() -> RailingInfill:
    """Create a sample RailingInfill for testing."""
    return RailingInfill(
        rods=[],
        fitness_score=0.85,
        iteration_count=100,
        duration_sec=5.2,
    )


def test_model_initialization(model: RailingProjectModel) -> None:
    """Test that model initializes with default state."""
    assert isinstance(model, QObject)
    assert model.railing_shape_type is None
    assert model.railing_shape_parameters is None
    assert model.railing_frame is None
    assert model.infill_generator_type is None
    assert model.infill_generator_parameters is None
    assert model.railing_infill is None
    assert model.project_file_path is None
    assert model.project_modified is False
    assert model.rod_annotation_visible is False


def test_set_railing_shape_type_emits_signal(model: RailingProjectModel) -> None:
    """Test that setting shape type emits signal."""
    signal_spy = MagicMock()
    model.railing_shape_type_changed.connect(signal_spy)

    model.set_railing_shape_type("staircase")

    assert model.railing_shape_type == "staircase"
    signal_spy.assert_called_once_with("staircase")


def test_set_railing_shape_type_clears_frame(
    model: RailingProjectModel, sample_frame: RailingFrame
) -> None:
    """Test that changing shape type clears the frame."""
    # Set initial frame
    model.set_railing_frame(sample_frame)
    assert model.railing_frame is not None

    # Change shape type should clear frame
    frame_signal_spy = MagicMock()
    model.railing_frame_updated.connect(frame_signal_spy)

    model.set_railing_shape_type("rectangular")

    assert model.railing_frame is None
    frame_signal_spy.assert_called_once_with(None)


def test_set_railing_shape_parameters_emits_signal(model: RailingProjectModel) -> None:
    """Test that setting shape parameters emits signal and marks modified."""
    signal_spy = MagicMock()
    modified_spy = MagicMock()
    model.railing_shape_parameters_changed.connect(signal_spy)
    model.project_modified_changed.connect(modified_spy)

    params = MockShapeParameters(value=20.0)
    model.set_railing_shape_parameters(params)

    assert model.railing_shape_parameters == params
    signal_spy.assert_called_once_with(params)
    modified_spy.assert_called_once_with(True)
    assert model.project_modified is True


def test_set_railing_frame_emits_signal(
    model: RailingProjectModel, sample_frame: RailingFrame
) -> None:
    """Test that setting frame emits signal and marks modified."""
    signal_spy = MagicMock()
    modified_spy = MagicMock()
    model.railing_frame_updated.connect(signal_spy)
    model.project_modified_changed.connect(modified_spy)

    model.set_railing_frame(sample_frame)

    assert model.railing_frame == sample_frame
    signal_spy.assert_called_once_with(sample_frame)
    modified_spy.assert_called_once_with(True)
    assert model.project_modified is True


def test_set_railing_frame_clears_infill(
    model: RailingProjectModel, sample_frame: RailingFrame, sample_infill: RailingInfill
) -> None:
    """Test that changing frame clears the infill."""
    # Set initial infill
    model.set_railing_infill(sample_infill)
    assert model.railing_infill is not None

    # Change frame should clear infill
    infill_signal_spy = MagicMock()
    model.railing_infill_updated.connect(infill_signal_spy)

    model.set_railing_frame(sample_frame)

    assert model.railing_infill is None
    # Called once for clearing infill (set_railing_frame triggers set_railing_infill(None))
    infill_signal_spy.assert_called_once_with(None)


def test_set_infill_generator_type_emits_signal(model: RailingProjectModel) -> None:
    """Test that setting infill generator type emits signal and marks modified."""
    signal_spy = MagicMock()
    modified_spy = MagicMock()
    model.infill_generator_type_changed.connect(signal_spy)
    model.project_modified_changed.connect(modified_spy)

    model.set_infill_generator_type("random")

    assert model.infill_generator_type == "random"
    signal_spy.assert_called_once_with("random")
    modified_spy.assert_called_once_with(True)
    assert model.project_modified is True


def test_set_infill_generator_parameters_emits_signal(model: RailingProjectModel) -> None:
    """Test that setting infill generator parameters emits signal and marks modified."""
    signal_spy = MagicMock()
    modified_spy = MagicMock()
    model.infill_generator_parameters_changed.connect(signal_spy)
    model.project_modified_changed.connect(modified_spy)

    params = MockInfillGeneratorParameters(value=30.0)
    model.set_infill_generator_parameters(params)

    assert model.infill_generator_parameters == params
    signal_spy.assert_called_once_with(params)
    modified_spy.assert_called_once_with(True)
    assert model.project_modified is True


def test_set_railing_infill_emits_signal(
    model: RailingProjectModel, sample_infill: RailingInfill
) -> None:
    """Test that setting infill emits signal and marks modified."""
    signal_spy = MagicMock()
    modified_spy = MagicMock()
    model.railing_infill_updated.connect(signal_spy)
    model.project_modified_changed.connect(modified_spy)

    model.set_railing_infill(sample_infill)

    assert model.railing_infill == sample_infill
    signal_spy.assert_called_once_with(sample_infill)
    modified_spy.assert_called_once_with(True)
    assert model.project_modified is True


def test_set_project_file_path_emits_signal(model: RailingProjectModel) -> None:
    """Test that setting file path emits signal."""
    signal_spy = MagicMock()
    model.project_file_path_changed.connect(signal_spy)

    file_path = Path("/tmp/test.rig.zip")
    model.set_project_file_path(file_path)

    assert model.project_file_path == file_path
    signal_spy.assert_called_once_with(file_path)


def test_mark_project_saved_clears_modified_flag(model: RailingProjectModel) -> None:
    """Test that marking project as saved clears modified flag."""
    # First mark as modified
    model.set_railing_shape_type("staircase")
    assert model.project_modified is True

    # Now mark as saved
    signal_spy = MagicMock()
    model.project_modified_changed.connect(signal_spy)

    model.mark_project_saved()

    assert model.project_modified is False
    signal_spy.assert_called_once_with(False)


def test_set_rod_annotation_visible_emits_signal(model: RailingProjectModel) -> None:
    """Test that setting enumeration visibility emits signal."""
    signal_spy = MagicMock()
    model.rod_annotation_visibility_changed.connect(signal_spy)

    model.set_rod_annotation_visible(True)

    assert model.rod_annotation_visible is True
    signal_spy.assert_called_once_with(True)


def test_reset_to_defaults_clears_all_state(
    model: RailingProjectModel, sample_frame: RailingFrame, sample_infill: RailingInfill
) -> None:
    """Test that reset_to_defaults clears all state and emits all signals."""
    # Set up some state
    model.set_railing_shape_type("staircase")
    model.set_railing_shape_parameters(MockShapeParameters(value=15.0))
    model.set_railing_frame(sample_frame)
    model.set_infill_generator_type("random")
    model.set_infill_generator_parameters(MockInfillGeneratorParameters(value=25.0))
    model.set_railing_infill(sample_infill)
    model.set_project_file_path(Path("/tmp/test.rig.zip"))
    model.set_rod_annotation_visible(True)

    # Connect signal spies
    shape_type_spy = MagicMock()
    shape_params_spy = MagicMock()
    frame_spy = MagicMock()
    gen_type_spy = MagicMock()
    gen_params_spy = MagicMock()
    infill_spy = MagicMock()
    file_path_spy = MagicMock()
    modified_spy = MagicMock()
    enum_spy = MagicMock()

    model.railing_shape_type_changed.connect(shape_type_spy)
    model.railing_shape_parameters_changed.connect(shape_params_spy)
    model.railing_frame_updated.connect(frame_spy)
    model.infill_generator_type_changed.connect(gen_type_spy)
    model.infill_generator_parameters_changed.connect(gen_params_spy)
    model.railing_infill_updated.connect(infill_spy)
    model.project_file_path_changed.connect(file_path_spy)
    model.project_modified_changed.connect(modified_spy)
    model.rod_annotation_visibility_changed.connect(enum_spy)

    # Reset to defaults
    model.reset_to_defaults()

    # Verify all state is cleared
    assert model.railing_shape_type is None
    assert model.railing_shape_parameters is None
    assert model.railing_frame is None
    assert model.infill_generator_type is None
    assert model.infill_generator_parameters is None
    assert model.railing_infill is None
    assert model.project_file_path is None
    assert model.project_modified is False
    assert model.rod_annotation_visible is False

    # Verify all signals were emitted
    shape_type_spy.assert_called_once_with("")
    shape_params_spy.assert_called_once_with(None)
    frame_spy.assert_called_once_with(None)
    gen_type_spy.assert_called_once_with("")
    gen_params_spy.assert_called_once_with(None)
    infill_spy.assert_called_once_with(None)
    file_path_spy.assert_called_once_with(None)
    modified_spy.assert_called_once_with(False)
    enum_spy.assert_called_once_with(False)


def test_has_railing_frame(model: RailingProjectModel, sample_frame: RailingFrame) -> None:
    """Test has_railing_frame utility method."""
    assert model.has_railing_frame() is False

    model.set_railing_frame(sample_frame)
    assert model.has_railing_frame() is True

    model.set_railing_frame(None)
    assert model.has_railing_frame() is False


def test_has_railing_infill(model: RailingProjectModel, sample_infill: RailingInfill) -> None:
    """Test has_railing_infill utility method."""
    assert model.has_railing_infill() is False

    model.set_railing_infill(sample_infill)
    assert model.has_railing_infill() is True

    model.set_railing_infill(None)
    assert model.has_railing_infill() is False


def test_modified_flag_not_set_multiple_times(model: RailingProjectModel) -> None:
    """Test that modified flag is only set once and signal emitted once."""
    modified_spy = MagicMock()
    model.project_modified_changed.connect(modified_spy)

    # First modification should emit signal
    model.set_railing_shape_type("staircase")
    assert modified_spy.call_count == 1

    # Second modification should not emit signal again
    model.set_infill_generator_type("random")
    assert modified_spy.call_count == 1  # Still 1, not 2


def test_shape_type_change_only_emits_when_different(model: RailingProjectModel) -> None:
    """Test that shape type signal only emits when value actually changes."""
    signal_spy = MagicMock()
    model.railing_shape_type_changed.connect(signal_spy)

    # First set should emit
    model.set_railing_shape_type("staircase")
    assert signal_spy.call_count == 1

    # Setting same value should not emit
    model.set_railing_shape_type("staircase")
    assert signal_spy.call_count == 1  # Still 1, not 2

    # Setting different value should emit
    model.set_railing_shape_type("rectangular")
    assert signal_spy.call_count == 2
