Each file here is one step of the live demo. They can be run on their own:

    zsh 01-ngspice-crosstalk.sh

or all in order, with a pause between each:

    cd .. && zsh RUN-LIVE.sh

01  the crosstalk fault and the fix, simulated in ngspice          ~2 s
02  a stored data row re-simulated live, and compared              ~1 s
03  the Verilog controller compiled and run, 8 properties          ~2 s
04  the same test against a deliberately broken version            ~4 s
05  the MATLAB analysis re-run in GNU Octave                       ~20 s
06  Result 2 -- what re-tuning is worth (5.2 %)                    ~3 s
07  Result 3 -- the 25.1 % / 3.9 % split                           ~5 s
08  Result 4 -- board inductance decides it                        ~3 s
09  the waveforms, plotted on screen from a live ngspice run       ~3 s
10  the converter: 100 V DC in, 48.6 V DC out, 97.6 %% efficient    ~5 s
11  named cases, one ngspice run each, with what came out          ~10 s
12  the same circuit drawn in LTspice (see 12-ltspice-schematic.txt)
13  ngspice on screen: what it solved, and what the answer means    ~5 s
