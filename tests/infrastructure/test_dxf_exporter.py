"""Tests for DXF export functionality."""

from pathlib import Path

import ezdxf
import pytest
from shapely.geometry import LineString

from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill
from railing_generator.domain.rod import Rod
from railing_generator.infrastructure.dxf_exporter import DxfExporter


def _create_rectangular_frame() -> RailingFrame:
    """Create a simple rectangular frame for testing."""
    # Create a 100x50 cm rectangular frame
    rods = [
        Rod(
            geometry=LineString([(0, 0), (100, 0)]),  # Bottom
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 0), (100, 50)]),  # Right
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(100, 50), (0, 50)]),  # Top
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
        Rod(
            geometry=LineString([(0, 50), (0, 0)]),  # Left
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.5,
            layer=0,
        ),
    ]
    return RailingFrame(rods=rods)


def _create_simple_infill() -> RailingInfill:
    """Create a simple infill with rods in two layers for testing."""
    rods = [
        # Layer 1 rods
        Rod(
            geometry=LineString([(25, 0), (25, 50)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.3,
            layer=1,
        ),
        Rod(
            geometry=LineString([(75, 0), (75, 50)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.3,
            layer=1,
        ),
        # Layer 2 rods
        Rod(
            geometry=LineString([(0, 25), (100, 25)]),
            start_cut_angle_deg=0,
            end_cut_angle_deg=0,
            weight_kg_m=0.3,
            layer=2,
        ),
    ]
    return RailingInfill(rods=rods)


class TestDxfExporter:
    """Tests for DxfExporter class."""

    def test_export_frame_only(self, tmp_path: Path) -> None:
        """Test exporting only frame geometry."""
        frame = _create_rectangular_frame()
        dxf_path = tmp_path / "test_frame.dxf"

        exporter = DxfExporter(frame)
        exporter.export(dxf_path)

        # Verify file was created
        assert dxf_path.exists()

        # Read and verify DXF content
        doc = ezdxf.readfile(str(dxf_path))
        msp = doc.modelspace()

        # Verify FRAME layer exists
        assert DxfExporter.FRAME_LAYER_NAME in doc.layers

        # Verify frame lines were added
        frame_lines = [e for e in msp if e.dxf.layer == DxfExporter.FRAME_LAYER_NAME]
        assert len(frame_lines) == 4  # 4 sides of rectangle

    def test_export_frame_and_infill(self, tmp_path: Path) -> None:
        """Test exporting both frame and infill geometry."""
        frame = _create_rectangular_frame()
        infill = _create_simple_infill()
        dxf_path = tmp_path / "test_full.dxf"

        exporter = DxfExporter(frame, infill)
        exporter.export(dxf_path)

        # Verify file was created
        assert dxf_path.exists()

        # Read and verify DXF content
        doc = ezdxf.readfile(str(dxf_path))
        msp = doc.modelspace()

        # Verify FRAME layer exists
        assert DxfExporter.FRAME_LAYER_NAME in doc.layers

        # Verify infill layers exist
        assert f"{DxfExporter.INFILL_LAYER_PREFIX}1" in doc.layers
        assert f"{DxfExporter.INFILL_LAYER_PREFIX}2" in doc.layers

        # Verify frame lines
        frame_lines = [e for e in msp if e.dxf.layer == DxfExporter.FRAME_LAYER_NAME]
        assert len(frame_lines) == 4

        # Verify infill lines by layer
        layer1_lines = [e for e in msp if e.dxf.layer == f"{DxfExporter.INFILL_LAYER_PREFIX}1"]
        assert len(layer1_lines) == 2  # 2 rods in layer 1

        layer2_lines = [e for e in msp if e.dxf.layer == f"{DxfExporter.INFILL_LAYER_PREFIX}2"]
        assert len(layer2_lines) == 1  # 1 rod in layer 2

    def test_export_coordinates_accuracy(self, tmp_path: Path) -> None:
        """Test that exported coordinates match original geometry."""
        frame = _create_rectangular_frame()
        dxf_path = tmp_path / "test_coords.dxf"

        exporter = DxfExporter(frame)
        exporter.export(dxf_path)

        # Read DXF and verify coordinates
        doc = ezdxf.readfile(str(dxf_path))
        msp = doc.modelspace()

        # Get all LINE entities
        lines = list(msp.query("LINE"))
        assert len(lines) == 4

        # Collect all start and end points
        points = set()
        for line in lines:
            start = (line.dxf.start.x, line.dxf.start.y)
            end = (line.dxf.end.x, line.dxf.end.y)
            points.add(start)
            points.add(end)

        # Verify corner points of 100x50 rectangle
        expected_corners = {(0, 0), (100, 0), (100, 50), (0, 50)}
        assert points == expected_corners

    def test_init_raises_on_none_frame(self) -> None:
        """Test that constructor raises ValueError when frame is None."""
        with pytest.raises(ValueError, match="frame is None"):
            DxfExporter(None)  # type: ignore[arg-type]

    def test_init_raises_on_empty_frame(self) -> None:
        """Test that constructor raises ValueError when frame has no rods."""
        with pytest.raises(ValueError, match="no rods"):
            # Create a mock frame-like object with empty rods
            class EmptyFrame:
                rods: list[Rod] = []

            DxfExporter(EmptyFrame())  # type: ignore[arg-type]

    def test_export_with_empty_infill(self, tmp_path: Path) -> None:
        """Test exporting frame with empty infill (no rods)."""
        frame = _create_rectangular_frame()
        empty_infill = RailingInfill(rods=[])
        dxf_path = tmp_path / "test_empty_infill.dxf"

        exporter = DxfExporter(frame, empty_infill)
        exporter.export(dxf_path)

        # Verify file was created
        assert dxf_path.exists()

        # Read and verify DXF content
        doc = ezdxf.readfile(str(dxf_path))
        msp = doc.modelspace()

        # Verify only FRAME layer has content
        frame_lines = [e for e in msp if e.dxf.layer == DxfExporter.FRAME_LAYER_NAME]
        assert len(frame_lines) == 4

        # Verify no infill layers were created
        # doc.layers contains Layer objects, so we need to access .dxf.name
        infill_layers = [
            layer
            for layer in doc.layers
            if layer.dxf.name.startswith(DxfExporter.INFILL_LAYER_PREFIX)
        ]
        assert len(infill_layers) == 0

    def test_export_dxf_format_version(self, tmp_path: Path) -> None:
        """Test that exported DXF uses R2010 format for compatibility."""
        frame = _create_rectangular_frame()
        dxf_path = tmp_path / "test_version.dxf"

        exporter = DxfExporter(frame)
        exporter.export(dxf_path)

        # Read and verify DXF version
        doc = ezdxf.readfile(str(dxf_path))
        # R2010 corresponds to AC1024
        assert doc.dxfversion == "AC1024"
