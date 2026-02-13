function sig_pb = waveform_generator(output_len, fs, Tsymb, fc, M, modulation, varargin)
    % WAVEFORM_GENERATOR - Unified RF waveform generator with pulse shaping
    %
    % Main entry point for all single-carrier modulation schemes
    %
    % Inputs:
    %   output_len   - Length of output vector (total samples)
    %   fs           - Sample Rate (Hz)
    %   Tsymb        - Symbol Period (s)
    %   fc           - Carrier Frequency (Hz)
    %   M            - Modulation order
    %   modulation   - 'PAM','QAM','PSK','FSK','FHSS','LFM','Barker','FMCW','WiFi','LTE','5G_NR'
    %   varargin     - Optional name-value pairs:
    %                  'alpha' (default 0.35) - RRC roll-off
    %                  'span' (default 8) - Filter span in symbols
    %                  'pulse_shape' (default 'rrc') - 'rrc' or 'rect'
    %
    % Output:
    %   sig_pb       - Pulse-shaped passband signal (real-valued)
    %
    % Examples:
    %   % QAM with RRC pulse shaping
    %   sig = waveform_generator(98304, 48000, 0.001, 6000, 16, 'QAM');
    %   
    %   % PAM with rectangular pulses
    %   sig = waveform_generator(98304, 48000, 0.001, 6000, 4, 'PAM', ...
    %                            'pulse_shape', 'rect');
    %   
    %   % PSK with custom roll-off
    %   sig = waveform_generator(98304, 48000, 0.001, 6000, 8, 'PSK', ...
    %                            'alpha', 0.5);
    
    %% Parse optional arguments
    p = inputParser;
    addParameter(p, 'alpha', 0.35, @isnumeric);      % RRC roll-off
    addParameter(p, 'span', 8, @isnumeric);          % Filter span
    addParameter(p, 'pulse_shape', 'rrc', @ischar);  % Pulse shape type
    parse(p, varargin{:});
    
    alpha = p.Results.alpha;
    span = p.Results.span;
    pulse_shape = p.Results.pulse_shape;
    
    %% Common parameters
    sps = round(fs * Tsymb);  % Samples per symbol (must be integer)
    
    %% Design pulse shaping filter
    if strcmp(pulse_shape, 'rrc')
        h = rcosdesign(alpha, span, sps, 'sqrt');
        filter_delay = span * sps / 2;  % Group delay
    else
        % Rectangular pulse (backward compatibility)
        h = ones(sps, 1) / sqrt(sps);  % Normalized
        filter_delay = 0;
    end
    
    %% Calculate number of symbols needed
    % Account for filter delay on both sides
    total_samples_needed = output_len + 2 * filter_delay;
    num_symbols = ceil(total_samples_needed / sps);
    
    %% Handle FSK separately (doesn't use standard pulse shaping)
    if strcmpi(modulation, 'FSK')
        sig_pb = generate_fsk_signal(output_len, fs, Tsymb, fc, M);
        return;
    end
    
    %% Handle FHSS separately (frequency hopping spread spectrum)
    if strcmpi(modulation, 'FHSS')
        sig_pb = generate_fhss_signal(output_len, fs, Tsymb, fc, M);
        return;
    end

    %% ---- Advanced waveforms (toolbox-based) ----

    if strcmpi(modulation, 'LFM')
        sig_pb = generate_lfm_signal(output_len, fs, Tsymb, fc, M);
        return;
    end

    if strcmpi(modulation, 'Barker')
        sig_pb = generate_barker_signal(output_len, fs, Tsymb, fc, M);
        return;
    end

    if strcmpi(modulation, 'FMCW')
        sig_pb = generate_fmcw_signal(output_len, fs, Tsymb, fc, M);
        return;
    end

    if strcmpi(modulation, 'WiFi')
        sig_pb = generate_wifi_signal(output_len, fs, fc);
        return;
    end

    if strcmpi(modulation, 'LTE')
        sig_pb = generate_lte_signal(output_len, fs, fc);
        return;
    end

    if strcmpi(modulation, '5G_NR')
        sig_pb = generate_5gnr_signal(output_len, fs, fc);
        return;
    end

    %% Generate symbols based on modulation type
    symbols = generate_symbols(num_symbols, M, modulation);
    
    %% Apply pulse shaping
    % upfirdn: upsample by sps, filter with h, downsample by 1
    sig_bb = upfirdn(symbols, h, sps, 1);
    
    %% Trim to exact output length
    % Remove filter delay from start
    start_idx = filter_delay + 1;
    end_idx = start_idx + output_len - 1;
    
    % Ensure we don't exceed signal length
    if end_idx > length(sig_bb)
        % Pad with zeros if needed
        sig_bb(end_idx) = 0;
    end
    
    sig_bb = sig_bb(start_idx:end_idx);
    
    %% Upconvert to passband
    sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
end


%% ========================================================================
%  HELPER FUNCTIONS (Local to this file)
%% ========================================================================

function sig_pb = generate_fsk_signal(output_len, fs, Tsymb, fc, M)
    % GENERATE_FSK_SIGNAL - Generate CPFSK (Continuous Phase FSK) signal
    %
    % FSK requires generating actual frequency-modulated waveforms,
    % not pulse-shaped symbols. This generates a proper CPFSK signal.
    %
    % Inputs:
    %   output_len - Total output samples
    %   fs         - Sample rate (Hz)
    %   Tsymb      - Symbol period (s)
    %   fc         - Center frequency (Hz)
    %   M          - Number of frequency tones
    
    sps = round(fs * Tsymb);  % Samples per symbol (must be integer)
    freq_sep = 1 / Tsymb;  % Minimum orthogonal frequency separation
    
    % Calculate number of symbols
    num_symbols = ceil(output_len / sps);
    
    % Generate random data symbols (0 to M-1)
    data = randi([0 M-1], num_symbols, 1);
    
    % Map data to frequency offsets centered around fc
    % e.g., for M=4: [-1.5, -0.5, 0.5, 1.5] * freq_sep
    freq_offsets = (data - (M-1)/2) * freq_sep;
    
    % Generate CPFSK signal with continuous phase
    sig_pb = zeros(output_len, 1);
    phase = 0;  % Running phase for continuity
    
    sample_idx = 1;
    for sym = 1:num_symbols
        % Instantaneous frequency for this symbol
        f_inst = fc + freq_offsets(sym);
        
        % Generate samples for this symbol
        num_samp = min(sps, output_len - sample_idx + 1);
        if num_samp <= 0
            break;
        end
        
        for k = 1:num_samp
            sig_pb(sample_idx) = cos(phase);
            phase = phase + 2*pi * f_inst / fs;
            sample_idx = sample_idx + 1;
        end
        
        % Keep phase bounded to avoid numerical issues
        phase = mod(phase, 2*pi);
    end
end


function sig_pb = generate_fhss_signal(output_len, fs, Tsymb, fc, M)
    % GENERATE_FHSS_SIGNAL - Generate Frequency Hopping Spread Spectrum signal
    %
    % Generates an FHSS signal with M hopping channels. Each symbol period
    % the carrier hops to a new pseudo-random frequency channel.
    %
    % Inputs:
    %   output_len - Total output samples
    %   fs         - Sample rate (Hz)
    %   Tsymb      - Symbol/hop period (s) - time spent on each frequency
    %   fc         - Center frequency (Hz)
    %   M          - Number of hopping channels
    
    sps = round(fs * Tsymb);  % Samples per hop
    
    % Hopping bandwidth - spread channels around fc
    % Channel spacing to avoid overlap
    channel_spacing = fs / (2 * M);  % Spread across half the bandwidth
    hop_bw = channel_spacing * (M - 1);
    
    % Calculate number of hops
    num_hops = ceil(output_len / sps);
    
    % Generate pseudo-random hopping sequence (0 to M-1)
    hop_sequence = randi([0 M-1], num_hops, 1);
    
    % Map hop indices to frequency offsets centered around fc
    freq_offsets = (hop_sequence - (M-1)/2) * channel_spacing;
    
    % Generate FHSS signal with continuous phase between hops
    sig_pb = zeros(output_len, 1);
    phase = 0;  % Running phase for continuity
    
    sample_idx = 1;
    for hop = 1:num_hops
        % Instantaneous frequency for this hop
        f_inst = fc + freq_offsets(hop);
        
        % Generate samples for this hop period
        num_samp = min(sps, output_len - sample_idx + 1);
        if num_samp <= 0
            break;
        end
        
        for k = 1:num_samp
            sig_pb(sample_idx) = cos(phase);
            phase = phase + 2*pi * f_inst / fs;
            sample_idx = sample_idx + 1;
        end
        
        % Keep phase bounded to avoid numerical issues
        phase = mod(phase, 2*pi);
    end
end


function symbols = generate_symbols(num_symbols, M, modulation)
    % GENERATE_SYMBOLS - Generate random modulated symbols
    %
    % Unified symbol generation for different modulation schemes
    
    % Generate random data
    data = randi([0 M-1], num_symbols, 1);
    
    switch upper(modulation)
        case 'PAM'
            % Pulse Amplitude Modulation
            symbols = pammod(data, M);
            % Normalize for unit average power
            symbols = symbols / sqrt(mean(abs(symbols).^2));
            
        case 'QAM'
            % Quadrature Amplitude Modulation
            symbols = qammod(data, M, 'UnitAveragePower', true);
            
        case 'PSK'
            % Phase Shift Keying
            symbols = pskmod(data, M, 0, 'gray');  % Gray coding
            % Already unit power
            
        otherwise
            error('Unsupported modulation type: %s', modulation);
    end
end


function sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len)
    % UPCONVERT_TO_PASSBAND - Convert complex baseband to real passband
    %
    % Uses quadrature upconversion: s(t) = I(t)*cos(wc*t) - Q(t)*sin(wc*t)
    % This is the standard method for all digital modulations
    
    % Ensure correct length
    sig_bb = sig_bb(1:output_len);
    
    % Extract I and Q components
    I = real(sig_bb);
    Q = imag(sig_bb);
    
    % Generate carriers
    t = (0:output_len-1)' / fs;
    carrier_I = cos(2*pi*fc*t);
    carrier_Q = -sin(2*pi*fc*t);
    
    % Quadrature upconversion
    sig_pb = I .* carrier_I + Q .* carrier_Q;
