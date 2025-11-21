# FH11_RFML

Project Repo for Faculty Honors team FH11: Spectrum Sensing and Signal Classification using Deep Neural Networks

## Contents

- `bpsk.m`, `pam.m`, `mqam.m`, `fhss_bpsk.m`, `fhss_bpsk.m` - MATLAB functions that generate modulated signals and save them to `.npy` files
- `gui/main_window.py` - Interactive Qt GUI application for waveform generation and visualization
- `gui/waveform_functions/` - Modified MATLAB functions that return waveforms for real-time plotting
- `examples/interactive_test.ipynb` - interactive notebook that calls `bpsk()` via the MATLAB Engine
- `test_wav.ipynb` - example notebook demonstrating basic MATLAB Engine usage
- `data_bpsk/`, `data_pam/` - generated example data (NumPy .npy files)

## Overview

This repository demonstrates how to:

- Start and control a MATLAB session from Python using the MATLAB Engine for Python
- Transfer data between NumPy and MATLAB
- Use MATLAB toolboxes (e.g., signal processing) from Python
- Save MATLAB arrays to NumPy `.npy` files from MATLAB using the `npy-matlab` helper
- **NEW:** Generate and visualize RF waveforms in real-time using a Qt-based GUI

## GUI Application

The repository includes an interactive GUI application (`gui/main_window.py`) for generating and visualizing RF modulation waveforms. See the gui/ folder for more details

#### Configure Python enviroment variables

Copy and paste the .env.example into a new .env file, and then replace the ROOT variable with the (FH11) repository's root directory on your computer.

## Install MATLAB Engine for Python

The MATLAB Engine Python package must match your MATLAB release series. For R2025b (MATLAB version 25.2.x) install the matching engine. Example (PowerShell):

```powershell
# Example: install engine matching MATLAB R2025b (25.2.x)
& "C:\Python311\python.exe" -m pip install --user "matlabengine==25.2.2"
```

If you previously tried to install a different engine (e.g., 26.1.1) you may see an error similar to:

> No compatible MATLAB installation found in Windows Registry. This release of MATLAB Engine API for Python is compatible with version X.Y. The found versions were A.B.

In that case pick the engine version that matches your MATLAB release, or install the MATLAB release that matches the engine.

## Install npy-matlab (writeNPY/readNPY)

The MATLAB functions in this repo call `writeNPY()` to save `.npy` files from MATLAB. MATLAB doesn't include `writeNPY` by default — use the `npy-matlab` project.

Clone it into the repo:

```powershell
cd C:\Users\madan\FH11_RFML
git clone https://github.com/kwikteam/npy-matlab.git
```

Then add it to MATLAB's path in your Python notebook (example already in `examples/interactive_test.ipynb`):

```python
# from your Python session
eng.addpath(r'c:\Users\madan\FH11_RFML\npy-matlab', nargout=0)
```

Alternatively, add the cloned folder to your MATLAB path permanently using `pathtool` or `addpath` in your MATLAB startup script.

## Running the examples

1. Start MATLAB Engine from Python (in a notebook or script):

```python
import matlab.engine
eng = matlab.engine.start_matlab()
print('MATLAB engine started!')
```

2. Make sure the repository and `npy-matlab` are on MATLAB's path:

```python
eng.addpath(r'c:\Users\madan\FH11_RFML', nargout=0)
eng.addpath(r'c:\Users\madan\FH11_RFML\npy-matlab', nargout=0)
```

3. Call the `bpsk()` generator (note this function does not return values — it writes files to disk):

```python
# bpsk() writes .npy files to disk; it does not return outputs
eng.bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc, nargout=0)
```

4. Example notebooks to open and run:

- `examples/interactive_test.ipynb` — runs `bpsk()` and demonstrates PSD extraction
- `test_wav.ipynb` — notebooks with MATLAB Engine demo code

## Important Gotchas / Troubleshooting

- "Too many output arguments":

  - Cause: You called a MATLAB function from Python expecting a return value but the MATLAB function is defined with no outputs.
  - Fix: Call the function with `nargout=0` from Python (e.g., `eng.bpsk(..., nargout=0)`).
  - **Note:** There are two versions of some functions (e.g., `pam.m`): root versions save to disk (no outputs), while `gui/waveform_functions/` versions return data for plotting. Make sure the correct path is added to MATLAB when using the GUI.

- "Undefined function 'writeNPY'":

  - Cause: `writeNPY()` is provided by the `npy-matlab` project, not by MATLAB core.
  - Fix: Clone `npy-matlab` and add it to the MATLAB path as described above.

- MATLAB Engine version mismatch:
  - The pip package name must match your MATLAB release. If pip install fails with a message about registry-found versions, install the engine that corresponds to your MATLAB release (or install a matching MATLAB release).

## Recommended workflow

- Use Python for orchestration, ML code, and visualization (NumPy, matplotlib, PyTorch/TensorFlow).
- Use MATLAB for DSP-heavy routines or toolbox-specific functions.
- Move arrays with `matlab.double()` (from Python NumPy -> MATLAB) and read results back with `np.array(eng.workspace['var'])`.

## Quick tests to verify setup

In a Python REPL or notebook cell:

```python
import matlab.engine
import numpy as np
eng = matlab.engine.start_matlab()
eng.addpath(r'c:\Users\madan\FH11_RFML\npy-matlab', nargout=0)

# test saving and loading using MATLAB helper
arr = np.arange(10).astype(float)
mat_arr = matlab.double(arr.tolist())
eng.workspace['arr'] = mat_arr
eng.eval("writeNPY(arr, fullfile(pwd, 'test_arr.npy'));", nargout=0)
# Back in Python, verify the file exists or read it with numpy
import os
print(os.path.exists(r'c:\Users\madan\FH11_RFML\test_arr.npy'))
```

If the file is created successfully, `npy-matlab` is working.

## Where to go next

- **Try the GUI:** Run `python gui/main_window.py` to experiment with real-time waveform generation and visualization
- Clone `npy-matlab` (if not done) and re-run the example notebooks
- Customize waveform parameters in the GUI or notebooks to see different modulation schemes
- If you want `bpsk()` to also return the generated vector to Python (instead of only saving), update `bpsk.m` to include an output argument and return `bpsk_pb`

## License

This README and repository are provided as-is for demo/learning purposes. Check toolbox/license constraints for MATLAB code if you plan to reuse in other projects.

## Attribution

**Software Receiver Design (SRD) Code**

The `tools/SRD/` directory contains MATLAB code examples from the book "Software Receiver Design" by C. Richard Johnson, Jr. and William A. Sethares. These files are used for educational purposes as reference implementations for signal processing and receiver design concepts.

- Book: "Software Receiver Design: Build Your Own Digital Communication System in Five Easy Steps"
- Authors: C. Richard Johnson, Jr. and William A. Sethares
- Original code repository: [(https://github.com/gopmc/SRD)]
- Used under educational/research purposes

If you use this code in your own projects, please cite the original authors and their work appropriately.
