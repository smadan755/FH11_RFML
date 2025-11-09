import matlab.engine
import numpy as np
import matplotlib.pyplot as plt


eng = matlab.engine.start_matlab()

print("matlab engine started")


eng.addpath(f"C:\\Users\\madan\\FH11_RFML\\gui\\waveform_functions", nargout=0)

def main():
    fs = 48e3
    Tsymb = 1e-3
    fc = 20e3
    M = 4.0
    Var = 1.0

    sps = fs*Tsymb  
    Nsymb = 2048

    output_len = Nsymb*sps 
    
    data = eng.mqam_gui(output_len, fs, Tsymb, fc, M)
    data = np.array(data).flatten()

    T = len(data)/fs

    t = np.linspace(0,T,len(data))
    

    
    
    freqs, ft = eng.plotspec_gui(data, 1/fs, nargout = 2)
    freqs = np.array(freqs).flatten()
    ft = np.array(ft).flatten()
    
    
    
        
    plt.figure(figsize=(12,6))
    plt.plot(t,data)
    plt.grid(True)
    plt.xlabel("Seconds")
    plt.ylabel("Amplitude")
    plt.xlim([0,0.0425])
    
    
    plt.figure(figsize=(12,6))
    plt.plot(freqs, np.abs(ft))
    plt.grid(True)
    plt.show()
    
if __name__ == "__main__":
    main()