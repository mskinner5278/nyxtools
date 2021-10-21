from typing import Tuple
import time

from ophyd import (
    Device,
    EpicsSignal,
    EpicsSignalRO,
    Component as Cpt,
    FormattedComponent as FCpt
)
from bluesky import plan_stubs as bps


class VectorSignalWithRBV(EpicsSignal):
    """
    An EPICS signal that uses 'pvname-SP' for the setpoint and
    'pvname-I' for the read-back
    """

    def __init__(self, prefix, **kwargs):
        super().__init__(f"{prefix}-I", write_pv=f"{prefix}-SP", **kwargs)


class VectorMotor(Device):
    #
    # Configuration
    #

    # Start position of this motor (in EGU)
    start = FCpt(VectorSignalWithRBV, "{prefix}Pos:{motor_name}Start")

    # End position of this motor (in EGU)
    end = FCpt(VectorSignalWithRBV, "{prefix}Pos:{motor_name}End")

    #
    # Status
    #

    # If true, indicates that the requested motion exceeds the max speed for this motor
    too_fast = FCpt(EpicsSignalRO, "{prefix}Sts:{motor_name}TooFast-Sts")

    #
    # Debugging: calculated motion characteristics
    #

    # Acceleration (ct/ms^2)
    accel = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}Accel-I")

    # Distance travelled during data acquisition motion (ct)
    daq_dist = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}DataAcqDist-I")

    # Desired speed (ct/ms)
    des_speed = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}DesSpeed-I")

    # Time it will take to reach the desired speed (ms)
    time_to_speed = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}TimeToSpeed-I")

    # Motion direction (+1 or -1)
    direction = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}Dir-I")

    # Distance travelled during speedup motion (ct)
    speedup_dist = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}SpeedUpDist-I")

    # Distance travelled during buffer motion (ct)
    buffer_dist = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}BufferDist-I")

    # Distance travelled while the shutter is opening  (ct)
    shutter_open_dist = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}ShutOpenDist-I")

    # Distance travelled during backup motion (ct)
    backup_dist = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}BackUpDist-I")

    # Distance travelled while waiting for the shutter lag (ct)
    shutter_lag_dist = FCpt(EpicsSignalRO, "{prefix}Val:{motor_name}ShutLagDist-I")

    def __init__(self, prefix, motor_name=None, **kwargs):
        self.motor_name = motor_name
        super().__init__(prefix, **kwargs)


