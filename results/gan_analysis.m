%% GAN_ANALYSIS  Analysis of the segmented GaN gate-driver sweep.
%
%  Put this file and sweep_matlab.csv in the same folder, then run:
%      >> gan_analysis
%
%  Works in MATLAB and in GNU Octave (no toolboxes required -- only core
%  functions, so it runs on a basic MATLAB Online licence).
%
%  Part 1  Pareto analysis of the 720-point control-word sweep
%  Part 2  Schedule look-up table extraction
%  Part 3  Analytical crosstalk model checked against the SPICE result

clear; clc; close all;

%% ------------------------------------------------------------------
%  Load
%% ------------------------------------------------------------------
f = 'sweep_matlab.csv';
if exist(f,'file') ~= 2
    error('gan_analysis:missing', ...
          'Cannot find %s. Upload it into the same folder as this script.', f);
end
D = dlmread(f, ',', 1, 0);          % skip the one header row

NPU=D(:,1); NPD=D(:,2); NPD_HS=D(:,3); DT=D(:,4); CLK=D(:,5); VNEG=D(:,6);
E_on=D(:,7); E_off=D(:,8); E_dt=D(:,9); E_tot=D(:,10);
ov=D(:,11); margin=D(:,12); spur=D(:,13);
N = numel(E_tot);
fprintf('Loaded %d control words.\n\n', N);

%% ------------------------------------------------------------------
%  Part 1 -- feasibility and the Pareto front
%% ------------------------------------------------------------------
VTH = 1.4;
ok  = margin > 0;                        % no false turn-on
fprintf('=== Part 1: Pareto ===\n');
fprintf('Feasible words (no false turn-on): %d of %d  (%.0f%%)\n', ...
        sum(ok), N, 100*sum(ok)/N);

x = E_tot(ok); y = ov(ok);
front = false(size(x));
for i = 1:numel(x)
    dominated = any( x <= x(i) & y <= y(i) & (x < x(i) | y < y(i)) );
    front(i) = ~dominated;
end
[xf, idx] = sort(x(front)); yf = y(front); yf = yf(idx);
fprintf('Pareto front: %d words\n', numel(xf));

if numel(xf) > 1 && (yf(1) - yf(end)) > 0
    rate = (xf(end) - xf(1)) / (yf(1) - yf(end));
    fprintf('Exchange rate: %.4f uJ of loss per point of overshoot removed\n', rate);
    fprintf('               (at a 100 V bus, %.4f uJ per volt)\n', rate);
end

%  margin bought per ns of dead time, at 0 V off-bias, clamp off
sel = (VNEG==0) & (CLK==0);
dts = unique(DT(sel));
mbar = zeros(size(dts));
for k = 1:numel(dts)
    mbar(k) = mean(margin(sel & DT==dts(k)));
end
%  Do NOT fit a straight line here: the relationship saturates hard, and a
%  single slope (least-squares or endpoint) is a misleading summary.  Report
%  the marginal gain segment by segment instead.
fprintf('Crosstalk margin vs dead time (0 V off-bias, clamp off):\n');
for k = 1:numel(dts)
    if k == 1
        fprintf('   %5.0f ns  %+6.3f V\n', dts(k), mbar(k));
    else
        rate = 1000*(mbar(k)-mbar(k-1))/(dts(k)-dts(k-1));
        fprintf('   %5.0f ns  %+6.3f V   marginal gain %7.1f mV/ns\n', ...
                dts(k), mbar(k), rate);
    end
end
knee = dts(find(diff(mbar) < 0.05*max(diff(mbar)), 1));
if ~isempty(knee)
    fprintf('   -> saturates around %g ns; beyond that dead time costs\n', knee);
    fprintf('      conduction loss and buys essentially no margin.\n');
end

%  the GaN-specific negative-bias trade
for vn = [0 -2]
    s = (VNEG==vn) & (CLK==0) & (DT==max(dts));
    fprintf('  V_GS,off = %+d V at %g ns: margin %+.2f V, E_dt %.2f uJ\n', ...
            vn, max(dts), mean(margin(s)), mean(E_dt(s)));
end
fprintf('\n');

%% ------------------------------------------------------------------
%  Part 2 -- schedule LUT
%% ------------------------------------------------------------------
fprintf('=== Part 2: schedule LUT ===\n');
%  Cost function stated explicitly: minimise loss, penalise overshoot,
%  hard-reject anything that false-turns-on.
W_OV   = 0.05;                    % uJ per point of overshoot
cost   = E_tot + W_OV*ov;
cost(~ok) = Inf;                  % infeasible
[cbest, ibest] = min(cost);
fprintf('Cost = E_tot + %.2f*overshoot, infeasible words rejected.\n', W_OV);
fprintf('Best word: NPU=%d NPD=%d NPD_HS=%d DT=%gns CLKEN=%d VNEG=%gV\n', ...
        NPU(ibest), NPD(ibest), NPD_HS(ibest), DT(ibest), CLK(ibest), VNEG(ibest));
fprintf('  -> E_tot %.2f uJ, overshoot %.1f%%, margin %+.2f V, cost %.3f\n\n', ...
        E_tot(ibest), ov(ibest), margin(ibest), cbest);

