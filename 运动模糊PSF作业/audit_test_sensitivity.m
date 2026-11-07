function audit_test_sensitivity()
% Check that equality tests reject four plausible implementation mistakes.
root = fileparts(mfilename('fullpath'));
mutantDir = fullfile(root,'tmp','mutants');
if ~exist(mutantDir,'dir'), mkdir(mutantDir); end
source = fileread(fullfile(root,'motion_psf.m'));
names = {'wrong_half_length','missing_flip','missing_eps','degree_trig'};
before = {'halfLength = (len - 1) / 2;', ...
    'if cosPhi > 0, h = flipud(h); end', ...
    'h = h ./ (sum(h(:)) + eps*len*len);', ...
    'cosPhi = cos(phi);'};
after = {'halfLength = len / 2;', ...
    '% intentionally omitted flip', ...
    'h = h ./ sum(h(:));', ...
    'cosPhi = cosd(mod(theta,180));'};
params = [9 0;9 30;9 45;9 89.5;9 90;13.7 135];
addpath(mutantDir);
pathCleanup = onCleanup(@() rmpath(mutantDir));
fid = fopen(fullfile(root,'results','test_sensitivity_log.txt'),'w');
fileCleanup = onCleanup(@() fclose(fid));
for k=1:numel(names)
    functionName = ['mutant_' names{k}];
    assert(contains(source,before{k}));
    modified = strrep(source,'function h = motion_psf(', ...
        ['function h = ' functionName '(']);
    modified = strrep(modified,before{k},after{k});
    if k==4
        modified = strrep(modified,'sinPhi = sin(phi);', ...
            'sinPhi = sind(mod(theta,180));');
    end
    codeFid = fopen(fullfile(mutantDir,[functionName '.m']),'w');
    fwrite(codeFid,modified); fclose(codeFid);
    caught = false;
    for j=1:size(params,1)
        actual = feval(functionName,params(j,1),params(j,2));
        ref = fspecial('motion',params(j,1),params(j,2));
        if ~isequal(actual,ref)
            caught = true;
            fprintf(fid,'%s: DETECTED at LEN=%g THETA=%g\n', ...
                names{k},params(j,1),params(j,2));
            break;
        end
    end
    assert(caught,'Tests failed to reject mutant %s.',names{k});
end
fprintf(fid,'All 4 plausible faults were detected.\n');
fprintf('PASS: All 4 deliberate faults were detected.\n');
end
