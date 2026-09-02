%% GAN_MASTER  Regenerate every result in the Review-I deck from the raw CSVs.
%
%  ONE entry point for the whole results section. Runs in MATLAB and in GNU
%  Octave with no toolboxes (core functions only), so it works on a basic
%  MATLAB Online licence.
%
%  USAGE
%      Put this file in the same folder as the CSVs, then:
%          >> gan_master
%      Figures are written as PNG next to the script; every headline number
%      is printed to the console with the deck slide it appears on.
%
%  DATA
%      sweep_nominal.csv   720 words at the nominal corner
%      full_corners.csv    720 words x 3 further corners
%      robust.csv          720 words x 2 corners x 11 device perturbations
%      lloop_sweep.csv.gz  720 words across 8 loop inductances  (gunzip first)
%      sweep_matlab.csv    tidy nominal sweep, pre-named columns
%
%  METHOD NOTE -- the cost function
%      cost = E_tot [uJ] + w_ov * ov_pct
%      w_ov = 0.05 is the weight used for the headline numbers. Section 6
%      sweeps it, because a result that only holds at one weight is not a
%      result. Only words with margin > 0 at EVERY corner are admissible:
%      a faster word that false-turns-on is not a cheaper word, it is broken.
% -------------------------------------------------------------------------

clear; clc; close all;
W_OV = 0.05;
FIELDS = {'NPU_LS','NPD_LS','NPD_HS','DT','CLKEN','VNEG'};

fprintf('\n=====================================================================\n');
fprintf('  GaN segmented gate driver -- full results regeneration\n');
fprintf('=====================================================================\n');

%% ------------------------------------------------------------------------
%  0.  Loader.  readtable exists in both MATLAB and Octave >= 6, but its
%      behaviour differs, so parse manually and keep one code path.
%% ------------------------------------------------------------------------
function [hdr, M] = readcsv(fname)
    fid = fopen(fname, 'r');
    if fid < 0, error('gan_master:missing', 'Cannot find %s', fname); end
    line = fgetl(fid);
    hdr  = strsplit(strtrim(line), ',');
    M    = []; row = 0;
    while true
        line = fgetl(fid);
        if ~ischar(line) || isempty(strtrim(line)), break; end
        parts = strsplit(strtrim(line), ',');
        v = zeros(1, numel(hdr));
        for k = 1:numel(hdr)
            if k <= numel(parts)
                x = str2double(parts{k});
                if isnan(x), x = NaN; end       % text column (corner, case)
                v(k) = x;
            else
                v(k) = NaN;
            end
        end
        row = row + 1; M(row,:) = v; %#ok<AGROW>
    end
    fclose(fid);
end

function [hdr, M, T] = readcsv_all(fname)
    % returns numeric matrix M and the RAW text of every cell in T.
    % DT is stored as '15n' etc, so it must be keyed as text, never str2double.
    fid = fopen(fname, 'r');
    if fid < 0, error('gan_master:missing', 'Cannot find %s', fname); end
    hdr = strsplit(strtrim(fgetl(fid)), ',');
    M = []; T = {}; row = 0;
    while true
        line = fgetl(fid);
        if ~ischar(line) || isempty(strtrim(line)), break; end
        parts = strsplit(strtrim(line), ',');
        v = NaN(1, numel(hdr)); t = repmat({''}, 1, numel(hdr));
        for k = 1:min(numel(hdr), numel(parts))
            v(k) = str2double(parts{k});
            t{k} = parts{k};
        end
        row = row + 1; M(row,:) = v; T(row,:) = t; %#ok<AGROW>
    end
    fclose(fid);
end

