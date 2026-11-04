import numpy as np
import matplotlib.pyplot as plt


def compare_solar_profiles(optimiser, solar_mw, week_start_hour=0, save_prefix=None):
    """
    Compare flat-average solar with time-resolved solar for one solar size.
    solar_mw: installed solar in MW (e.g. result.x[3]).
    """
    solar_kw = solar_mw * 1000
    solar_df = optimiser.solar_south.calculate_supply(solar_kw)
    solar_hourly = solar_df["Electricity Output (MWh)"].to_numpy(dtype=float)  # MWh per hour = average MW
    light = np.asarray(optimiser.light_demand["MWh"], dtype=float)              # MWh per hour = average MW

    annual_mwh = solar_hourly.sum()
    flat_mw = annual_mwh / 8760                                                # same energy, spread evenly
    flat_hourly = np.full_like(solar_hourly, flat_mw)

    # Grid needed after solar, hour by hour, for each approach
    grid_resolved = np.maximum(0, light - solar_hourly)
    grid_flat = np.maximum(0, light - flat_hourly)

    # ---- Figure 1: one week, hourly ----
    s = slice(week_start_hour, week_start_hour + 168)
    hours = np.arange(168)
    fig1, ax = plt.subplots(figsize=(10, 4))
    ax.plot(hours, light[s], color="black", label="Light demand")
    ax.plot(hours, solar_hourly[s], color="orange", label="Solar (time-resolved)")
    ax.axhline(flat_mw, color="grey", linestyle="--", label="Solar (flat average)")
    ax.set_xlabel("Hour of week")
    ax.set_ylabel("Power (MW)")
    ax.set_title(f"Light demand vs solar, {solar_kw:.1f} kW (one week)")
    ax.legend()
    fig1.tight_layout()

    # ---- Figure 2: monthly solar energy, both methods ----
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_hours = np.array(days) * 24
    edges = np.concatenate([[0], np.cumsum(month_hours)])
    resolved_month = [solar_hourly[edges[i]:edges[i + 1]].sum() for i in range(12)]
    flat_month = [flat_hourly[edges[i]:edges[i + 1]].sum() for i in range(12)]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig2, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(12)
    ax.bar(x - 0.2, resolved_month, width=0.4, color="orange", label="Time-resolved")
    ax.bar(x + 0.2, flat_month, width=0.4, color="grey", label="Flat average")
    ax.set_xticks(x, months)
    ax.set_ylabel("Energy (MWh per month)")
    ax.set_title("Monthly solar energy: time-resolved vs flat average")
    ax.legend()
    fig2.tight_layout()

    # ---- Figure 3: grid still needed, by month ----
    grid_res_month = [grid_resolved[edges[i]:edges[i + 1]].sum() for i in range(12)]
    grid_flat_month = [grid_flat[edges[i]:edges[i + 1]].sum() for i in range(12)]

    fig3, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x - 0.2, grid_res_month, width=0.4, color="orange", label="Time-resolved")
    ax.bar(x + 0.2, grid_flat_month, width=0.4, color="grey", label="Flat average")
    ax.set_xticks(x, months)
    ax.set_ylabel("Grid energy needed for light (MWh per month)")
    ax.set_title("Grid energy still needed after solar, by month")
    ax.legend()
    fig3.tight_layout()

    if save_prefix:
        fig1.savefig(f"{save_prefix}_week.png", dpi=300)
        fig2.savefig(f"{save_prefix}_monthly_solar.png", dpi=300)
        fig3.savefig(f"{save_prefix}_monthly_grid.png", dpi=300)

    print(f"Annual solar (time-resolved): {annual_mwh:.2f} MWh")
    print(f"Flat average: {flat_mw:.6f} MW (same annual energy)")
    print(f"Annual grid energy, time-resolved: {grid_resolved.sum():.1f} MWh")
    print(f"Annual grid energy, flat: {grid_flat.sum():.1f} MWh")

    plt.show()


# Usage, after the optimisation has run:
# compare_solar_profiles(optimiser, solar_mw=result.x[3], save_prefix="solar_compare")