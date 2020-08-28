from nmigen import *
from nmigen.back.pysim import Simulator, Active
from nmigen.back import cxxrtl
from nmigen.test.utils import FHDLTestCase
from nmigen.asserts import *

from .. import Applet

from math import cos, pi

class VccioCtrl(Elaboratable):
    def __init__(self, vccio_pins):
        self.vccio_pins = vccio_pins
        
    def elaborate(self, platform):
        m = Module()

        pwm_timer = Signal(14)

        m.d.sync += pwm_timer.eq(pwm_timer + 1)

        m.d.comb += self.vccio_pins.pdm[0].eq(pwm_timer < int(2**14 * (0.1)))
        m.d.comb += self.vccio_pins.pdm[1].eq(pwm_timer < int(2**14 * (0.1)))
        m.d.comb += self.vccio_pins.pdm[2].eq(pwm_timer < int(2**14 * (0.70)))

        m.d.comb += self.vccio_pins.en.eq(1)

        return m


class Blinky(Elaboratable):
    def __init__(self, led, btn, timer_width=30):
        self.led = led.a
        self.ledc = led.c
        self.btn = btn
        self.timer_width = timer_width

    def elaborate(self, platform):
        m = Module()

        self.timer = timer = Signal(self.timer_width)

        led_multiplex = Signal(2)
        led_multiplex_timer = Signal(12)


        mem_init = [int(max(1024 + 2048*cos(i/256 * 2*pi), 0)) for i in range(256)]
        mem = Memory(width=12, depth=256, init=mem_init)
        m.submodules.read = read = mem.read_port()

        m.d.sync += [
            led_multiplex_timer.eq(led_multiplex_timer + 1),
            timer.eq(timer + 1)
        ]

        with m.If(led_multiplex_timer == 0):
            with m.If(led_multiplex < 2):
                m.d.sync += led_multiplex.eq(led_multiplex + 1)
            with m.Else():
                m.d.sync += led_multiplex.eq(0)

        val = Signal()


        led_values = Array([Signal(12, name=f'led{j}_value') for j in range(7)])
        
        led_idx = Signal(8)

        m.d.sync += [
            led_idx.eq(led_multiplex_timer)
        ]
        
        m.d.sync += [
            read.addr.eq(0)
        ]
        with m.If((led_multiplex_timer >= 1) & (led_multiplex_timer < 8)):
            m.d.sync += read.addr.eq((timer[19:27] + (led_multiplex * 64) + (led_multiplex * 16) + (led_multiplex_timer*8)) & 0xFF),
            
        with m.If((led_multiplex_timer >= 3) & (led_multiplex_timer < 10)):
            m.d.sync += led_values[led_multiplex_timer-3].eq(read.data)
            with m.If(led_multiplex == 0):
                m.d.sync += led_values[led_multiplex_timer-3].eq(read.data >> 1)
            with m.If(led_multiplex == 2):
                m.d.sync += led_values[led_multiplex_timer-3].eq(read.data >> 2)

        for i in range(len(self.led)):
            m.d.comb += self.led[i].eq(led_values[i] > led_multiplex_timer)

        m.d.comb += self.ledc.eq(1 << led_multiplex)

        return m


class BlinkyTest(FHDLTestCase):
    def test_blinky(self):
        btn = Signal()
        led = Record([
            ('a', 7),
            ('c', 3)
        ])
        #m = Module()
        m = blinky = Blinky(led, btn)

        sim = Simulator(m)
        sim.add_clock(1e-6)
        def process():
            yield Active()
            for _ in range(32):
                yield

        sim.add_sync_process(process)
        with sim.write_vcd("blinky.vcd"):
            sim.run()


class BlinkyApplet(Applet, applet_name="blinky"):
    description = "Blinks some LEDs"
    help = "Blinks some LEDs"

    def __init__(self, args):
        pass

    def elaborate(self, platform):
        led = platform.request("led", 0)
        btn = platform.request("button", 0)
        vccio_ctrl = platform.request("vccio_ctrl", 0)

        m = Module()

        m.submodules.blinky = Blinky(led, btn)
        m.submodules.vccio_ctrl = VccioCtrl(vccio_ctrl)
        

        return m
