import getpass
import grp
import logging
import os
import time as ttime

from ophyd.sim import NullStatus
from ophyd.status import SubscriptionStatus

from .flyer_eiger2 import NYXEiger2Flyer

logger = logging.getLogger(__name__)

INTERNAL_SERIES = 0
INTERNAL_ENABLE = 1
EXTERNAL_SERIES = 2
EXTERNAL_ENABLE = 3


class NYXRasterFlyer(NYXEiger2Flyer):
    def __init__(self, vector, zebra, detector=None) -> None:
        super().__init__(vector, zebra, detector)
        self.name = "NYXRasterFlyer"

    def kickoff(self):
        print("kickoff")
        # still need to stage the detector in lsdc

        def armed_callback(value, old_value, **kwargs):
            if old_value == 0 and value == 1:
                return True
            return False

        zebra_status = SubscriptionStatus(self.zebra.pc.arm.output, armed_callback, run=False)
        self.zebra.pc.arm_signal.put(1)
        zebra_status.wait()
        print(f"zebra arm status success: {zebra_status.success}")
        self.vector.move()
        return NullStatus()  # why not return the status object?

    def update_parameters(self, *args, **kwargs):
        logger.debug(f"starting updating parameters with {kwargs}")
        self.configure_vector(**kwargs)
        row_index = kwargs.get("row_index", 0)
        kwargs["num_images"] = float(kwargs["num_images"])
        numImages = kwargs["num_images"]

        if row_index == 0:
            print("row 0: fully configuring zebra")
            self.zebra.pc.pulse.max.put(numImages)
            self.configure_zebra(**kwargs)
        else:
            print(f"row {row_index}: only setting pulse max")
            self.zebra.pc.pulse.max.put(numImages)
        print("finished updating parameters")

    def configure_detector(self, *args, **kwargs):
        file_prefix = kwargs["file_prefix"]
        data_directory_name = kwargs["data_directory_name"]
        self.detector.file.external_name.put(file_prefix, wait=True)
        self.detector.file.write_path_template = data_directory_name

    def setup_zebra_vector_scan(
        self,
        angle_start,
        gate_width,
        scan_width,
        pulse_width,
        pulse_step,
        exposure_period_per_image,
        num_images,
        is_still=False,
    ):
        print("setuip zebra vector scan")
        self.zebra.pc.encoder.put(0, wait=True)  # 0 = omega for nyx
        self.zebra.pc.direction.put(0, wait=True)  # 0 = positive trigger
        self.zebra.pc.gate.start.put(angle_start, wait=True)
        if is_still is False:
            print(f"before: gate width: {gate_width} gate step: {scan_width}")
            self.zebra.pc.gate.width.put(gate_width, wait=True)
            self.zebra.pc.gate.step.put(scan_width, wait=True)
        self.zebra.pc.gate.num_gates.put(1, wait=True)
        # self.zebra.pc.pulse.start.put(0, wait=True)
        self.zebra.pc.pulse.start.put(55, wait=True)
        print(f"before: pulse width: {pulse_width}")
        self.zebra.pc.pulse.width.put(pulse_width, wait=True)
        self.zebra.pc.pulse.step.put(pulse_step, wait=True)
        print(f"before: pulse delay: {exposure_period_per_image / 2 * 1000}")
        self.zebra.pc.pulse.delay.put((exposure_period_per_image / 2 * 1000), wait=True)
        print(
            f"after: gate width: {self.zebra.pc.gate.width.get()} gate step: {self.zebra.pc.gate.step.get()}"
            f"after: pulse width: {self.zebra.pc.pulse.width.get()} pulse delay: {self.zebra.pc.pulse.delay.get()}"
        )
        self.zebra.pc.pulse.max.put(num_images, wait=True)
        # self.vector.hold.put(0)  # necessary to prevent problems upon
        # exposure time change  elf.detector.cam.acquire.put(1)

    def detector_arm(self, **kwargs):
        start = kwargs["angle_start"]
        width = kwargs["img_width"]
        total_num_images = float(kwargs["total_num_images"])
        exposure_per_image = kwargs["exposure_period_per_image"]
        file_prefix = kwargs["file_prefix"]
        data_directory_name = kwargs["data_directory_name"]
        file_number_start = kwargs["file_number_start"]
        x_beam = kwargs["x_beam"]
        y_beam = kwargs["y_beam"]
        wavelength = kwargs["wavelength"]
        det_distance_m = kwargs["det_distance_m"]
        num_images_per_file = kwargs["num_images_per_file"]

        self.detector.cam.save_files.put(1)
        self.detector.cam.file_owner.put(getpass.getuser())
        self.detector.cam.file_owner_grp.put(grp.getgrgid(os.getgid())[0])
        self.detector.cam.file_perms.put(420)
        file_prefix_minus_directory = str(file_prefix)
        file_prefix_minus_directory = file_prefix_minus_directory.split("/")[-1]

        self.detector.cam.acquire_time.put(exposure_per_image)
        self.detector.cam.acquire_period.put(exposure_per_image)
        self.detector.cam.num_triggers.put(total_num_images)
        self.detector.cam.file_path.put(data_directory_name, wait=True)
        self.detector.cam.fw_name_pattern.put(f"{file_prefix_minus_directory}_$id", wait=True)

        self.detector.cam.sequence_id.put(file_number_start, wait=True)

        # originally from detector_set_fileheader
        self.detector.cam.beam_center_x.put(x_beam)
        self.detector.cam.beam_center_y.put(y_beam)
        self.detector.cam.omega_incr.put(width)
        self.detector.cam.omega_start.put(start)
        self.detector.cam.wavelength.put(wavelength)
        self.detector.cam.det_distance.put(det_distance_m)
        self.detector.cam.trigger_mode.put(
            EXTERNAL_ENABLE
        )  # must be external_enable to get the correct number of triggers and stop acquire

        self.detector.file.file_write_images_per_file.put(num_images_per_file, wait=True)

        start_arm = ttime.time()

        def armed_callback(value, old_value, **kwargs):
            if old_value == 0 and value == 1:
                return True
            return False

        status = SubscriptionStatus(self.detector.cam.armed, armed_callback, run=False)

        self.detector.cam.acquire.put(1)

        status.wait()
        logger.info(f"arm time = {ttime.time() - start_arm}")

    def describe_collect(self):
        return {"stream_name": {}}

    def collect(self):
        logger.debug("raster_flyer.collect(): going to unstage now")
        yield {"data": {}, "timestamps": {}, "time": 0, "seq_num": 0}

    def unstage(self):
        logger.debug("flyer unstaging")
        # self.detector.cam.acquire.put(0)

    def collect_asset_docs(self):
        for _ in ():
            yield _
