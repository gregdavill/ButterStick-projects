#!/usr/bin/env python3

# This file is Copyright (c) Greg Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from .. import Applet


from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.cores.clock import *

class CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()

        clk = platform.request("clk_in")

        platform.add_period_constraint(clk, 1e9/30e6)

        # pll
        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk, 30e6)
        pll.create_clkout(self.cd_sys, 60e6)

        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll.locked)

class SoCApplet(Applet, applet_name="litex.blinky"):
    def __init__(self, args, platform):
        self.submodules.crg = CRG(platform)

        counter = Signal(24)

        self.sync += [
            counter.eq(counter + 1)
        ]

        self.comb += [
            platform.request("leda").eq(1),
            platform.request("ledc").eq(counter[-1])
        ]
        