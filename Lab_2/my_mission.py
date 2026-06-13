import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.motion_commander import MotionCommander

# TODO: Replace XX with your assigned drone number (e.g. 01, 02 ... 0A)
URI = 'radio://0/80/2M/DABADA55XX'

# Set by param callback when the Lighthouse deck is detected
lh_deck_attached = Event()


def param_deck_lighthouse(_, value_str):
    """Param callback: set event if Lighthouse deck is present (value == 1)."""
    if int(value_str):
        lh_deck_attached.set()


def pre_flight_check(scf):
    """
    Task 1: Pre-Flight Safety Check.

    Verifies the following conditions before allowing any flight command:
      1. Lighthouse deck attached and callback confirmed (hardware present).
      2. Kalman filter variance low enough to confirm LH positioning is
         stable and precise (varPX < 0.01, i.e. std-dev < 0.1 m).
         Simply detecting the deck is insufficient — the filter must have
         converged on a reliable position estimate before take-off.
      3. Drone is level: |roll| <= 2° and |pitch| <= 2°.
      4. Drone is stationary: |vx| < 0.2 m/s and |vy| < 0.2 m/s.
      5. Battery voltage strictly above 3.7 V.
      6. Radio link quality: RSSI absolute value < 80 dBm.
         In cflib, radio.rssi is the absolute value of the received signal
         strength in dBm (e.g. 40 means -40 dBm). Higher values mean weaker
         signal. A value >= 80 indicates a marginal link likely to drop mid-
         flight and cause a crash.

    Returns True if all checks pass, False otherwise.

    Byte budget (LogConfig limit: 26 bytes):
      pm.vbat             float  4 B
      kalman.varPX        float  4 B
      stateEstimate.roll  FP16   2 B
      stateEstimate.pitch FP16   2 B
      stateEstimate.vx    FP16   2 B
      stateEstimate.vy    FP16   2 B
      radio.rssi          FP16   2 B
      Total                     18 B
    """
    print("--- Starting Pre-Flight Check ---")

    # ── Check 1: Lighthouse deck ────────────────────────────────────────────
    # Register param callback; fires immediately with the current value
    scf.cf.param.add_update_callback(
        group='deck', name='bcLighthouse4', cb=param_deck_lighthouse
    )
    # Allow time for the parameter callback to be invoked
    time.sleep(1)

    if not lh_deck_attached.is_set():
        print("[FAIL] Lighthouse deck not detected.")
        return False
    print("[OK] Lighthouse deck detected.")

    # ── Checks 2-6: Telemetry ───────────────────────────────────────────────
    logconf = LogConfig(name='PreFlight', period_in_ms=250)

    # float (4 B each) — full precision needed for voltage and variance
    logconf.add_variable('pm.vbat',      'float')
    logconf.add_variable('kalman.varPX', 'float')

    # FP16 (2 B each) — sufficient precision for state estimates
    logconf.add_variable('stateEstimate.roll',  'FP16')
    logconf.add_variable('stateEstimate.pitch', 'FP16')
    logconf.add_variable('stateEstimate.vx',    'FP16')
    logconf.add_variable('stateEstimate.vy',    'FP16')
    logconf.add_variable('radio.rssi',          'FP16')

    passed = False

    with SyncLogger(scf, logconf) as logger:
        # Collect telemetry for 3 seconds then evaluate a single snapshot
        end_time = time.time() + 3.0
        for log_entry in logger:
            data = log_entry[1]
            if time.time() < end_time:
                continue

            # Read all telemetry values
            vbat   = data['pm.vbat']
            var_px = data['kalman.varPX']
            roll   = data['stateEstimate.roll']
            pitch  = data['stateEstimate.pitch']
            vx     = data['stateEstimate.vx']
            vy     = data['stateEstimate.vy']
            rssi   = data['radio.rssi']

            print(f"  Battery   : {vbat:.2f} V")
            print(f"  varPX     : {var_px:.4f} (std {var_px**0.5:.3f} m)")
            print(f"  Roll/Pitch: {roll:.1f}° / {pitch:.1f}°")
            print(f"  Velocity  : vx={vx:.2f} m/s  vy={vy:.2f} m/s")
            print(f"  RSSI      : {rssi:.0f} dBm (abs)")

            # Check 2: Kalman variance — confirms LH positioning is stable
            if var_px >= 0.01:
                print(f"[FAIL] Kalman variance too high: "
                      f"varPX={var_px:.4f} >= 0.01 "
                      f"(std={var_px**0.5:.3f} m, threshold 0.1 m)")
                break

            # Check 3: Level surface
            if abs(roll) > 2.0 or abs(pitch) > 2.0:
                print(f"[FAIL] Attitude out of range: "
                      f"roll={roll:.1f}°, pitch={pitch:.1f}° (limit ±2°)")
                break

            # Check 4: Stationary
            if abs(vx) >= 0.2 or abs(vy) >= 0.2:
                print(f"[FAIL] Drone not stationary: "
                      f"vx={vx:.2f} m/s, vy={vy:.2f} m/s (limit 0.2 m/s)")
                break

            # Check 5: Battery voltage
            if vbat <= 3.7:
                print(f"[FAIL] Battery too low: {vbat:.2f} V (<= 3.7 V)")
                break

            # Check 6: Radio link quality
            if rssi >= 80:
                print(f"[FAIL] Weak radio link: RSSI={rssi:.0f} dBm (>= 80)")
                break

            # All checks passed
            passed = True
            break

    if passed:
        print("--- Pre-Flight Check: PASSED ---")
    else:
        print("--- Pre-Flight Check: FAILED ---")

    return passed


