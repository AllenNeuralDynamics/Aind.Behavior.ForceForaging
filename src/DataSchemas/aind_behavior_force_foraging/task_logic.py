from __future__ import annotations

from enum import Enum
from functools import partial
from typing import Annotated, Dict, List, Literal, Optional, Self, Union

import aind_behavior_services.task_logic.distributions as distributions
from aind_behavior_services.task_logic import AindBehaviorTaskLogicModel, TaskParameters
from pydantic import BaseModel, Field, RootModel, field_validator, model_validator

__version__ = "0.1.0"

MAX_LOAD_CELL_FORCE = 32768


def scalar_value(value: float) -> distributions.Scalar:
    """
    Helper function to create a scalar value distribution for a given value.

    Args:
        value (float): The value of the scalar distribution.

    Returns:
        distributions.Scalar: The scalar distribution type.
    """
    return distributions.Scalar(distribution_parameters=distributions.ScalarDistributionParameter(value=value))


def uniform_distribution_value(min: float, max: float) -> distributions.Uniform:
    """
    Helper function to create a uniform distribution for a given range.

    Args:
        min (float): The minimum value of the uniform distribution.
        max (float): The maximum value of the uniform distribution.

    Returns:
        distributions.Uniform: The uniform distribution type.
    """
    return distributions.UniformDistribution(
        distribution_parameters=distributions.UniformDistributionParameters(max=max, min=min)
    )


def normal_distribution_value(mean: float, std: float) -> distributions.Normal:
    """
    Helper function to create a normal distribution for a given range.

    Args:
        mean (float): The mean value of the normal distribution.
        std (float): The standard deviation of the normal distribution.

    Returns:
        distributions.Normal: The normal distribution type.
    """
    return distributions.NormalDistribution(
        distribution_parameters=distributions.NormalDistributionParameters(mean=mean, std=std)
    )


class HarvestActionLabel(str, Enum):
    """Defines the harvest actions"""

    LEFT = "Left"
    RIGHT = "Right"
    NONE = "None"


# Updaters
class NumericalUpdaterOperation(str, Enum):
    NONE = "None"
    ADD = "Offset"
    MULTIPLY = "Gain"
    SET = "Set"


class NumericalUpdaterParameters(BaseModel):
    value: distributions.Distribution = Field(
        default=scalar_value(0),
        validate_default=True,
        description="The value of the update. This value will be multiplied by the optional input event value.",
    )
    minimum: float = Field(default=0, description="Minimum value of the parameter")
    maximum: float = Field(default=0, description="Maximum value of the parameter")


class NumericalUpdater(BaseModel):
    operation: NumericalUpdaterOperation = Field(
        default=NumericalUpdaterOperation.NONE, description="Operation to perform on the parameter"
    )
    parameters: NumericalUpdaterParameters = Field(
        NumericalUpdaterParameters(), description="Parameters of the updater"
    )


class UpdateTargetParameterBy(str, Enum):
    """Defines the independent variable used for the update"""

    TIME = "Time"
    REWARD = "Reward"
    TRIAL = "Trial"


class UpdateTargetParameter(str, Enum):
    """Defines the target parameters"""

    LOWER_FORCE_THRESHOLD = "LowerForceThreshold"
    UPPER_FORCE_THRESHOLD = "UpperForceThreshold"
    PROBABILITY = "Probability"
    AMOUNT = "Amount"
    FORCE_DURATION = "ForceDuration"
    DELAY = "Delay"


class ActionUpdater(BaseModel):
    target_parameter: UpdateTargetParameter = Field(
        default=UpdateTargetParameter.PROBABILITY, description="Target parameter"
    )
    updated_by: UpdateTargetParameterBy = Field(
        default=UpdateTargetParameterBy.TIME, description="Independent variable"
    )
    updater: NumericalUpdater = Field(..., description="Updater")


class TrialType(str, Enum):
    """Defines the trial types"""

    NONE = "None"
    ACCUMULATION = "Accumulation"
    ROI = "RegionOfInterest"


class ContinuousFeedbackMode(str, Enum):
    """Defines the feedback mode"""

    NONE = "None"
    AUDIO = "Audio"
    VISUAL = "Visual"
    MANIPULATOR = "Manipulator"


