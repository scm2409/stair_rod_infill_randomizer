"""DXF export functionality for railing designs."""

import logging
from pathlib import Path

from ezdxf.document import Drawing
from ezdxf.filemanagement import new as ezdxf_new
from ezdxf.layouts.layout import Modelspace
from ezdxf.sections.table import LayerTable

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod

logger = logging.getLogger(__name__)


class DxfExporter:
    """
    Exports railing designs to DXF format.

    Creates DXF files with separate layers for frame and infill elements.
    Frame rods are placed on the "FRAME" layer.
    Infill rods are placed on "INFILL_LAYER_N" layers where N is the layer number.
    """

    FRAME_LAYER_NAME = "FRAME"
    INFILL_LAYER_PREFIX = "INFILL_LAYER_"

    # DXF color codes (skip yellow=2 as it's hard to see)
    INFILL_LAYER_COLORS = [1, 3, 4, 5, 6]  # red, green, cyan, blue, magenta

    def __init__(self, frame: RailingFrame, infill: RailingInfill | None = None) -> None:
        """
        Initialize the DXF exporter.

        Args:
            frame: The railing frame to export
            infill: Optional railing infill to export

        Raises:
            ValueError: If frame is None or has no rods
        """
        if frame is None:
            raise ValueError("Cannot export DXF: frame is None")

        if not frame.rods:
            raise ValueError("Cannot export DXF: frame has no rods")

        self._frame = frame
        self._infill = infill

    def export(self, file_path: Path) -> None:
        """
        Export the railing design to a DXF file.

        Args:
            file_path: Path to save the DXF file

        Raises:
            IOError: If file cannot be written
        """
        logger.info(f"Exporting DXF to {file_path}")

        # Create new DXF document (R2010 format for wide compatibility)
        doc: Drawing = ezdxf_new("R2010")
        msp: Modelspace = doc.modelspace()

        self._add_frame_layer(doc.layers, msp)
        self._add_infill_layers(doc.layers, msp)

        # Save the DXF file
        doc.saveas(file_path)
        logger.info(f"DXF exported successfully to {file_path}")

    def _add_frame_layer(self, layers: LayerTable, msp: Modelspace) -> None:
        """
        Add frame rods to the FRAME layer.

        Args:
            layers: The layer table
            msp: The modelspace
        """
        # Create FRAME layer (color 7 = white/black)
        layers.add(self.FRAME_LAYER_NAME, color=7)

        # Add frame rods
        for rod in self._frame.rods:
            self._add_rod_to_modelspace(msp, rod, self.FRAME_LAYER_NAME)

        logger.debug(f"Added {len(self._frame.rods)} frame rods to FRAME layer")

    def _add_infill_layers(self, layers: LayerTable, msp: Modelspace) -> None:
        """
        Add infill rods to their respective layers.

        Args:
            layers: The layer table
            msp: The modelspace
        """
        if self._infill is None or not self._infill.rods:
            return

        # Collect unique layer numbers from infill rods
        layer_numbers = sorted(set(rod.layer for rod in self._infill.rods))

        # Create layers for each infill layer
        for i, layer_num in enumerate(layer_numbers):
            layer_name = f"{self.INFILL_LAYER_PREFIX}{layer_num}"
            color = self.INFILL_LAYER_COLORS[i % len(self.INFILL_LAYER_COLORS)]
            layers.add(layer_name, color=color)

        # Add infill rods to their respective layers
        for rod in self._infill.rods:
            layer_name = f"{self.INFILL_LAYER_PREFIX}{rod.layer}"
            self._add_rod_to_modelspace(msp, rod, layer_name)

        logger.debug(
            f"Added {len(self._infill.rods)} infill rods across {len(layer_numbers)} layers"
        )

    def _add_rod_to_modelspace(self, msp: Modelspace, rod: Rod, layer_name: str) -> None:
        """
        Add a rod as a LINE entity to the modelspace.

        Args:
            msp: The modelspace to add the line to
            rod: The rod to add
            layer_name: The DXF layer name to place the line on
        """
        # Get coordinates from rod geometry
        coords = list(rod.geometry.coords)
        start = coords[0]
        end = coords[-1]

        # Add LINE entity (coordinates are in cm)
        msp.add_line(
            start=(start[0], start[1]),
            end=(end[0], end[1]),
            dxfattribs={"layer": layer_name},
        )
