"""Default configuration for Pass-Through Evaluator."""

from dataclasses import dataclass


@dataclass
class PassThroughEvaluatorDefaults:
    """
    Default configuration for Pass-Through Evaluator.

    The Pass-Through Evaluator has no configurable parameters.
    This dataclass exists for consistency with other evaluators
    and to support the Hydra configuration system.

    Loaded from: conf/evaluators/passthrough.yaml
    """

    pass