function [hdr, M, txt] = readcsv_txt(fname, txtcol)
    % same, but also returns one named text column (e.g. 'corner')
    fid = fopen(fname, 'r');
    if fid < 0, error('gan_master:missing', 'Cannot find %s', fname); end
    hdr = strsplit(strtrim(fgetl(fid)), ',');
    ci  = find(strcmp(hdr, txtcol), 1);
    M = []; txt = {}; row = 0;
    while true
        line = fgetl(fid);
        if ~ischar(line) || isempty(strtrim(line)), break; end
        parts = strsplit(strtrim(line), ',');
        v = NaN(1, numel(hdr));
        for k = 1:min(numel(hdr), numel(parts))
            v(k) = str2double(parts{k});
        end
        row = row + 1; M(row,:) = v; %#ok<AGROW>
        if ~isempty(ci) && ci <= numel(parts), txt{row,1} = parts{ci}; else txt{row,1} = ''; end
    end
    fclose(fid);
end

col = @(hdr, name) find(strcmp(hdr, name), 1);

%% ------------------------------------------------------------------------
%  1.  THE PROBLEM  --  crosstalk is real and the actuator removes it
%      Deck slides 12 and 15.
%% ------------------------------------------------------------------------
fprintf('\n1.  CROSSTALK  (slides 12, 15)\n');
fprintf('    Worst case over every word in each configuration. The deck quotes\n');
fprintf('    the FASTEST-drive word specifically (1.65 / 0.83 / -1.18 V); those\n');
fprintf('    come from scripts/gansim.py. Both are correct, different words.\n');
fprintf('    ---------------------------------------------------------------\n');
[h1, S, T1] = readcsv_all('sweep_nominal.csv');
iCLK = col(h1,'CLKEN'); iVN = col(h1,'VNEG'); iMar = col(h1,'margin');
iSpur = col(h1,'Vgs_spur_hs'); iTot = col(h1,'E_tot'); iOv = col(h1,'ov_pct');
iNPU = col(h1,'NPU_LS'); iNPD = col(h1,'NPD_LS'); iDT = col(h1,'DT');

sel = @(ck, vn) S(S(:,iCLK)==ck & S(:,iVN)==vn, :);
cases = {  'no clamp,  0 V off-bias', 0,  0;
           'clamp on,  0 V off-bias', 1,  0;
           'clamp on, -2 V off-bias', 1, -2 };
for k = 1:size(cases,1)
    R = sel(cases{k,2}, cases{k,3});
    if isempty(R), continue; end
    [~, j] = min(R(:,iMar));            % worst case in that configuration
    fprintf('    %-26s WORST-CASE margin %+7.3f V   spurious %+7.3f V\n', ...
            cases{k,1}, R(j,iMar), R(j,iSpur));
end
nfeas = sum(S(:,iMar) > 0);
fprintf('    feasible words at the nominal corner   %d of %d  (%.0f %%)\n', ...
        nfeas, size(S,1), 100*nfeas/size(S,1));

%% ------------------------------------------------------------------------
%  2.  THE SEARCH  --  the control word spans a huge range
%      Deck slide 22.
%% ------------------------------------------------------------------------
fprintf('\n2.  THE SEARCH  (slide 22)\n');
fprintf('    ---------------------------------------------------------------\n');
feas = S(S(:,iMar) > 0, :);
spread = 100 * (max(feas(:,iTot)) - min(feas(:,iTot))) / min(feas(:,iTot));
fprintf('    switching-energy spread across feasible words   %.0f %%\n', spread);
fprintf('    E_tot  min %.3f uJ   max %.3f uJ\n', min(feas(:,iTot))*1e6, max(feas(:,iTot))*1e6);

%% ------------------------------------------------------------------------
%  3.  PARETO FRONT  --  the objectives genuinely conflict
%      Deck slide 16.
%% ------------------------------------------------------------------------
fprintf('\n3.  PARETO FRONT  (slide 16)\n');
fprintf('    ---------------------------------------------------------------\n');
E = feas(:,iTot)*1e6; O = feas(:,iOv);   % E_tot is in joules; plot in uJ
isPar = true(size(E));
for a = 1:numel(E)
    isPar(a) = ~any(E <= E(a) & O <= O(a) & (E < E(a) | O < O(a)));
