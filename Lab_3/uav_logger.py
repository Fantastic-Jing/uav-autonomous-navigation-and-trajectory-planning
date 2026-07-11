import sys
import time
import csv
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# 替换为你的无人机实际通信地址
URI = 'radio://0/80/2M/DABADA55XX'

lh_deck_attached = Event()
logging_complete = Event()

def param_deck_lighthouse(_, value_str):
    if int(value_str):
        lh_deck_attached.set()

def pre_flight_check(scf):
    print("--- Starting Pre-Flight Check ---")
    scf.cf.param.add_update_callback(
        group='deck', name='bcLighthouse4', cb=param_deck_lighthouse
    )
    time.sleep(1)

    if not lh_deck_attached.is_set():
        print("[FAIL] Lighthouse deck not detected.")
        return False
    print("[OK] Lighthouse deck detected.")
    return True

def start_high_speed_logging(scf, output_filename="uav_data_log.csv", duration_seconds=30.0):
    """配置高频异步日志并采集数据"""
    print(f"\n--- Starting Data Acquisition ({duration_seconds}s) ---")
    print("Please move the drone up and down by hand now...")

    # 打开 CSV 文件准备写入
    csv_file = open(output_filename, mode='w', newline='')
    csv_writer = csv.writer(csv_file)
    
    # 写入表头
    header = ['timestamp', 'baro_asl', 'acc_x', 'acc_y', 'acc_z', 'qw', 'qx', 'qy', 'qz', 'state_z']
    csv_writer.writerow(header)

    # 配置日志通道，周期设为 10ms (100 Hz)
    log_config = LogConfig(name='UAV_Sensor_Fusion', period_in_ms=10)
    log_config.add_variable('baro.asl', 'float')
    log_config.add_variable('acc.x', 'float')
    log_config.add_variable('acc.y', 'float')
    log_config.add_variable('acc.z', 'float')
    log_config.add_variable('stateEstimate.qw', 'float')
    log_config.add_variable('stateEstimate.qx', 'float')
    log_config.add_variable('stateEstimate.qy', 'float')
    log_config.add_variable('stateEstimate.qz', 'float')
    log_config.add_variable('stateEstimate.z', 'float')

    start_time = time.time()

    def log_callback(timestamp, data, logconf):
        # 提取时间戳（秒）
        current_time = time.time() - start_time
        try:
            csv_writer.writerow([
                current_time,
                data['baro.asl'],
                data['acc.x'],
                data['acc.y'],
                data['acc.z'],
                data['stateEstimate.qw'],
                data['stateEstimate.qx'],
                data['stateEstimate.qy'],
                data['stateEstimate.qz'],
                data['stateEstimate.z']
            ])
        except Exception as e:
            print(f"Error writing row: {e}")

    # 注册回调函数并启动
    scf.cf.log.add_config(log_config)
    log_config.data_received_cb.add_callback(log_callback)
    log_config.start()

    # 维持主线程运行指定的录制时长
    time.sleep(duration_seconds)

    # 停止日志并关闭文件
    log_config.stop()
    csv_file.close()
    print(f"--- Data Acquisition Complete. Saved to {output_filename} ---")

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    print(f"Drivers initialized. Connecting to drone: {URI} ...")

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Connected!")

        if not pre_flight_check(scf):
            print("Mission aborted due to Pre-Flight Check failure.")
            sys.exit(1)

        # 触发数据记录任务（手持移动 30 秒）
        start_high_speed_logging(scf, output_filename="flight_data.csv", duration_seconds=30.0)
        
        print("\nData collection finished successfully.")