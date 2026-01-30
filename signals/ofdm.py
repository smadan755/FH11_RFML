import numpy as np
from specs import SignalSpec, Waveform
from channel_effects import normalize_power

def generate_ofdm(spec: SignalSpec) -> Waveform:
    p = spec.params or {}
    nfft = int(p.get("nfft", 64))
    ncp  = int(p.get("ncp", 16))
    nused = int(p.get("nused", 48))
    mod = p.get("mod", "QPSK")  # "QPSK" or "16QAM"
    rng = np.random.default_rng(spec.seed)

    # number of OFDM symbols to fill spec.n samples
    sym_len = nfft + ncp
    n_syms = int(np.ceil(spec.n / sym_len))

    def qpsk_syms(m):
        b = rng.integers(0, 2, size=(2*m,))
        I = 2*b[0::2]-1
        Q = 2*b[1::2]-1
        return (I + 1j*Q)/np.sqrt(2), b

    def qam16_syms(m):
        # simple 16QAM constellation levels {-3,-1,1,3}
        b = rng.integers(0,2,size=(4*m,))
        # pack 2 bits -> I, 2 bits -> Q (binary mapping MVP)
        def bits2level(bb0, bb1):
            val = bb0*2 + bb1
            levels = np.array([-3,-1, 3, 1], dtype=np.float32)  # quick mapping
            return levels[val]
        I = bits2level(b[0::4], b[1::4])
        Q = bits2level(b[2::4], b[3::4])
        s = (I + 1j*Q)
        s = s/np.sqrt(np.mean(np.abs(s)**2))
        return s, b

    out = []
    all_bits = []

    # choose used subcarriers around DC with guard bands
    # typical: avoid DC bin, use symmetric bins
    half = nused//2
    used_bins = np.r_[np.arange(-half,0), np.arange(1,half+1)]  # excludes DC
    used_bins = (used_bins % nfft).astype(int)

    for _ in range(n_syms):
        X = np.zeros(nfft, dtype=np.complex64)

        if mod == "QPSK":
            s, b = qpsk_syms(nused)
        else:
            s, b = qam16_syms(nused)

        X[used_bins] = s
        x = np.fft.ifft(X)
        x_cp = np.r_[x[-ncp:], x]  # cyclic prefix
        out.append(x_cp)
        all_bits.append(b)

    x = np.concatenate(out)[:spec.n].astype(np.complex64)
    x = normalize_power(x)

    return Waveform(
        x=x,
        bits=np.concatenate(all_bits).astype(np.int8),
        meta={"label": "OFDM", "nfft": nfft, "ncp": ncp, "nused": nused, "mod": mod}
    )
