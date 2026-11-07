% Optional comparison only. Core experiment outputs are produced in Python.
% Run from the output directory in MATLAB R2023b with Image Processing Toolbox:
%   matlab -batch "run('matlab_compare_histeq.m')"
inputImage = imread(fullfile('data', 'processed', 'dark_face_512.png'));
if size(inputImage, 3) ~= 1
    error('Expected the prepared 512-by-512 grayscale input.');
end
matlabResult = histeq(inputImage);
imwrite(matlabResult, fullfile('results', 'matlab_histeq.png'));
pythonResult = imread(fullfile('results', 'histogram_equalized.png'));
absoluteDifference = abs(double(matlabResult) - double(pythonResult));
fprintf('MATLAB_VERSION=%s\n', version);
fprintf('INPUT_SIZE=%d x %d\n', size(inputImage, 1), size(inputImage, 2));
fprintf('FUNCTION=histeq (Image Processing Toolbox)\n');
fprintf('OUTPUT_CLASS=%s\n', class(matlabResult));
fprintf('MAE_VS_PYTHON=%.6f\n', mean(absoluteDifference(:)));
fprintf('MAX_ABS_DIFF_VS_PYTHON=%.0f\n', max(absoluteDifference(:)));
