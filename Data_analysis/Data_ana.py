import serial
import time
import csv

# 1. Setup Serial
port = 'com5'
baud = 115200
ser = serial.Serial(port, baud)
time.sleep(2) 

def get_raw_data():
    """Helper to get a clean list of [ax, ay, az, gx, gy, gz]."""
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            data = line.split(',')
            if len(data) == 6:
                return [float(val) for val in data]
        except (ValueError, UnicodeDecodeError):
            return None
    return None

def get_linear_params(axis_idx, axis_name, calibration_time=5):
    """Calculates m and b for a specific axis using the 3-step toggling method."""
    steps = [
        {"label": f"UP (+9.81 m/s^2) on {axis_name}", "target": 9.81},
        {"label": f"DOWN (-9.81 m/s^2) on {axis_name}", "target": -9.81},
        {"label": f"PERPENDICULAR (0 m/s^2) on {axis_name}", "target": 0}
    ]
    
    n = 0
    x_sum, y_sum, x2_sum, xy_sum = 0, 0, 0, 0
    
    print(f"\n--- CALIBRATING {axis_name} AXIS ---")
    for step in steps:
        print(f"--> Orient {step['label']}. Press Enter when ready...")
        input()
        end_loop = time.time() + calibration_time
        while time.time() < end_loop:
            readings = get_raw_data()
            if readings:
                n += 1
                meas, exp = readings[axis_idx], step['target']
                x_sum += exp
                y_sum += meas
                x2_sum += exp**2
                xy_sum += exp * meas
    
    m = (n * xy_sum - (x_sum * y_sum)) / ((n * x2_sum) - (x_sum)**2)
    b = (y_sum - (m * x_sum)) / n
    return m, b

def get_static_bias(calibration_time=5):
    """Calculates the average offset while the sensor is completely still."""
    print('\n' + '--' * 25)
    print('Calculating Static Bias - DO NOT MOVE THE SENSOR')
    offsets = [0] * 6
    count = 0
    end_time = time.time() + calibration_time
    while time.time() < end_time:
        readings = get_raw_data()
        if readings:
            for i in range(6): offsets[i] += readings[i]
            count += 1
    return [i / count for i in offsets]

# --- EXECUTION FLOW ---

# 1. Master Linear Calibration for ALL THREE axes
accel_map = {}
for i, name in enumerate(['X', 'Y', 'Z']):
    m, b = get_linear_params(i, name, calibration_time=5)
    accel_map[name] = {'m': m, 'b': b}

# 2. Per-Trial Gyro Bias
gyro_bias = get_static_bias(5)

# 3. Start Recording
filename = f"gait_trial.csv"
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"])
    
    print(f"\nRECORDING STARTED: {filename}")
    print("Perform the Sit-to-Stand movement now. Press Ctrl+C to stop.")
    
    try:
        while True:
            raw = get_raw_data()
            if raw:
                # Apply Linear Correction to all three axes
                cal_ax = (raw[0] - accel_map['X']['b']) / accel_map['X']['m']
                cal_ay = (raw[1] - accel_map['Y']['b']) / accel_map['Y']['m']
                cal_az = (raw[2] - accel_map['Z']['b']) / accel_map['Z']['m']
                
                # Apply Static Gyro Bias
                cal_gx = raw[3] - gyro_bias[3]
                cal_gy = raw[4] - gyro_bias[4]
                cal_gz = raw[5] - gyro_bias[5]

                writer.writerow([cal_ax, cal_ay, cal_az, cal_gx, cal_gy, cal_gz])
    except KeyboardInterrupt:
        print(f"\nTrial captured and saved to {filename}")
        ser.close()
