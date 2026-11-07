function test_motion_psf()
% Compare motion_psf against MATLAB fspecial for varied lengths and angles.
% Exact equality is intentional: the exercise targets MATLAB R2023b behavior.

lengths = [0.25, 1, 1.25, 2.5, 5, 9, 13.7, 20];
thetas = [-180, -90, -45, 0, 30, 45, 89.5, 90, 135, 180, 225, 270, 360];
caseCount = 0;
maxAbsError = 0;

for len = lengths
    for theta = thetas
        expected = fspecial('motion', len, theta);
        actual = motion_psf(len, theta);
        caseCount = caseCount + 1;
        assert(isequal(size(actual), size(expected)), ...
            'Size mismatch for LEN=%g, THETA=%g.', len, theta);
        difference = max(abs(actual(:) - expected(:)));
        maxAbsError = max(maxAbsError, difference);
        assert(isequal(actual, expected), ...
            'Kernel mismatch for LEN=%g, THETA=%g; max abs error=%g.', ...
            len, theta, difference);
    end
end

assert(isequal(motion_psf(), fspecial('motion')),...
    'Default call does not match fspecial(''motion'').');
assert(isequal(motion_psf(9), fspecial('motion', 9)),...
    'Default theta does not match fspecial(''motion'', 9).');

fprintf('PASS: %d LEN/THETA pairs and 2 default-call checks match exactly.\n', ...
    caseCount);
fprintf('Maximum absolute element-wise error: %.17g\n', maxAbsError);
fprintf('MATLAB version: %s\n', version);
end
