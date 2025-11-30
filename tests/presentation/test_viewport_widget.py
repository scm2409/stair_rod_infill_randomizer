"""Tests for ViewportWidget."""

import pytest

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.presentation.viewport_widget import ViewportWidget


@pytest.fixture
def project_model() -> RailingProjectModel:
    """Create a RailingProjectModel for testing."""
    return RailingProjectModel()


@pytest.fixture
def viewport(qtbot, project_model: RailingProjectModel):  # type: ignore[no-untyped-def]
    """Create a ViewportWidget for testing."""
    widget = ViewportWidget(project_model)
    qtbot.addWidget(widget)
    return widget


class TestViewportCreation:
    """Test viewport widget creation and initialization."""

    def test_create_viewport(self, viewport: ViewportWidget) -> None:
        """Test that viewport is created successfully."""
        assert viewport is not None
        assert viewport.scene() is not None

    def test_viewport_has_scene(self, viewport: ViewportWidget) -> None:
        """Test that viewport has a graphics scene."""
        scene = viewport.scene()
        assert scene is not None

    def test_initial_zoom_level(self, viewport: ViewportWidget) -> None:
        """Test that initial zoom level is 1.0."""
        assert viewport._current_zoom == pytest.approx(1.0)


class TestViewportZoom:
    """Test viewport zoom functionality."""

    def test_reset_zoom(self, viewport: ViewportWidget) -> None:
        """Test resetting zoom to 1:1 scale."""
        # Zoom in first
        viewport.scale(2.0, 2.0)
        viewport._current_zoom = 2.0

        # Reset zoom
        viewport.reset_zoom()

        assert viewport._current_zoom == pytest.approx(1.0)
        assert viewport.transform().m11() == pytest.approx(1.0)

    def test_zoom_limits(self, viewport: ViewportWidget) -> None:
        """Test that zoom is clamped to min/max limits."""
        assert viewport._min_zoom == pytest.approx(0.1)
        assert viewport._max_zoom == pytest.approx(10.0)


class TestViewportScene:
    """Test viewport scene management."""

    def test_clear_scene(self, viewport: ViewportWidget) -> None:
        """Test clearing all items from the scene."""
        scene = viewport.scene()
        assert scene is not None

        # Add some items
        scene.addEllipse(0, 0, 10, 10)
        scene.addEllipse(20, 20, 10, 10)

        assert len(scene.items()) == 2

        # Clear scene
        viewport.clear_scene()

        assert len(scene.items()) == 0

    def test_fit_in_view_with_items(self, viewport: ViewportWidget) -> None:
        """Test fitting items in view."""
        scene = viewport.scene()
        assert scene is not None

        # Add an item
        scene.addEllipse(0, 0, 100, 100)

        # Fit in view
        viewport.fit_in_view()

        # Zoom should be updated
        assert viewport._current_zoom > 0

    def test_fit_in_view_empty_scene(self, viewport: ViewportWidget) -> None:
        """Test fitting empty scene doesn't crash."""
        viewport.clear_scene()
        viewport.fit_in_view()  # Should not crash

        # Zoom should remain at default
        assert viewport._current_zoom == pytest.approx(1.0)


