import datetime
from ophyd.areadetector.detectors import PilatusDetector
from ophyd import Component as Cpt
from ophyd import Device, EpicsPathSignal, EpicsSignal, ImagePlugin, Signal
from ophyd.areadetector.base import ADComponent
from ophyd.areadetector.filestore_mixins import FileStoreBase

class PilatusSimulatedFilePlugin(Device, FileStoreBase):
    file_path = ADComponent(EpicsPathSignal, "FilePath", string=True, path_semantics="posix")
    external_name = Cpt(Signal, value="")

    def __init__(self, *args, **kwargs):
        self.filestore_spec = "AD_PILATUS_MX"
        super().__init__(*args, **kwargs)

    def stage(self):
        write_path = datetime.datetime.now().strftime(self.write_path_template)
        super().stage()

    def generate_datum(self, key, timestamp, datum_kwargs):
        if self.frame_num is not None:
            datum_kwargs.update({"frame_num": self.frame_num})
        return super().generate_datum(key, timestamp, datum_kwargs)

class PilatusBase(PilatusDetector):
    file = Cpt(PilatusSimulatedFilePlugin,
               suffix="cam1:",
               write_path_template="",
               root="")
    image = Cpt(ImagePlugin, "image1:")

    def stage(self, *args, **kwargs):
        ret = super().stage(*args, **kwargs)
        return ret

    def unstage(self):
        super().unstage()

    def describe(self):
        return super().describe()

    def trigger(self):
        return super().trigger()

