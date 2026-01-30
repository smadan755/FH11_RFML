import numpy as np
import matplotlib.pyplot as plt

def quick_plot(x: np.ndarray, fs: float, title=""):
    # time
    plt.figure()
    plt.plot(np.real(x[:400]))
    plt.title("Time (Real) " + title)
    plt.show()

    # IQ
    plt.figure()
    plt.scatter(np.real(x[::10]), np.imag(x[::10]), s=2)
    plt.title("IQ " + title)
    plt.axis("equal")
    plt.show()

    # PSD (rough)
    X = np.fft.fftshift(np.fft.fft(x))
    f = np.linspace(-fs/2, fs/2, len(x))
    plt.figure()
    plt.plot(f/1e6, 20*np.log10(np.abs(X)+1e-12))
    plt.title("FFT mag " + title)
    plt.xlabel("MHz")
    plt.show()
