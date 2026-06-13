#!/usr/bin/env python3
"""
run_tests.py - UAV Lab 2 Pre-Flight Test Harness
=================================================

Usage:
    python run_tests.py <your_script.py>

The script injects a mock cflib into sys.modules so the code runs
without real hardware or a Crazyradio dongle.  It then checks:

  Pre-Flight Check tests
  ----------------------
  1. PASS scenario        - mission must continue
  2. Low battery          - must abort
  3. Bad attitude         - must abort
  4. High Kalman variance - must abort
  5. Unstable velocity    - must abort
  6. Bad RSSI             - must abort
  7. No LH deck           - must abort

  Trajectory tests (run against healthy scenario)
  ------------------------------------------------
  8. Task 2 - hover       - takeoff + hover + land present
  9. Task 3 - rectangle   - all 4 sides, correct height (~1 m), sane speed
"""

import sys
import os
import importlib
import importlib.util
import types
import traceback

# ---------------------------------------------------------------------------
# 0.  Inject mock cflib
# ---------------------------------------------------------------------------
MOCK_DIR = os.path.join(os.path.dirname(__file__), "cflib_mock")
sys.path.insert(0, MOCK_DIR)

# Pre-load the mock packages so sub-imports resolve correctly
import cflib                                                        # noqa: E402
import cflib.crtp                                                   # noqa: E402
import cflib.crazyflie                                              # noqa: E402
import cflib.crazyflie.log                                          # noqa: E402
import cflib.crazyflie.syncCrazyflie                                # noqa: E402
import cflib.crazyflie.syncLogger                                   # noqa: E402
import cflib.positioning                                            # noqa: E402
import cflib.positioning.motion_commander                           # noqa: E402

from cflib.positioning.motion_commander import MotionCommander      # noqa: E402


# ---------------------------------------------------------------------------
# 1.  Helpers
# ---------------------------------------------------------------------------
PASS  = "\033[32m PASS \033[0m"
FAIL  = "\033[31m FAIL \033[0m"
WARN  = "\033[33m WARN \033[0m"
INFO  = "\033[36m INFO \033[0m"

_results: list[tuple[str, bool, str]] = []   # (test_name, ok, detail)

def record(name: str, ok: bool, detail: str = ""):
    _results.append((name, ok, detail))
    icon = PASS if ok else FAIL
    print(f"  [{icon}] {name}" + (f"  — {detail}" if detail else ""))


