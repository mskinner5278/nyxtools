import getpass
import grp
import logging
import os
import time as ttime
from collections import deque

import fabio
from mxtools.flyer import MXFlyer
from ophyd.sim import NullStatus

logger = logging.getLogger(__name__)
DEFAULT_DATUM_DICT = {"data": None, "omega": None}


class NYXFlyer(MXFlyer):
    def __init__(self, vector, zebra, detector=None) -> None:
        self.name = "NYXFlyer"
        self.vector = vector
        self.zebra = zebra
        self.detector = detector

        self._asset_docs_cache = deque()
        self._resource_uids = []
        self._datum_counter = None
        self._datum_ids = DEFAULT_DATUM_DICT
        self._first_file = None

        self._collection_dictionary = None

    def kickoff(self):
        self.detector.stage()
        self.vector.move()

        return NullStatus()

    def collect(self):
        self.unstage()

        now = ttime.time()
        data = {
            f"{self.detector.name}_image": self._datum_ids["data"],
            "omega": self._datum_ids["omega"],
        }
        yield {
            "data": data,
            "timestamps": {key: now for key in data},
            "time": now,
            "filled": {key: False for key in data},
        }

    def collect_asset_docs(self):

        asset_docs_cache = []

        # Get the Resource which was produced when the detector was staged.
        ((name, resource),) = self.detector.file.collect_asset_docs()

        asset_docs_cache.append(("resource", resource))
        self._datum_ids = DEFAULT_DATUM_DICT
        # Generate Datum documents from scratch here, because the detector was
        # triggered externally by the DeltaTau, never by ophyd.
        resource_uid = resource["uid"]
        # num_points = int(math.ceil(self.detector.cam.num_images.get() /
        #                 self.detector.cam.fw_num_images_per_file.get()))

        # We are currently generating only one datum document for all frames, that's why
        #   we use the 0th index below.
        #
        # Uncomment & update the line below if more datum documents are needed:
        # for i in range(num_points):

        self._first_file = f"{resource['root']}/{resource['resource_path']}_00001.cbf"
        if not os.path.isfile(self._first_file):
            raise RuntimeError(f"File {self._first_file} does not exist")

        # The pseudocode below is from Tom Caswell explaining the relationship between resource, datum, and events.
        #
        # resource = {
        #     "resource_id": "RES",
        #     "resource_kwargs": {},  # this goes to __init__
        #     "spec": "AD-EIGER-MX",
        #     ...: ...,
        # }
        # datum = {
        #     "datum_id": "a",
        #     "datum_kwargs": {"data_key": "data"},  # this goes to __call__
        #     "resource": "RES",
        #     ...: ...,
        # }
        # datum = {
        #     "datum_id": "b",
        #     "datum_kwargs": {"data_key": "omega"},
        #     "resource": "RES",
        #     ...: ...,
        # }

        # event = {...: ..., "data": {"detector_img": "a", "omega": "b"}}

        for data_key in self._datum_ids.keys():
            datum_id = f"{resource_uid}/{data_key}"
            self._datum_ids[data_key] = datum_id
            datum = {
                "resource": resource_uid,
                "datum_id": datum_id,
                "datum_kwargs": {"data_key": data_key},
            }
            asset_docs_cache.append(("datum", datum))
        return tuple(asset_docs_cache)

    def _extract_metadata(self, field="omega"):
        with fabio.open(self._first_file, "r") as cbf:
            return cbf.pilatus_headers("omega")

    def detector_arm(self, **kwargs):
        start = kwargs["angle_start"]
        width = kwargs["img_width"]
        num_images = kwargs["num_images"]
        exposure_per_image = kwargs["exposure_period_per_image"]
        file_prefix = kwargs["file_prefix"]
        data_directory_name = kwargs["data_directory_name"]
        x_beam = kwargs["x_beam"]
        y_beam = kwargs["y_beam"]
        wavelength = kwargs["wavelength"]
        det_distance_m = kwargs["det_distance_m"]

        self.detector.cam.save_files.put(1, wait=True)
        self.detector.cam.file_owner.put(getpass.getuser(), wait=True)
        self.detector.cam.file_owner_grp.put(grp.getgrgid(os.getgid())[0], wait=True)
        self.detector.cam.file_perms.put(420, wait=True)
        file_prefix_minus_directory = str(file_prefix)
        file_prefix_minus_directory = file_prefix_minus_directory.split("/")[-1]

        self.detector.cam.acquire_time.put(exposure_per_image, wait=True)
        self.detector.cam.acquire_period.put(exposure_per_image, wait=True)
        self.detector.cam.num_images.put(num_images, wait=True)
        self.detector.cam.file_path.put(data_directory_name, wait=True)
        self.detector.cam.file_name.put(file_prefix_minus_directory, wait=True)

        # originally from detector_set_fileheader
        self.detector.cam.beam_center_x.put(x_beam, wait=True)
        self.detector.cam.beam_center_y.put(y_beam, wait=True)
        self.detector.cam.omega_incr.put(width, wait=True)
        self.detector.cam.omega_start.put(start, wait=True)
        self.detector.cam.wavelength.put(wavelength, wait=True)
        self.detector.cam.det_distance.put(det_distance_m, wait=True)

        start_arm = ttime.monotonic()
        self.detector.cam.acquire.put(1, wait=True)
        logger.info(f"arm time = {ttime.monotonic() - start_arm}")

    def configure_detector(self, **kwargs):
        ...

    def configure_vector(self, **kwargs):
        angle_start = kwargs["angle_start"]
        scan_width = kwargs["scan_width"]
        exposure_ms = kwargs["exposure_period_per_image"]
        num_images = kwargs["num_images"]
        x_mm = (kwargs["x_start_um"] / 1000, kwargs["x_start_um"] / 1000)
        y_mm = (kwargs["y_start_um"] / 1000, kwargs["y_start_um"] / 1000)
        z_mm = (kwargs["z_start_um"] / 1000, kwargs["z_start_um"] / 1000)
        o = (angle_start, angle_start + scan_width)
        buffer_time_ms = 50
        shutter_lag_time_ms = 2
        shutter_time_ms = 2
        self.vector.prepare_move(
            o,
            x_mm,
            y_mm,
            z_mm,
            exposure_ms,
            num_images,
            buffer_time_ms,
            shutter_lag_time_ms,
            shutter_time_ms,
        )