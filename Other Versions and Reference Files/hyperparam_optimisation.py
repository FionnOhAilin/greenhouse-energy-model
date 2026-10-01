import numpy as np
import pandas as pd
from scipy.optimize import dual_annealing
from joblib import load
import time
from datetime import timedelta, datetime
from functools import partial
import optuna
import matplotlib.pyplot as plt

# Import your original optimization class
from Optimise_dual_anealling import OptimizeEnergySources


def objective_hyperparameters(trial, heat_demand, light_demand, co2_demand, max_evals=30):
    """
    Objective function for hyperparameter optimization with Optuna

    Parameters:
    -----------
    trial : optuna.Trial
        Trial object for hyperparameter suggestion
    heat_demand, light_demand, co2_demand : DataFrames
        The demand data needed for optimization
    max_evals : int
        Maximum number of function evaluations to allow for each dual annealing run

    Returns:
    --------
    float
        The best cost achieved with the suggested hyperparameters
    """
    # Hyperparameters to optimize
    initial_temp = trial.suggest_float("initial_temp", 1000, 10000, log=True)
    visit = trial.suggest_float("visit", 1.1, 2.9)
    accept = trial.suggest_float("accept", -10.0, -1.0)
    maxiter = trial.suggest_int("maxiter", 50, 150)

    # Create optimizer instance
    optimizer = OptimizeEnergySources(heat_demand, light_demand, co2_demand)

    # Define bounds for optimization variables
    bounds = [
        (0, optimizer.chp_max_power),
        (0, optimizer.geo_max_power),
        (0, optimizer.gshp_max_power),
        (0, optimizer.solar_max_power),
        (0, optimizer.wasteheat_max_power),
        (0, optimizer.grid_max_power),
        (0, optimizer.boiler_max_power),
        (0, optimizer.co2_max_power)
    ]

    # Set up a modified objective function with early stopping based on function evaluations
    optimizer.max_evaluations = max_evals
    optimizer.evaluation_count = 0

    original_objective = optimizer.objective

    def objective_with_limit(x):
        if optimizer.evaluation_count >= optimizer.max_evaluations:
            return optimizer.best_cost  # Return best cost found so far if max evaluations reached
        optimizer.evaluation_count += 1
        return original_objective(x)

    # Store the original objective function to restore later
    optimizer.objective = objective_with_limit

    # Initial point
    x0 = [0.054, 0, 0, 0, 0.11, 0.036, 0, 0]

    # Run dual annealing with the suggested hyperparameters
    # Run dual annealing with the suggested hyperparameters
    try:
        result = dual_annealing(
            optimizer.objective,
            bounds=bounds,
            x0=x0,
            initial_temp=initial_temp,
            maxiter=maxiter,
            visit=visit,
            accept=accept,
            no_local_search=False,
            seed=42,
        )

        # Check for NaNs in result
        if np.isnan(result.fun) or np.any(np.isnan(result.x)):
            print(f"WARNING: NaN detected in result with params: temp={initial_temp}, visit={visit}, accept={accept}")
            return 1e10  # Return a high cost instead of NaN

        return optimizer.best_cost if optimizer.best_cost < float('inf') else 1e10

    except Exception as e:
        print(f"Exception in dual_annealing: {e}")
        return 1e10


def run_hyperparameter_optimization(n_trials=50):
    """
    Run hyperparameter optimization with Optuna

    Parameters:
    -----------
    n_trials : int
        Number of optimization trials to run

    Returns:
    --------
    optuna.Study
        The completed study object containing results
    """
    print("Loading demand data...")
    heat_demand = pd.read_json("heat_demand.json")
    light_demand = pd.read_json("light_demand.json")
    co2_demand = pd.read_json("co2_demand.json")

    # Create the objective function with fixed demand data
    objective_fn = partial(objective_hyperparameters,
                           heat_demand=heat_demand,
                           light_demand=light_demand,
                           co2_demand=co2_demand,
                           max_evals=30)

    # Create and run the study
    study = optuna.create_study(direction="minimize")
    study.optimize(objective_fn, n_trials=n_trials)

    # Print optimization results
    print("\nBest hyperparameters:")
    print(study.best_params)
    print(f"Best value: £{study.best_value:,.2f}")

    # Create a dataframe to log all trials
    trials_df = pd.DataFrame(
        {key: [trial.params[key] for trial in study.trials] for key in study.best_params.keys()}
    )
    trials_df["value"] = [trial.value for trial in study.trials]

    # Save trials to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hyperparameter_optimization_{timestamp}.csv"
    trials_df.to_csv(filename, index=False)
    print(f"Trial results saved to {filename}")

    # Run final optimization with best parameters
    print("\nRunning final optimization with best parameters...")
    optimizer = OptimizeEnergySources(heat_demand, light_demand, co2_demand)

    bounds = [
        (0, optimizer.chp_max_power),
        (0, optimizer.geo_max_power),
        (0, optimizer.gshp_max_power),
        (0, optimizer.solar_max_power),
        (0, optimizer.wasteheat_max_power),
        (0, optimizer.grid_max_power),
        (0, optimizer.boiler_max_power),
        (0, optimizer.co2_max_power)
    ]

    # Initial points to try
    initial_points = [
        [0.054, 0, 0, 0, 0.11, 0.036, 0, 0],
        [optimizer.chp_max_power, 0, 0, 0, 0, 0, 0, 0],
        [0.1, 0, 0.05, 0, 0, 0, 0, 0]
    ]

    results = []

    for i, x0 in enumerate(initial_points):
        print(f"\nStarting final optimization run {i + 1} with initial CHP power: {x0[0]:.2f} MW")

        result = dual_annealing(
            optimizer.objective,
            bounds=bounds,
            x0=x0,
            initial_temp=study.best_params['initial_temp'],
            maxiter=study.best_params['maxiter'],
            visit=study.best_params['visit'],
            accept=study.best_params['accept'],
            no_local_search=False,
            seed=42 + i,
        )

        results.append(result)

    best_result = min(results, key=lambda r: r.fun)

    # Print final optimization results
    print("\nFinal Optimization Results:")
    print(f"Best solution cost: £{best_result.fun:,.2f}")

    technologies = ['CHP', 'Geothermal', 'GSHP', 'Solar PV', 'Waste Heat', 'Grid', 'Boiler', 'CO2 Import']
    for tech, capacity in zip(technologies, best_result.x):
        print(f"{tech}: {capacity:.4f}")

    return study


if __name__ == "__main__":
    start_time = time.time()

    # Number of trials to run
    n_trials = 50

    print(f"Starting hyperparameter optimization with {n_trials} trials...")
    study = run_hyperparameter_optimization(n_trials)

    end_time = time.time()
    print(f"\nTotal runtime: {timedelta(seconds=end_time - start_time)}")

    # Optionally, visualize the optimization results
    try:
        import matplotlib.pyplot as plt

        # Plot optimization history
        plt.figure(figsize=(10, 6))
        optuna.visualization.matplotlib.plot_optimization_history(study)
        plt.title("Optimization History")
        plt.tight_layout()
        plt.savefig("optimization_history.png")

        # Plot parameter importances
        plt.figure(figsize=(10, 6))
        optuna.visualization.matplotlib.plot_param_importances(study)
        plt.title("Parameter Importances")
        plt.tight_layout()
        plt.savefig("parameter_importances.png")

        print("Visualizations saved as PNG files")
    except ImportError:
        print("Matplotlib not installed. Skipping visualizations.")