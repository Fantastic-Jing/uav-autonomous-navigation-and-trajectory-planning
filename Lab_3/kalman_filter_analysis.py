import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def run_offline_filter(csv_path="flight_data.csv"):
    # 1. 读取数据
    df = pd.read_csv(csv_path)
    N = len(df)

    # 打印实际列名进行确认
    print("CSV columns successfully loaded:", df.columns.tolist())

    # 2. 计算气压计零偏（利用前2秒在地面静止的数据）
    ground_data = df[df['time'] < 2.0]
    if len(ground_data) == 0:
        baro_offset = df['baro_asl'].iloc[0]
    else:
        baro_offset = ground_data['baro_asl'].mean()

    df['baro_corrected'] = df['baro_asl'] - baro_offset

    # 3. 基础物理常量定义
    g_constant = 9.80665
    g_navigation = -9.80665  # Z轴向上，重力加速度向下

    # 4. 预留结果存储空间
    estimated_z = np.zeros(N)
    estimated_vz = np.zeros(N)
    estimated_ba = np.zeros(N)
    sigma_z = np.zeros(N)  # 存储 1-sigma 误差范围

    # 5. 初始化卡尔曼滤波器参数
    # 状态向量初始化 x = [z, v_z, b_a]
    x = np.array([[df['baro_corrected'].iloc[0]],
                  [0.0],
                  [0.0]])

    # 状态协方差矩阵 P 初始化
    P = np.diag([0.1, 0.1, 0.01])

    # 噪声矩阵设定（通过匹配老师数据微调后的合理值）
    Q = np.diag([0.0001, 0.001, 0.00001])
    R = np.array([[0.04]])

    # 观测矩阵 H
    H = np.array([[1.0, 0.0, 0.0]])
    I = np.eye(3)

    # 6. 卡尔曼滤波核心循环
    for k in range(1, N):
        # 计算动态时间步长 dt（使用老师文件中的 'time' 列）
        dt = df['time'].iloc[k] - df['time'].iloc[k - 1]
        if dt <= 0:
            dt = 0.01

        # 提取当前时刻的四元数和机体系加速度
        qw, qx, qy, qz = df['qw'].iloc[k], df['qx'].iloc[k], df['qy'].iloc[k], df['qz'].iloc[k]
        ax_b, ay_b, az_b = df['acc_x'].iloc[k], df['acc_y'].iloc[k], df['acc_z'].iloc[k]

        # 坐标变换：将机体系加速度转至地球系
        az_n_g = 2 * (qx * qz - qw * qy) * ax_b + 2 * (qy * qz + qw * qx) * ay_b + (
                    qw ** 2 - qx ** 2 - qy ** 2 + qz ** 2) * az_b

        # 将单位从 G 转换为 m/s^2
        az_n = az_n_g * g_constant

        # 构建状态转移矩阵 A 与控制矩阵 B
        A = np.array([[1.0, dt, 0.5 * (dt ** 2)],
                      [0.0, 1.0, dt],
                      [0.0, 0.0, 1.0]])

        B = np.array([[0.5 * (dt ** 2)],
                      [dt],
                      [0.0]])

        # 控制输入 u 为导航系垂直加速度
        u = az_n

        # 预测步 (Prediction Step)
        x_minus = A @ x + B * (u + g_navigation)
        P_minus = A @ P @ A.T + Q

        # 更新步 (Update Step)
        y = df['baro_corrected'].iloc[k]

        # 计算卡尔曼增益 K
        S = H @ P_minus @ H.T + R
        K = P_minus @ H.T @ np.linalg.inv(S)

        # 更新状态与协方差矩阵
        x = x_minus + K @ (y - H @ x_minus)
        P = (I - K @ H) @ P_minus

        # 存储滤波解算结果
        estimated_z[k] = x[0, 0]
        estimated_vz[k] = x[1, 0]
        estimated_ba[k] = x[2, 0]
        sigma_z[k] = np.sqrt(P[0, 0])

    # 填充第一帧的初始值避免绘图断点
    estimated_z[0] = estimated_z[1]
    sigma_z[0] = sigma_z[1]

    # 7. 数据可视化绘图 (Evaluation & Plotting)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    time_axis = df['time']

    # 子图 1: 高度曲线与误差带对比（使用 ref_z 作为 Ground Truth）
    axes[0].plot(time_axis, df['baro_corrected'], label='Raw Baro Altitude', color='red', alpha=0.3)
    axes[0].plot(time_axis, estimated_z, label='Kalman Altitude', color='blue', linewidth=2)
    axes[0].fill_between(time_axis, estimated_z - sigma_z, estimated_z + sigma_z, color='blue', alpha=0.15,
                         label='1-Sigma Error Band')
    axes[0].plot(time_axis, df['ref_z'], label='Lighthouse Altitude (Ground Truth)', color='black', linestyle='--')
    axes[0].set_ylabel('Altitude [m]')
    axes[0].set_title('Kalman Filter States')
    axes[0].legend()
    axes[0].grid(True)

    # 子图 2: 估计的垂直速度
    axes[1].plot(time_axis, estimated_vz, label='Estimated V_z', color='orange')
    axes[1].set_ylabel('Velocity [m/s]')
    axes[1].legend()
    axes[1].grid(True)

    # 子图 3: 加速度计垂直零偏游走
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