end


%% ========================================================================
%  ADVANCED WAVEFORM HELPERS (Toolbox-based)
%% ========================================================================

function sig_pb = generate_lfm_signal(output_len, fs, Tsymb, fc, M)
    % GENERATE_LFM_SIGNAL - Linear Frequency Modulated (chirp) pulse
    % Requires: Phased Array System Toolbox
    try
        sweep_bw = M * fs / 8;         % M scales the sweep bandwidth
        pulse_width = Tsymb * 20;       % longer pulse for visible chirp
        pulse_width = min(pulse_width, (output_len - 1) / fs);  % cap at signal length

        % Snap pulse_width so it contains a whole number of samples
        pulse_width = round(pulse_width * fs) / fs;

        % PRF must satisfy: fs / PRF is an integer
        pri_desired = pulse_width * 1.5;
        pri_samples = max(round(pri_desired * fs), round(pulse_width * fs) + 1);
        prf = fs / pri_samples;

        wav = phased.LinearFMWaveform( ...
            'SweepBandwidth', sweep_bw, ...
            'PulseWidth', pulse_width, ...
            'SampleRate', fs, ...
            'PRF', prf, ...
            'OutputFormat', 'Samples', ...
            'NumSamples', output_len);
        sig_bb = wav();
        sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
    catch ME
        error('LFM generation failed (need Phased Array System Toolbox): %s', ME.message);
    end
