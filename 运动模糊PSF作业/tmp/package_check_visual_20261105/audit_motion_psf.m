function audit_motion_psf()
% Independent parameter stress checks against MATLAB R2023b.
taskDir = fileparts(mfilename('fullpath'));
rng(20261105, 'twister');
boundaryLengths = [eps, 0.999999, 1, 1+eps, 2, 3, ...
    9-eps(9), 9+eps(9), 31, 64.5, 100];
angleCenters = [-180, -90, 0, 90, 180, 270, 360];
boundaryAngles = zeros(1,5*numel(angleCenters));
for j=1:numel(angleCenters)
    center = angleCenters(j);
    step = eps(max(1,abs(center)));
    boundaryAngles((j-1)*5+(1:5)) = ...
        center + [-1e-10,-step,0,step,1e-10];
end
assert(numel(unique(boundaryAngles))==35, 'Duplicate boundary angles.');
[ll, tt] = ndgrid(boundaryLengths, boundaryAngles);
cases = [ll(:), tt(:); 0.05+100*rand(1000,1), -720+1440*rand(1000,1)];
group = [repmat("boundary", numel(ll), 1); repmat("random", 1000, 1)];
numCases = size(cases,1);
rows = zeros(numCases,1); cols = rows; errors = rows; massErrors = rows;
for k = 1:numCases
    len = cases(k,1); theta = cases(k,2);
    actual = motion_psf(len,theta);
    expected = fspecial('motion',len,theta);
    assert(isequal(size(actual),size(expected)), 'Size mismatch, case %d.',k);
    errors(k) = max(abs(actual(:)-expected(:)));
    assert(isequal(actual,expected), 'Element mismatch, case %d.',k);
    assert(all(isfinite(actual(:))) && all(actual(:)>=0), ...
        'Invalid coefficients, case %d.',k);
    assert(isequal(actual,rot90(actual,2)), 'Symmetry mismatch, case %d.',k);
    massErrors(k) = abs(sum(actual(:))-1);
    assert(massErrors(k)<1e-12, 'Mass mismatch, case %d.',k);
    [rows(k),cols(k)] = size(actual);
end
csvPath = fullfile(taskDir,'results','adversarial_cases.csv');
csvFid = fopen(csvPath,'w');
fprintf(csvFid,'group,LEN,THETA,rows,cols,max_abs_error,sum_error\n');
for k=1:numCases
    fprintf(csvFid,'%s,%.17g,%.17g,%d,%d,%.17g,%.17g\n', ...
        group(k),cases(k,1),cases(k,2),rows(k),cols(k),errors(k),massErrors(k));
end
fclose(csvFid);
parsed = readtable(csvPath);
assert(isequal(parsed.LEN,cases(:,1)) && isequal(parsed.THETA,cases(:,2)), ...
    'CSV parameter precision was lost.');
fid = fopen(fullfile(taskDir,'results','adversarial_test_log.txt'),'w');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'MATLAB version: %s\n',version);
fprintf(fid,'Random seed: 20261105 (twister)\n');
fprintf(fid,'Boundary cases: %d / %d exact\n',numel(ll),numel(ll));
fprintf(fid,'Random cases: 1000 / 1000 exact\n');
fprintf(fid,'Maximum absolute element-wise error: %.17g\n',max(errors));
fprintf(fid,'Maximum abs(sum(h)-1): %.17g\n',max(massErrors));
fprintf(fid,'Finite, nonnegative and centrosymmetric: %d / %d\n',numCases,numCases);
fprintf('PASS: %d boundary and 1000 random cases match exactly.\n',numel(ll));
fprintf('Maximum absolute element-wise error: %.17g\n',max(errors));
end
