import os
import subprocess

from nmigen.build import *
from nmigen.vendor.lattice_ecp5 import *
from nmigen_boards.resources import *


__all__ = ["ButterStickPlatform"]



class ButterStickPlatform(LatticeECP5Platform):
    device      = "LFE5UM5G-85F"
    package     = "BG381"
    speed       = 8

    default_clk = "clk30"

    DEFAULT_CLOCK_FREQUENCIES_MHZ = {
        "fast": 240,
        "sync": 120,
        "usb":  60
    }

    
    resources   = [
        Resource("clk30", 0, Pins("B12", dir="i"),
                 Clock(30e6), Attrs(GLOBAL=True, IO_TYPE="LVCMOS33")),

#        *LEDResources(pins="T1 R1 U1", invert=False, attrs=Attrs(IO_TYPE="LVCMOS33")),

        Resource("led", 0, 
            Subsignal("a", Pins("C13 D12 U2 T3 D13 E13 C16", dir="o")),
            Subsignal("c", Pins("T1 R1 U1", dir="o"))
        ),

        Resource("vccio_ctrl", 0, 
            Subsignal("pdm", Pins("V1 E11 T2", dir="o")),
            Subsignal("en", Pins("E12", dir="o"))
        ),

        Resource("usb0", 0,
            Subsignal("data",  Pins("B9 C6 A7 E9 A8 D9 C10 C7",  dir="io")),
            Subsignal("clk",   Pins("B6",    dir="o" )),
            Subsignal("dir",   Pins("A6",    dir="i" )),
            Subsignal("nxt",   Pins("B8",    dir="i" )),
            Subsignal("stp",   Pins("C8",    dir="o" )),
            Subsignal("rst",   PinsN("C9", dir="o" )),
            Attrs(IO_TYPE="LVCMOS18", SLEWRATE="FAST")
        ),

        *ButtonResources(pins="U16 T17", invert=True, attrs=Attrs(IO_TYPE="SSTL135_I", PULLMODE="UP")),

        
    ]
    connectors = [
    ]

    def toolchain_program(self, products, name):
        with products.extract("{}.bit".format(name)) as (bitstream):
            subprocess.check_call(["glasgow", "run", "program-ecp5-sram", "--voltage", "3.3", "-f", "2000", "--pin-tck", "0", "--pin-tms", "3", "--pin-tdi", "1", "--pin-tdo", "2", bitstream])

    def build(self, *args, **kwargs):
        LatticeECP5Platform.build(self, *args, **kwargs)
