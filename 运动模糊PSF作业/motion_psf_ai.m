function h = motion_psf_ai(len, theta)
% Motion PSF for a length-len segment at a counterclockwise Cartesian angle.
validateattributes(len, {'numeric'}, {'real','finite','scalar','positive'});
validateattributes(theta, {'numeric'}, {'real','finite','scalar'});
d = [cosd(theta), sind(theta)];
p0 = -len*d/2;
p1 =  len*d/2;
xmin = floor(min(p0(1),p1(1)) - 0.5);
xmax = ceil (max(p0(1),p1(1)) + 0.5);
ymin = floor(min(p0(2),p1(2)) - 0.5);
ymax = ceil (max(p0(2),p1(2)) + 0.5);
h = zeros(ymax-ymin+1, xmax-xmin+1);
for yy = ymin:ymax
    for xx = xmin:xmax
        q = [xx, yy]; lo = 0; hi = 1;
        for k = 1:2
            if d(k) == 0
                if abs(q(k)-p0(k)) > 0.5, lo = 1; hi = 0; end
            else
                t = sort((q(k)+[-0.5 0.5]-p0(k))/d(k));
                lo = max(lo,t(1)); hi = min(hi,t(2));
            end
        end
        h(ymax-yy+1,xx-xmin+1) = len*max(0,hi-lo);
    end
end
h = h/sum(h(:));
[r,c] = find(h > 0);
h = h(min(r):max(r),min(c):max(c));
end