%% ------------------------------------------------------------------
%  Part 3 -- analytical crosstalk model vs SPICE
%% ------------------------------------------------------------------
%  The textbook picture is a C_GD / C_GS capacitive divider: the switching
%  device's dV/dt drives current through C_GD into the off device's gate,
%  and the driver's pull-down resistance turns that current into a voltage.
%
%  Two limiting cases bracket it, and they are far apart because C_GD is
%  strongly non-linear (150 pF near 0 V, ~7 pF at 100 V):
%
%    peak-C bound      V = R_g * C_GD(0)  * dV/dt      (worst instant)
%    charge-average    V = R_g * Q_GD/t_slew           (whole transition)
%
fprintf('=== Part 3: analytical crosstalk model vs SPICE ===\n');
CGD0 = 150e-12; VJ = 1.0; M = 0.65; CGS = 350e-12;
VBUS = 100; R_G = 1.0;                       % 8 slices of 8 ohm in parallel

cgd  = @(v) CGD0 ./ (1 + v/VJ).^M;
vv   = linspace(0, VBUS, 4001);
Q_GD = trapz(vv, cgd(vv));                   % C, Miller charge over the swing
fprintf('Q_GD over 0..%g V = %.3f nC   (C_GD: %.0f pF at 0 V, %.1f pF at %g V)\n', ...
        VBUS, Q_GD*1e9, cgd(0)*1e12, cgd(VBUS)*1e12, VBUS);

dvdt = (10:5:100)*1e9;                       % V/s
t_sl = VBUS ./ dvdt;
v_peakC = R_G * cgd(0) * dvdt;
v_charge = R_G * Q_GD ./ t_sl;

SPICE_SPUR = 1.65;  SPICE_DVDT = 50e9;       % measured, fastest driver
i50 = find(abs(dvdt - SPICE_DVDT) < 1e6, 1);
fprintf('At dV/dt = %g V/ns:\n', SPICE_DVDT/1e9);
fprintf('   peak-C bound      %6.2f V\n', v_peakC(i50));
fprintf('   charge-average    %6.2f V\n', v_charge(i50));
fprintf('   SPICE (measured)  %6.2f V   <- threshold is %.2f V\n', SPICE_SPUR, VTH);
if SPICE_SPUR > v_charge(i50) && SPICE_SPUR < v_peakC(i50)
    fprintf('   The measurement sits INSIDE the bracket, as it should.\n');
    fprintf('   Neither bound is usable as a design number: they differ by %.1fx.\n', ...
            v_peakC(i50)/v_charge(i50));
    fprintf('   That gap is the argument for simulating rather than hand-calculating.\n');
else
    fprintf('   NOTE: measurement falls outside the bracket - worth investigating.\n');
end
fprintf('\n');

%% ------------------------------------------------------------------
%  Figures
%% ------------------------------------------------------------------
figure('Name','Pareto front','Color','w');
plot(E_tot(~ok), ov(~ok), '.', 'Color', [0.80 0.55 0.50]); hold on;
plot(E_tot(ok),  ov(ok),  '.', 'Color', [0.72 0.76 0.80]);
plot(xf, yf, 'o-', 'LineWidth', 1.6, 'MarkerSize', 6, 'Color', [0.16 0.47 0.84]);
plot(E_tot(ibest), ov(ibest), 'p', 'MarkerSize', 14, 'MarkerFaceColor', [0.05 0.42 0.27], ...
     'MarkerEdgeColor','none');
xlabel('Total loss per cycle  E_{on}+E_{off}+E_{dt}  (\muJ)');
ylabel('Drain overshoot (% of V_{bus})');
title(sprintf('Control-word sweep: %d words, %d feasible', N, sum(ok)));
legend('false turn-on','feasible','Pareto front','LUT choice','Location','NorthEast');
grid on; box off;
print('-dpng','-r150','pareto_matlab.png');

figure('Name','Crosstalk model','Color','w');
semilogy(dvdt/1e9, v_peakC, '-',  'LineWidth', 1.6, 'Color', [0.63 0.24 0.18]); hold on;
semilogy(dvdt/1e9, v_charge,'-',  'LineWidth', 1.6, 'Color', [0.16 0.47 0.84]);
semilogy(SPICE_DVDT/1e9, SPICE_SPUR, 'o', 'MarkerSize', 9, 'LineWidth', 2, ...
         'Color', [0.05 0.30 0.20]);
semilogy([min(dvdt) max(dvdt)]/1e9, [VTH VTH], '--', 'Color', [0.63 0.24 0.18]);
xlabel('Switch-node slew rate  dV/dt  (V/ns)');
ylabel('Spurious gate voltage (V)');
title('Analytical bracket vs SPICE');
legend('peak-C bound','charge-average','SPICE measurement','V_{th} = 1.4 V', ...
       'Location','SouthEast');
grid on; box off;
print('-dpng','-r150','crosstalk_model_matlab.png');

fprintf('Wrote pareto_matlab.png and crosstalk_model_matlab.png\n');