ValuePair = Annotated[List[float], Field(min_length=2, max_length=2, description="A tuple of two values")]


class _ContinuousFeedbackBase(BaseModel):
    continuous_feedback_mode: ContinuousFeedbackMode = Field(
        default=ContinuousFeedbackMode.NONE, description="Continuous feedback mode"
    )
    converter_lut_input: List[Annotated[float, Field(ge=0, le=1)]] = Field(
        default=[0, 1], min_length=2, description="Input domain. All values should be between 0 and 1"
    )
    converter_lut_output: List[float] = Field(
        default=[0, 1],
        min_length=2,
        description="Output domain used to linearly interpolate the input values to the output values",
    )

    @model_validator(mode="after")
    def _validate_lut(self) -> Self:
        if len(self.converter_lut_input) != len(self.converter_lut_output):
            raise ValueError("Input and output LUT must have the same length")
        return self


class ManipulatorFeedback(_ContinuousFeedbackBase):
    continuous_feedback_mode: Literal[ContinuousFeedbackMode.MANIPULATOR] = ContinuousFeedbackMode.MANIPULATOR


class AudioFeedback(_ContinuousFeedbackBase):
    continuous_feedback_mode: Literal[ContinuousFeedbackMode.AUDIO] = ContinuousFeedbackMode.AUDIO


class ContinuousFeedback(RootModel):
    root: Annotated[Union[ManipulatorFeedback, AudioFeedback], Field(discriminator="continuous_feedback_mode")]


class HarvestAction(BaseModel):
    """Defines an abstract class for an harvest action"""

    action: HarvestActionLabel = Field(default=HarvestActionLabel.NONE, description="Label of the action")
    trial_type: TrialType = Field(default=TrialType.NONE, description="Type of the trial")
    probability: float = Field(default=1, description="Probability of reward")
    amount: float = Field(default=1, description="Amount of reward to be delivered")
    delay: float = Field(default=0, description="Delay between successful harvest and reward delivery")
    force_duration: float = Field(default=0.5, description="Duration that the force much stay above threshold")
    upper_force_threshold: float = Field(
        default=MAX_LOAD_CELL_FORCE,
        le=MAX_LOAD_CELL_FORCE,
        ge=-MAX_LOAD_CELL_FORCE,
        description="Upper bound of the force target region or the target cached force required.",
    )
    lower_force_threshold: float = Field(
        default=5000,
        le=MAX_LOAD_CELL_FORCE,
        ge=-MAX_LOAD_CELL_FORCE,
        description="Lower bound of the force target region.",
    )
    is_operant: bool = Field(default=True, description="Whether the reward delivery is contingent on licking.")
    time_to_collect: Optional[float] = Field(
        default=None,
        ge=0,
        description="Time to collect the reward after it is available. If null, the reward will be available indefinitely.",
    )
    action_updaters: List[ActionUpdater] = Field(
        default=[], description="List of action updaters. All updaters are called at the start of a new trial."
    )
    continuous_feedback: Optional[ContinuousFeedback] = Field(default=None, description="Continuous feedback settings")

    @model_validator(mode="after")
    def _validate_thresholds(self) -> Self:
        if self.upper_force_threshold < self.lower_force_threshold:
            raise ValueError(
                f"Upper force threshold ({self.upper_force_threshold}) must be greater than lower force threshold({self.lower_force_threshold})"
            )
        return self

    @model_validator(mode="after")
    def _validate_trial_type(self) -> Self:
        if self.trial_type == TrialType.ROI:
            if not all(
                [
                    self._between_thresholds(self.upper_force_threshold),
                    self._between_thresholds(self.lower_force_threshold),
                ]
            ):
                raise ValueError("Force thresholds must be between -32768 and 32768 for ROI trials")
        return self

    @staticmethod
    def _between_thresholds(value: float) -> bool:
        return value <= MAX_LOAD_CELL_FORCE and value >= -MAX_LOAD_CELL_FORCE


class QuiescencePeriod(BaseModel):
    """Defines a quiescence settings"""

    duration: float = Field(default=0, ge=0, description="Duration of the quiescence period")
    force_threshold: float = Field(
        default=0, le=MAX_LOAD_CELL_FORCE, ge=-MAX_LOAD_CELL_FORCE, description="Time out for the quiescence period"
    )
    has_cue: bool = Field(default=False, description="Whether to use a cue to signal the start of the period.")


