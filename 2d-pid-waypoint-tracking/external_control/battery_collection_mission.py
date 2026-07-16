# battery_collection_mission.py
import time
import math
from retro_cflib import CrazyflieMock as Crazyflie

# %% Grid Utilities

def is_free(grid, x, y):
    row = int(round(y))
    col = int(round(x))
    if row < 0 or row >= len(grid):
        return False
    if col < 0 or col >= len(grid[row]):
        return False
    return grid[row][col] != "#"

# %% Path Planning Algorithms

def nearest_neighbor_order(start_x, start_y, batteries):
    remaining = list(batteries)
    ordered = []
    cx, cy = start_x, start_y
    while remaining:
        nearest = min(remaining,
                      key=lambda b: math.hypot(b["x"] - cx, b["y"] - cy))
        ordered.append(nearest)
        cx, cy = nearest["x"], nearest["y"]
        remaining.remove(nearest)
    return ordered


def find_approach_point(grid, bx, by, search_radius=3):
    ibx, iby = int(round(bx)), int(round(by))
    for r in range(1, search_radius + 1):
        candidates = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if abs(dx) != r and abs(dy) != r:
                    continue
                nx, ny = ibx + dx, iby + dy
                if not is_free(grid, nx, ny):
                    continue
                neighbors_free = sum(
                    1 for ox, oy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    if is_free(grid, nx + ox, ny + oy)
                )
                candidates.append((neighbors_free, nx, ny))
        if candidates:
            candidates.sort(reverse=True)
            _, nx, ny = candidates[0]
            return float(nx), float(ny)
    return None

# %% Mission Actions

def approach_battery(cf, bx, by, cruise_z, grid):
    approach = find_approach_point(grid, bx, by)
    if approach is not None:
        ax, ay = approach
        print(f"  Approach via ({ax:.1f}, {ay:.1f})")
        cf.commander.go_to(x=ax, y=ay, z=cruise_z, tolerance=0.3)

    cf.commander.go_to(x=bx, y=by, z=cruise_z,
                       tolerance=0.3, timeout=3.0)


def collect_batteries(cf, cruise_z, grid):
    batteries = cf.commander.get_batteries()
    print(f"Batteries to collect: {len(batteries)}")
    attempted = set()

    while True:
        remaining = cf.commander.get_batteries()
        if not remaining:
            print("All batteries collected.")
            break

        remaining = [b for b in remaining
                     if (b["x"], b["y"]) not in attempted]
        if not remaining:
            print("All reachable batteries attempted.")
            break

        state = cf.commander.get_state()
        target = min(remaining,
                     key=lambda b: math.hypot(b["x"] - state["x"],
                                              b["y"] - state["y"]))
        bx, by = target["x"], target["y"]

        if not is_free(grid, bx, by):
            print(f"Skipping blocked battery at ({bx:.1f}, {by:.1f})")
            attempted.add((bx, by))
            continue

        print(f"Flying to battery at ({bx:.1f}, {by:.1f})")
        approach_battery(cf, bx, by, cruise_z, grid)
        attempted.add((bx, by))

        state = cf.commander.get_state()
        print(f"Position: ({state['x']:.2f}, {state['y']:.2f}), "
              f"score: {state['score']}")

# %% Main Execution

def main():
    print("Starting mission...")
    cf = Crazyflie()

    world = cf.commander.get_map()
    grid  = world["grid"]

    batteries = cf.commander.get_batteries()
    print(f"Total batteries: {len(batteries)}")
    for b in batteries:
        status = "free" if is_free(grid, b["x"], b["y"]) else "BLOCKED"
        print(f"  Battery at ({b['x']:.1f}, {b['y']:.1f}) — {status}")

    cruise_z = 0.25

    print("Taking off...")
    cf.commander.go_to(x=2.0, y=2.0, z=cruise_z)

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

    collect_batteries(cf, cruise_z, grid)

    state = cf.commander.get_state()
    print(f"Mission complete. Final score: {state['score']}")


if __name__ == '__main__':
    main()