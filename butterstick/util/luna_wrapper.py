# This file is Copyright (c) 2020 Greg Davill <greg.davill@gmail.com>
# License: BSD

import os
from nmigen import Record, Signal
from nmigen.back import verilog

def luna_wrapper(platform, elaboratable):
    ports = []

    # Patch through all Records/Ports
    for port_name, port in vars(elaboratable).items():
        if not port_name.startswith("_") and isinstance(port, (Signal, Record)):
            ports += port._lhs_signals()

    verilog_text = verilog.convert(elaboratable, name="USBSerialDevice", ports=ports)
    verilog_file = "build/luna_wrapper.USBSerialDevice.v"
    
    vdir = os.path.join(os.getcwd(), "build")
    os.makedirs(vdir, exist_ok=True)

    with open(verilog_file, "w") as f:
        f.write(verilog_text)

    platform.add_source(os.path.join(vdir, "luna_wrapper.USBSerialDevice.v"))