end


function sig_pb = generate_barker_signal(output_len, fs, Tsymb, fc, M)
    % GENERATE_BARKER_SIGNAL - Phase-coded pulse using Barker sequence
    % Requires: Phased Array System Toolbox
    % M selects num_chips: valid Barker lengths are 2,3,4,5,7,11,13
    try
        valid_chips = [2 3 4 5 7 11 13];
        [~, idx] = min(abs(valid_chips - M));
        num_chips = valid_chips(idx);

        chip_width = Tsymb;
        chip_width = min(chip_width, (output_len - 1) / (fs * num_chips));

        % Snap chip_width so it contains a whole number of samples (min 1)
        chip_width = max(round(chip_width * fs), 1) / fs;

        % PRF must satisfy: fs / PRF is an integer
        pulse_dur = chip_width * num_chips;
        pri_desired = pulse_dur * 1.5;
        pri_samples = max(round(pri_desired * fs), round(pulse_dur * fs) + 1);
        prf = fs / pri_samples;

        wav = phased.PhaseCodedWaveform( ...
            'Code', 'Barker', ...
            'NumChips', num_chips, ...
            'ChipWidth', chip_width, ...
            'SampleRate', fs, ...
            'PRF', prf, ...
            'OutputFormat', 'Samples', ...
            'NumSamples', output_len);
        sig_bb = wav();
        sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
    catch ME
        error('Barker generation failed (need Phased Array System Toolbox): %s', ME.message);
    end
end


function sig_pb = generate_fmcw_signal(output_len, fs, Tsymb, fc, M)
    % GENERATE_FMCW_SIGNAL - Frequency Modulated Continuous Wave
    % Requires: Phased Array System Toolbox
    try
        sweep_bw = M * fs / 8;
        sweep_time = Tsymb * 50;
        sweep_time = min(sweep_time, (output_len - 1) / fs);

        % Snap sweep_time so it contains a whole number of samples
        sweep_time = max(round(sweep_time * fs), 1) / fs;

        wav = phased.FMCWWaveform( ...
            'SweepBandwidth', sweep_bw, ...
            'SweepTime', sweep_time, ...
            'SampleRate', fs, ...
            'SweepDirection', 'Triangle', ...
            'OutputFormat', 'Samples', ...
            'NumSamples', output_len);
        sig_bb = wav();
        sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
    catch ME
        error('FMCW generation failed (need Phased Array System Toolbox): %s', ME.message);
    end
end


