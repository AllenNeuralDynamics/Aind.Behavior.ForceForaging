# Import core types
from __future__ import annotations

# Import core types
from typing import List, Literal, Optional

import aind_behavior_services.calibration.load_cells as lcc
import aind_behavior_services.calibration.water_valve as wvc
import aind_behavior_services.rig as rig
from aind_behavior_services.calibration import aind_manipulator
from aind_behavior_services.rig import AindBehaviorRigModel
from pydantic import BaseModel, Field

__version__ = "0.2.0"


class AindManipulatorAdditionalSettings(BaseModel):
    """Additional settings for the manipulator device"""

    spout_axis: aind_manipulator.Axis = Field(default=aind_manipulator.Axis.Y1, description="Spout axis")


class AindManipulatorDevice(aind_manipulator.AindManipulatorDevice):
    """Overrides the default settings for the manipulator device by spec'ing additional_settings field"""

    additional_settings: AindManipulatorAdditionalSettings = Field(
        default=AindManipulatorAdditionalSettings(), description="Additional settings"
    )


class RigCalibration(BaseModel):
    water_valve: wvc.WaterValveCalibration = Field(default=..., description="Water valve calibration")


class AindForceForagingRig(AindBehaviorRigModel):
    version: Literal[__version__] = __version__
    triggered_camera_controller: rig.CameraController[rig.SpinnakerCamera] = Field(
        ..., description="Required camera controller to triggered cameras."
    )
    monitoring_camera_controller: Optional[rig.CameraController[rig.WebCamera]] = Field(
        default=None, description="Optional camera controller for monitoring cameras."
    )
    harp_behavior: rig.HarpBehavior = Field(..., description="Harp behavior")
    harp_lickometer: rig.HarpLickometer = Field(..., description="Harp lickometer")
    harp_load_cells: lcc.LoadCells = Field(..., description="Harp load cells")
    harp_clock_generator: rig.HarpClockGenerator = Field(..., description="Harp clock generator")
    harp_clock_repeaters: List[rig.HarpClockGenerator] = Field(default=[], description="Harp clock repeaters")
    harp_analog_input: Optional[rig.HarpAnalogInput] = Field(default=None, description="Harp analog input")
    manipulator: AindManipulatorDevice = Field(..., description="Manipulator")
    screen: rig.Screen = Field(default=rig.Screen(), description="Screen settings")
    calibration: RigCalibration = Field(default=None, description="Load cells calibration")
