function compare_overlap()
root = fileparts(mfilename('fullpath'));
fid = fopen(fullfile(root,'results','overlap_test_log.txt'),'w');
cleanup = onCleanup(@() fclose(fid));
for theta = [0 45 90]
    h = motion_psf_overlap(9,theta);
    ref = fspecial('motion',9,theta);
    fprintf(fid,'LEN=9 THETA=%g: corrected=%s, reference=%s, isequal=%d', ...
        theta,mat2str(size(h)),mat2str(size(ref)),isequal(h,ref));
    if isequal(size(h),size(ref))
        fprintf(fid,', max_abs_error=%.17g',max(abs(h(:)-ref(:))));
    end
    fprintf(fid,'\n');
end
fprintf('Saved corrected-parameterization comparison.\n');
end