def task2_manual_hover(scf):
    """
    Task 2: Take off to 0.5 m, hover for 5 seconds, then land.

    MotionCommander issues take_off() automatically on context entry
    and land() automatically on context exit.
    """
    print("\n--- Executing Task 2: Hover ---")

    with MotionCommander(scf, default_height=0.5) as mc:
        print("  Hovering at 0.5 m for 5 seconds...")
        time.sleep(5)
        print("  Hover complete, landing...")

    print("--- Task 2 complete ---")


def task3_autonomous_rectangle(scf):
    """
    Task 3: Fly a 1 m x 1 m rectangle at 1.0 m altitude.

    Flight sequence:
      - Take off to 1.0 m
      - Pause briefly to stabilize
      - Fly four sides: forward → left → back → right
      - Make a distinct stop at each corner
      - Return to start and land

    Corner stops use mc.stop() followed by a short sleep to ensure
    the drone is stationary before the next move.
    """
    print("\n--- Executing Task 3: 1x1m Rectangle ---")

    # Time to pause at each corner in seconds
    corner_pause = 1.0

    with MotionCommander(scf, default_height=1.0) as mc:
        print("  Stabilizing after takeoff...")
        time.sleep(1.0)

        # Side 1: forward 1 m
        print("  Side 1: forward 1.0 m")
        mc.forward(1.0)
        mc.stop()
        time.sleep(corner_pause)

        # Side 2: left 1 m
        print("  Side 2: left 1.0 m")
        mc.left(1.0)
        mc.stop()
        time.sleep(corner_pause)

        # Side 3: back 1 m
        print("  Side 3: back 1.0 m")
        mc.back(1.0)
        mc.stop()
        time.sleep(corner_pause)

        # Side 4: right 1 m — returns to starting XY position
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

        # 1. Run Pre-Flight Check
        is_safe_to_fly = pre_flight_check(scf)
        if not is_safe_to_fly:
            print("Mission aborted due to Pre-Flight Check failure.")
            sys.exit(1)

        # Arm the Crazyflie
        scf.cf.supervisor.send_arming_request(True)
        time.sleep(1.0)

        # 2. Run Task 2
        task2_manual_hover(scf)

        # 3. Run Task 3
        task3_autonomous_rectangle(scf)

        print("\nLab tasks completed successfully!")