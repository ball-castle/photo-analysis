root = 'C:/Users/CAI BIN/Desktop/photo_analysis/output';
outDir = 'C:/Users/CAI BIN/Desktop/photo_analysis/output/round2_final/verification_results';
inputPath = fullfile(root, 'data', 'processed', 'dark_face_512.png');
pythonPath = fullfile(root, 'results', 'histogram_equalized.png');
I = imread(inputPath);
P = imread(pythonPath);
if ~isequal(size(I), size(P)) || ~isequal(size(I), [512 512]) || ~isa(I, 'uint8') || ~isa(P, 'uint8')
    error('Input and Python result must be aligned 512-by-512 uint8 grayscale images.');
end
J64 = histeq(I);
J256 = histeq(I, 256);
counts = imhist(I, 256);
cdf = cumsum(double(counts)) / numel(I);
mapDirect = uint8(min(max(round(255 * cdf), 0), 255));
Pdirect = mapDirect(double(I) + 1);
occupied = find(counts > 0, 1, 'first');
cdfmin = cdf(occupied);
mapCdfMin = uint8(min(max(round(255 * (cdf - cdfmin) / (1 - cdfmin)), 0), 255));
Pcdfmin = mapCdfMin(double(I) + 1);
methods = string({'MATLAB histeq(I), default'; 'MATLAB histeq(I,256)'; 'Direct full-CDF mapping'; 'Python CDF-min mapping reproduced'});
outputs = {J64, J256, Pdirect, Pcdfmin};
maePython = zeros(4,1); maxDiffPython = zeros(4,1); uniqueLevels = zeros(4,1); meanGray = zeros(4,1);
for k = 1:4
    D = abs(double(outputs{k}) - double(P));
    maePython(k) = mean(D(:));
    maxDiffPython(k) = max(D(:));
    uniqueLevels(k) = numel(unique(outputs{k}));
    meanGray(k) = mean(double(outputs{k}(:)));
end
T = table(methods, maePython, maxDiffPython, uniqueLevels, meanGray, ...
    'VariableNames', {'method','mae_vs_python','max_abs_diff_vs_python','unique_output_levels','output_mean_gray'});
writetable(T, fullfile(outDir, 'histeq_method_comparison.csv'));
imwrite(J64, fullfile(outDir, 'matlab_histeq_default64.png'));
imwrite(J256, fullfile(outDir, 'matlab_histeq_256.png'));
fid = fopen(fullfile(outDir, 'histeq_bin_comparison.txt'), 'w');
fprintf(fid, 'MATLAB_VERSION=%s\n', version);
fprintf(fid, 'INPUT_PATH=%s\n', inputPath);
fprintf(fid, 'PYTHON_RESULT_PATH=%s\n', pythonPath);
fprintf(fid, 'INPUT_SIZE=%d x %d\n', size(I,1), size(I,2));
fprintf(fid, 'INPUT_CLASS=%s\n', class(I));
fprintf(fid, 'PYTHON_OUTPUT_CLASS=%s\n', class(P));
fprintf(fid, 'MATLAB_DEFAULT_BINS=64 (MathWorks documentation)\n');
fprintf(fid, 'DEFAULT64_VS_256_MAE=%.9f\n', mean(abs(double(J64(:))-double(J256(:)))));
fprintf(fid, 'MATLAB256_VS_DIRECT_FULL_CDF_MAE=%.9f\n', mean(abs(double(J256(:))-double(Pdirect(:)))));
fprintf(fid, 'PYTHON_CDFMIN_RECONSTRUCTION_MAE=%.9f\n', mean(abs(double(Pcdfmin(:))-double(P(:)))));
fclose(fid);
disp(fileread(fullfile(outDir, 'histeq_bin_comparison.txt')));
disp(T);
