from nmigen import Record, Signal, Module, Elaboratable, ClockDomain, ClockSignal, ResetSignal

from nmigen.hdl.rec import DIR_FANIN, DIR_FANOUT, DIR_NONE

from luna.full_devices import USBSerialDevice as LunaDeviceACM
from luna.gateware.architecture.car import PHYResetController


# Create a nmigen module that exposes external interfaces as Signal/Record attributes of the class
class USBSerialDevice(Elaboratable):
    def __init__(self):
        self.ulpi = Record(
            [
                ('data', [('i', 8, DIR_FANIN), ('o', 8, DIR_FANOUT), ('oe', 1, DIR_FANOUT)]),
                ('clk', [('o', 1, DIR_FANOUT)]),
                ('stp', 1, DIR_FANOUT),
                ('nxt', [('i', 1, DIR_FANIN)]),
                ('dir', [('i', 1, DIR_FANIN)]),
                ('rst', 1, DIR_FANOUT)
            ]
        )

        self.usb0 = usb = LunaDeviceACM(bus=self.ulpi, idVendor=0x16d0, idProduct=0x0f3b, 
                manufacturer_string="GsD", product_string="ButterStick r1.0")
        
        self.rx = Record(usb.rx.layout)
        self.tx = Record(usb.tx.layout)
            
        self.clk_sync = Signal()
        self.clk_usb = Signal()
        self.rst_sync = Signal()

        self.usb_holdoff  = Signal()
        ...

    def elaborate(self, platform):
        m = Module()

        # Create our clock domains.
        m.domains.sync = ClockDomain()
        m.domains.usb  = ClockDomain()
        m.submodules.usb_reset = controller = PHYResetController()
        m.d.comb += [
            ResetSignal("usb")  .eq(controller.phy_reset),
            self.usb_holdoff    .eq(controller.phy_stop)
        ]
        
        # Attach Clock domains
        m.d.comb += [
            ClockSignal(domain="sync")     .eq(self.clk_sync),
            ClockSignal(domain="usb")      .eq(self.clk_usb),
            ResetSignal("sync").eq(self.rst_sync),
        ]
        
        # Attach usb module
        m.submodules.usb0 = self.usb0

        m.d.comb += [
            # Wire up streams
            self.usb0.tx.valid    .eq(self.tx.valid),
            self.usb0.tx.first    .eq(self.tx.first),
            self.usb0.tx.last     .eq(self.tx.last),
            self.usb0.tx.payload  .eq(self.tx.payload),
            # --
            
            self.tx.ready    .eq(self.usb0.tx.ready),


            self.rx.valid    .eq(self.usb0.rx.valid),
            self.rx.first    .eq(self.usb0.rx.first),
            self.rx.last     .eq(self.usb0.rx.last),
            self.rx.payload  .eq(self.usb0.rx.payload),
            # --
            self.usb0.rx.ready    .eq(self.rx.ready),
        
            # ... and always connect by default.
            self.usb0.connect     .eq(1)
        ]
        return m