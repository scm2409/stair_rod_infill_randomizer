"""Viewport widget for rendering railing frame and infill."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsScene, QGraphicsView

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.railing_frame import RailingFrame


class ViewportWidget(QGraphicsView):
    """
    Vector-based viewport for rendering railing designs.

    Features:
    - Zoom with mouse wheel (centered on cursor)
    - Pan with mouse drag
    - Hardware-accelerated rendering
    - Observes RailingProjectModel for automatic updates
    """

    def __init__(self, project_model: RailingProjectModel) -> None:
        """
        Initialize the viewport widget.

        Args:
            project_model: The central state model to observe
        """
        super().__init__()

        # Store reference to model
        self.project_model = project_model

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

        # Flip Y-axis to match mathematical convention (Y increases upward)
        # Qt's default has Y increasing downward
        self.scale(1, -1)

        # Zoom settings
        self._zoom_factor = 1.15
        self._min_zoom = 0.1
        self._max_zoom = 10.0
        self._current_zoom = 1.0

        # Graphics item groups for different elements (allows selective update/remove)
        self._railing_frame_group: QGraphicsItemGroup | None = None
        self._railing_infill_group: QGraphicsItemGroup | None = None

        # Connect to model signals for automatic updates
        self._connect_model_signals()

    def _connect_model_signals(self) -> None:
        """Connect to model signals for observing state changes."""
        # Connect to frame and infill updates
        self.project_model.railing_frame_updated.connect(self._on_railing_frame_updated)
        self.project_model.railing_infill_updated.connect(self._on_railing_infill_updated)

    def _on_railing_frame_updated(self, frame: RailingFrame | None) -> None:
        """
        Handle railing frame updates from the model.

        Args:
            frame: The new railing frame, or None to clear
        """
        if frame is None:
            self.clear_railing_frame()
        else:
            self.set_railing_frame(frame)

    def _on_railing_infill_updated(self, infill: RailingInfill | None) -> None:
        """
        Handle railing infill updates from the model.

        Args:
            infill: The new railing infill, or None to clear
        """
        if infill is None:
            self.clear_railing_infill()
        else:
            self.set_railing_infill(infill)

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

    def set_railing_frame(self, railing_frame: RailingFrame) -> None:
        """
        Set the railing frame to display (replaces existing frame).

        Args:
            railing_frame: Immutable RailingFrame containing frame rods and boundary
        """
        scene = self.scene()
        if scene is None:
            return

        # Remove existing frame group if present
        if self._railing_frame_group is not None:
            scene.removeItem(self._railing_frame_group)
            self._railing_frame_group = None

        # Create new frame group
        self._railing_frame_group = QGraphicsItemGroup()
        scene.addItem(self._railing_frame_group)

        # Frame pen (blue, 2px width)
        frame_pen = QPen(Qt.GlobalColor.blue, 2)

        # Render frame rods
        for rod in railing_frame.rods:
            coords = list(rod.geometry.coords)
            if len(coords) >= 2:
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                line = scene.addLine(x1, y1, x2, y2, frame_pen)
                self._railing_frame_group.addToGroup(line)

    def clear_railing_frame(self) -> None:
        """Remove the railing frame from the viewport."""
        scene = self.scene()
        if scene is not None and self._railing_frame_group is not None:
            scene.removeItem(self._railing_frame_group)
            self._railing_frame_group = None

    def set_railing_infill(self, railing_infill: RailingInfill) -> None:
        """
        Set the railing infill to display (replaces existing infill).

        Args:
            railing_infill: Immutable RailingInfill containing infill rods
        """
        scene = self.scene()
        if scene is None:
            return

        # Remove existing infill group if present
        if self._railing_infill_group is not None:
            scene.removeItem(self._railing_infill_group)
            self._railing_infill_group = None

        # Create new infill group
        self._railing_infill_group = QGraphicsItemGroup()
        scene.addItem(self._railing_infill_group)

        # Define colors for different layers
        layer_colors = [
            Qt.GlobalColor.red,  # Layer 1
            Qt.GlobalColor.green,  # Layer 2
            Qt.GlobalColor.magenta,  # Layer 3
            Qt.GlobalColor.cyan,  # Layer 4
            Qt.GlobalColor.yellow,  # Layer 5
        ]

        # Render infill rods with layer-specific colors
        for rod in railing_infill.rods:
            # Get color for this layer (default to red if layer exceeds color list)
            layer_index = rod.layer - 1  # Layer 1 -> index 0
            if 0 <= layer_index < len(layer_colors):
                color = layer_colors[layer_index]
            else:
                color = Qt.GlobalColor.red

            infill_pen = QPen(color, 1.5)

            coords = list(rod.geometry.coords)
            if len(coords) >= 2:
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                line = scene.addLine(x1, y1, x2, y2, infill_pen)
                self._railing_infill_group.addToGroup(line)

    def clear_railing_infill(self) -> None:
        """Remove the railing infill from the viewport."""
        scene = self.scene()
        if scene is not None and self._railing_infill_group is not None:
            scene.removeItem(self._railing_infill_group)
            self._railing_infill_group = None