class TestViewportColorMode:
    """Test viewport color mode functionality."""

    def test_colored_mode_uses_distinct_colors(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that colored mode renders each layer in a distinct color."""
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString

        # Create infill with multiple layers
        rods = [
            Rod(
                geometry=LineString([(0, 0), (100, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            ),
            Rod(
                geometry=LineString([(0, 10), (100, 10)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=2,
            ),
            Rod(
                geometry=LineString([(0, 20), (100, 20)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=3,
            ),
        ]
        infill = RailingInfill(
            rods=rods,
            fitness_score=0.8,
            iteration_count=100,
            duration_sec=5.0,
            anchor_points=[],
            is_complete=True,
        )

        # Ensure colored mode is active
        project_model.set_infill_layers_colored_by_layer(True)

        # Set infill
        viewport.set_railing_infill(infill)

        # Verify infill group exists
        assert viewport._railing_infill_group is not None

        # Get all line items
        scene = viewport.scene()
        assert scene is not None
        lines = [item for item in scene.items() if hasattr(item, "pen")]

        # Should have 3 lines (one per rod)
        assert len(lines) == 3

        # Collect colors
        colors = [line.pen().color().name() for line in lines]

        # All colors should be different (distinct colors for each layer)
        assert len(set(colors)) == 3

        # None should be yellow (reserved for highlighting)
        from PySide6.QtCore import Qt

        yellow_name = Qt.GlobalColor.yellow
        assert yellow_name not in [line.pen().color() for line in lines]

    def test_monochrome_mode_uses_single_color(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that monochrome mode renders all layers in black."""
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString
        from PySide6.QtCore import Qt

        # Create infill with multiple layers
        rods = [
            Rod(
                geometry=LineString([(0, 0), (100, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            ),
            Rod(
                geometry=LineString([(0, 10), (100, 10)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=2,
            ),
            Rod(
                geometry=LineString([(0, 20), (100, 20)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=3,
            ),
        ]
        infill = RailingInfill(
            rods=rods,
            fitness_score=0.8,
            iteration_count=100,
            duration_sec=5.0,
            anchor_points=[],
            is_complete=True,
        )

        # Set monochrome mode
        project_model.set_infill_layers_colored_by_layer(False)

        # Set infill
        viewport.set_railing_infill(infill)

        # Verify infill group exists
        assert viewport._railing_infill_group is not None

        # Get all line items
        scene = viewport.scene()
        assert scene is not None
        lines = [item for item in scene.items() if hasattr(item, "pen")]

        # Should have 3 lines (one per rod)
        assert len(lines) == 3

        # All lines should be black
        black_color = Qt.GlobalColor.black
        for line in lines:
            assert line.pen().color() == black_color

    def test_viewport_updates_on_color_mode_change(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that viewport re-renders infill when color mode changes."""
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString
        from PySide6.QtCore import Qt

        # Create infill with multiple layers
        rods = [
            Rod(
                geometry=LineString([(0, 0), (100, 0)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=1,
            ),
            Rod(
                geometry=LineString([(0, 10), (100, 10)]),
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=2,
            ),
        ]
        infill = RailingInfill(
            rods=rods,
            fitness_score=0.8,
            iteration_count=100,
            duration_sec=5.0,
            anchor_points=[],
            is_complete=True,
        )

        # Start in colored mode
        project_model.set_infill_layers_colored_by_layer(True)
        viewport.set_railing_infill(infill)

        # Get initial colors
        scene = viewport.scene()
        assert scene is not None
        lines = [item for item in scene.items() if hasattr(item, "pen")]
        initial_colors = [line.pen().color().name() for line in lines]

        # Colors should be different (colored mode)
        assert len(set(initial_colors)) == 2

        # Switch to monochrome mode
        project_model.set_infill_layers_colored_by_layer(False)

        # Get new colors
        lines = [item for item in scene.items() if hasattr(item, "pen")]
        new_colors = [line.pen().color() for line in lines]

        # All colors should now be black
        black_color = Qt.GlobalColor.black
        for color in new_colors:
            assert color == black_color

        # Switch back to colored mode
        project_model.set_infill_layers_colored_by_layer(True)

        # Get colors again
        lines = [item for item in scene.items() if hasattr(item, "pen")]
        final_colors = [line.pen().color().name() for line in lines]

        # Colors should be different again (colored mode)
        assert len(set(final_colors)) == 2

    def test_color_mode_change_without_infill(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that color mode change without infill doesn't crash."""
        # No infill set
        assert viewport._current_infill is None

        # Change color mode should not crash
        project_model.set_infill_layers_colored_by_layer(False)
        project_model.set_infill_layers_colored_by_layer(True)

        # Still no infill
        assert viewport._current_infill is None
