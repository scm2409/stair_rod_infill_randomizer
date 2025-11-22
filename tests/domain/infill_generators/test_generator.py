"""Tests for Generator base class."""
from PySide6.QtCore import QObject

from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.railing_frame import RailingFrame
from railing_generator.domain.railing_infill import RailingInfill


class MockGenerator(Generator):
    """Mock generator for testing."""

    def generate(
        self, frame: RailingFrame, params: InfillGeneratorParameters
    ) -> RailingInfill:
        """Mock generate method."""
        return RailingInfill(rods=[])


def test_generator_is_qobject() -> None:
    """Test that Generator inherits from QObject."""
    generator = MockGenerator()
    assert isinstance(generator, QObject)


def test_generator_has_signals() -> None:
    """Test that Generator has required signals."""
    generator = MockGenerator()
    assert hasattr(generator, "progress_updated")
    assert hasattr(generator, "best_result_updated")
    assert hasattr(generator, "generation_completed")
    assert hasattr(generator, "generation_failed")


def test_generator_initialization() -> None:
    """Test generator initialization."""
    generator = MockGenerator()
    assert not generator.is_cancelled()


def test_generator_cancel() -> None:
    """Test cancellation flag."""
    generator = MockGenerator()
    assert not generator.is_cancelled()

    generator.cancel()
    assert generator.is_cancelled()


def test_generator_reset_cancellation() -> None:
    """Test resetting cancellation flag."""
    generator = MockGenerator()
    generator.cancel()
    assert generator.is_cancelled()

    generator.reset_cancellation()
    assert not generator.is_cancelled()
