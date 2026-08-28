#!/bin/sh
# Bundle the project for transfer to the Windows laptop.
cd "$(dirname "$0")/.." || exit 1
rm -f gan-driver-prototype.zip
zip -qr gan-driver-prototype.zip \
    README.md models sim scripts ltspice results pdk \
    -x 'results/*.dat' -x '**/__pycache__/*' -x 'sim/out.dat'
ls -lh gan-driver-prototype.zip
