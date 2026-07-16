import sys
import time
import csv
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# Replace with your drone URI
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


def start_high_speed_logging(scf, output_filename="flight_data.csv", duration_seconds=30.0):
    """Configure logging and collect data"""
    print(f"\n--- Starting Data Acquisition ({duration_seconds}s) ---")
    print("Please move the drone up and down by hand now...")

    # Open CSV file to write
    csv_file = open(output_filename, mode='w', newline='')
    csv_writer = csv.writer(csv_file)

    # Use the exact header format from the template
    header = ['time', 'baro_asl', 'acc_x', 'acc_y', 'acc_z', 'qw', 'qx', 'qy', 'qz', 'ref_z']
    csv_writer.writerow(header)

    # Configure log block with 10ms period (100 Hz)
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
        # Calculate relative timestamp in seconds
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

    # Register callback and start logging
    scf.cf.log.add_config(log_config)
    log_config.data_received_cb.add_callback(log_callback)
    log_config.start()

    # Keep main thread running for the duration
    time.sleep(duration_seconds)

    # Stop logging and close file
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

        # Start data logging
        start_high_speed_logging(scf, output_filename="flight_data.csv", duration_seconds=30.0)

        print("\nData collection finished successfully.")