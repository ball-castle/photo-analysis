function compare_ai_initial()
taskDir = fileparts(mfilename('fullpath'));
logFile = fullfile(taskDir,'results','ai_initial_test_log.txt');
fid = fopen(logFile,'w');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'Actual first-round AI code, tested in MATLAB %s\n',version);
for theta = [0 45 90]
    h = motion_psf_ai(9,theta);
    ref = fspecial('motion',9,theta);
    fprintf(fid,'LEN=9 THETA=%g: AI=%s, reference=%s, isequal=%d\n', ...
        theta,mat2str(size(h)),mat2str(size(ref)),isequal(h,ref));
    fprintf('LEN=9 THETA=%g: AI=%s, reference=%s, isequal=%d\n', ...
        theta,mat2str(size(h)),mat2str(size(ref)),isequal(h,ref));
end
end
