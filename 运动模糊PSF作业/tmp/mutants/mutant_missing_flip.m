function h = mutant_missing_flip(len, theta)
%MOTION_PSF Motion-blur PSF compatible with MATLAB R2023b fspecial.
% Discretization follows the R2023b fspecial motion branch.
% LEN is in pixels; THETA is counter-clockwise from the horizontal axis.
narginchk(0, 2);
if nargin < 1, len = 9; end
if nargin < 2, theta = 0; end
validateattributes(len, {'double'}, ...
    {'positive','finite','real','nonempty','scalar'}, mfilename, 'LEN', 1);
validateattributes(theta, {'double'}, ...
    {'finite','real','nonempty','scalar'}, mfilename, 'THETA', 2);
len = max(1, len);
halfLength = (len - 1) / 2;
phi = mod(theta, 180) / 180 * pi;
cosPhi = cos(phi);
sinPhi = sin(phi);
xSign = sign(cosPhi);
lineWidth = 1;

% Smallest half-grid for this angle.
sx = fix(halfLength*cosPhi + lineWidth*xSign - len*eps);
sy = fix(halfLength*sinPhi + lineWidth - len*eps);
[x, y] = meshgrid(0:xSign:sx, 0:sy);

% Perpendicular distance, with endpoint correction.
distToLine = y*cosPhi - x*sinPhi;
radialDistance = sqrt(x.^2 + y.^2);
lastPixel = find((radialDistance >= halfLength) & ...
    (abs(distToLine) <= lineWidth));
parallelEndpointDistance = halfLength - abs( ...
    (x(lastPixel) + distToLine(lastPixel)*sinPhi) / cosPhi);
distToLine(lastPixel) = sqrt( ...
    distToLine(lastPixel).^2 + parallelEndpointDistance.^2);

% Convert distance to weights, mirror, and normalize.
distToLine = lineWidth + eps - abs(distToLine);
distToLine(distToLine < 0) = 0;
h = rot90(distToLine, 2);
h(end+(1:end)-1, end+(1:end)-1) = distToLine;
h = h ./ (sum(h(:)) + eps*len*len);
% intentionally omitted flip
end