end
P = sortrows([E(isPar), O(isPar)], 1);
fprintf('    Pareto-optimal words   %d of %d feasible\n', size(P,1), numel(E));
% The deck's "one point of overshoot costs 0.039 uJ" comes from
% gan_analysis.m, which defines the knee differently (local slope at the
% chosen operating region). Not recomputed here rather than print a second,
% conflicting number for the same quantity.

figure('visible','off');
plot(E, O, '.', 'Color', [0.72 0.76 0.82], 'MarkerSize', 6); hold on;
plot(P(:,1), P(:,2), '-o', 'Color', [0.11 0.37 0.61], 'LineWidth', 1.8, 'MarkerSize', 4);
xlabel('total switching energy  E_{tot}  (\muJ)');
ylabel('drain overshoot  (%)');
title('Objectives conflict: the Pareto front over the control word');
legend({'feasible words','Pareto front'}, 'Location','northeast'); grid on;
print('-dpng','-r170','fig_master_pareto.png'); close;
fprintf('    -> fig_master_pareto.png\n');

%% ------------------------------------------------------------------------
%  4.  THE CEILING ON SCHEDULING  --  four corners, exhaustive
%      Deck slide 17.  Reproduces scripts/ceiling.py.
%% ------------------------------------------------------------------------
fprintf('\n4.  CEILING ON SCHEDULING  (slide 17)\n');
fprintf('    ---------------------------------------------------------------\n');
[h2, F, T2] = readcsv_all('full_corners.csv');
cornerTxt = T2(:, col(h2,'corner'));
jMar = col(h2,'margin'); jTot = col(h2,'E_tot'); jOv = col(h2,'ov_pct');
jf = zeros(1,numel(FIELDS));
for k = 1:numel(FIELDS), jf(k) = col(h2, FIELDS{k}); end

% nominal rows carry no corner label in sweep_nominal.csv; tag them
nomKey = '100V_10A_25C';
kf = zeros(1,numel(FIELDS));
for k = 1:numel(FIELDS), kf(k) = col(h1, FIELDS{k}); end
allC  = [repmat({nomKey}, size(S,1), 1); cornerTxt];
allE  = [S(:,iTot);          F(:,jTot)];
allO  = [S(:,iOv);           F(:,jOv)];
allM  = [S(:,iMar);          F(:,jMar)];

% Key each control word on the RAW TEXT of its six fields. DT is written
% '15n', not 15e-9, so keying on str2double silently merges every dead time
% into NaN and collapses 720 words to 144 -- which moves the ceiling from
% 5.2 % to 12 %. Text keys keep the words distinct.
nS = size(S,1); nF = size(F,1);
wkey = cell(nS + nF, 1);
for a = 1:nS
    p = '';
    for k = 1:numel(FIELDS), p = [p T1{a, kf(k)} '_']; end
    wkey{a} = p;
end
for a = 1:nF
    p = '';
    for k = 1:numel(FIELDS), p = [p T2{a, jf(k)} '_']; end
    wkey{nS + a} = p;
end

corners = unique(allC);
words = unique(wkey);

fprintf('    corners %d, distinct words %d\n', numel(corners), numel(words));

    function [ceil_pct, bestFixed, perCorner] = ceiling_at(w_ov, ...
            words, wkey, allC, allE, allO, allM, corners)
        cost = allE * 1e6 + w_ov * allO;   % E_tot is in JOULES
        nW = numel(words); nC = numel(corners);
        C = NaN(nW, nC); OK = false(nW, nC);
        idx = containers.Map(words, num2cell(1:nW));
        cidx = containers.Map(corners, num2cell(1:nC));
        for a = 1:numel(wkey)
            r = idx(wkey{a}); c = cidx(allC{a});
            C(r,c) = cost(a); OK(r,c) = allM(a) > 0;
        end
        univ = all(OK,2) & all(~isnan(C),2);        % safe at EVERY corner
        meanC = mean(C(univ,:), 2);
        [~, bi] = min(meanC);
        ui = find(univ); bestFixed = ui(bi);
        % per-corner optimum searches EVERY word feasible at that corner,
        % not only the universally-safe ones -- that is what makes it a true
        % ceiling rather than a ceiling over a restricted shortlist.
        Cf = C; Cf(~OK) = Inf;
        perCornerOpt = min(Cf, [], 1);
        schedMean = mean(perCornerOpt);
        ceil_pct  = 100 * (min(meanC) - schedMean) / min(meanC);
        perCorner = 100 * (C(bestFixed,:) - perCornerOpt) ./ C(bestFixed,:);
    end

