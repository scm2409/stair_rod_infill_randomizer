"""Factory for creating infill generator instances."""
from railing_generator.domain.infill_generators.generator import Generator
from railing_generator.domain.infill_generators.generator_parameters import (
    InfillGeneratorParameters,
)
from railing_generator.domain.infill_generators.random_generator import RandomGenerator


class GeneratorFactory:
    """
    Factory for creating infill generator instances.

    This factory creates generator instances based on a type string and parameters.
    Each generator class defines its own PARAMETER_TYPE attribute.
    """

    # Registry of available generator types
    _GENERATOR_TYPES: dict[str, type[Generator]] = {
        "random": RandomGenerator,
    }

    @classmethod
    def create_generator(
        cls, generator_type: str, parameters: InfillGeneratorParameters
    ) -> Generator:
        """
        Create a generator instance of the specified type.

        Args:
            generator_type: The generator type identifier (e.g., "random")
            parameters: The validated generator parameters

        Returns:
            Generator instance

        Raises:
            ValueError: If the generator type is unknown or parameters don't match
        """
        if generator_type not in cls._GENERATOR_TYPES:
            available = ", ".join(cls._GENERATOR_TYPES.keys())
            raise ValueError(
                f"Unknown generator type: {generator_type}. "
                f"Available types: {available}"
            )

        # Get generator class and its parameter type
        generator_class = cls._GENERATOR_TYPES[generator_type]
        expected_param_type = generator_class.PARAMETER_TYPE

        # Verify parameter type matches generator type
        if not isinstance(parameters, expected_param_type):
            raise ValueError(
                f"Generator type '{generator_type}' requires {expected_param_type.__name__}, "
                f"got {type(parameters).__name__}"
            )

        # Create and return generator instance
        return generator_class()

    @classmethod
    def get_available_generator_types(cls) -> list[str]:
        """
        Get list of available generator type identifiers.

        Returns:
            List of generator type strings (e.g., ["random"])
        """
        return list(cls._GENERATOR_TYPES.keys())

    @classmethod
    def get_parameter_type(cls, generator_type: str) -> type[InfillGeneratorParameters]:
        """
        Get the parameter type for a given generator type.

        Args:
            generator_type: The generator type identifier

        Returns:
            Parameter class for the generator type

        Raises:
            ValueError: If the generator type is unknown
        """
        if generator_type not in cls._GENERATOR_TYPES:
            available = ", ".join(cls._GENERATOR_TYPES.keys())
            raise ValueError(
                f"Unknown generator type: {generator_type}. "
                f"Available types: {available}"
            )

        # Get parameter type from the generator class
        generator_class = cls._GENERATOR_TYPES[generator_type]
        return generator_class.PARAMETER_TYPE
