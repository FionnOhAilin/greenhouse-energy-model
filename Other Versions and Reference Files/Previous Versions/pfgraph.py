import numpy as np
import matplotlib.pyplot as plt

# Define parameters for power factor improvement visualization
# Before adding capacitive power
theta_before = np.deg2rad(45)  # Lagging power factor angle
theta_after = np.deg2rad(20)  # Reduced lagging power factor angle

# Generate vectors for visualization
x = [np.cos(theta_before), np.cos(theta_after)]  # Real power components
y = [np.sin(theta_before), np.sin(theta_after)]  # Reactive power components

# Create the plot
plt.figure(figsize=(8, 6))
plt.quiver(0, 0, x[0], y[0], angles='xy', scale_units='xy', scale=1, color='red', label='Before Capacitive Power')
plt.quiver(0, 0, x[1], y[1], angles='xy', scale_units='xy', scale=1, color='green', label='After Capacitive Power')

# Add reference lines and grid
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.grid(True, linestyle='--', alpha=0.6)

# Annotations
plt.text(x[0] / 2, y[0] / 2, 'Before Q (Lagging)', color='red', fontsize=10)
plt.text(x[1] / 2, y[1] / 2, 'After Q (Reduced)', color='green', fontsize=10)

# Labels and title
plt.xlabel('Real Power (P)', fontsize=12)
plt.ylabel('Reactive Power (Q)', fontsize=12)
plt.title('Impact of Capacitive Power on Lagging Power Factor', fontsize=14)
plt.legend(loc='upper right')
plt.axis('equal')
plt.show()
