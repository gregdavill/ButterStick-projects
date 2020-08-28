
class AppletBase():
    all = {}

    help = "applet help missing"
    description = "applet description missing"
    


from .nmigen import blinky
from .nmigen import usb_acm

from .litex import litex_blinky
from .litex import litex_luna