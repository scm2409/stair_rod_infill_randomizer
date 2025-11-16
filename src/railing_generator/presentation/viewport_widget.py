"""Viewport widget for rendering railing frame and infill."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class ViewportWidget(QGraphicsView):
    """
    Vector-based viewport for rendering railing designs.

    Features:
    - Zoom with mouse wheel (centered on cursor)
    - Pan with mouse drag
    - Hardware-accelerated rendering
    """

    def __init__(self) -> None:
        """Initialize the viewport widget."""
        super().__init__()

        # Create scene
        scene = QGraphicsScene()
        self.setScene(scene)

        # Configure rendering
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # Enable drag mode for panning
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Zoom settings
        self._zoom_factor = 1.15
        self._min_zoom = 0.1
        self._max_zoom = 10.0
        self._current_zoom = 1.0

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle mouse wheel events for zooming.

        Args:
            event: Wheel event containing delta and position
        """
        # Get wheel delta
        delta = event.angleDelta().y()

        if delta > 0:
            # Zoom in
            zoom_factor = self._zoom_factor
        else:
            # Zoom out
            zoom_factor = 1.0 / self._zoom_factor

        # Calculate new zoom level
        new_zoom = self._current_zoom * zoom_factor

        # Clamp zoom level
        if new_zoom < self._min_zoom or new_zoom > self._max_zoom:
            return

        # Apply zoom
        self.scale(zoom_factor, zoom_factor)
        self._current_zoom = new_zoom

    def fit_in_view(self) -> None:
        """Fit all items in the viewport."""
        scene = self.scene()
        if scene is not None and scene.items():
            self.fitInView(scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            # Update current zoom based on transform
            self._current_zoom = self.transform().m11()

    def reset_zoom(self) -> None:
        """Reset zoom to 1:1 scale."""
        self.resetTransform()
        self._current_zoom = 1.0

    def clear_scene(self) -> None:
        """Clear all items from the scene."""
        scene = self.scene()
        if scene is not None:
            scene.clear()
