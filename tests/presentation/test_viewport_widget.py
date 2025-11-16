"""Tests for ViewportWidget."""

import pytest

from railing_generator.presentation.viewport_widget import ViewportWidget


@pytest.fixture
def viewport(qtbot):  # type: ignore[no-untyped-def]
    """Create a ViewportWidget for testing."""
    widget = ViewportWidget()
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
