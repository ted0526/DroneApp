import pandas as pd
from datetime import datetime, timedelta
import numpy as np

num_points = 100
start_time = datetime.now()

data = {
    "Timestamp": [start_time + timedelta(seconds=i) for i in range(num_points)],

    # GAN ESC Data (Lower Temps, Higher RPM)
    "Voltage_GAN": np.random.uniform(11.0, 12.6, num_points),
    "Current_GAN": np.random.uniform(4.0, 6.5, num_points),
    "RPM_GAN": np.random.randint(2000, 4000, num_points),  # Increased RPM range
    "Temp1_GAN": np.random.uniform(20, 40, num_points),  # Lower temperatures
    "Temp2_GAN": np.random.uniform(20, 40, num_points),
    "Temp3_GAN": np.random.uniform(20, 40, num_points),
    "Temp4_GAN": np.random.uniform(20, 40, num_points),

    # Control ESC Data (Normal Temps, Lower RPM)
    "Voltage_Control": np.random.uniform(11.0, 12.6, num_points),
    "Current_Control": np.random.uniform(4.0, 6.5, num_points),
    "RPM_Control": np.random.randint(1000, 3000, num_points),  # Default RPM range
    "Temp1_Control": np.random.uniform(30, 50, num_points),  # Normal temperatures
    "Temp2_Control": np.random.uniform(30, 50, num_points),
    "Temp3_Control": np.random.uniform(30, 50, num_points),
    "Temp4_Control": np.random.uniform(30, 50, num_points),
}

# Save to logs folder
csv_filename = "logs/gui_test.csv"
df = pd.DataFrame(data)
df.to_csv(csv_filename, index=False)

print(f"Test CSV saved at {csv_filename}")
