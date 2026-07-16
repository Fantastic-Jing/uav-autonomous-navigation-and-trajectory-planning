# preflight_and_trajectory.py
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.motion_commander import MotionCommander

URI = 'radio://0/80/2M/DABADA55XX'

lh_deck_attached = Event()



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

    logconf = LogConfig(name='PreFlight', period_in_ms=250)
    logconf.add_variable('pm.vbat',      'float')
    logconf.add_variable('kalman.varPX', 'float')
    logconf.add_variable('stateEstimate.roll',  'FP16')
    logconf.add_variable('stateEstimate.pitch', 'FP16')
    logconf.add_variable('stateEstimate.vx',    'FP16')
    logconf.add_variable('stateEstimate.vy',    'FP16')
    logconf.add_variable('radio.rssi',          'FP16')

    passed = False

    with SyncLogger(scf, logconf) as logger:
        end_time = time.time() + 3.0
        for log_entry in logger:
            data = log_entry[1]
            if time.time() < end_time:
                continue

            vbat   = data['pm.vbat']
            var_px = data['kalman.varPX']
            roll   = data['stateEstimate.roll']
            pitch  = data['stateEstimate.pitch']
            vx     = data['stateEstimate.vx']
            vy     = data['stateEstimate.vy']
            rssi   = data['radio.rssi']

            print(f"  Battery   : {vbat:.2f} V")
            print(f"  varPX     : {var_px:.4f} (std {var_px**0.5:.3f} m)")
            print(f"  Roll/Pitch: {roll:.1f} degree / {pitch:.1f} degree")
            print(f"  Velocity  : vx={vx:.2f} m/s  vy={vy:.2f} m/s")
            print(f"  RSSI      : {rssi:.0f} dBm (abs)")

            if var_px >= 0.01:
                print(f"[FAIL] Kalman variance too high: varPX={var_px:.4f} >= 0.01")
                break

            if abs(roll) > 2.0 or abs(pitch) > 2.0:
                print(f"[FAIL] Attitude out of range: roll={roll:.1f}, pitch={pitch:.1f}")
                break

            if abs(vx) >= 0.2 or abs(vy) >= 0.2:
                print(f"[FAIL] Drone not stationary: vx={vx:.2f}, vy={vy:.2f}")
                break

            if vbat <= 3.7:
                print(f"[FAIL] Battery too low: {vbat:.2f} V")
                break

            if rssi >= 80:
                print(f"[FAIL] Weak radio link: RSSI={rssi:.0f}")
                break

            passed = True
            break

    if passed:
        print("--- Pre-Flight Check: PASSED ---")
    else:
        print("--- Pre-Flight Check: FAILED ---")

    return passed


def task2_manual_hover(scf):
    print("\n--- Executing Task 2: Hover ---")
    with MotionCommander(scf, default_height=0.5) as mc:
        print("  Hovering at 0.5 m for 5 seconds...")
        time.sleep(5)
        print("  Hover complete, landing...")
    print("--- Task 2 complete ---")


def task3_autonomous_rectangle(scf):
    print("\n--- Executing Task 3: 1x1m Rectangle ---")
    corner_pause = 1.0

    with MotionCommander(scf, default_height=1.0) as mc:
        print("  Stabilizing after takeoff...")
        time.sleep(1.0)

        print("  Side 1: forward 1.0 m")
        mc.forward(1.0)
        mc.stop()
        time.sleep(corner_pause)

        print("  Side 2: left 1.0 m")
        mc.left(1.0)
        mc.stop()
        time.sleep(corner_pause)

        print("  Side 3: back 1.0 m")
        mc.back(1.0)
        mc.stop()
        time.sleep(corner_pause)

        print("  Side 4: right 1.0 m")
        mc.right(1.0)
        mc.stop()
        time.sleep(corner_pause)

        print("  Rectangle complete, landing...")
    print("--- Task 3 complete ---")


if __name__ == '__main__':
    cflib.crtp.init_drivers()
    print(f"Drivers initialized. Connecting to drone: {URI} ...")

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Connected!")

        is_safe_to_fly = pre_flight_check(scf)
        if not is_safe_to_fly:
            print("Mission aborted due to Pre-Flight Check failure.")
            sys.exit(1)

        scf.cf.supervisor.send_arming_request(True)
        time.sleep(1.0)

        task2_manual_hover(scf)
        task3_autonomous_rectangle(scf)

        print("\nLab tasks completed successfully!")