# This file is Copyright (c) Greg Davill <greg.davill@gmail.com>
# License: BSD

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

_butterstick_r1d0_io = [
    
    ("clk_in", 0,   Pins("B12"), IOStandard("LVCMOS18")),
    ("leda", 0, Pins("C13"),  IOStandard("LVCMOS33")),
    ("ledc", 0, Pins("T1"),  IOStandard("LVCMOS33")),

     ("usb0", 0,
        Subsignal("data",  Pins("B9 C6 A7 E9 A8 D9 C10 C7")),
        Subsignal("clk",   Pins("B6")),
        Subsignal("dir",   Pins("A6")),
        Subsignal("nxt",   Pins("B8")),
        Subsignal("stp",   Pins("C8")),
        Subsignal("rst",   Pins("C9")),
        IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")
    ),   

    ("vccio_ctrl", 0, 
        Subsignal("pdm", Pins("V1 E11 T2")),
        Subsignal("en", Pins("E12"))
    ),
]

_connectors = [
]


class ButterStickPlatform(LatticePlatform):
    default_clk_name = "clk_sys"
    default_clk_period = 1e9 / 25e6

    def __init__(self, **kwargs):
        LatticePlatform.__init__(self, "LFE5UM5G-85F-8BG381C", _butterstick_r1d0_io, _connectors, toolchain="trellis", **kwargs)
        self.toolchain.build_template[2] += ' --compress'
       
    def do_finalize(self, fragment):
        LatticePlatform.do_finalize(self, fragment)
        
