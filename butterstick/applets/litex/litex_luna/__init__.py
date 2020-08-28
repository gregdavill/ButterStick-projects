#!/usr/bin/env python3

# This file is Copyright (c) Greg Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from .. import Applet

from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.cores.clock import *

from ....util.luna_wrapper import luna_wrapper
from .usb_serial import USBSerialDevice

from litex.soc.interconnect.stream import Endpoint

class CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_usb = ClockDomain()
        self.clock_domains.cd_sys = ClockDomain()

        clk = platform.request("clk_in")

        platform.add_period_constraint(clk, period_ns(30e6))
        platform.add_period_constraint(self.cd_sys.clk, period_ns(60e6))
        platform.add_period_constraint(self.cd_usb.clk, period_ns(60e6))

        # pll
        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk, 30e6)
        pll.create_clkout(self.cd_sys, 60e6)
        pll.create_clkout(self.cd_usb, 60e6)

        self.comb += self.cd_sys.rst.eq(~pll.locked)
        self.comb += self.cd_usb.rst.eq(~pll.locked)
        #self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll.locked)
        

# BaseSoC ------------------------------------------------------------------------------------------



class SoCApplet(Applet, applet_name="litex.luna"):
    def __init__(self, args, platform):
        self.submodules.crg = CRG(platform)

        counter = Signal(24)

        ulpi_pads = platform.request("usb0")
        ulpi_data = TSTriple(8)
        reset = Signal()
        self.comb += ulpi_pads.rst.eq(~reset)
        luna_wrapper(platform, USBSerialDevice())

        usb_tx = Endpoint([("data", 8)])
        usb_rx = Endpoint([("data", 8)])

        self.specials += ulpi_data.get_tristate(ulpi_pads.data)

        self.params = dict(
            # Clock / Reset
            i_clk_usb   = ClockSignal("usb"),
            i_clk_sync   = ClockSignal("sys"),
            i_rst_sync   = ResetSignal(),

            o_ulpi__data__o = ulpi_data.o,
            o_ulpi__data__oe = ulpi_data.oe,
            i_ulpi__data__i = ulpi_data.i,
            o_ulpi__clk__o = ulpi_pads.clk,
            o_ulpi__stp = ulpi_pads.stp,
            i_ulpi__nxt__i = ulpi_pads.nxt,
            i_ulpi__dir__i = ulpi_pads.dir,
            o_ulpi__rst = reset, 

            # Tx stream (Data out to computer)
            o_tx__ready = usb_tx.ready,
            i_tx__valid = usb_tx.valid,
            i_tx__first = usb_tx.first,
            i_tx__last = usb_tx.last,
            i_tx__payload = usb_tx.data,
            
            # Rx Stream (Data in from a Computer)
            i_rx__ready = usb_rx.ready,
            o_rx__valid = usb_rx.valid,
            o_rx__first = usb_rx.first,
            o_rx__last = usb_rx.last,
            o_rx__payload = usb_rx.data,
        )


        # Loopback toggle case
        self.comb += [
            # Litex ordering when connecting streams:
            #  [Source] -> connect -> [Sink]
            usb_rx.connect(usb_tx),

            # If we have [A-Za-z] toggle case
            If(((usb_rx.data >= ord('A')) & (usb_rx.data <= ord('Z'))) | ((usb_rx.data >= ord('a')) & (usb_rx.data <= ord('z'))),
                usb_tx.data.eq(usb_rx.data ^ 0x20)
            )
        ]


        # ButterStick r1.0 requires 
        # VccIO set on port 2 before ULPI signals work.
        vccio_pins = platform.request("vccio_ctrl")
        pwm_timer = Signal(14)
        self.sync += pwm_timer.eq(pwm_timer + 1)
        self.comb += [
            vccio_pins.pdm[0].eq(pwm_timer < int(2**14 * (0.1))),  # 3.3v
            vccio_pins.pdm[1].eq(pwm_timer < int(2**14 * (0.1))),  # 3.3v
            vccio_pins.pdm[2].eq(pwm_timer < int(2**14 * (0.70))), # 1.8v
            vccio_pins.en.eq(1),
        ]

        self.sync += [
            counter.eq(counter + 1)
        ]

        self.comb += [
            platform.request("leda").eq(1),
            platform.request("ledc").eq(counter[23])
        ]
        
    def do_finalize(self):
        self.specials += Instance("USBSerialDevice",
            **self.params
        )