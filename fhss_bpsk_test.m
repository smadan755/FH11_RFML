% generate_fhss_bpsk_dataset.m
% Usage example for fhss_bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list, Thop)

clear; clc; close all;

data_samp_count = 1;                               % number of waveforms to generate
save_path       = fullfile(pwd, 'data_fhss_bpsk'); % output folder for .npy files

% Choose parameters
fs     = 48e3;           % Hz (sample rate)
Tsymb  = 1e-3;           % s  (symbol period) -> sps = fs*Tsymb = 48 samples/symbol
sps    = fs * Tsymb;     % should be integer
Nsym   = 2000;           % symbols per file (Nhops = Nsym / symbols_per_hop must be an integer)
output_len = Nsym * sps; % total samples per file

% FHSS-specific parameters
% Choose a set of carrier frequencies (all < fs/2)
fc_center = 6e3;         % Hz
delta_f   = 5e3;         % spacing between hop channels
fc_list   = fc_center + delta_f * (-1:1);   % e.g. [5e3, 6e3, 7e3]

% Hop every 10 symbols (slow FHSS)
symbols_per_hop = 10;
Thop            = symbols_per_hop * Tsymb;  % hop duration (s)

% -----------------------
% Generate dataset
% -----------------------
fhss_bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list, Thop);
fprintf('Generated %d FHSS-BPSK files in: %s\n', data_samp_count, save_path);

% -----------------------
% Quick inspection
% -----------------------
% Load one file (requires readNPY from npy-matlab)
npys = dir(fullfile(save_path, 'fhss_bpsk_*.npy'));

sample_path = fullfile(npys(1).folder, npys(1).name);
x = readNPY(sample_path);        % real passband FHSS-BPSK (column vector)

% Plot a short time snippet
Nplot = round(3e-3 * fs);        % ~3 ms
Nplot = min(Nplot, numel(x));
t_ms  = (0:Nplot-1)/fs * 1e3;    % ms
figure; plot(t_ms, x(1:Nplot));
xlabel('Time (ms)'); ylabel('Amplitude'); grid on;
title(sprintf('FHSS BPSK passband snippet — %s', npys(1).name), 'Interpreter','none');

% Simple spectrum via Welch
figure;
pwelch(x, hamming(4096), 2048, 4096, fs, 'onesided');
title('Welch PSD of FHSS BPSK passband');
