from nmigen import *
from .. import AppletBase

class Applet(Elaboratable, AppletBase):
    # Applet may override these and add arguments to the parser
    @classmethod
    def add_build_arguments(cls, parser):
        pass

    @classmethod
    def add_run_arguments(cls, parser):
        pass

    @classmethod
    def add_test_arguments(cls, parser):
        pass

    def __init_subclass__(cls, applet_name, **kwargs):
        super().__init_subclass__(**kwargs)

        if applet_name in cls.all:
            raise ValueError("Applet {!r} already exists".format(applet_name))

        cls.all[applet_name] = cls
        cls.applet_name = applet_name

    async def run(self):
        pass

from .blinky import Blinky
from .usb_acm import BlinkyApplet