class VectorProgram(Device):
    """
    Wraps PVs that control the vector program.
    """

    #
    # Configuration
    #

    # Exposure per sample (ms)
    exposure = Cpt(VectorSignalWithRBV, "Val:Exposure")

    # Number of samples
    num_samples = Cpt(VectorSignalWithRBV, "Val:NumSamples")

    # "Buffer" motion time (ms)
    buffer_time = Cpt(VectorSignalWithRBV, "Val:BufferTime")

    # Shutter opening / closing time (ms)
    shutter_time = Cpt(VectorSignalWithRBV, "Val:ShutTime")

    # Shutter lag (ms)
    shutter_lag_time = Cpt(VectorSignalWithRBV, "Val:ShutLagTime")

    # Whether to expose (whether to open the shutter during acquisition)
    expose = Cpt(EpicsSignal, "Expose-Sel")

    # Whether to actually execute the motion
    # If calc_only==True, no motion is performed but the vector profile is calculated
    # (useful for debugging)
    calc_only = Cpt(EpicsSignal, "CalcOnly-Sel")

    # Whether to pause the vector after backing up but before the start of the motion
    hold = Cpt(EpicsSignal, "Hold-Sel")

    #
    # Individual motor configuration / status
    #

    # Omega motor
    o = Cpt(VectorMotor, "O")

    # X motor
    x = Cpt(VectorMotor, "X")

    # Y motor
    y = Cpt(VectorMotor, "Y")

    # Z motor
    z = Cpt(VectorMotor, "Z")

    #
    # Debugging
    #

    # Calculated data acquisition duration (ms)
    data_acq_duration = Cpt(EpicsSignalRO, "Val:DataAcqDuration-I")

    # Calculated maximum time to reach desired speeds (ms)
    max_time_to_speed = Cpt(EpicsSignalRO, "Val:MaxTimeToSpeed-I")

    #
    # Status
    #

    # Indicates whether a vector motion is running
    running = Cpt(EpicsSignalRO, "Sts:Running-Sts")

    # Current state of the vector:
    #   Idle, Backup, Holding or Acquiring
    state = Cpt(EpicsSignalRO, "Sts:State-Sts")

    # Error reported by the vector program:
    #   None, Aborted, Zero Exposure, Too Fast, Zero Shutter, Too Slow
    error = Cpt(EpicsSignalRO, "Sts:Error-Sts")

    #
    # Commands
    #

    # Start a vector motion
    go = Cpt(EpicsSignal, "Cmd:Go-Cmd")

    # Proceed with the vector motion when it is paused
    # Only needed if hold==True
    proceed = Cpt(EpicsSignal, "Cmd:Proceed-Cmd")

    # Abort the current vector motion
    abort = Cpt(EpicsSignal, "Cmd:Abort-Cmd")

    # Set all vector motors start and end position to their current RBV values
    sync = Cpt(EpicsSignal, "Cmd:Sync-Cmd")

    def run(
        self,
        o: Tuple[float,float], x: Tuple[float,float], y: Tuple[float, float], z: Tuple[float,float],
        exposure_ms: float, num_samples: float, buffer_time_ms: float, shutter_lag_time_ms: float,
        shutter_time_ms: float):

        # Configure motion
        yield from bps.abs_set(self.sync, 1, wait=True)

        yield from bps.mv(
            self.calc_only, True, # Check for errors first
            self.expose, True,
            self.hold, False,

            self.exposure, exposure_ms,
            self.num_samples, num_samples,
            self.buffer_time, buffer_time_ms,
            self.shutter_lag_time, shutter_lag_time_ms,
            self.shutter_time, shutter_time_ms,

            self.o.start, o[0],
            self.o.end, o[1],

            self.x.start, x[0],
            self.x.end, x[1],

            self.y.start, y[0],
            self.y.end, y[1],

            self.z.start, z[0],
            self.z.end, z[1],

            group='vec_config'
        )

        yield from bps.wait('vec_config')

        # Start "motion"
        yield from bps.abs_set(self.go, 1, wait=False)

        # There's no way to know it is done, so wait a little, it should be very fast
        yield from bps.sleep(1.0)

        # Check for errors
        error = yield from bps.rd(self.error, as_string=True, use_monitor=False)

        if error != "None":
            raise Exception(f"Failed to run vector. Error: {error}")

        # Estimate total motion time (in ms)
        time_to_speed = yield from bps.rd(self.max_time_to_speed)
        buffer_time = yield from bps.rd(self.buffer_time)
        shutter_time = yield from bps.rd(self.shutter_time)
        daq_duration = yield from bps.rd(self.data_acq_duration)

        estimated_total_time_ms = 2*time_to_speed + buffer_time + 2*shutter_time + daq_duration
        timeout = 5*estimated_total_time_ms/1000.0

        # Start actual motion
        yield from bps.abs_set(self.calc_only, False, wait=True)
        yield from bps.abs_set(self.go, 1, wait=False)

        # Wait until it is done

        # NOTE: ideally we should catch self.running going from 0->1 and then from 1->0
        # but it is not guaranteed that we can observe these two transitions.
        # instead, we wait a little bit after the motion is started (hopefully past 0->1)
        # and then wait until either we see 1->0 or a timeout expires

        yield from bps.sleep(0.2)

        t = time.time()

        while True:
            running = yield from bps.rd(self.running)
            elapsed = time.time() - t

            if not running or elapsed > timeout:
                break

            yield from bps.sleep(0.1)
