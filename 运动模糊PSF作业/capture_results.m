taskDir = fileparts(mfilename('fullpath'));
resultDir = fullfile(taskDir, 'results');
screenshotDir = fullfile(taskDir, '截图');
logPath = fullfile(resultDir, 'matlab_test_log.txt');
if exist(logPath, 'file'), delete(logPath); end
diary(logPath);
fprintf('Motion PSF exact-comparison run\n');
fprintf('Reference: fspecial(''motion'', LEN, THETA)\n');
test_motion_psf();

angles = [0, 45, 90];
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1440 450]);
palette = interp1([0 0.45 1], [1 1 1; 0.61 0.77 0.84; 0.13 0.30 0.40], ...
    linspace(0,1,256));
colormap(fig, palette);
layout = tiledlayout(fig,1,3,'TileSpacing','compact','Padding','compact');
canvasSize = 9;
for k = 1:numel(angles)
    theta = angles(k);
    h = motion_psf(9, theta);
    fprintf('\nExample LEN=9, THETA=%g degrees; size=%s; sum=%.17g\n', ...
        theta, mat2str(size(h)), sum(h(:)));
    disp(h);
    canvas = zeros(canvasSize, canvasSize);
    rowStart = floor((canvasSize - size(h, 1)) / 2) + 1;
    colStart = floor((canvasSize - size(h, 2)) / 2) + 1;
    canvas(rowStart:rowStart+size(h,1)-1, ...
        colStart:colStart+size(h,2)-1) = h;
    ax = nexttile(layout);
    % Matrix rows increase downward; Cartesian y increases upward.
    imagesc(ax, -4:4, -4:4, flipud(canvas), [0, 1/9]);
    axis image;
    set(ax, 'YDir', 'normal', 'XTick', [-4 0 4], 'YTick', [-4 0 4], ...
        'FontName','Times New Roman','FontSize',16,'TickDir','out', ...
        'XColor',[0.30 0.35 0.39],'YColor',[0.30 0.35 0.39], ...
        'LineWidth',0.7,'TickLength',[0.012 0.012],'Box','on','Layer','top');
    hold(ax,'on');
    for edge=-4.5:1:4.5
        plot(ax,[edge edge],[-4.5 4.5],'-','Color',[0.87 0.90 0.92],'LineWidth',0.35);
        plot(ax,[-4.5 4.5],[edge edge],'-','Color',[0.87 0.90 0.92],'LineWidth',0.35);
    end
    xlim(ax,[-4.5 4.5]); ylim(ax,[-4.5 4.5]);
    xlabel('x / pixel'); ylabel('y / pixel');
    title(sprintf('(%c)  \\theta = %g^{\\circ}', 'a'+k-1, theta), ...
        'FontWeight','normal','Color',[0.13 0.24 0.31],'FontSize',18);
end
cb = colorbar;
cb.Layout.Tile = 'east';
cb.Label.String = 'h';
cb.FontName = 'Times New Roman';
cb.FontSize = 15;
cb.Ticks = [0 0.04 0.08 1/9];
cb.TickLabels = {'0','0.04','0.08','0.111'};
cb.Color = [0.30 0.35 0.39];
exportgraphics(fig, fullfile(screenshotDir, 'psf_kernels.png'), 'Resolution', 250);
close(fig);
diary off;
fprintf('Saved MATLAB results and PSF plot.\n');
