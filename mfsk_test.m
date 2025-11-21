% generate_mfsk_dataset.m
% Usage example for mfsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list)

clear; clc; close all;


data_samp_count = 1;   % number of waveforms to generate
save_path = fullfile(pwd, sprintf('data_mfsk_M%d', M)); % Output folder for .npy files

% Choose parameters so constraints hold:
M = 4;                 % M-ary FSK (number of tones)
fs = 48e3;             % Hz (sample rate)
Tsymb = 1e-3;          % s  (symbol period) -> sps = fs*Tsymb = 48 samples/symbol
sps = fs * Tsymb;      % should be integer
Nsym = 2048;           % symbols per file
output_len = Nsym * sps; % total samples per file

% Choose M distinct carrier frequencies (all < fs/2 to avoid aliasing)
fc_list = [4e3 10e3 16e3 22e3];   % Hz, length(fc_list) = M




% -----------------------
% Generate dataset
% -----------------------
mfsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list);
fprintf('Generated %d MFSK files (M = %d) in: %s\n', data_samp_count, M, save_path);

% -----------------------
% Quick inspection
% -----------------------
% Load one file (requires readNPY from npy-matlab)
npys = dir(fullfile(save_path, 'mfsk_M*.npy'));
if isempty(npys)
    error('No mfsk_M*.npy files found in %s', save_path);
end

sample_path = fullfile(npys(1).folder, npys(1).name);
x = readNPY(sample_path);   % real passband MFSK (column vector)

% Plot a short time snippet
Nplot = round(3e-3 * fs);   % ~3 ms
Nplot = min(Nplot, numel(x));
t = (0:Nplot-1)/fs * 1e3;   % ms
figure;
plot(t, x(1:Nplot));
xlabel('Time (ms)'); ylabel('Amplitude'); grid on;
title(sprintf('MFSK passband snippet (M = %d) — %s', M, npys(1).name),'Interpreter', 'none');

% Simple spectrum via Welch
figure;
pwelch(x, hamming(4096), 2048, 4096, fs, 'onesided');
title(sprintf('Welch PSD of MFSK passband (M = %d)', M));


% Spectrogram (windows match symbol windows)
figure;
win = hamming(sps);   % sps = 48
noverlap = 0;
nfft = 4*sps;
x_slice = x(1 : floor(length(x)/20)); % Use only part of the signal
spectrogram(x_slice, win, noverlap, nfft, fs, 'yaxis');
title(sprintf('Spectrogram of MFSK passband (M = %d)', M));
ylabel('Frequency (Hz)');
xlabel('Time (s)');
colorbar;