class InitiationPeriod(BaseModel):
    """Defines an initiation period"""

    duration: float = Field(default=0, ge=0, description="Duration of the initiation period")
    has_cue: bool = Field(default=True, description="Whether to use a cue to signal the start of the period.")
    abort_on_force: bool = Field(
        default=False, description="Whether to abort the trial if a choice is made during the initiation period."
    )
    abort_on_force_threshold: float = Field(
        default=0, le=MAX_LOAD_CELL_FORCE, ge=-MAX_LOAD_CELL_FORCE, description="Time out for the quiescence period"
    )


class ResponsePeriod(BaseModel):
    """Defines a response period"""

    duration: float = Field(
        default=0, ge=0, description="Duration of the response period. I.e. the time the animal has to make a choice."
    )
    has_cue: bool = Field(default=True, description="Whether to use a cue to signal the start of the period.")
    has_feedback: bool = Field(
        default=False, description="Whether to provide feedback to the animal after the response period."
    )


RightHarvestAction = partial(HarvestAction, action=HarvestActionLabel.RIGHT)
LeftHarvestAction = partial(HarvestAction, action=HarvestActionLabel.LEFT)


class Trial(BaseModel):
    """Defines a trial"""

    inter_trial_interval: float = Field(default=0, ge=0, description="Time between trials")
    quiescence_period: Optional[QuiescencePeriod] = Field(default=None, description="Quiescence settings")
    initiation_period: InitiationPeriod = Field(
        default=InitiationPeriod(), validate_default=True, description="Initiation settings"
    )
    response_period: ResponsePeriod = Field(
        default=ResponsePeriod(), validate_default=True, description="Response settings"
    )
    left_harvest: Optional[HarvestAction] = Field(
        default=LeftHarvestAction(), validate_default=True, description="Specification of the left action"
    )
    right_harvest: Optional[HarvestAction] = Field(
        default=RightHarvestAction(), validate_default=True, description="Specification of the right action"
    )

    @field_validator("left_harvest", mode="after")
    @classmethod
    def _validate_left_harvest(cls, value: Optional[HarvestAction]) -> Optional[HarvestAction]:
        return cls._validate_harvest(value, HarvestActionLabel.LEFT)

    @field_validator("right_harvest", mode="after")
    @classmethod
    def _validate_right_harvest(cls, value: Optional[HarvestAction]) -> Optional[HarvestAction]:
        return cls._validate_harvest(value, HarvestActionLabel.RIGHT)

    @staticmethod
    def _validate_harvest(value: Optional[HarvestAction], harvest_label: HarvestActionLabel) -> Optional[HarvestAction]:
        if value is None:
            return value
        if value.action == HarvestActionLabel.NONE:
            return HarvestAction(action=harvest_label)
        if value.action != harvest_label:
            raise ValueError(f"Harvest action must be of type {harvest_label}")
        return value


class BlockStatisticsMode(str, Enum):
    """Defines the mode of the environment"""

    BLOCK = "Block"
    BROWNIAN = "BrownianRandomWalk"
    BLOCK_GENERATOR = "BlockGenerator"


class Block(BaseModel):
    mode: Literal[BlockStatisticsMode.BLOCK] = BlockStatisticsMode.BLOCK
    is_baited: bool = Field(default=False, description="Whether the trials are baited")
    trials: List[Trial] = Field(default=[], description="List of trials in the block")
    shuffle: bool = Field(default=False, description="Whether to shuffle the trials in the block")
    repeat_count: Optional[int] = Field(
        default=0, description="Number of times to repeat the block. If null, the block will be repeated indefinitely"
    )


class BlockGenerator(BaseModel):
    mode: Literal[BlockStatisticsMode.BLOCK_GENERATOR] = BlockStatisticsMode.BLOCK_GENERATOR
    is_baited: bool = Field(default=False, description="Whether the trials are baited")
    block_size: distributions.Distribution = Field(
        default=uniform_distribution_value(min=50, max=60), validate_default=True, description="Size of the block"
    )
    trial_statistics: Trial = Field(..., description="Statistics of the trials in the block")


