import numpy as np
# Specs are above current gen_single.py in the project structure
from specs import SignalSpec, ChannelSpec, MixSpec  # use relative import to go up one directory

from dataset_orchestration import generate_one
from visualization import quick_plot  # see below

fs = 10e6
n = 4096

signal_specs = [
    SignalSpec(name="OFDM", fs=fs, n=n, seed=0, params={"nfft":64, "ncp":16, "nused":48, "mod":"QPSK"})
]
channel = ChannelSpec(snr_db=10.0, cfo_hz=2000.0, multipath_taps=None)
mix = MixSpec(k=1)

x, meta = generate_one(0, fs, n, signal_specs, channel, mix)
print(meta)
quick_plot(x, fs, title=str(meta["signals"][0]))
