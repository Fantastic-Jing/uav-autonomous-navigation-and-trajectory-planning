# --- retroflight/controller.py ---
import numpy as np


class UAVController:
    def __init__(self):
        # --- Single-loop position PID gains [x, y, z] ---
        # self.Kp = np.array([4.5, 4.5, 0.0])  # proportional: position error -> thrust
        # self.Ki = np.array([0.4, 0.4, 0.0])  # integral: compensates steady-state wind
        # self.Kd = np.array([4.0, 4.0, 0.0])  # derivative: velocity damping

        # --- Cascaded PID gains [x, y, z] ---
        self.Kp = np.array([1.0, 1.0, 0.0])  # outer loop: position error -> target velocity
        self.Ki = np.array([2.0, 2.0, 0.0])  # inner loop proportional: velocity error -> thrust
        self.Kd = np.array([0.9, 0.9, 0.0])  # inner loop derivative: velocity damping

        # --- Test Cascaded PID gains [x, y, z] ---
        # self.Kp = np.array([10.0, 10.0, 0.0])  # outer loop: position error -> target velocity
        # self.Ki = np.array([0.1, 0.1, 0.0])  # inner loop proportional: velocity error -> thrust
        # self.Kd = np.array([0.1, 0.1, 0.0])  # inner loop derivative: velocity damping

        # Low-pass filter state for velocity (reduces sensor noise fed into Kd)
        self.vel_filtered = np.zeros(3)
        self.alpha = 0.8  # filter coefficient: higher = less smoothing, lower = less noise

        self.error_sum  = np.zeros(3)
        self.last_error = np.zeros(3)
        self.thrust     = np.zeros(3)

    # --- Single-loop position PID (commented out) ---
    # Directly maps position error to thrust via one PID stage.
    # Simple but couples response speed and wind rejection;
    # prone to arc trajectories under wind.
    #
    # def compute_thrust(self, state, setpoint, dt, time):
    #     pos = state[0:3]
    #     vel = state[3:6]
    #
    #     error = setpoint - pos
    #     error[2] = 0.0  # altitude ignored
    #
    #     p_term = self.Kp * error
    #
    #     # Reset integral when error crosses zero to avoid overshoot on new segment
    #     sign_changed = np.sign(error) != np.sign(self.last_error)
    #     self.error_sum[sign_changed] = 0.0
    #     self.error_sum += error * dt
    #     self.error_sum = np.clip(self.error_sum, -10.0, 10.0)
    #     i_term = self.Ki * self.error_sum
    #
    #     # Use current velocity as derivative to
    #     # avoid derivative kick on setpoint change
    #     d_term = -self.Kd * vel
    #
    #     self.last_error = error.copy()
    #     self.thrust = p_term + i_term + d_term
    #     return self.thrust

    # --- Cascaded PID (active) ---
    # Outer loop converts position error to a velocity setpoint.
    # Inner loop converts velocity error to thrust,
    # decoupling response speed from wind rejection.
    def compute_thrust(self, state, setpoint, dt, time):
        """
        Calculate thrust for vehicle.
        x, y, z in meter
        vx, vy, vz in m/s
        and ax, ay, az m/s^2

        :param state: np.array [x, y, z, vx, vy, vz, ax, ay, az]
        :param setpoint: np.array [target_x, target_y, target_z]
        :param dt: delta time
        :param time: absolute simulation time
        :return: np.array [thrust_x, thrust_y, thrust_z]
        """
        pos = state[0:3]
        vel = state[3:6]

        error = setpoint - pos
        error[2] = 0.0  # altitude ignored

        # Outer loop: position error -> target velocity,
        # clamped to avoid aggressive acceleration
        target_vel = np.clip(self.Kp * error, -3.0, 3.0)

        # Inner loop: filter velocity to suppress sensor noise before feeding into Kd
        self.vel_filtered = self.alpha * vel + (1.0 - self.alpha) * self.vel_filtered
        vel_error = target_vel - self.vel_filtered
        vel_error[2] = 0.0  # altitude ignored

        # Reset integral when velocity error crosses zero to
        # prevent windup between waypoints
        sign_changed = np.sign(vel_error) != np.sign(self.last_error)
        self.error_sum[sign_changed] = 0.0
        self.error_sum += vel_error * dt
        self.error_sum = np.clip(self.error_sum, -10.0, 10.0)

        # Ki acts as inner-loop proportional on
        # integrated velocity error (wind rejection)
        p_term = self.Ki * self.error_sum
        d_term = self.Kd * vel_error

        self.last_error = vel_error.copy()
        self.thrust = p_term + d_term
        return self.thrust

    def on_collision(self, state, type_string):
        """
        Handle collision event.
        type_string can be e.g. "level" or "battery".
        """
        # print(type_string)