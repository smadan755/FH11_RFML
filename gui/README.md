## Features

- **Parameter Control Panel**: Configure waveform parameters including:

  - Waveform type (PAM, QAM, FM)
  - Sample rate (fs)
  - Symbol period (Tsymb)
  - Carrier frequency (fc)
  - Modulation order (M)
  - Variance (Var)
  - Number of symbols (Nsymb)

- **Multi-Domain Visualization** with tabbed interface:

  - **Time Domain**: View the modulated waveform over time
  - **Frequency Domain**: FFT spectrum analysis showing frequency components
  - **IQ Constellation**: For QAM signals, displays the demodulated constellation diagram
    - Includes proper I/Q demodulation with carrier recovery
    - Low-pass filtering to remove high-frequency components
    - Symbol-rate downsampling for clean constellation display

- **Interactive Plotting**: Real-time matplotlib visualization with:

  - Zoom and pan controls
  - Export to image
  - Grid display
  - Navigation toolbar on each plot

- **Signal Processing**:
  - Uses MATLAB engine for waveform generation
  - Python-based I/Q demodulation using scipy Butterworth filters
  - FFT analysis for frequency domain representation

### Running the GUI

#### Prerequisites

Install required Python packages:

```powershell
pip install PySide6 matplotlib numpy scipy
```

Make sure MATLAB Engine for Python is installed (see installation section above).

#### Launch the GUI

```powershell
python gui/main_window.py
```

The GUI will:

1. Automatically start a MATLAB engine session
2. Load the waveform generation functions from `gui/waveform_functions/`
3. Display a parameter input panel and interactive plot window

#### Using the GUI

1. Select your desired waveform type from the dropdown (PAM, QAM, FM)
2. Adjust parameters using the input fields (default values are pre-populated)
3. Click "Run" to generate the waveform
4. View results in three different tabs:
   - **Time Domain**: See the modulated signal amplitude over time
   - **Frequency Domain**: Analyze the spectrum using FFT
   - **IQ Plot**: For QAM signals, view the constellation diagram with properly demodulated symbols
5. Use the matplotlib toolbar on each plot to zoom, pan, or save the visualization

**Note:** The GUI uses modified MATLAB functions from `gui/waveform_functions/` that return waveform data instead of saving to disk. The IQ demodulation for QAM signals is performed using Python/scipy with Butterworth low-pass filtering.

## Prerequisites

- Windows (tested on Windows 10/11)
- MATLAB R2025b (or matching release — see notes below)
- Python 3.11 (your environment may vary)
- Git (to clone helper libraries)
- **For GUI:** PySide6, matplotlib, numpy, scipy (see GUI section for installation)
