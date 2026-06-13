# --- my_mission.py ---
import time
from retro_cflib import CrazyflieMock as Crazyflie


def collect_batteries(cf, cruise_z):
    """Retrieve all battery positions and fly to each one."""
    batteries = cf.commander.get_batteries()
    for b in batteries:
        print(f"Flying to battery at ({b['x']:.1f}, {b['y']:.1f})")
        cf.commander.go_to(x=b["x"], y=b["y"], z=cruise_z)


def main():
    print("Starting mission...")
    cf = Crazyflie()

    # Get the map
    world = cf.commander.get_map()
    grid  = world["grid"]

    # Get batteries (preview only)
    batteries = cf.commander.get_batteries()
    for b in batteries:
        print(f"Battery at ({b['x']:.1f}, {b['y']:.1f})")

    # ── Task 2: Waypoint sequencer ──────────────────────────────────────────
    cruise_z = 0.25  # flight altitude in metres

    # Take off
    print("Taking off...")
    cf.commander.go_to(x=2.0, y=2.0, z=cruise_z)

    # 5 m × 5 m square (corners in order)
    square = [
        (2.0, 2.0),
        (7.0, 2.0),
        (7.0, 7.0),
        (2.0, 7.0),
        (2.0, 2.0),
    ]
    for wx, wy in square:
        print(f"Waypoint -> ({wx:.1f}, {wy:.1f}, {cruise_z:.1f})")
        cf.commander.go_to(x=wx, y=wy, z=cruise_z)

    # ── Task 3: Battery ──────────────────────────────────────────
    world = cf.commander.get_map()
    print("width:", world.get("width"))
    print("height:", world.get("height"))
    for row in world["grid"]:
        print(row)

    batteries = cf.commander.get_batteries()
    print("battery count:", len(batteries))
    for b in batteries:
        print(f"  ({b['x']:.1f}, {b['y']:.1f})")


if __name__ == '__main__':
    main()