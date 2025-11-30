"""Tests for ApplicationController save/load functionality."""

import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from shapely.geometry import LineString

from railing_generator.application.application_controller import ApplicationController
from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.application.persistable_project_state import (
    PersistedFrame,
    PersistedInfill,
    PersistableProjectState,
    UIState,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod
from railing_generator.domain.shapes.rectangular_railing_shape import (
    RectangularRailingShapeParameters,
)
from railing_generator.domain.shapes.staircase_railing_shape import (
    StaircaseRailingShapeParameters,
)
from railing_generator.domain.infill_generators.random_generator_parameters import (
    RandomGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator_v2_parameters import (
    RandomGeneratorParametersV2,
)

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


class TestApplicationControllerPersistence:
    """Test suite for ApplicationController save/load functionality."""

    @pytest.fixture
    def project_model(self, qtbot: "QtBot") -> RailingProjectModel:
        """Create a RailingProjectModel for testing."""
        return RailingProjectModel()

    @pytest.fixture
    def controller(self, project_model: RailingProjectModel) -> ApplicationController:
        """Create an ApplicationController for testing."""
        return ApplicationController(project_model)

    @pytest.fixture
    def staircase_params(self) -> StaircaseRailingShapeParameters:
        """Create staircase shape parameters for testing."""
        return StaircaseRailingShapeParameters(
            post_length_cm=150.0,
            stair_width_cm=280.0,
            stair_height_cm=280.0,
            num_steps=10,
            frame_weight_per_meter_kg_m=0.5,
        )

    @pytest.fixture
    def rectangular_params(self) -> RectangularRailingShapeParameters:
        """Create rectangular shape parameters for testing."""
        return RectangularRailingShapeParameters(
            width_cm=200.0,
            height_cm=100.0,
            frame_weight_per_meter_kg_m=0.5,
        )

    @pytest.fixture
    def sample_infill(self) -> RailingInfill:
        """Create a sample infill for testing."""
        rods = [
            Rod(
                geometry=LineString([(10, 0), (10, 100)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.3,
                layer=1,
            ),
            Rod(
                geometry=LineString([(50, 0), (50, 100)]),
                start_cut_angle_deg=5.0,
                end_cut_angle_deg=-5.0,
                weight_kg_m=0.3,
                layer=2,
            ),
        ]
        return RailingInfill(
            rods=rods,
            fitness_score=0.85,
            iteration_count=100,
            duration_sec=5.5,
            is_complete=True,
        )


class TestBuildProjectState(TestApplicationControllerPersistence):
    """Tests for _build_project_state method."""

    def test_build_empty_project(
        self, controller: ApplicationController, project_model: RailingProjectModel
    ) -> None:
        """Test building state from empty project."""
        state = controller._build_project_state()

        assert state.shape_type is None
        assert state.shape_parameters is None
        assert state.frame is None
        assert state.infill is None
        assert state.ui_state.rod_annotation_visible is False
        assert state.ui_state.infill_layers_colored_by_layer is True

    def test_build_with_shape_only(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
    ) -> None:
        """Test building state with shape but no infill."""
        controller.update_railing_shape("staircase", staircase_params)

        state = controller._build_project_state()

        assert state.shape_type == "staircase"
        assert state.shape_parameters is not None
        assert isinstance(state.shape_parameters, StaircaseRailingShapeParameters)
        assert state.shape_parameters.post_length_cm == 150.0
        assert state.frame is not None
        assert len(state.frame.rods) > 0
        assert state.infill is None

    def test_build_with_infill(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        sample_infill: RailingInfill,
    ) -> None:
        """Test building state with shape and infill."""
        controller.update_railing_shape("staircase", staircase_params)
        project_model._railing_infill = sample_infill

        state = controller._build_project_state()

        assert state.infill is not None
        assert state.infill.fitness_score == 0.85
        assert state.infill.iteration_count == 100
        assert len(state.infill.rods) == 2

    def test_build_ui_state(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
    ) -> None:
        """Test that UI state is built correctly."""
        controller.update_railing_shape("staircase", staircase_params)
        project_model.set_rod_annotation_visible(True)
        project_model.set_infill_layers_colored_by_layer(False)

        state = controller._build_project_state()

        assert state.ui_state.rod_annotation_visible is True
        assert state.ui_state.infill_layers_colored_by_layer is False


class TestApplyProjectState(TestApplicationControllerPersistence):
    """Tests for _apply_project_state method."""

    def test_apply_staircase_shape(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
    ) -> None:
        """Test applying staircase shape state."""
        frame_rod = Rod(
            geometry=LineString([(0, 0), (0, 150)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=0,
        )
        state = PersistableProjectState(
            shape_type="staircase",
            shape_parameters=StaircaseRailingShapeParameters(
                post_length_cm=150.0,
                stair_width_cm=280.0,
                stair_height_cm=280.0,
                num_steps=10,
                frame_weight_per_meter_kg_m=0.5,
            ),
            frame=PersistedFrame(rods=[frame_rod]),
        )

        controller._apply_project_state(state)

        assert project_model.railing_shape_type == "staircase"
        assert project_model.railing_shape_parameters is not None
        assert project_model.railing_shape_parameters.post_length_cm == 150.0
        assert project_model.railing_frame is not None

    def test_apply_rectangular_shape(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
    ) -> None:
        """Test applying rectangular shape state."""
        state = PersistableProjectState(
            shape_type="rectangular",
            shape_parameters=RectangularRailingShapeParameters(
                width_cm=200.0,
                height_cm=100.0,
                frame_weight_per_meter_kg_m=0.5,
            ),
        )

        controller._apply_project_state(state)

        assert project_model.railing_shape_type == "rectangular"
        assert project_model.railing_shape_parameters is not None
        assert project_model.railing_shape_parameters.width_cm == 200.0

    def test_apply_with_infill(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
    ) -> None:
        """Test applying state with infill."""
        infill_rod = Rod(
            geometry=LineString([(50, 0), (50, 100)]),
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
            layer=1,
        )
        state = PersistableProjectState(
            infill=PersistedInfill(
                rods=[infill_rod],
                fitness_score=0.9,
                iteration_count=50,
                duration_sec=2.5,
                is_complete=True,
            ),
        )

        controller._apply_project_state(state)

        assert project_model.railing_infill is not None
        assert len(project_model.railing_infill.rods) == 1
        assert project_model.railing_infill.fitness_score == 0.9

    def test_apply_ui_state(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
    ) -> None:
        """Test applying UI state."""
        state = PersistableProjectState(
            ui_state=UIState(
                rod_annotation_visible=True,
                infill_layers_colored_by_layer=False,
            ),
        )

        controller._apply_project_state(state)

        assert project_model.rod_annotation_visible is True
        assert project_model.infill_layers_colored_by_layer is False


class TestSaveProject(TestApplicationControllerPersistence):
    """Tests for save_project method."""

    def test_save_project_creates_zip(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test that save_project creates a valid ZIP archive."""
        controller.update_railing_shape("staircase", staircase_params)
        file_path = tmp_path / "test_project.rig.zip"

        controller.save_project(file_path)

        assert file_path.exists()
        with zipfile.ZipFile(file_path, "r") as zf:
            assert "project.json" in zf.namelist()

    def test_save_project_includes_png(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test that save_project includes PNG when provided."""
        controller.update_railing_shape("staircase", staircase_params)
        file_path = tmp_path / "test_project.rig.zip"
        png_data = b"\x89PNG\r\n\x1a\n"

        controller.save_project(file_path, png_data=png_data)

        with zipfile.ZipFile(file_path, "r") as zf:
            assert "preview.png" in zf.namelist()
            assert zf.read("preview.png") == png_data

    def test_save_project_includes_bom_csv(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test that save_project includes BOM CSV files."""
        controller.update_railing_shape("staircase", staircase_params)
        file_path = tmp_path / "test_project.rig.zip"

        controller.save_project(file_path)

        with zipfile.ZipFile(file_path, "r") as zf:
            assert "frame_bom.csv" in zf.namelist()
            csv_content = zf.read("frame_bom.csv").decode("utf-8")
            assert "id,length_cm,start_cut_angle_deg,end_cut_angle_deg,weight_kg" in csv_content

    def test_save_project_updates_model_state(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test that save_project updates model state correctly."""
        controller.update_railing_shape("staircase", staircase_params)
        file_path = tmp_path / "test_project.rig.zip"
        assert project_model.project_modified is True

        controller.save_project(file_path)

        assert project_model.project_file_path == file_path
        assert project_model.project_modified is False

    def test_save_project_without_frame_raises_error(
        self,
        controller: ApplicationController,
        tmp_path: Path,
    ) -> None:
        """Test that save_project raises error when no frame exists."""
        file_path = tmp_path / "test_project.rig.zip"

        with pytest.raises(ValueError, match="no railing frame exists"):
            controller.save_project(file_path)


class TestLoadProject(TestApplicationControllerPersistence):
    """Tests for load_project method."""

    def test_load_project_restores_state(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test that load_project restores saved state."""
        controller.update_railing_shape("staircase", staircase_params)
        file_path = tmp_path / "test_project.rig.zip"
        controller.save_project(file_path)

        controller.create_new_project()
        assert project_model.railing_shape_type is None

        controller.load_project(file_path)

        assert project_model.railing_shape_type == "staircase"
        assert project_model.railing_shape_parameters is not None
        assert project_model.railing_frame is not None
        assert project_model.project_file_path == file_path
        assert project_model.project_modified is False

    def test_load_project_file_not_found(
        self,
        controller: ApplicationController,
        tmp_path: Path,
    ) -> None:
        """Test that load_project raises error for missing file."""
        file_path = tmp_path / "nonexistent.rig.zip"

        with pytest.raises(FileNotFoundError):
            controller.load_project(file_path)

    def test_load_project_invalid_archive(
        self,
        controller: ApplicationController,
        tmp_path: Path,
    ) -> None:
        """Test that load_project raises error for invalid archive."""
        file_path = tmp_path / "invalid.rig.zip"
        with zipfile.ZipFile(file_path, "w") as zf:
            zf.writestr("dummy.txt", "dummy content")

        with pytest.raises(ValueError, match="missing project.json"):
            controller.load_project(file_path)


class TestRoundTrip(TestApplicationControllerPersistence):
    """Tests for save/load round-trip consistency."""

    def test_round_trip_staircase_shape(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test round-trip save/load preserves staircase shape data."""
        controller.update_railing_shape("staircase", staircase_params)
        original_rod_count = (
            project_model.railing_frame.rod_count if project_model.railing_frame else 0
        )
        file_path = tmp_path / "test_project.rig.zip"

        controller.save_project(file_path)
        controller.create_new_project()
        controller.load_project(file_path)

        assert project_model.railing_shape_type == "staircase"
        params = project_model.railing_shape_parameters
        assert isinstance(params, StaircaseRailingShapeParameters)
        assert params.post_length_cm == staircase_params.post_length_cm
        assert project_model.railing_frame is not None
        assert project_model.railing_frame.rod_count == original_rod_count

    def test_round_trip_rectangular_shape(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        rectangular_params: RectangularRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test round-trip save/load preserves rectangular shape data."""
        controller.update_railing_shape("rectangular", rectangular_params)
        file_path = tmp_path / "test_project.rig.zip"

        controller.save_project(file_path)
        controller.create_new_project()
        controller.load_project(file_path)

        assert project_model.railing_shape_type == "rectangular"
        params = project_model.railing_shape_parameters
        assert isinstance(params, RectangularRailingShapeParameters)
        assert params.width_cm == rectangular_params.width_cm

    def test_round_trip_with_infill(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        sample_infill: RailingInfill,
        tmp_path: Path,
    ) -> None:
        """Test round-trip save/load preserves infill data."""
        controller.update_railing_shape("staircase", staircase_params)
        project_model._railing_infill = sample_infill
        file_path = tmp_path / "test_project.rig.zip"

        controller.save_project(file_path)
        controller.create_new_project()
        controller.load_project(file_path)

        assert project_model.railing_infill is not None
        assert project_model.railing_infill.rod_count == sample_infill.rod_count
        assert project_model.railing_infill.fitness_score == sample_infill.fitness_score

    def test_round_trip_ui_state(
        self,
        qtbot: "QtBot",
        controller: ApplicationController,
        project_model: RailingProjectModel,
        staircase_params: StaircaseRailingShapeParameters,
        tmp_path: Path,
    ) -> None:
        """Test round-trip save/load preserves UI state."""
        controller.update_railing_shape("staircase", staircase_params)
        project_model.set_rod_annotation_visible(True)
        project_model.set_infill_layers_colored_by_layer(False)
        file_path = tmp_path / "test_project.rig.zip"

        controller.save_project(file_path)
        controller.create_new_project()
        controller.load_project(file_path)

        assert project_model.rod_annotation_visible is True
        assert project_model.infill_layers_colored_by_layer is False