[ceilPct, bestIdx, perC] = ceiling_at(W_OV, words, wkey, allC, allE, allO, allM, corners);
fprintf('    CEILING on scheduling at w_ov=%.2f :  %.1f %%\n', W_OV, ceilPct);
fprintf('    per-corner penalty of the best fixed word:\n');
for c = 1:numel(corners)
    fprintf('        %-16s %6.1f %%\n', corners{c}, perC(c));
end

%% ------------------------------------------------------------------------
%  5.  THE DECOMPOSITION  --  fixed word vs adaptation
%      Deck slides 11, 18, 23.  Reproduces scripts/novelty.py.
%% ------------------------------------------------------------------------
fprintf('\n5.  DECOMPOSITION  (slides 11, 18, 23)\n');
fprintf('    ---------------------------------------------------------------\n');

    function [A, B, share] = decompose_at(w_ov, words, wkey, allC, allE, allO, allM, corners)
        cost = allE * 1e6 + w_ov * allO;   % E_tot is in JOULES
        nW = numel(words); nC = numel(corners);
        C = NaN(nW, nC); OK = false(nW, nC);
        idx = containers.Map(words, num2cell(1:nW));
        cidx = containers.Map(corners, num2cell(1:nC));
        for a = 1:numel(wkey)
            r = idx(wkey{a}); c = cidx(allC{a});
            C(r,c) = cost(a); OK(r,c) = allM(a) > 0;
        end
        univ = all(OK,2) & all(~isnan(C),2);
        meanC = mean(C(univ,:), 2);
        med   = median(meanC);
        bestF = min(meanC);
        Cf = C; Cf(~OK) = Inf;
        sched = mean(min(Cf, [], 1));
        A = 100*(med - bestF)/med;      % choosing a better FIXED word
        B = 100*(bestF - sched)/med;    % ADAPTING on top of that
        share = 100*(bestF - sched)/(med - sched);
    end

[A, B, share] = decompose_at(W_OV, words, wkey, allC, allE, allO, allM, corners);
fprintf('    (A) choose a better FIXED word     %5.1f %% of baseline\n', A);
fprintf('    (B) ADAPT it per operating point   %5.1f %% of baseline\n', B);
fprintf('    -> adaptation is %.1f %% of the total gain.\n', share);
fprintf('       the other %.1f %% needs no sensing, no ADC, no lookup table.\n', 100-share);

%% ------------------------------------------------------------------------
%  6.  DOES THE SPLIT DEPEND ON THE WEIGHTING?
%      Deck slide 18.  This is the answer to the sharpest objection.
%% ------------------------------------------------------------------------
fprintf('\n6.  WEIGHT SENSITIVITY  (slide 18)\n');
fprintf('    ---------------------------------------------------------------\n');
ws = [0:0.05:1.0, 1.25, 1.5, 2.0, 3.0, 5.0];
As = zeros(size(ws)); Bs = As;
for k = 1:numel(ws)
    [As(k), Bs(k), ~] = decompose_at(ws(k), words, wkey, allC, allE, allO, allM, corners);
end
in01 = ws <= 1.0;
fprintf('    over w_ov 0..1   (A) %.1f-%.1f %%   (B) %.1f-%.1f %%\n', ...
        min(As(in01)), max(As(in01)), min(Bs(in01)), max(Bs(in01)));
fprintf('    over w_ov 0..5   (A) %.1f-%.1f %%   (B) %.1f-%.1f %%\n', ...
        min(As), max(As), min(Bs), max(Bs));
