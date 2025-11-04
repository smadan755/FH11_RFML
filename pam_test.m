% pam_test.m — usage/inspection for pam(...)
clear; clc; close all;

% addpath('path/to/npy-matlab');  % ensure writeNPY/readNPY available

data_samp_count = 1;
save_path       = fullfile(pwd, 'data_pam');

fs     = 48e3;        % Hz
Tsymb  = 1e-3;        % s  -> sps = 48
sps    = fs * Tsymb;  % should be integer (48)
Nsym   = 2048;
output_len = Nsym * sps;

fc   = 6e3;           % Hz (fc < fs/2)
M    = 4;             % 4-PAM
Var  = 1;             % symbol variance

% Optional reproducibility
rng(123);

% Generate
pam(data_samp_count, save_path, output_len, fs, Tsymb, fc, M, Var);
fprintf('Generated %d files in: %s\n', data_samp_count, save_path);

% Inspect
npys = dir(fullfile(save_path, sprintf('pam%u_*.npy', M)));
assert(~isempty(npys), 'No .npy files found.');
sample_path = fullfile(npys(1).folder, npys(1).name);

x = readNPY(sample_path);               % real passband PAM (column)
x = x(:);                               % force column for plotting

% Time snippet
Nplot = min(round(3e-3 * fs), numel(x));  % ~3 ms
tms = (0:Nplot-1)/fs * 1e3;
figure; plot(tms, x(1:Nplot)); grid on;
xlabel('Time (ms)'); ylabel('Amplitude');
title(sprintf('%d-PAM passband snippet — %s', M, npys(1).name), 'Interpreter','none');

% Spectrum (Welch)
figure;
pwelch(x, hamming(4096), 2048, 4096, fs, 'onesided');
title(sprintf('Welch PSD of %d-PAM passband', M));
