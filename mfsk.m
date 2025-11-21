function mfsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list, noise_ratio)
    % data_samp_count      % Number of waveforms (files) to generate
    % save_path            % Path where .npy is saved
    % output_len           % Length of each saved output vector (samples)
    % fs                   % Sample Rate (Hz)
    % Tsymb                % Symbol Period (s)
    % fc_list              % Vector of M carrier frequencies [f1 f2 ... fM]
    % noise_ratio          % ratio of noise to signal, P_noise / P_signal   (linear)
    %
    % ***** IMPORTANT *****
    % constraints (errors not handled)
    % fs*Tsymb must be an integer
    % output_len/(fs*Tsymb) must be an integer
    % *********************

    % set default values for parameters
    if nargin < 1 || isempty(data_samp_count), data_samp_count = 10; end
    if nargin < 2 || isempty(save_path), save_path = pwd; end
    if nargin < 3 || isempty(output_len), output_len = 2000; end
    if nargin < 4 || isempty(fs), fs = 500; end
    if nargin < 5 || isempty(Tsymb), Tsymb = 0.1; end
    if nargin < 6 || isempty(fc_list), fc_list = [100 150]; end  % default 2-FSK
    if nargin < 7 || isempty(noise_ratio), noise_ratio = 0;     end

    % create save path directory if it doesn't already exist
    if ~exist(save_path, 'dir')
        mkdir(save_path);
    end

    samp_per_symb = fs * Tsymb;          % samples per symbol (must be integer)
    M = numel(fc_list);                  % number of FSK tones
    n_symb = output_len / samp_per_symb; % symbols per file (must be integer)

    % (no extra error checks: assuming constraints are satisfied)

    for n = 1:data_samp_count
        % create random M-ary symbol sequence: 0...(M-1)
        sym_seq = randi([0 M-1], n_symb, 1);

        % repeat each symbol to cover all its samples
        sym_idx = repelem(sym_seq, samp_per_symb);   % length = output_len

        % time vector
        t = (0:output_len-1) / fs;

        % map each sample index to its corresponding tone frequency
        freq_per_sample = fc_list(sym_idx + 1);

        % generate MFSK passband signal
        mfsk_pb = cos(2*pi .* freq_per_sample(:) .* t(:));
           
        % Add noise if noise_ratio >0
        if noise_ratio > 0
            sig_power   = mean(mfsk_pb.^2);           % average signal power
            noise_power = noise_ratio * sig_power;         % desired noise power
            sigma       = sqrt(noise_power);
            noise       = sigma * randn(size(mfsk_pb)); % AWGN
            mfsk_pb_noisy = mfsk_pb + noise;
        else
            mfsk_pb_noisy = mfsk_pb;
        end

        % save file
        filename = fullfile(save_path, sprintf('mfsk_M%d_%d.npy', M, n));
        writeNPY(mfsk_pb_noisy, filename);
    end
end