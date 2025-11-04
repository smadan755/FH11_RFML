% generate_bpsk_dataset.m
% Usage example for bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc)

clear; clc; close all;


data_samp_count = 1;                          % number of waveforms to generate
save_path       = fullfile(pwd, 'data_bpsk');  % output folder for .npy files

% Choose parameters so constraints hold:
fs     = 48e3;          % Hz (sample rate)
Tsymb  = 1e-3;          % s  (symbol period) -> sps = fs*Tsymb = 48 samples/symbol
sps    = fs*Tsymb;      % should be integer
Nsym   = 2048;          % symbols per file
output_len = Nsym * sps; % total samples per file

fc = 6e3;               % Hz (carrier); must be < fs/2 to avoid aliasing


% -----------------------
% Generate dataset
% -----------------------
bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc);
fprintf('Generated %d files in: %s\n', data_samp_count, save_path);

% -----------------------
% Quick inspection
% -----------------------
% Load one file (requires readNPY from npy-matlab)
npys = dir(fullfile(save_path, 'bpsk_*.npy'));

sample_path = fullfile(npys(1).folder, npys(1).name);
x = readNPY(sample_path);      % real passband BPSK (column vector)

% Plot a short time snippet
Nplot = round(3e-3 * fs);      % ~3 ms
Nplot = min(Nplot, numel(x));
t = (0:Nplot-1)/fs * 1e3;      % ms
figure; plot(t, x(1:Nplot));
xlabel('Time (ms)'); ylabel('Amplitude'); grid on;
title(sprintf('BPSK passband snippet — %s', npys(1).name), 'Interpreter','none');

% Simple spectrum via Welch
figure;
pwelch(x, hamming(4096), 2048, 4096, fs, 'onesided');
title('Welch PSD of BPSK passband');

