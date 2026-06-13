# --- my_mission.py ---
import time
import math
from retro_cflib import CrazyflieMock as Crazyflie


def is_free(grid, x, y):
    """Return True if grid cell (x, y) is passable (not a wall).

    Grid is indexed as grid[row][col] where row=y and col=x.
    Out-of-bounds coordinates are treated as blocked.
    """
    row = int(round(y))
    col = int(round(x))
    # Reject coordinates outside the map boundary
    if row < 0 or row >= len(grid):
        return False
    if col < 0 or col >= len(grid[row]):
        return False
    return grid[row][col] != "#"


def nearest_neighbor_order(start_x, start_y, batteries):
    """Return batteries sorted by greedy nearest-neighbor from start.

    At each step, picks the closest unvisited battery from the current
    position. Not globally optimal but runs in O(n^2) and works well
    for sparse battery layouts.
    """
    remaining = list(batteries)
    ordered = []
    cx, cy = start_x, start_y
    while remaining:
        # Find the closest battery to the current position
        nearest = min(remaining,
                      key=lambda b: math.hypot(b["x"] - cx, b["y"] - cy))
        ordered.append(nearest)
        # Advance current position to the chosen battery
        cx, cy = nearest["x"], nearest["y"]
        remaining.remove(nearest)
    return ordered


def find_approach_point(grid, bx, by, search_radius=3):
    """Find the best free cell near (bx, by) to use as an approach waypoint.

    Scans the perimeter ring at each radius from 1 to search_radius.
    Among free cells on each ring, prefers those with the most free
    4-connected neighbors to avoid placing the waypoint in a corridor.
    Returns (x, y) of the chosen cell, or None if nothing is found.
    """
    ibx, iby = int(round(bx)), int(round(by))
    for r in range(1, search_radius + 1):
        candidates = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                # Only examine cells on the outer perimeter of this radius
                if abs(dx) != r and abs(dy) != r:
                    continue
                nx, ny = ibx + dx, iby + dy
                if not is_free(grid, nx, ny):
                    continue
                # Count free 4-connected neighbors as an openness score;
                # higher score means more room to maneuver
                neighbors_free = sum(
                    1 for ox, oy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    if is_free(grid, nx + ox, ny + oy)
                )
                candidates.append((neighbors_free, nx, ny))
        if candidates:
            # Pick the most open candidate at this radius
            candidates.sort(reverse=True)
            _, nx, ny = candidates[0]
            return float(nx), float(ny)
    # No free cell found within search_radius
    return None


def approach_battery(cf, bx, by, cruise_z, grid):
    """Collect a battery using a two-step approach maneuver.

    Step 1 — approach point: fly to a nearby open cell to align the
    UAV heading and reduce speed before entering the target cell.
    Step 2 — collection: fly into the battery cell. The simulation
    triggers collection via on_collision, so an exact stop is not
    required; a short timeout prevents indefinite waiting.
    """
    approach = find_approach_point(grid, bx, by)
    if approach is not None:
        ax, ay = approach
        print(f"  Approach via ({ax:.1f}, {ay:.1f})")
        # Fly to intermediate waypoint to align heading
        cf.commander.go_to(x=ax, y=ay, z=cruise_z, tolerance=0.3)

    # Enter the battery cell; collision triggers collection in the sim
    cf.commander.go_to(x=bx, y=by, z=cruise_z,
                       tolerance=0.3, timeout=3.0)


def collect_batteries(cf, cruise_z, grid):
    """Collect all batteries autonomously using nearest-neighbor routing.

    The battery list is refreshed at the start of every iteration so
    batteries already collected are automatically excluded from routing.
    Positions that time out or are found blocked are added to the
    attempted set and will not be retried.
    """
    batteries = cf.commander.get_batteries()
    print(f"Batteries to collect: {len(batteries)}")

    attempted = set()  # (x, y) of positions already tried this session

    while True:
        # Re-fetch live battery list; collected ones will not appear
        remaining = cf.commander.get_batteries()
        if not remaining:
            print("All batteries collected.")
            break

        # Exclude positions already attempted (blocked or timed out)
        remaining = [b for b in remaining
                     if (b["x"], b["y"]) not in attempted]
        if not remaining:
            print("All reachable batteries attempted.")
            break

        # Choose the nearest unattempted battery from current position
        state = cf.commander.get_state()
        target = min(remaining,
                     key=lambda b: math.hypot(b["x"] - state["x"],
                                              b["y"] - state["y"]))
        bx, by = target["x"], target["y"]

        # Guard against batteries placed inside wall cells (map error)
        if not is_free(grid, bx, by):
            print(f"Skipping blocked battery at ({bx:.1f}, {by:.1f})")
            attempted.add((bx, by))
            continue

        print(f"Flying to battery at ({bx:.1f}, {by:.1f})")
        approach_battery(cf, bx, by, cruise_z, grid)
        # Mark as attempted regardless of whether collection succeeded
        attempted.add((bx, by))

        # Log position and running score after each attempt
        state = cf.commander.get_state()
        print(f"Position: ({state['x']:.2f}, {state['y']:.2f}), "
              f"score: {state['score']}")


def main():
    print("Starting mission...")
    cf = Crazyflie()

    # ── Pre-flight: fetch map and battery layout ────────────────────────────
    # Obstacle map: grid[y][x] == '#' means wall, '.' means free
    world = cf.commander.get_map()
    grid  = world["grid"]

    # Print all battery positions and whether their cells are passable
    batteries = cf.commander.get_batteries()
    print(f"Total batteries: {len(batteries)}")
    for b in batteries:
        status = "free" if is_free(grid, b["x"], b["y"]) else "BLOCKED"
        print(f"  Battery at ({b['x']:.1f}, {b['y']:.1f}) — {status}")

    # ── Task 2: Waypoint sequencer ──────────────────────────────────────────
    cruise_z = 0.25  # fixed flight altitude in metres (Z control disabled)

    # Step 1: take off by flying to the first corner at cruise altitude
    print("Taking off...")
    cf.commander.go_to(x=2.0, y=2.0, z=cruise_z)

    # Step 2: fly a 5 m x 5 m square, returning to the start corner
    # Corners visited in order: SW -> SE -> NE -> NW -> SW
    square = [
        (2.0, 2.0),   # start (SW)
        (7.0, 2.0),   # SE
        (7.0, 7.0),   # NE
        (2.0, 7.0),   # NW
        (2.0, 2.0),   # back to start (SW)
    ]
    for wx, wy in square:
        print(f"Waypoint -> ({wx:.1f}, {wy:.1f}, {cruise_z:.1f})")
        cf.commander.go_to(x=wx, y=wy, z=cruise_z)

    # ── Task 3: Autonomous battery collection ───────────────────────────────
    # Fly to every battery on the map using nearest-neighbor routing.
    # Each battery is collected by flying into its cell (collision-based).
    # Already-collected batteries are excluded from routing each iteration.
    collect_batteries(cf, cruise_z, grid)

    # ── Post-mission: report final score ───────────────────────────────────
    state = cf.commander.get_state()
    print(f"Mission complete. Final score: {state['score']}")


if __name__ == '__main__':
    main()