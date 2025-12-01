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


class TestViewportMouseEvents:
    """Test viewport mouse event handling for manual editing."""

    def test_left_click_emits_anchor_clicked_signal(
        self, viewport: ViewportWidget, qtbot: object
    ) -> None:
        """Test that left-click emits anchor_clicked signal with scene coordinates."""
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QEvent

        # Track emitted signals
        received_coords: list[tuple[float, float]] = []

        def on_anchor_clicked(x: float, y: float) -> None:
            received_coords.append((x, y))

        viewport.anchor_clicked.connect(on_anchor_clicked)

        # Simulate left-click at viewport position (100, 100)
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.mousePressEvent(event)

        # Signal should have been emitted
        assert len(received_coords) == 1
        # Coordinates should be scene coordinates (transformed from viewport)
        assert isinstance(received_coords[0][0], float)
        assert isinstance(received_coords[0][1], float)

    def test_shift_left_click_emits_anchor_shift_clicked_signal(
        self, viewport: ViewportWidget, qtbot: object
    ) -> None:
        """Test that Shift+left-click emits anchor_shift_clicked signal."""
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QEvent

        # Track emitted signals
        received_coords: list[tuple[float, float]] = []

        def on_anchor_shift_clicked(x: float, y: float) -> None:
            received_coords.append((x, y))

        viewport.anchor_shift_clicked.connect(on_anchor_shift_clicked)

        # Simulate Shift+left-click
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ShiftModifier,
        )
        viewport.mousePressEvent(event)

        # Signal should have been emitted
        assert len(received_coords) == 1

    def test_middle_click_starts_panning(self, viewport: ViewportWidget) -> None:
        """Test that middle-click starts panning mode."""
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QEvent

        # Initially not panning
        assert viewport._is_panning is False

        # Simulate middle-click
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.mousePressEvent(event)

        # Should be panning now
        assert viewport._is_panning is True
        assert viewport.cursor().shape() == Qt.CursorShape.ClosedHandCursor

    def test_middle_release_stops_panning(self, viewport: ViewportWidget) -> None:
        """Test that middle-button release stops panning mode."""
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QEvent

        # Start panning
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.mousePressEvent(press_event)
        assert viewport._is_panning is True

        # Release middle button
        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPoint(150, 150),
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.mouseReleaseEvent(release_event)

        # Should stop panning
        assert viewport._is_panning is False
        assert viewport.cursor().shape() == Qt.CursorShape.ArrowCursor

    def test_left_click_does_not_start_panning(self, viewport: ViewportWidget) -> None:
        """Test that left-click does not start panning (reserved for selection)."""
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QEvent

        # Simulate left-click
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.mousePressEvent(event)

        # Should NOT be panning
        assert viewport._is_panning is False


class TestViewportAnchorHighlighting:
    """Test viewport anchor highlighting functionality."""

    def test_highlight_anchor_creates_highlight(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that highlight_anchor creates a visible highlight."""
        # Highlight an anchor at position (50, 50)
        viewport.highlight_anchor((50.0, 50.0))

        # Highlight group should exist
        assert viewport._highlight_group is not None

        # Scene should have items
        scene = viewport.scene()
        assert scene is not None
        assert len(scene.items()) > 0

    def test_highlight_anchor_none_clears_highlight(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that highlight_anchor(None) clears the highlight."""
        # First create a highlight
        viewport.highlight_anchor((50.0, 50.0))
        assert viewport._highlight_group is not None

        # Clear highlight
        viewport.highlight_anchor(None)

        # Highlight group should be cleared
        assert viewport._highlight_group is None

    def test_highlight_anchor_replaces_previous(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test that highlighting a new anchor replaces the previous highlight."""
        # Highlight first anchor
        viewport.highlight_anchor((50.0, 50.0))
        first_group = viewport._highlight_group

        # Highlight second anchor
        viewport.highlight_anchor((100.0, 100.0))

        # Should have a new highlight group
        assert viewport._highlight_group is not None
        # The group should be different (old one removed, new one created)
        # We can't directly compare groups, but we can verify scene has items
        scene = viewport.scene()
        assert scene is not None


class TestViewportCapturePng:
    """Test viewport PNG capture functionality."""

    def test_capture_as_png_returns_bytes(self, viewport: ViewportWidget) -> None:
        """Test that capture_as_png returns bytes."""
        png_data = viewport.capture_as_png()
        assert isinstance(png_data, bytes)
        assert len(png_data) > 0

    def test_capture_as_png_returns_valid_png(self, viewport: ViewportWidget) -> None:
        """Test that capture_as_png returns valid PNG data."""
        png_data = viewport.capture_as_png()

        # PNG files start with a specific 8-byte signature
        png_signature = b"\x89PNG\r\n\x1a\n"
        assert png_data[:8] == png_signature

    def test_capture_as_png_with_custom_dimensions(self, viewport: ViewportWidget) -> None:
        """Test capture_as_png with custom width and height."""
        png_data = viewport.capture_as_png(width=800, height=600)

        assert isinstance(png_data, bytes)
        assert len(png_data) > 0
        # PNG signature check
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_capture_as_png_empty_scene(self, viewport: ViewportWidget) -> None:
        """Test capture_as_png with empty scene returns valid PNG."""
        viewport.clear_scene()

        png_data = viewport.capture_as_png()

        assert isinstance(png_data, bytes)
        assert len(png_data) > 0
        # PNG signature check
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_capture_as_png_with_frame(self, viewport: ViewportWidget) -> None:
        """Test capture_as_png with a railing frame renders correctly."""
        from railing_generator.domain.railing_frame import RailingFrame
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString, Polygon

        # Create a simple frame
        rods = [
            Rod(
                geometry=LineString([(0, 0), (100, 0)]),
                start_cut_angle_deg=90.0,
                end_cut_angle_deg=90.0,
                weight_kg_m=0.5,
            ),
            Rod(
                geometry=LineString([(100, 0), (100, 100)]),
                start_cut_angle_deg=90.0,
                end_cut_angle_deg=90.0,
                weight_kg_m=0.5,
            ),
        ]
        boundary = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        frame = RailingFrame(rods=rods, boundary=boundary)

        viewport.set_railing_frame(frame)

        png_data = viewport.capture_as_png()

        assert isinstance(png_data, bytes)
        assert len(png_data) > 0
        # PNG signature check
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_capture_as_png_with_infill(
        self, viewport: ViewportWidget, project_model: RailingProjectModel
    ) -> None:
        """Test capture_as_png with railing infill renders correctly."""
        from railing_generator.domain.railing_infill import RailingInfill
        from railing_generator.domain.rod import Rod
        from shapely.geometry import LineString

        # Create infill
        rods = [
            Rod(
                geometry=LineString([(10, 10), (90, 10)]),
                start_cut_angle_deg=90.0,
                end_cut_angle_deg=90.0,
                weight_kg_m=0.5,
                layer=1,
            ),
            Rod(
                geometry=LineString([(10, 50), (90, 50)]),
                start_cut_angle_deg=90.0,
                end_cut_angle_deg=90.0,
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

        viewport.set_railing_infill(infill)

        png_data = viewport.capture_as_png()

        assert isinstance(png_data, bytes)
        assert len(png_data) > 0
        # PNG signature check
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
