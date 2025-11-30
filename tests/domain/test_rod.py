"""Tests for Rod model."""

import pytest
from pydantic import ValidationError
from shapely.geometry import LineString, Point

from railing_generator.domain.rod import Rod


class TestRodCreation:
    """Test Rod instance creation and validation."""

    def test_create_valid_rod(self) -> None:
        """Test creating a valid rod with all required fields."""
        geometry = LineString([(0, 0), (0, 100)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )

        assert rod.geometry == geometry
        assert rod.start_cut_angle_deg == 0.0
        assert rod.end_cut_angle_deg == 0.0
        assert rod.weight_kg_m == 0.5
        assert rod.layer == 1

    def test_create_rod_with_default_layer(self) -> None:
        """Test that layer defaults to 0 (frame) when not specified."""
        geometry = LineString([(0, 0), (100, 0)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        assert rod.layer == 0

    def test_create_rod_with_angled_cuts(self) -> None:
        """Test creating a rod with angled cuts."""
        geometry = LineString([(10, 20), (30, 80)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=45.0,
            end_cut_angle_deg=-30.0,
            weight_kg_m=0.3,
            layer=2,
        )

        assert rod.start_cut_angle_deg == 45.0
        assert rod.end_cut_angle_deg == -30.0


class TestRodValidation:
    """Test Rod field validation."""

    def test_start_cut_angle_too_low(self) -> None:
        """Test that start_cut_angle_deg below -90 is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=-91.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("start_cut_angle_deg",) for e in errors)

    def test_start_cut_angle_too_high(self) -> None:
        """Test that start_cut_angle_deg above 90 is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=91.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("start_cut_angle_deg",) for e in errors)

    def test_end_cut_angle_too_low(self) -> None:
        """Test that end_cut_angle_deg below -90 is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=-91.0,
                weight_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("end_cut_angle_deg",) for e in errors)

    def test_end_cut_angle_too_high(self) -> None:
        """Test that end_cut_angle_deg above 90 is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=91.0,
                weight_kg_m=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("end_cut_angle_deg",) for e in errors)

    def test_weight_kg_m_zero(self) -> None:
        """Test that weight_kg_m of zero is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.0,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("weight_kg_m",) for e in errors)

    def test_weight_kg_m_negative(self) -> None:
        """Test that negative weight_kg_m is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=-0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("weight_kg_m",) for e in errors)

    def test_layer_negative(self) -> None:
        """Test that negative layer is rejected."""
        geometry = LineString([(0, 0), (0, 100)])
        with pytest.raises(ValidationError) as exc_info:
            Rod(
                geometry=geometry,
                start_cut_angle_deg=0.0,
                end_cut_angle_deg=0.0,
                weight_kg_m=0.5,
                layer=-1,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("layer",) for e in errors)


class TestRodComputedFields:
    """Test Rod computed properties."""

    def test_length_cm_vertical_rod(self) -> None:
        """Test length calculation for a vertical rod."""
        geometry = LineString([(0, 0), (0, 100)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        assert rod.length_cm == pytest.approx(100.0)

    def test_length_cm_horizontal_rod(self) -> None:
        """Test length calculation for a horizontal rod."""
        geometry = LineString([(0, 0), (150, 0)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        assert rod.length_cm == pytest.approx(150.0)

    def test_length_cm_diagonal_rod(self) -> None:
        """Test length calculation for a diagonal rod."""
        geometry = LineString([(0, 0), (30, 40)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        assert rod.length_cm == pytest.approx(50.0)

    def test_weight_kg_calculation(self) -> None:
        """Test weight calculation from length and weight per meter."""
        geometry = LineString([(0, 0), (0, 200)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        assert rod.weight_kg == pytest.approx(1.0)

    def test_weight_kg_with_different_weight_per_meter(self) -> None:
        """Test weight calculation with different weight per meter."""
        geometry = LineString([(0, 0), (0, 100)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.3,
        )

        assert rod.weight_kg == pytest.approx(0.3)

    def test_start_point(self) -> None:
        """Test start_point property."""
        geometry = LineString([(10, 20), (30, 40)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        start = rod.start_point
        assert isinstance(start, Point)
        assert start.x == pytest.approx(10.0)
        assert start.y == pytest.approx(20.0)

    def test_end_point(self) -> None:
        """Test end_point property."""
        geometry = LineString([(10, 20), (30, 40)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
        )

        end = rod.end_point
        assert isinstance(end, Point)
        assert end.x == pytest.approx(30.0)
        assert end.y == pytest.approx(40.0)


class TestRodBOMGeneration:
    """Test BOM entry generation."""

    def test_to_bom_entry(self) -> None:
        """Test converting rod to BOM entry."""
        geometry = LineString([(0, 0), (0, 100)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=45.0,
            end_cut_angle_deg=-30.5,
            weight_kg_m=0.5,
        )

        bom_entry = rod.to_bom_entry(rod_id=1)

        assert bom_entry["id"] == 1
        assert bom_entry["length_cm"] == pytest.approx(100.0)
        assert bom_entry["start_cut_angle_deg"] == pytest.approx(45.0)
        assert bom_entry["end_cut_angle_deg"] == pytest.approx(-30.5)
        assert bom_entry["weight_kg"] == pytest.approx(0.5)

    def test_to_bom_entry_rounding(self) -> None:
        """Test that BOM entry values are properly rounded."""
        geometry = LineString([(0, 0), (0, 123.456)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=12.3456,
            end_cut_angle_deg=-45.6789,
            weight_kg_m=0.333,
        )

        bom_entry = rod.to_bom_entry(rod_id=5)

        assert bom_entry["length_cm"] == pytest.approx(123.46)
        assert bom_entry["start_cut_angle_deg"] == pytest.approx(12.3)
        assert bom_entry["end_cut_angle_deg"] == pytest.approx(-45.7)
        assert bom_entry["weight_kg"] == pytest.approx(0.411)


class TestRodSerialization:
    """Test Rod serialization methods."""

    def test_model_dump_excludes_geometry(self) -> None:
        """Test that model_dump excludes geometry field."""
        geometry = LineString([(0, 0), (0, 100)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=0.0,
            end_cut_angle_deg=0.0,
            weight_kg_m=0.5,
            layer=1,
        )

        data = rod.model_dump()

        # Geometry is now included in model_dump with custom serializer
        assert "geometry" in data
        assert data["start_cut_angle_deg"] == 0.0
        assert data["end_cut_angle_deg"] == 0.0
        assert data["weight_kg_m"] == 0.5
        assert data["layer"] == 1

    def test_model_dump_includes_geometry_coordinates(self) -> None:
        """Test that model_dump includes geometry coordinates."""
        geometry = LineString([(10, 20), (30, 40)])
        rod = Rod(
            geometry=geometry,
            start_cut_angle_deg=45.0,
            end_cut_angle_deg=-30.0,
            weight_kg_m=0.5,
            layer=2,
        )

        data = rod.model_dump()

        assert "geometry" in data
        assert data["geometry"] == [[10.0, 20.0], [30.0, 40.0]]
        assert data["start_cut_angle_deg"] == 45.0
        assert data["end_cut_angle_deg"] == -30.0
        assert data["weight_kg_m"] == 0.5
        assert data["layer"] == 2
