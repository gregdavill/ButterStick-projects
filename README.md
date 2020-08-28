# ButterStick projects
> Project structure based off [Pergola projects](https://github.com/kbeckmann/pergola_projects) from kbechmann
 
 ---

[ButterStick](https://github.com/gregdavill/ButterStick) is an ECP5 FPGA development board featuring SYZYGY expansion connectors, These projects target the r1.0 version of the board.

These are my personal projects that run on ButterStick. They are unsupported, probably full of bugs and most likely doing some things incorrectly.

Verilog projects are located in `verilog`. Change working directory to a project and type `make` to build, `make prog` to build and program.

nMigen/Litex projects are in `butterstick`. To explore the cli, remain in this directory and run `python -m butterstick --help` and read the docs for more help. Running blinky is done like so `python -m butterstick run blinky`.

Run tests and proofs with `python -m unittest -v`.