function sig_pb = generate_wifi_signal(output_len, fs, fc)
    % GENERATE_WIFI_SIGNAL - 802.11ax (WiFi 6) HE-SU packet
    % Requires: WLAN Toolbox
    try
        cfg = wlanHESUConfig;
        cfg.ChannelBandwidth = 'CBW20';     % 20 MHz
        cfg.MCS = 0;                         % BPSK, rate 1/2

        % Generate random data bits matching the required PSDU length
        psduLen = getPSDULength(cfg);        % bytes
        dataBits = randi([0 1], psduLen * 8, 1);

        % Generate at native rate, then resample to fs
        sig_bb_native = wlanWaveformGenerator(dataBits, cfg);
        native_fs = 20e6;  % CBW20 native rate

        % Resample to target fs
        if abs(fs - native_fs) > 1
            [P, Q] = rat(fs / native_fs, 1e-6);
            sig_bb = resample(sig_bb_native(:,1), P, Q);
        else
            sig_bb = sig_bb_native(:,1);
        end

        % Repeat to fill output_len if needed
        while length(sig_bb) < output_len
            sig_bb = [sig_bb; sig_bb]; %#ok<AGROW>
        end
        sig_bb = sig_bb(1:output_len);

        sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
    catch ME
        error('WiFi generation failed (need WLAN Toolbox): %s', ME.message);
    end
end


function sig_pb = generate_lte_signal(output_len, fs, fc)
    % GENERATE_LTE_SIGNAL - LTE downlink reference measurement channel
    % Requires: LTE Toolbox
    try
        % R.0 = 1.4MHz BW, QPSK, 1 antenna
        bits = randi([0 1], 2000, 1);
        [sig_bb_native, ~, rmccfg] = lteRMCDLTool('R.0', bits);
        native_fs = rmccfg.SamplingRate;

        % Resample to target fs
        if abs(fs - native_fs) > 1
            [P, Q] = rat(fs / native_fs, 1e-6);
            sig_bb = resample(sig_bb_native(:,1), P, Q);
        else
            sig_bb = sig_bb_native(:,1);
        end

        % Repeat to fill output_len
        while length(sig_bb) < output_len
            sig_bb = [sig_bb; sig_bb]; %#ok<AGROW>
        end
        sig_bb = sig_bb(1:output_len);

        sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
    catch ME
        error('LTE generation failed (need LTE Toolbox): %s', ME.message);
    end
end


function sig_pb = generate_5gnr_signal(output_len, fs, fc)
    % GENERATE_5GNR_SIGNAL - 5G NR downlink waveform
    % Requires: 5G Toolbox
    try
        cfg = nrDLCarrierConfig;
        cfg.ChannelBandwidth = 10;          % 10 MHz (smallest FR1)
        cfg.NumSubframes = 10;              % 10 ms frame

        [sig_bb_native, info] = nrWaveformGenerator(cfg);
        native_fs = info.ResourceGrids(1).Info.SampleRate;

        % Resample to target fs
        if abs(fs - native_fs) > 1
            [P, Q] = rat(fs / native_fs, 1e-6);
            sig_bb = resample(sig_bb_native(:,1), P, Q);
        else
            sig_bb = sig_bb_native(:,1);
        end

        % Repeat to fill output_len
        while length(sig_bb) < output_len
            sig_bb = [sig_bb; sig_bb]; %#ok<AGROW>
        end
        sig_bb = sig_bb(1:output_len);

        sig_pb = upconvert_to_passband(sig_bb, fs, fc, output_len);
    catch ME
        error('5G NR generation failed (need 5G Toolbox): %s', ME.message);
    end
end


%% ========================================================================
%  BACKWARD COMPATIBILITY WRAPPER FUNCTIONS
%% ========================================================================
% These allow old code to still work, but they call the new unified function

function pam_pb = pam_gui(output_len, fs, Tsymb, fc, M, Var)
    % PAM_GUI - Legacy wrapper for backward compatibility
    % Calls waveform_generator with 'rect' pulse shape
    pam_pb = waveform_generator(output_len, fs, Tsymb, fc, M, 'PAM', ...
                                'pulse_shape', 'rect');
end


function mqam_pb = mqam_gui(output_len, fs, Tsymb, fc, M)
    % MQAM_GUI - Legacy wrapper for backward compatibility
    % Calls waveform_generator with 'rect' pulse shape
    mqam_pb = waveform_generator(output_len, fs, Tsymb, fc, M, 'QAM', ...
                                 'pulse_shape', 'rect');
end


function fsk_pb = fsk_gui(output_len, fs, Tsymb, fc, M, freq_sep)
    % FSK_GUI - Legacy wrapper for backward compatibility
    % Calls waveform_generator with 'rect' pulse shape
    if nargin < 6
        freq_sep = 1/Tsymb;  % Default frequency separation
    end
    fsk_pb = waveform_generator(output_len, fs, Tsymb, fc, M, 'FSK', ...
                                'pulse_shape', 'rect');
end