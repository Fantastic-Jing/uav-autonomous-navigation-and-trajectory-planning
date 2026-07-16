import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""
DISCUSSION:

1. How is the subtraction of gravity handled?
The accelerometer measures total force in the local body frame. The code 
rotates the 3D acceleration vector into the world frame using the rotation 
matrix. Then, it subtracts 9.81 from the vertical Z component to remove 
the effect of gravity.

2. What values did you ultimately choose for Q and R, and how did changing 
   them affect the "lag" vs. "smoothness" of your plot?
Chosen values: acc_std = 0.05, process_noise_acc = 0.0001, baro_std = 1.25.
Changing these values creates a trade-off:
- Increasing baro_std (larger R) or decreasing acc_std (smaller Q) makes 
  the plot smoother because the filter trusts the IMU more, but it adds lag.
- Decreasing baro_std (smaller R) or increasing acc_std (larger Q) makes 
  the filter trust the barometer more, which reduces lag but adds noise.
"""

def quat_to_matrix(q):
    """Convert unit quaternion to 3x3 rotation matrix."""
    a, b, c, d = q
    return np.array([
        [a * a + b * b - c * c - d * d, 2 * (b * c - a * d), 2 * (b * d + a * c)],
        [2 * (b * c + a * d), a * a - b * b + c * c - d * d, 2 * (c * d - a * b)],
        [2 * (b * d - a * c), 2 * (c * d + a * b), a * a - b * b - c * c + d * d]
    ])


def run_altitude_filter(csv_path="flight_data.csv"):
    df = pd.read_csv(csv_path)
    N = len(df)
    G_CONSTANT = 9.80665

    # Calculate average initial altitude to remove sensor offset
    ground_data = df[df['time'] <= 2.5]
    h0 = ground_data['baro_asl'].mean() if len(ground_data) > 0 else df['baro_asl'].iloc[0]
    df['baro_corrected'] = df['baro_asl'] - h0

    # Filter tuning parameters
    # acc_std: Increase for high vibration, decrease for low vibration
    acc_std = 0.05
    # process_noise_acc: Increase for faster bias change, decrease for smoother bias
    process_noise_acc = 0.0001
    # baro_std: Increase to trust IMU more (smoother but lags), decrease to trust baro more (faster but noisier)
    baro_std = 1.25

    # State vector: [altitude, velocity, acceleration bias]
    x = np.array([df['baro_corrected'].iloc[0], 0.0, 0.0])

    # Initialize covariance and measurement matrices
    # P = np.eye(3)
    P = np.diag([
        0.1 ** 2,  # z uncertainty
        0.1 ** 2,  # vz uncertainty
        0.01 ** 2  # bias uncertainty
    ]).astype(float)
    H = np.array([[1.0, 0.0, 0.0]])

    # Lists to save results
    heights, velocities, sigmas, biases, bias_sigmas = [], [], [], [], []

    # Main loop
    for i in range(N):
        if i == 0:
            dt = 0.01
        else:
            dt = df['time'].iloc[i] - df['time'].iloc[i - 1]
            if dt <= 0: dt = 0.01

        # 1. Prediction Step
        Phi = np.array([
            [1.0, dt, 0.5 * (dt ** 2)],
            [0.0, 1.0, dt],
            [0.0, 0.0, 1.0]
        ])
        B = np.array([0.5 * (dt ** 2), dt, 0.0])

        # Get values and convert acceleration from g to m/s^2
        qw, qx, qy, qz = df['qw'].iloc[i], df['qx'].iloc[i], df['qy'].iloc[i], df['qz'].iloc[i]
        ax_ms2 = df['acc_x'].iloc[i] * G_CONSTANT
        ay_ms2 = df['acc_y'].iloc[i] * G_CONSTANT
        az_ms2 = df['acc_z'].iloc[i] * G_CONSTANT

        # Rotate acceleration to world frame and subtract gravity
        R_rot = quat_to_matrix([qw, qx, qy, qz])
        a_z = (R_rot @ np.array([ax_ms2, ay_ms2, az_ms2]))[2] - 9.81

        # Update state prediction
        x = Phi @ x + B * a_z

        # Calculate process noise covariance matrix
        q_a = acc_std ** 2
        q_b = process_noise_acc ** 2
        B_mat = B.reshape(3, 1)
        Q_acc = B_mat @ [[q_a]] @ B_mat.T + np.diag([0.0, 0.0, q_b])

        # Update covariance prediction
        P = Phi @ P @ Phi.T + Q_acc

        # 2. Correction Step
        h_baro = df['baro_corrected'].iloc[i]

        # Calculate innovation and Kalman gain
        y = h_baro - (H @ x)[0]
        S = (H @ P @ H.T)[0, 0] + baro_std ** 2
        K = (P @ H.T) / S

        # Update state and covariance with measurement
        x = x + (K * y).ravel()
        P = (np.eye(3) - K @ H) @ P

        # Save data for plotting
        heights.append(x[0])
        velocities.append(x[1])
        sigmas.append(np.sqrt(P[0, 0]))
        biases.append(x[2])
        bias_sigmas.append(np.sqrt(P[2, 2]))

    # Plot results
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    t = df['time'].to_numpy()

    axes[0].plot(t, df['baro_corrected'], label='Raw Baro', alpha=0.3, color='red')
    axes[0].plot(t, heights, label='Kalman Height', color='blue', linewidth=2)
    axes[0].plot(t, df['ref_z'], label='Reference Truth', color='green', linestyle='--')
    axes[0].fill_between(t, np.array(heights) - np.array(sigmas), np.array(heights) + np.array(sigmas), color='blue',
                         alpha=0.2, label='1-sigma')
    axes[0].set_ylabel('Altitude [m]')
    axes[0].set_title('Kalman Filter Altitude Estimation')
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(t, velocities, label='Estimated v_z', color='orange', linewidth=2)
    axes[1].set_ylabel('Velocity [m/s]')
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(t, biases, label='Estimated Bias', color='purple', linewidth=2)
    axes[2].fill_between(t, np.array(biases) - np.array(bias_sigmas), np.array(biases) + np.array(bias_sigmas),
                         color='purple', alpha=0.2)
    axes[2].set_xlabel('Time [s]')
    axes[2].set_ylabel('Bias [m/s²]')
    axes[2].legend()
    axes[2].grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    run_altitude_filter()