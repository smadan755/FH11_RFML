function fhss_bpsk(data_samp_count, save_path, output_len, fs, Tsymb, fc_list, Thop)
    % fhss_bpsk
    %
    % Generate real passband BPSK signals with frequency-hopping spread spectrum.
    %
    % data_samp_count  - number of waveforms to generate
    % save_path        - folder where .npy files are saved
    % output_len       - total samples per waveform
    % fs               - sample rate (Hz)
    % Tsymb            - symbol period (s)
    % fc_list          - vector of hop carrier frequencies (Hz), e.g. [5e3 6e3 7e3]
    % Thop             - hop duration (s)
    %
    % ***** IMPORTANT CONSTRAINTS (not enforced) *****
    % fs*Tsymb must be an integer          -> samples per symbol
    % fs*Thop  must be an integer          -> samples per hop
    % output_len/(fs*Tsymb)  must be int   -> total symbols
    % output_len/(fs*Thop)   must be int   -> total hops
    % max(fc_list) < fs/2 to avoid aliasing
    % ************************************************

    if nargin < 1 || isempty(data_samp_count), data_samp_count = 10; end
    if nargin < 2 || isempty(save_path),      save_path      = pwd;   end
    if nargin < 3 || isempty(output_len),     output_len     = 2000;  end
    if nargin < 4 || isempty(fs),             fs             = 48e3;  end
    if nargin < 5 || isempty(Tsymb),          Tsymb          = 1e-3;  end
    if nargin < 6 || isempty(fc_list),        fc_list        = [5e3 6e3 7e3 8e3]; end
    if nargin < 7 || isempty(Thop),           Thop           = 10*Tsymb;          end

    % Ensure save directory exists
    if ~exist(save_path, 'dir')
        mkdir(save_path);
    end

    % Derived parameters
    samp_per_symb = fs * Tsymb;              % samples per symbol
    samp_per_hop  = fs * Thop;               % samples per hop

    % You *should* check these are integers; using round here for safety
    samp_per_symb = round(samp_per_symb);
    samp_per_hop  = round(samp_per_hop);

    Nsym  = output_len / samp_per_symb;      % symbols per file
    Nhops = output_len / samp_per_hop;       % hops per file

    if abs(Nsym - round(Nsym)) > 1e-9 || abs(Nhops - round(Nhops)) > 1e-9
        error('output_len, Tsymb, Thop, and fs must be chosen so that Nsym and Nhops are integers.');
    end

    Nsym  = round(Nsym);
    Nhops = round(Nhops);

    % Time vector (column)
    t = (0:output_len-1)' / fs;

    for n = 1:data_samp_count
        % create random bit sequence
        bit_seq = randi([0 1], Nsym, 1);
        
        % Reshape bits into symbols
        bpsk_imp_train = bit_seq * 2 - 1;
        bpsk_bb = repelem(bpsk_imp_train, samp_per_symb);

        %Construct frequency hop pattern
        Nc = numel(fc_list);

        % Random hop index per hop interval
        hop_idx = randi(Nc, Nhops, 1);       % each entry ∈ {1,...,Nc}

        % Instantaneous carrier frequency per sample
        f_inst = zeros(output_len, 1);
        for k = 1:Nhops
            idx_start = (k-1)*samp_per_hop + 1;
            idx_end   = k*samp_per_hop;
            f_inst(idx_start:idx_end) = fc_list(hop_idx(k));
        end

        %Setup FHSS carrier
        carrier = cos(2*pi .* f_inst .* t);

        % upconvert
        fhss_bpsk_pb = bpsk_bb .* carrier;

        % save file
        filename = fullfile(save_path, sprintf('fhss_bpsk_%d.npy', n));
        writeNPY(fhss_bpsk_pb, filename);
    end
end
