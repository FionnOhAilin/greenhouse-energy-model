# Greenhouse energy model

An Irish techno-economic tool for the optimisation of greenhouse energy modelling with a GUI for prospective greenhouse operators. Allows the operator to analyse different energy system technologies under accurate Irish climate and economic conditions.

## Installation
### Requirments
- Python 3.9 or higher
- Git

### Steps
1: Clone the repository:
```bash
git clone https://github.com/FionnOhAilin/greenhouse-energy-model.git
cd greenhouse-energy-model
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the package:
```bash
pip install -e .
```
## Getting started

Before running, ensure you have climate and solar radiation data in the `CSV Inputs/` folder (the script will prompt you for data sources).

**Run the main optimisation:**
```bash
python -m greenhouse_model.MainScript
```

**Or run the interactive dashboard:**
```bash
python Dash/interactive_capacity_explorer.py
```

## Testing

Not yet set up

## Contributing

Pull requests welcome. For major changes, open an issue first.

## License
This project is licensed under the [MIT License](https://github.com/FionnOhAilin/greenhouse-energy-model/blob/main/LICENSE)
