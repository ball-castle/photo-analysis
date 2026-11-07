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
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1400 430]);
colormap(fig, parula(256));
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
        'FontName','Times New Roman','FontSize',15,'TickDir','out');
    xlabel('x (pixel)'); ylabel('y (pixel)');
    title(sprintf('(%c)  %g deg,  %d x %d', 'a'+k-1, theta, size(h)), ...
        'FontWeight','normal');
end
cb = colorbar;
cb.Layout.Tile = 'east';
cb.Label.String = 'PSF coefficient';
exportgraphics(fig, fullfile(screenshotDir, 'psf_kernels.png'), 'Resolution', 220);
close(fig);
diary off;
fprintf('Saved MATLAB results and PSF plot.\n');
