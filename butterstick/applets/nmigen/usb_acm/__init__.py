
from nmigen import *
from nmigen.back.pysim import Simulator, Active
from nmigen.back import cxxrtl
from nmigen.test.utils import FHDLTestCase
from nmigen.asserts import *

from .. import Applet

from math import cos, pi


from luna.full_devices import USBSerialDevice
from .car import LunaECP5DomainGenerator

class USBSerialDeviceExample(Elaboratable):
    """ Device that acts as a 'USB-to-serial' loopback using our premade gateware. """

    def elaborate(self, platform):
        m = Module()

        # Generate our domain clocks/resets.
        #m.submodules.car = platform.clock_domain_generator()
        m.submodules.car = LunaECP5DomainGenerator()

        # Create our USB-to-serial converter.
        ulpi = platform.request("usb0")
        m.submodules.usb_serial = usb_serial = \
                USBSerialDevice(bus=ulpi, idVendor=0x16d0, idProduct=0x0f3b, manufacturer_string="GsD", product_string="ButterStick r1.0")

        m.d.comb += [
            # Place the streams into a loopback configuration...
            usb_serial.tx.payload  .eq(usb_serial.rx.payload),
            usb_serial.tx.valid    .eq(usb_serial.rx.valid),
            usb_serial.tx.first    .eq(usb_serial.rx.first),
            usb_serial.tx.last     .eq(usb_serial.rx.last),
            usb_serial.rx.ready    .eq(usb_serial.tx.ready),

            # ... and always connect by default.
            usb_serial.connect     .eq(1)
        ]

        return m

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

class BlinkyApplet(Applet, applet_name="usb_acm"):
    description = "Enumerate HS USB ACM using."
    help = "Enumerate HS USB ACM using."

    def __init__(self, args):
        pass

    def elaborate(self, platform):
        led = platform.request("led", 0)
        btn = platform.request("button", 0)
        vccio_ctrl = platform.request("vccio_ctrl", 0)

        m = Module()

        m.submodules.blinky = Blinky(led, btn)
        m.submodules.vccio_ctrl = VccioCtrl(vccio_ctrl)
        m.submodules.usb = USBSerialDeviceExample()
        

        return m
