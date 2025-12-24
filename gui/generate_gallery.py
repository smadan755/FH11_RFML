"""
RF Waveform Gallery Generator

Generates a gallery image showcasing randomized RF signals from different
modulation types, demonstrating the dataset generation pipeline's capabilities.
"""

import numpy as np
import matplotlib.pyplot as plt
import matlab.engine
import os
import random

def generate_gallery(rows=3, cols=3, save_path=None, show=True):
    """
    Generate a gallery of random RF waveforms.
    
    Args:
        rows: Number of rows in the gallery
        cols: Number of columns in the gallery
        save_path: Path to save the image (optional)
        show: Whether to display the plot
    
    Returns:
        Figure object
    """
    print("Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    
    # Add waveform functions path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    waveform_functions_path = os.path.join(current_dir, "waveform_functions")
    eng.addpath(waveform_functions_path, nargout=0)
    
    # Modulation types and their valid M values
    modulations = {
        'PAM': [2, 4, 8, 16],
        'QAM': [4, 16, 64, 256],
        'PSK': [2, 4, 8, 16],
        'FSK': [2, 4, 8],
        'FHSS': [4, 8, 16, 32]
    }
    
    # Parameter ranges for randomization
    fs_options = [48000, 96000]
    fc_range = (4000, 12000)  # Hz
    tsymb_range = (0.0005, 0.002)  # seconds
    nsymb = 512  # Fixed for consistent display length
    alpha_range = (0.2, 0.5)
    
    # Create figure
    fig, axes = plt.subplots(rows, cols, figsize=(12, 8))
    fig.suptitle('RF Waveform Gallery - Randomized Dataset Samples', fontsize=14, fontweight='bold')
    
    # Flatten axes for easy iteration
    axes_flat = axes.flatten()
    
    total_plots = rows * cols
    
    for i in range(total_plots):
        ax = axes_flat[i]
        
        # Randomly select modulation type
        mod_type = random.choice(list(modulations.keys()))
        M = random.choice(modulations[mod_type])
        
        # Randomize parameters
        fs = random.choice(fs_options)
        fc = random.randint(fc_range[0], fc_range[1])
        tsymb = random.uniform(tsymb_range[0], tsymb_range[1])
        
        # Ensure fs*Tsymb is an integer (required constraint)
        sps = round(fs * tsymb)
        tsymb = sps / fs
        
        # Ensure fc < fs/2 (Nyquist)
        fc = min(fc, int(fs / 2 * 0.8))
        
        alpha = random.uniform(alpha_range[0], alpha_range[1])
        
        # Calculate output length
        output_len = sps * nsymb
        
        # Choose pulse shape (rect for FSK/FHSS, random for others)
        if mod_type in ['FSK', 'FHSS']:
            pulse_shape = 'rect'
        else:
            pulse_shape = random.choice(['rrc'])
        
        try:
            print(f"Generating {mod_type}-{M} (fc={fc}Hz, fs={fs}Hz)...")
            
            # Generate waveform using MATLAB
            data = eng.waveform_generator(
                float(output_len),
                float(fs),
                float(tsymb),
                float(fc),
                float(M),
                mod_type,
                'alpha', float(alpha),
                'span', 8.0,
                'pulse_shape', pulse_shape,
                nargout=1
            )
            
            data = np.array(data).flatten()
            
            # Create time vector
            t = np.arange(len(data)) / fs
            
            # Zoom in to show ~10-20 symbol periods for visibility
            # This makes the waveform structure clearly visible
            num_symbols_to_show = 15
            samples_to_show = min(sps * num_symbols_to_show, len(data))
            
            # Start from a random position (but not too close to edges)
            max_start = max(0, len(data) - samples_to_show - 100)
            if max_start > 0:
                start_idx = random.randint(100, max_start)
            else:
                start_idx = 0
            end_idx = start_idx + samples_to_show
            
            # Plot zoomed waveform
            t_zoom = t[start_idx:end_idx] * 1000  # Convert to ms
            data_zoom = data[start_idx:end_idx]
            
            ax.plot(t_zoom, data_zoom, color='#1f77b4', linewidth=0.8)
            ax.set_xlim(t_zoom[0], t_zoom[-1])
            
            # Clean minimal style
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(True)
            ax.spines['right'].set_visible(True)
            ax.spines['bottom'].set_visible(True)
            ax.spines['left'].set_visible(True)
            
            # Add label
            label = f"{mod_type}-{M}"
            ax.set_title(label, fontsize=10, pad=2)
            
        except Exception as e:
            print(f"Error generating {mod_type}-{M}: {e}")
            ax.text(0.5, 0.5, f"Error\n{mod_type}-{M}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Gallery saved to: {save_path}")
    
    if show:
        plt.show()
    
    # Cleanup
    eng.quit()
    
    return fig


def generate_modulation_showcase(save_path=None, show=True):
    """
    Generate a gallery showing one example of each modulation type.
    """
    print("Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    
    # Add waveform functions path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    waveform_functions_path = os.path.join(current_dir, "waveform_functions")
    eng.addpath(waveform_functions_path, nargout=0)
    
    # One of each modulation type with representative M values
    showcase = [
        ('PAM', 4),
        ('QAM', 16),
        ('PSK', 8),
        ('FSK', 4),
        ('FHSS', 8),
    ]
    
    # Fixed parameters for consistency
    fs = 48000
    fc = 6000
    tsymb = 0.001
    nsymb = 512
    sps = int(fs * tsymb)
    output_len = sps * nsymb
    
    # Create figure - 1 row, 5 columns
    fig, axes = plt.subplots(1, 5, figsize=(15, 3))
    fig.suptitle('Modulation Types Overview', fontsize=14, fontweight='bold')
    
    for i, (mod_type, M) in enumerate(showcase):
        ax = axes[i]
        
        pulse_shape = 'rect' if mod_type in ['FSK', 'FHSS'] else 'rrc'
        
        try:
            print(f"Generating {mod_type}-{M}...")
            
            data = eng.waveform_generator(
                float(output_len),
                float(fs),
                float(tsymb),
                float(fc),
                float(M),
                mod_type,
                'alpha', 0.35,
                'span', 8.0,
                'pulse_shape', pulse_shape,
                nargout=1
            )
            
            data = np.array(data).flatten()
            t = np.arange(len(data)) / fs
            
            # Zoom in to show ~15 symbol periods
            num_symbols_to_show = 15
            samples_to_show = min(sps * num_symbols_to_show, len(data))
            start_idx = 100  # Skip transients
            end_idx = start_idx + samples_to_show
            
            t_zoom = t[start_idx:end_idx] * 1000
            data_zoom = data[start_idx:end_idx]
            
            ax.plot(t_zoom, data_zoom, color='#1f77b4', linewidth=0.8)
            ax.set_xlim(t_zoom[0], t_zoom[-1])
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{mod_type}-{M}", fontsize=11, fontweight='bold')
            
            for spine in ax.spines.values():
                spine.set_linewidth(1.5)
                
        except Exception as e:
            print(f"Error: {e}")
            ax.text(0.5, 0.5, f"Error", ha='center', va='center')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"Showcase saved to: {save_path}")
    
    if show:
        plt.show()
    
    eng.quit()
    return fig


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate RF waveform gallery images')
    parser.add_argument('--rows', type=int, default=3, help='Number of rows')
    parser.add_argument('--cols', type=int, default=3, help='Number of columns')
    parser.add_argument('--output', '-o', type=str, default=None, 
                       help='Output file path (e.g., gallery.png)')
    parser.add_argument('--showcase', action='store_true',
                       help='Generate modulation type showcase instead of random gallery')
    parser.add_argument('--no-show', action='store_true',
                       help='Do not display the plot (useful for batch generation)')
    
    args = parser.parse_args()
    
    if args.showcase:
        generate_modulation_showcase(save_path=args.output, show=not args.no_show)
    else:
        generate_gallery(rows=args.rows, cols=args.cols, 
                        save_path=args.output, show=not args.no_show)