class BrownianRandomWalk(BaseModel):
    mode: Literal[BlockStatisticsMode.BROWNIAN] = BlockStatisticsMode.BROWNIAN
    is_baited: bool = Field(default=False, description="Whether the trials are baited")
    block_size: distributions.Distribution = Field(
        default=uniform_distribution_value(min=50, max=60), validate_default=True, description="Size of the block"
    )
    trial_statistics: Trial = Field(..., description="Statistics of the trials in the block")


class BlockStatistics(RootModel):
    root: Annotated[Union[Block, BlockGenerator, BrownianRandomWalk], Field(discriminator="mode")]


class Environment(BaseModel):
    block_statistics: List[BlockStatistics] = Field(..., description="Statistics of the environment")
    shuffle: bool = Field(default=False, description="Whether to shuffle the blocks")
    repeat_count: Optional[int] = Field(
        default=0,
        description="Number of times to repeat the environment. If null, the environment will be repeated indefinitely",
    )


class PressMode(str, Enum):
    """Defines the press mode"""

    DOUBLE = "Double"
    SINGLE_AVERAGE = "SingleAverage"
    SINGLE_MAX = "SingleMax"
    SINGLE_MIN = "SingleMin"
    SINGLE_LEFT = "SingleLeft"
    SINGLE_RIGHT = "SingleRight"
    SINGLE_LOOKUP_TABLE = "SingleLookupTable"


class ForceLookUpTable(BaseModel):
    path: str = Field(
        ..., description="Reference to the look up table image. Should be a 1 channel image. Value = LUT[Left, Right]"
    )

    offset: float = Field(default=0, description="Offset to add to the look up table value")

    scale: float = Field(default=1, description="Scale to multiply the look up table value")

    left_min: float = Field(
        ..., description="The lower value of Left force used to linearly scale the input coordinate to."
    )
    left_max: float = Field(
        ..., description="The upper value of Left force used to linearly scale the input coordinate to."
    )
    right_min: float = Field(
        ..., description="The lower value of Right force used to linearly scale the input coordinate to."
    )
    right_max: float = Field(
        ..., description="The upper value of Right force used to linearly scale the input coordinate to."
    )

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        if self.left_min > self.left_max:
            raise ValueError("Left min must be less than left max")
        if self.right_min > self.right_max:
            raise ValueError("Right min must be less than right max")
        return self


class ForceOperationControl(BaseModel):
    press_mode: PressMode = Field(
        default=PressMode.DOUBLE, description="Defines the press mode. Default is to use both sensors individually"
    )
    left_index: int = Field(default=0, description="Index of the left sensor")
    right_index: int = Field(default=1, description="Index of the right sensor")
    force_lookup_table: Optional[ForceLookUpTable] = Field(
        default=None, description="Look up table for force projection"
    )

    @model_validator(mode="after")
    def _validate_press_mode_versus_lut(self) -> Self:
        if self.press_mode == PressMode.SINGLE_LOOKUP_TABLE and self.force_lookup_table is None:
            raise ValueError("Look up table must be provided when using single lookup table mode")
        if self.press_mode != PressMode.SINGLE_LOOKUP_TABLE:
            self.force_lookup_table = None
        return self


class SpoutOperationControl(BaseModel):
    default_retracted_position: float = Field(default=0, description="Default retracted position (mm)")
    default_extended_position: float = Field(default=0, description="Default extended position (mm)")
    enabled: bool = Field(default=True, description="Whether the spout control is enabled")


class OperationControl(BaseModel):
    force: ForceOperationControl = Field(
        default=ForceOperationControl(), validate_default=True, description="Operation control for force sensor"
    )
    spout: SpoutOperationControl = Field(
        default=SpoutOperationControl(), validate_default=True, description="Operation control for spout"
    )


class AindForceForagingTaskParameters(TaskParameters):
    environment: Environment = Field(..., description="Environment settings")
    updaters: Dict[str, NumericalUpdater] = Field(default_factory=dict, description="List of numerical updaters")
    operation_control: OperationControl = Field(
        default=OperationControl(), validate_default=True, description="Operation control"
    )


class AindForceForagingTaskLogic(AindBehaviorTaskLogicModel):
    version: Literal[__version__] = __version__
    name: str = Field(default="AindForceForaging", description="Name of the task logic", frozen=True)
    task_parameters: AindForceForagingTaskParameters = Field(..., description="Parameters of the task logic")
