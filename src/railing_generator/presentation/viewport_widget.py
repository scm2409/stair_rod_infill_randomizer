"""Viewport widget for rendering railing frame and infill."""

import logging

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsScene, QGraphicsView

from railing_generator.application.railing_project_model import RailingProjectModel
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.railing_frame import RailingFrame

logger = logging.getLogger(__name__)


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
        self._anchor_points_group: QGraphicsItemGroup | None = None
        self._highlight_group: QGraphicsItemGroup | None = None

        # Store current frame and infill for highlighting
        self._current_frame: RailingFrame | None = None
        self._current_infill: RailingInfill | None = None

        # Connect to model signals for automatic updates
        self._connect_model_signals()

    def _connect_model_signals(self) -> None:
        """Connect to model signals for observing state changes."""
        # Connect to frame and infill updates
        self.project_model.railing_frame_updated.connect(self._on_railing_frame_updated)
        self.project_model.railing_infill_updated.connect(self._on_railing_infill_updated)

        # Connect to color mode changes
        self.project_model.infill_layers_colored_by_layer_changed.connect(
            self._on_color_mode_changed
        )

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

        # Store current frame for highlighting
        self._current_frame = railing_frame

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
        self._current_frame = None
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

        # Store current infill for highlighting
        self._current_infill = railing_infill

        # Remove existing infill group if present
        if self._railing_infill_group is not None:
            scene.removeItem(self._railing_infill_group)
            self._railing_infill_group = None

        # Remove existing anchor points group if present
        if self._anchor_points_group is not None:
            scene.removeItem(self._anchor_points_group)
            self._anchor_points_group = None

        # Create new infill group
        self._railing_infill_group = QGraphicsItemGroup()
        scene.addItem(self._railing_infill_group)

        # Get color mode from model
        colored_mode = self.project_model.infill_layers_colored_by_layer

        # Define colors for different layers (exclude yellow - reserved for highlighting)
        layer_colors_colored = [
            Qt.GlobalColor.red,  # Layer 1
            Qt.GlobalColor.green,  # Layer 2
            Qt.GlobalColor.magenta,  # Layer 3
            Qt.GlobalColor.cyan,  # Layer 4
            Qt.GlobalColor.blue,  # Layer 5
        ]

        # Monochrome mode: all layers use black
        layer_colors_monochrome = [Qt.GlobalColor.black]

        # Select color palette based on mode
        layer_colors = layer_colors_colored if colored_mode else layer_colors_monochrome

        # Render infill rods with layer-specific colors
        for rod in railing_infill.rods:
            # Get color for this layer
            if colored_mode:
                # Colored mode: use layer-specific color
                layer_index = rod.layer - 1  # Layer 1 -> index 0
                if 0 <= layer_index < len(layer_colors):
                    color = layer_colors[layer_index]
                else:
                    color = Qt.GlobalColor.red
            else:
                # Monochrome mode: all layers use black
                color = Qt.GlobalColor.black

            infill_pen = QPen(color, 1.5)

            coords = list(rod.geometry.coords)
            if len(coords) >= 2:
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                line = scene.addLine(x1, y1, x2, y2, infill_pen)
                self._railing_infill_group.addToGroup(line)

        # Render anchor points if available
        if railing_infill.anchor_points is not None:
            self._anchor_points_group = QGraphicsItemGroup()
            scene.addItem(self._anchor_points_group)

            for anchor in railing_infill.anchor_points:
                # Get color for this layer
                if colored_mode:
                    # Colored mode: use layer-specific color
                    if anchor.layer is not None:
                        layer_index = anchor.layer - 1
                        if 0 <= layer_index < len(layer_colors_colored):
                            color = layer_colors_colored[layer_index]
                        else:
                            color = Qt.GlobalColor.red
                    else:
                        color = Qt.GlobalColor.gray  # Unassigned anchors in gray
                else:
                    # Monochrome mode: all anchors use black
                    color = Qt.GlobalColor.black

                # Create small circle (1 pixel width pen, 2cm diameter)
                anchor_pen = QPen(color, 1)
                x, y = anchor.position
                circle = scene.addEllipse(x - 1, y - 1, 2, 2, anchor_pen)
                self._anchor_points_group.addToGroup(circle)

    def clear_railing_infill(self) -> None:
        """Remove the railing infill from the viewport."""
        self._current_infill = None
        scene = self.scene()
        if scene is not None:
            if self._railing_infill_group is not None:
                scene.removeItem(self._railing_infill_group)
                self._railing_infill_group = None
            if self._anchor_points_group is not None:
                scene.removeItem(self._anchor_points_group)
                self._anchor_points_group = None

    def highlight_frame_rod(self, rod_index: int) -> None:
        """
        Highlight a specific frame rod.

        Args:
            rod_index: 0-based index of the rod to highlight
        """
        if (
            self._current_frame is None
            or rod_index < 0
            or rod_index >= len(self._current_frame.rods)
        ):
            return

        scene = self.scene()
        if scene is None:
            return

        # Clear existing highlight
        self.clear_highlight()

        # Create highlight group
        self._highlight_group = QGraphicsItemGroup()
        scene.addItem(self._highlight_group)

        # Highlight pen (thick yellow line)
        highlight_pen = QPen(Qt.GlobalColor.yellow, 4)

        # Get the rod to highlight
        rod = self._current_frame.rods[rod_index]
        coords = list(rod.geometry.coords)
        if len(coords) >= 2:
            x1, y1 = coords[0]
            x2, y2 = coords[1]
            line = scene.addLine(x1, y1, x2, y2, highlight_pen)
            self._highlight_group.addToGroup(line)

    def highlight_infill_rod(self, rod_index: int) -> None:
        """
        Highlight a specific infill rod.

        Args:
            rod_index: 0-based index of the rod to highlight
        """
        if (
            self._current_infill is None
            or rod_index < 0
            or rod_index >= len(self._current_infill.rods)
        ):
            return

        scene = self.scene()
        if scene is None:
            return

        # Clear existing highlight
        self.clear_highlight()

        # Create highlight group
        self._highlight_group = QGraphicsItemGroup()
        scene.addItem(self._highlight_group)

        # Highlight pen (thick yellow line)
        highlight_pen = QPen(Qt.GlobalColor.yellow, 4)

        # Get the rod to highlight
        rod = self._current_infill.rods[rod_index]
        coords = list(rod.geometry.coords)
        if len(coords) >= 2:
            x1, y1 = coords[0]
            x2, y2 = coords[1]
            line = scene.addLine(x1, y1, x2, y2, highlight_pen)
            self._highlight_group.addToGroup(line)

    def clear_highlight(self) -> None:
        """Clear any rod highlighting."""
        scene = self.scene()
        if scene is not None and self._highlight_group is not None:
            scene.removeItem(self._highlight_group)
            self._highlight_group = None

    def _on_color_mode_changed(self, colored: bool) -> None:
        """
        Handle color mode changes from the model.

        Re-renders the current infill with the new color scheme.

        Args:
            colored: True for colored mode, False for monochrome mode
        """
        # Re-render current infill if it exists
        if self._current_infill is not None:
            self.set_railing_infill(self._current_infill)

    def capture_as_png(self, width: int = 1920, height: int = 1080) -> bytes:
        """
        Capture the current viewport content as PNG image data.

        The image is rendered with the viewport zoomed to show the entire design.

        Args:
            width: Width of the output image in pixels (default: 1920)
            height: Height of the output image in pixels (default: 1080)

        Returns:
            PNG image data as bytes
        """
        logger.debug(f"capture_as_png called with width={width}, height={height}")

        try:
            scene = self.scene()
            if scene is None:
                logger.debug("No scene, creating empty white image")
                # Return empty PNG if no scene
                image = QImage(width, height, QImage.Format.Format_ARGB32)
                image.fill(Qt.GlobalColor.white)
            else:
                # Get scene bounding rect
                scene_rect = scene.itemsBoundingRect()
                logger.debug(f"Scene bounding rect: {scene_rect}")

                # Add some padding
                padding = 20
                scene_rect.adjust(-padding, -padding, padding, padding)

                # Create image
                image = QImage(width, height, QImage.Format.Format_ARGB32)
                image.fill(Qt.GlobalColor.white)

                # Create painter and render scene
                painter = QPainter(image)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                # Flip Y-axis for rendering (scene uses mathematical convention)
                painter.scale(1, -1)
                painter.translate(0, -height)

                # Render scene to image, fitting the scene rect to the image
                scene.render(painter, target=image.rect(), source=scene_rect)
                painter.end()

            # Convert to PNG bytes using QByteArray
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            # PySide6 6.10.0: runtime accepts str "PNG" despite stubs saying bytes
            success = image.save(buffer, "PNG")  # type: ignore[call-overload]
            buffer.close()
            if not success:
                logger.error("Failed to save image to buffer as PNG")
                raise RuntimeError("Failed to encode image as PNG")

            png_data = bytes(byte_array.data())
            logger.debug(f"PNG capture successful, size: {len(png_data)} bytes")
            return png_data
        except Exception as e:
            logger.exception(f"Error in capture_as_png: {e}")
            raise