if all(As > Bs)
    fprintf('    (A) exceeds (B) at EVERY weight tested -- the ordering is\n');
    fprintf('    weight-independent even though the magnitude is not.\n');
else
    fprintf('    NOTE: (A) does NOT exceed (B) everywhere -- check before quoting.\n');
end

figure('visible','off');
plot(ws, As, 'LineWidth', 2, 'Color', [0.11 0.37 0.61]); hold on;
plot(ws, Bs, 'LineWidth', 2, 'Color', [0.76 0.27 0.18]);
xlabel('overshoot weight  w_{ov}'); ylabel('% of baseline switching energy');
title('The split does not rest on the weighting');
legend({'(A) better fixed word','(B) adaptation on top'}, 'Location','east');
xlim([0 2]); ylim([0 max(As)*1.15]); grid on;
print('-dpng','-r170','fig_master_weight.png'); close;
fprintf('    -> fig_master_weight.png\n');

%% ------------------------------------------------------------------------
%  7.  WHERE THE ANSWER CHANGES  --  loop inductance
%      Deck slides 19, 20.
%% ------------------------------------------------------------------------
fprintf('\n7.  LOOP INDUCTANCE  (slides 19, 20)\n');
fprintf('    ---------------------------------------------------------------\n');
if exist('lloop_sweep.csv','file') == 2
    [h3, L, T3] = readcsv_all('lloop_sweep.csv');
    lc = col(h3,'lloop'); lm = col(h3,'margin'); le = col(h3,'E_tot');
    % lloop is written in SPICE notation ('3n'), so str2double gives NaN.
    % Parse the suffix rather than trusting the numeric column.
    Lnh = zeros(size(L,1),1);
    for a = 1:size(L,1)
        tok = strtrim(T3{a, lc});
        mult = 1;
        if ~isempty(tok)
            last = lower(tok(end));
            if last == 'n', mult = 1e-9; tok = tok(1:end-1);
            elseif last == 'p', mult = 1e-12; tok = tok(1:end-1);
            elseif last == 'u', mult = 1e-6;  tok = tok(1:end-1); end
        end
        Lnh(a) = str2double(tok) * mult;
    end
    L(:,lc) = Lnh;
    Ls = unique(L(:,lc));
    fprintf('    %8s  %10s  %14s\n', 'L (nH)', 'feasible', 'median E_tot');
    for k = 1:numel(Ls)
        R = L(L(:,lc)==Ls(k), :);
        f = R(R(:,lm) > 0, :);
        if isempty(f)
            fprintf('    %8.1f  %10d  %14s\n', Ls(k)*1e9, 0, '(none feasible)');
        else
            fprintf('    %8.1f  %10d  %11.3f uJ\n', Ls(k)*1e9, size(f,1), median(f(:,le))*1e6);
        end
    end
else
    fprintf('    lloop_sweep.csv not present. It ships gzipped -- run:\n');
    fprintf('        gunzip -k lloop_sweep.csv.gz\n');
    fprintf('    then re-run this script to include section 7.\n');
end

%% ------------------------------------------------------------------------
%  8.  SUMMARY TABLE
%% ------------------------------------------------------------------------
fprintf('\n=====================================================================\n');
fprintf('  SUMMARY -- cross-check these against RESULTS-SUMMARY.txt\n');
fprintf('=====================================================================\n');
fprintf('  feasible at nominal                  %d of %d (%.0f %%)\n', nfeas, size(S,1), 100*nfeas/size(S,1));
fprintf('  Pareto-optimal words                 %d\n', size(P,1));
fprintf('  ceiling on scheduling  (w_ov=%.2f)    %.1f %%\n', W_OV, ceilPct);
fprintf('  (A) better fixed word                %.1f %% of baseline\n', A);
fprintf('  (B) adaptation on top                %.1f %% of baseline\n', B);
fprintf('  adaptation as share of total gain    %.1f %%\n', share);
fprintf('  (A) > (B) at every weight tested     %d\n', all(As > Bs));
fprintf('\n  figures written: fig_master_pareto.png, fig_master_weight.png\n\n');
