% generate_fhss_bpsk_dataset.m
% Usage example for fhss_bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list, Thop, noise_ratio)

clear; clc; close all;

data_samp_count = 1;                               % number of waveforms to generate
save_path       = fullfile(pwd, 'data_fhss_bpsk'); % output folder for .npy files

% Choose parameters
fs     = 48e3;           % Hz (sample rate)
Tsymb  = 1e-3;           % s  (symbol period) -> sps = fs*Tsymb = 48 samples/symbol
sps    = fs * Tsymb;     % should be integer
Nsym   = 2000;           % symbols per file (Nhops = Nsym / symbols_per_hop must be an integer)
output_len = Nsym * sps; % total samples per file
noise_ratio = 0.1;         % ratio of noise to signal, P_noise / P_signal   (linear)

% FHSS-specific parameters
% Choose distinct carrier frequencies (all < fs/2 to avoid aliasing)
fc_list = [6e3 12e3 18e3];

% Hop every 10 symbols
symbols_per_hop = 10;
Thop            = symbols_per_hop * Tsymb;  % hop duration (s)

% -----------------------
% Generate dataset
% -----------------------
fhss_bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list, Thop, noise_ratio);
fprintf('Generated %d FHSS-BPSK files in: %s\n', data_samp_count, save_path);

% -----------------------
% Quick inspection
% -----------------------
% Load one file (requires readNPY from npy-matlab)
npys = dir(fullfile(save_path, 'fhss_bpsk_*.npy'));

sample_path = fullfile(npys(1).folder, npys(1).name);
x = readNPY(sample_path);        % real passband FHSS-BPSK (column vector)

% Plot a short time snippet
Nplot = round(2e-2 * fs);        % ~30 ms
Nplot = min(Nplot, numel(x));
t_ms  = (0:Nplot-1)/fs * 1e3;    % ms
figure; plot(t_ms, x(1:Nplot));
xlabel('Time (ms)'); ylabel('Amplitude'); grid on;
title(sprintf('FHSS BPSK passband snippet — %s', npys(1).name), 'Interpreter','none');

% Simple spectrum via Welch
figure;
pwelch(x, hamming(4096), 2048, 4096, fs, 'onesided');
title('Welch PSD of FHSS BPSK passband');


% Spectrogram (windows match symbol windows)
figure;
win = hamming(sps);   % sps = 48 samples/symbol
noverlap = 0;
nfft = 4*sps;
x_slice = x(1 : floor(length(x)/10)); % Use only part of the signal
spectrogram(x_slice, win, noverlap, nfft, fs, 'yaxis');
title('Spectrogram of FHSS BPSK passband (symbol-aligned)');
ylabel('Frequency (Hz)');
xlabel('Time (s)');
colorbar;