def load_student_module(path: str) -> types.ModuleType:
    """Load the test script as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location("student_mission", path)
    mod  = importlib.util.module_from_spec(spec)
    # Prevent the if __name__ == '__main__' block from running
    mod.__name__ = "student_mission"
    spec.loader.exec_module(mod)
    return mod


def _reset_student_events(mod):
    """
    Clear all threading.Event objects at module level in the student script.
    Events like lh_deck_attached are global state — once set in scenario N
    they would bleed into scenario N+1 otherwise.
    """
    import threading
    for name, obj in vars(mod).items():
        if isinstance(obj, threading.Event):
            obj.clear()


def run_preflight(mod, scenario_overrides: dict) -> "bool | None":
    """
    Run the student's pre_flight_check() under a specific scenario.
    Returns True/False (passed/failed) or None on crash.
    """
    cflib.reset_scenario()
    cflib.set_scenario(scenario_overrides)
    _reset_student_events(mod)   # clear lh_deck_attached etc. between runs

    from cflib.crazyflie import Crazyflie, SyncCrazyflie
    scf = SyncCrazyflie.__new__(SyncCrazyflie)
    scf.uri = "radio://0/80/2M/TESTTEST"
    scf.cf  = Crazyflie()

    try:
        result = mod.pre_flight_check(scf)
        return bool(result)
    except SystemExit as e:
        # sys.exit(1) counts as "aborted" = False
        return False
    except Exception:
        print("    [EXCEPTION in pre_flight_check]")
        traceback.print_exc()
        return None


def run_task(mod, func_name: str, scenario_overrides: dict | None = None):
    """
    Run a flight task function and return the MotionCommander session.
    Returns the MotionCommander instance or None on crash.
    """
    cflib.reset_scenario()
    if scenario_overrides:
        cflib.set_scenario(scenario_overrides)

    from cflib.crazyflie import Crazyflie, SyncCrazyflie
    scf = SyncCrazyflie.__new__(SyncCrazyflie)
    scf.uri = "radio://0/80/2M/TESTTEST"
    scf.cf  = Crazyflie()

    MotionCommander.last_session = None
    try:
        getattr(mod, func_name)(scf)
    except SystemExit:
        pass
    except Exception:
        print(f"    [EXCEPTION in {func_name}]")
        traceback.print_exc()
        return None

    return MotionCommander.last_session


# ---------------------------------------------------------------------------
# 2.  Pre-Flight Check tests
# ---------------------------------------------------------------------------
def test_preflight(mod):
    print("\n── Pre-Flight Check Tests ──────────────────────────────────────")

    # 2.1 Healthy → should PASS
    r = run_preflight(mod, {})
    record("Healthy scenario → pre-flight PASSES", r is True,
           "returned False or crashed" if r is not True else "")

    # 2.2 Low battery
    r = run_preflight(mod, {"vbat": 3.5})
    record("Low battery (3.5 V) → pre-flight ABORTS", r is False,
           "should have returned False but didn't" if r is not False else "")

    # 2.3 Bad attitude (roll too high)
    r = run_preflight(mod, {"roll": 5.0})
    record("Bad attitude (roll=5°) → pre-flight ABORTS", r is False,
           "should have returned False but didn't" if r is not False else "")

    # 2.4 High Kalman variance (sqrt(0.02) ≈ 0.14 m > 0.08 threshold)
    r = run_preflight(mod, {"varPX": 0.02})
    record("High Kalman variance (varPX=0.02) → pre-flight ABORTS", r is False,
           "should have returned False but didn't" if r is not False else "")

    # 2.5 Unstable velocity
    r = run_preflight(mod, {"vx": 0.5})
    record("Unstable velocity (vx=0.5 m/s) → pre-flight ABORTS", r is False,
           "should have returned False but didn't" if r is not False else "")

    # 2.6 Bad RSSI  (very weak signal)
    r = run_preflight(mod, {"rssi": 85})
    record("Bad RSSI (85 dBm) → pre-flight ABORTS", r is False,
           "RSSI check missing or threshold too low" if r is not False else "")

    # 2.7 No Lighthouse deck
    r = run_preflight(mod, {"lh_deck": False})
    record("No LH deck attached → pre-flight ABORTS", r is False,
           "Lighthouse deck check missing" if r is not False else "")


# ---------------------------------------------------------------------------
# 3.  Task 2 — hover
# ---------------------------------------------------------------------------
def test_task2(mod):
    print("\n── Task 2: Hover ───────────────────────────────────────────────")

    if not hasattr(mod, "task2_manual_hover"):
        record("task2_manual_hover() exists", False, "function not found in script")
        return

    mc = run_task(mod, "task2_manual_hover")
    if mc is None:
        record("task2_manual_hover() runs without crash", False)
        return

    record("task2_manual_hover() runs without crash", True)
    record("Task 2: takeoff was issued",
           mc.has_cmd("takeoff"),
           "no takeoff recorded")
    record("Task 2: land was issued",
           mc.has_cmd("land") or mc.has_cmd("stop"),
           "no land/stop recorded — drone never lands?")

    height = mc.default_height
    record(f"Task 2: takeoff height 0.5 m (got {height:.2f} m)",
           abs(height - 0.5) < 0.05,
           f"expected ~0.5 m, got {height:.2f} m")


# ---------------------------------------------------------------------------
# 4.  Task 3 - rectangle
# ---------------------------------------------------------------------------
def _rectangle_check(mc: MotionCommander):
    """
    Check that the four rectangle sides are present.

    Rules:
    - Need at least one forward/back AND at least one left/right move
    - The dominant moves should cover ~1 m each
    - Exactly 4 lateral move commands makes a rectangle (we allow 3–6 for
      approaches where the test might split a side or add extra steps)
    - Takeoff height should be ~1.0 m
    - Velocity should be > 0 and ≤ 3.0 m/s (sanity bound)
    """
    issues = []
    moves = mc.movement_commands()

    lateral = [c for c in moves if c["cmd"] in ("forward", "back", "left", "right")]
    fwd_back = [c for c in lateral if c["cmd"] in ("forward", "back")]
    lr       = [c for c in lateral if c["cmd"] in ("left", "right")]

    ok_sides = len(fwd_back) >= 1 and len(lr) >= 1
    if not ok_sides:
        issues.append("need both forward/back AND left/right moves for a rectangle")

    # Distance check — each lateral move should be close to 1 m
    all_lateral_dists = [c.get("distance", 0) for c in lateral]
    if all_lateral_dists:
        avg_dist = sum(all_lateral_dists) / len(all_lateral_dists)
        if not (0.7 <= avg_dist <= 1.5):
            issues.append(f"average lateral distance {avg_dist:.2f} m — expected ~1.0 m")

    # Side count
    n_sides = len(lateral)
    if n_sides < 3:
        issues.append(f"only {n_sides} lateral move(s) — a rectangle needs 4")

    # Velocity sanity
    vels = [c.get("velocity", 0) for c in lateral if "velocity" in c]
    if vels:
        max_v = max(vels)
        if max_v > 3.0:
            issues.append(f"velocity {max_v:.1f} m/s seems dangerously high (> 3 m/s)")
        if max_v <= 0:
            issues.append("velocity is zero or negative")

    return issues, n_sides, all_lateral_dists


def test_task3(mod):
    print("\n── Task 3: Rectangle ───────────────────────────────────────────")

    if not hasattr(mod, "task3_autonomous_rectangle"):
        record("task3_autonomous_rectangle() exists", False, "function not found in script")
        return

    mc = run_task(mod, "task3_autonomous_rectangle")
    if mc is None:
        record("task3_autonomous_rectangle() runs without crash", False)
        return

    record("task3_autonomous_rectangle() runs without crash", True)

    # Height
    height = mc.default_height
    record(f"Task 3: takeoff height ~1.0 m (got {height:.2f} m)",
           abs(height - 1.0) < 0.1,
           f"expected ~1.0 m, got {height:.2f} m")

    # Rectangle geometry
    issues, n_sides, dists = _rectangle_check(mc)

    dist_str = ", ".join(f"{d:.2f}" for d in dists) if dists else "none"
    record(f"Task 3: lateral moves present ({n_sides} recorded, distances: {dist_str} m)",
           n_sides >= 3,
           "; ".join(issues) if issues else "")

    # Individual direction checks
    moves = mc.movement_commands()
    for direction in ("forward", "back", "left", "right"):
        present = any(c["cmd"] == direction for c in moves)
        record(f"Task 3: '{direction}' command present", present,
               f"'{direction}' never called — rectangle incomplete")

    # Landing
    record("Task 3: land was issued",
           mc.has_cmd("land") or mc.has_cmd("stop"),
           "no land/stop recorded")


# ---------------------------------------------------------------------------
# 5.  Summary
# ---------------------------------------------------------------------------
def print_summary():
    print("\n" + "═" * 60)
    print("  SUMMARY")
    print("═" * 60)
    passed = sum(1 for _, ok, _ in _results if ok)
    total  = len(_results)
    for name, ok, detail in _results:
        icon = "✓" if ok else "✗"
        line = f"  {icon}  {name}"
        if not ok and detail:
            line += f"\n       → {detail}"
        print(line)
    print("─" * 60)
    color = "\033[32m" if passed == total else "\033[33m" if passed >= total // 2 else "\033[31m"
    print(f"{color}  {passed}/{total} checks passed\033[0m")
    print("═" * 60)
    return passed == total


# ---------------------------------------------------------------------------
# 6.  Entry point
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <test_script.py>")
        sys.exit(1)

    script_path = sys.argv[1]
    if not os.path.isfile(script_path):
        print(f"Error: file not found: {script_path}")
        sys.exit(1)

    print("=" * 60)
    print(f"  UAV Lab 2 — Mock Test Harness")
    print(f"  Testing: {script_path}")
    print("=" * 60)

    try:
        mod = load_student_module(script_path)
    except Exception as e:
        print(f"\n[FATAL] Could not load test script: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Check required functions exist first
    for fn in ("pre_flight_check", "task2_manual_hover", "task3_autonomous_rectangle"):
        if not hasattr(mod, fn):
            print(f"\n[FATAL] Required function '{fn}' not found in {script_path}")
            print("        Make sure you haven't renamed or deleted it.")
            sys.exit(1)

    test_preflight(mod)
    test_task2(mod)
    test_task3(mod)

    all_ok = print_summary()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
