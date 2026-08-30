# UAV Control, Mission Planning, and Altitude Estimation

Python implementations for 2D waypoint control, Crazyflie flight safety checks, battery-collection mission logic, and barometer–IMU altitude estimation.

| Area | Implementation |
|---|---|
| Simulation control | Cascaded position–velocity PID in RetroFlight |
| Mission logic | Grid-aware waypoint routing and battery collection |
| Flight operations | Lighthouse, attitude, velocity, battery, and radio checks |
| Sensor fusion | Three-state Kalman filter for altitude, vertical velocity, and accelerometer bias |
| Hardware | Bitcraze Crazyflie 2.1 Brushless, Crazyradio, Lighthouse positioning |

## Results at a Glance

- The cascaded controller converts position error into a bounded velocity target, then converts velocity error into planar thrust.
- The mission layer approaches batteries through a free neighbouring cell before entering the target cell.
- The Crazyflie flight script performs a pre-flight gate before hover and rectangle trajectories.
- The included video shows a recorded hardware flight. It is qualitative validation; no tracking metric is inferred from the video.
- The supplied CSV contains 1,500 sensor rows over approximately 30 seconds. Although the logger requests a 10 ms period, the recorded timestamps average approximately 20 ms, so this file represents about 50 Hz effective logging.

## Repository Map

```text
2d-pid-waypoint-tracking/
├── src/retroflight/controller.py       # Cascaded PID controller
├── external_control/battery_collection_mission.py
├── retroflight.png                     # Simulation result
└── pyproject.toml

flight-ops-mission-planning/
├── preflight_and_trajectory.py         # Crazyflie checks and flight sequence
├── run_tests.py                         # Mock test harness
└── uav_preflight_and_trajectory_demo.mp4

kalman-altitude-estimation/
├── uav_logger.py                        # Crazyflie sensor logger
├── kalman_altitude_filter.py            # Barometer–IMU filter
├── flight_data.csv                      # Recorded sensor data
└── kalman_altitude_filter_states_output.png
```

## Cascaded PID and Waypoint Control

The active controller uses two planar loops. The outer loop maps position error to a velocity target and clips it to ±3 m/s. The inner loop filters measured velocity, integrates velocity error, and applies derivative damping. The integral state is reset when the velocity-error sign changes to reduce carry-over between waypoints.

```python
target_vel = np.clip(self.Kp * error, -3.0, 3.0)
vel_error = target_vel - self.vel_filtered
d_term = self.Kd * vel_error
```

The altitude channel is intentionally disabled (`z` gain = 0). The simulation also contains a grid-based battery mission: it reads obstacles and battery positions, selects the nearest remaining target, and inserts an approach point when possible.

![Figure 1: RetroFlight battery-collection simulation](2d-pid-waypoint-tracking/retroflight.png)

*Figure 1: Simulated waypoint and battery-collection mission in RetroFlight.*

The controller gains are hand-tuned for the simulation. The nearest-neighbour route is fast to compute but is not an optimal travelling-salesperson solution. A future version could add altitude control, absolute-position waypoint correction, and systematic gain tuning.

## Crazyflie Flight Operations

`preflight_and_trajectory.py` uses `cflib` and `MotionCommander` for a hardware pre-flight gate followed by two flight sequences:

1. A hover sequence with a 0.5 m take-off height and a five-second hold.
2. A relative 1 m × 1 m rectangle at a 1.0 m take-off height, with pauses at the corners.

The gate checks Lighthouse deck presence, position-estimate variance, roll and pitch, horizontal velocity, battery voltage, and radio signal. The logging configuration uses `FP16` for non-critical values so the variables fit within the Crazyflie log packet limit.

The test harness contains mock checks for pre-flight failure cases, hover commands, rectangle commands, and landing commands. It requires the course-provided mock `cflib` package; that package is retained locally and is not treated as portfolio code. The suite was not re-run in this environment because the mock package is not installed as an importable module, and no saved test report was found. This README therefore does not claim a numeric test-pass result or a measured landing offset.

[Watch the recorded Crazyflie flight](flight-ops-mission-planning/uav_preflight_and_trajectory_demo.mp4)

The video demonstrates the recorded flight sequence, not a position log. The current safety check runs before flight and does not provide a mid-flight abort supervisor.

## Barometer–IMU Altitude Estimation

`uav_logger.py` records barometric altitude, accelerometer samples, orientation quaternion, and `stateEstimate.z` to CSV. The filter in `kalman_altitude_filter.py`:

1. Converts accelerometer readings from `g` to m/s².
2. Rotates body-frame acceleration into the world frame and subtracts gravity.
3. Removes the initial barometer offset using the first 2.5 seconds.
4. Propagates and corrects the state `[altitude, vertical velocity, accelerometer bias]` with a barometer measurement.

The saved tuning values are `acc_std = 0.05`, `process_noise_acc = 0.0001`, and `baro_std = 1.25`. Increasing the assumed barometer noise makes the estimate smoother but slower to follow barometer changes; increasing acceleration uncertainty has the opposite effect.

![Figure 2: Kalman altitude estimate](kalman-altitude-estimation/kalman_altitude_filter_states_output.png)

*Figure 2: Recorded barometer, filtered altitude, reference altitude, velocity, and estimated accelerometer bias.*

The model assumes a near-constant accelerometer bias and does not reject barometer outliers. The included CSV is a recorded data sample rather than a complete benchmark across flights.

## Reproduction

### RetroFlight simulation

```bash
cd 2d-pid-waypoint-tracking
python -m pip install -e .
python -m retroflight.main
```

### Crazyflie scripts

Install a compatible `cflib` environment, configure the Crazyflie URI and hardware safety conditions in the scripts, then run the selected flight or logging script from its directory. Do not arm a real vehicle without a clear test area, an accessible stop procedure, and a verified positioning estimate.

### Offline altitude filter

```bash
cd kalman-altitude-estimation
python kalman_altitude_filter.py
```

The offline filter requires NumPy, pandas, and Matplotlib. It reads `flight_data.csv` by default and displays the estimated states.

## Limitations

- The cascaded PID controls planar motion only; its gains are hand-tuned and not scheduled for changing dynamics.
- Mission routing uses nearest-neighbour selection and assumes the simulator's grid and battery APIs.
- The hardware flight script performs pre-flight checks but does not continuously supervise all safety signals during motion.
- Relative rectangle commands can accumulate position error across sides.
- The altitude filter uses simplified dynamics, a fixed gravity constant, and no innovation gate for outliers.
- The repository contains course-derived test material and recorded hardware data. Publication of each file requires a separate review of ownership, privacy, and redistribution rights.

## Acknowledgments

This work comes from the *Advanced UAV Sensor Fusion and Control* module of the M.Sc. Automation programme at Hochschule Darmstadt, Faculty of Electrical Engineering and Information Technology, under the supervision of Prof. Dr.-Ing. Jan Zwiener.
