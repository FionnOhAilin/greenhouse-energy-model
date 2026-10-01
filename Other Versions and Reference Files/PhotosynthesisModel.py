import numpy as np
import matplotlib.pyplot as plt

# Define the radiation values
radiation_values = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
CO2_values = np.arange(400, 1201, 1)  # From 400 to 1200 ppm as shown in the plot

# Store results for each radiation value
results = {}

for I in radiation_values:
    # Constants
    a_a = 8.9e-5
    b_a = 0.021
    k = 0.94
    m = 0.1
    L = 2.275
    I_s = 8.572170659
    I_adjusted = I * 0.5 * 0.7

    tau = a_a / (b_a * k) * np.log((b_a * I_adjusted * k + (1 - m)) / (b_a * I_adjusted * np.exp(-k * L) + (1 - m)))

    a_leaf = 2.11e-5
    a_canopy = a_leaf * (1 - ((np.exp(-k * L)) / (1 - m)))

    t = 3600
    rho_co2 = 1.83e-3

    # Store p_n values for this radiation level
    p_n_values = []

    for C in CO2_values:
        p_g = ((a_canopy * I_adjusted * tau * rho_co2 * C) / (a_canopy * I_adjusted + tau * rho_co2 * C)) * t
        r = 4e-5
        p_n = (p_g - r * t * L)
        p_n_values.append(p_n)

    # Store the results for this radiation value
    results[I] = p_n_values

# Create the plot with more space at the bottom
plt.figure(figsize=(12, 9))

# Line styles and markers for different radiation values
line_styles = {
    100: ('black', '-'),  # Solid black
    200: ('black', '--'),  # Dashed black
    300: ('black', ':'),  # Dotted black
    400: ('black', '-.'),  # Dash-dot black
    500: ('black', '-.'),  # Dash-dot black
    600: ('gray', '-'),  # Solid gray
    700: ('gray', '-'),  # Solid gray
    800: ('lightgray', '-'),  # Solid light gray
    900: ('black', '-.'),  # Dash-dot black with different dash pattern
    1000: ('black', '-')  # Solid black, thicker
}

# Plot each line
for I in radiation_values:
    color, style = line_styles[I]
    linewidth = 2 if I == 1000 else 1
    plt.plot(CO2_values, results[I], linestyle=style, color=color, linewidth=linewidth, label=str(I))

# Set up the plot labels and appearance
plt.xlabel('CO$_2$ (ppm)', fontsize=20, labelpad=15)  # Added padding for the x-label
plt.ylabel('Canopy net photosynthesis (g CO$_2$ m$^{-2}$ hr$^{-1}$)', fontsize=19.5)
plt.xlim(400, 1200)
plt.ylim(0, 20)
plt.yticks(np.arange(0, 21, 2))
plt.grid(False)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)

# Create a custom legend box outside the plot
legend_box = plt.legend(
    [plt.Line2D([0], [0], color=line_styles[i][0], linestyle=line_styles[i][1],
                linewidth=2 if i == 1000 else 1) for i in radiation_values],
    [str(i) for i in radiation_values],
    loc='upper center',
    bbox_to_anchor=(0.5, -0.15),  # Position below the plot
    ncol=5,  # 5 items per row for 2 rows total
    fontsize=16,
    frameon=True,  # Add a frame
    title="External global radiation (W m$^{-2}$)",
    title_fontsize=16
)

# Adjust layout with extra space at the bottom for legend
plt.tight_layout()
plt.subplots_adjust(bottom=0.35)  # Increased bottom margin for legend

# Save the figure
plt.savefig('photosynthesis_model_plot.png', dpi=300, bbox_inches='tight')

# Show the plot
plt.show()