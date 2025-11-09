function bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc)
    % data_samp_count      % Number of data samples to generate
    % save_path            % Path where .npy is saved
    % output_len           % Length of each saved output vector
    % fs                   % Sample Rate (Hz)
    % Tsymb                % Symbol Period (s)
    % fc                   % Carrier Frequency (Hz)
    
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
    if nargin < 6 || isempty(fc), fc = 100; end

    % create save path directory if it doesn't already exist
    if ~exist(save_path, 'dir')
        mkdir(save_path);
    end
    
    samp_per_symb = fs*Tsymb;
    for n=1:data_samp_count
        % create random bit sequence
        bit_seq = randi([0 1], output_len/samp_per_symb, 1);
    
        % Reshape bits into symbols
        bpsk_imp_train = bit_seq*2 - 1;
        bpsk_bb = repelem(bpsk_imp_train, samp_per_symb);
        
        % set up carrier
        t = (0:output_len-1) / fs;
        carrier = cos(2*pi*fc*t).';
        
        % upconvert to passband
        bpsk_pb = bpsk_bb .* carrier;
        
        % save file
        filename = fullfile(save_path, sprintf('bpsk_%d.npy', n));
        writeNPY(bpsk_pb, filename);
    end
end
