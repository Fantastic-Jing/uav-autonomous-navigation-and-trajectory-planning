clc
clear 

disp('Kalman Example')

% Initial state: [x, y, v_x, v_y]
x = [2, 2, 5, 1]';

% Initial covariance (4x4)
P = diag([0.1, 0.1,  1, 1]);

% Define process noise covariance
Q = diag([0.1, 0.1, 0.5, 0.5]); 

% Time step in seconds (Delta t)
dt = 1.0;

% State transition matrix (Phi): x = x + v * dt
Phi = [
[1.0, 0.0, dt, 0.0],
[0.0, 1.0, 0.0, dt],
[0.0, 0.0, 1.0, 0.0],
[0.0, 0.0, 0.0, 1.0]
];

% Control input matrix (B): adding 0.5*a*dt^2
B = [
[0.5 * dt^2, 0.0],
[0.0, 0.5 * dt^2],
[dt, 0.0]
[0.0, dt]
];

% Control input: acceleration in [x, y]
u = [0.5; 0.0];

% Process noise (4x4)
Q = diag([0.1, 0.1, 0.5, 0.5]);

% Prediction from epoch k-1 to k:
x = Phi * x + B * u   % Kinematic prediction with control u
P = Phi * P * Phi' + Q

% Measurement matrix (H) with 2 rows: only the position is measured
H = [
[1.0, 0.0, 0.0, 0.0],
[0.0, 1.0, 0.0, 0.0]
];

z = [7.5; 2.5];

% GNSS position (2D)
R = [0.65, 0.78; 0.78, 1.55]; % Measurement noise (2x2)

I = eye(4);

%--- MEASUREMENT UPDATE (FUSION) ---
S = H * P * H' + R;          % Innovation covariance
K = P * H' * inv(S)         % Kalman Gain
x = x + K * (z - H * x)     % Fused 4D state
P = (I - K * H) * P         % Fused 4x4 covariance

