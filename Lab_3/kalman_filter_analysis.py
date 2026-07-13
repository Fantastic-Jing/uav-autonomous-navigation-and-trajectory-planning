import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def run_offline_filter(csv_path="flight_data.csv"):
    # 1. Load data
    df = pd.read_csv(csv_path)
    N = len(df)

    print("CSV columns successfully loaded:", df.columns.tolist())

    # 2. Calculate barometer offset using first 2 seconds of ground data
    ground_data = df[df['time'] < 2.0]
    if len(ground_data) == 0:
        baro_offset = df['baro_asl'].iloc[0]
    else:
        baro_offset = ground_data['baro_asl'].mean()

    df['baro_corrected'] = df['baro_asl'] - baro_offset

    # 3. Define physical constants
    g_constant = 9.80665
    g_navigation = -9.80665  # Z-axis points up, gravity points down

    # 4. Allocate memory for results
    estimated_z = np.zeros(N)
    estimated_vz = np.zeros(N)
    estimated_ba = np.zeros(N)
    sigma_z = np.zeros(N)  # 1-sigma error band

    # 5. Initialize Kalman filter parameters
    # State vector x = [z, v_z, b_a]
    x = np.array([[df['baro_corrected'].iloc[0]],
                  [0.0],
                  [0.0]])

    # State covariance matrix P
    P = np.diag([0.1, 0.1, 0.01])

    # Process and measurement noise matrices
    Q = np.diag([0.0001, 0.001, 0.00001])
    R = np.array([[0.04]])

    # Measurement matrix H
    H = np.array([[1.0, 0.0, 0.0]])
    I = np.eye(3)

    # 6. Kalman filter loop
    for k in range(1, N):
        # Calculate time step dt
        dt = df['time'].iloc[k] - df['time'].iloc[k - 1]
        if dt <= 0:
            dt = 0.01

        # Get current quaternion and body acceleration
        qw, qx, qy, qz = df['qw'].iloc[k], df['qx'].iloc[k], df['qy'].iloc[k], df['qz'].iloc[k]
        ax_b, ay_b, az_b = df['acc_x'].iloc[k], df['acc_y'].iloc[k], df['acc_z'].iloc[k]

        # Rotate body acceleration to navigation frame
        az_n_g = 2 * (qx * qz - qw * qy) * ax_b + 2 * (qy * qz + qw * qx) * ay_b + (
                    qw ** 2 - qx ** 2 - qy ** 2 + qz ** 2) * az_b

        # Convert unit from G to m/s^2
        az_n = az_n_g * g_constant

        # Build matrices A and B
        A = np.array([[1.0, dt, 0.5 * (dt ** 2)],
                      [0.0, 1.0, dt],
                      [0.0, 0.0, 1.0]])

        B = np.array([[0.5 * (dt ** 2)],
                      [dt],
                      [0.0]])

        # Control input u is vertical acceleration
        u = az_n

        # Prediction step
        x_minus = A @ x + B * (u + g_navigation)
        P_minus = A @ P @ A.T + Q

        # Update step
        y = df['baro_corrected'].iloc[k]

        # Calculate Kalman gain K
        S = H @ P_minus @ H.T + R
        K = P_minus @ H.T @ np.linalg.inv(S)

        # Update state and covariance
        x = x_minus + K @ (y - H @ x_minus)
        P = (I - K @ H) @ P_minus

        # Save filter results
        estimated_z[k] = x[0, 0]
        estimated_vz[k] = x[1, 0]
        estimated_ba[k] = x[2, 0]
        sigma_z[k] = np.sqrt(P[0, 0])

    # Set initial value for the first frame to avoid gaps in plotting
    estimated_z[0] = estimated_z[1]
    sigma_z[0] = sigma_z[1]

    # 7. Plot results
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    time_axis = df['time']

    # Subplot 1: Altitude comparison
    axes[0].plot(time_axis, df['baro_corrected'], label='Raw Baro Altitude', color='red', alpha=0.3)
    axes[0].plot(time_axis, estimated_z, label='Kalman Altitude', color='blue', linewidth=2)
    axes[0].fill_between(time_axis, estimated_z - sigma_z, estimated_z + sigma_z, color='blue', alpha=0.15,
                         label='1-Sigma Error Band')
    axes[0].plot(time_axis, df['ref_z'], label='Lighthouse Altitude (Ground Truth)', color='black', linestyle='--')
    axes[0].set_ylabel('Altitude [m]')
    axes[0].set_title('Kalman Filter States')
    axes[0].legend()
    axes[0].grid(True)

    # Subplot 2: Estimated velocity
    axes[1].plot(time_axis, estimated_vz, label='Estimated V_z', color='orange')
    axes[1].set_ylabel('Velocity [m/s]')
    axes[1].legend()
    axes[1].grid(True)

    # Subplot 3: Estimated accelerometer bias
    axes[2].plot(time_axis, estimated_ba, label='Estimated Accel Bias (b_a)', color='purple')
    axes[2].set_xlabel('Time [s]')
    axes[2].set_ylabel('Bias [m/s^2]')
    axes[2].legend()
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig("kalman_filter_states_output.png", dpi=300)
    plt.show()


if __name__ == '__main__':
    run_offline_filter()