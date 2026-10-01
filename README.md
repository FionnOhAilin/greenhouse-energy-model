# Greenhouse energy model

An Irish techno-economic tool for the optimisation of greenhouse energy modelling with a GUI for prospective greenhouse operators. Allows the operator to analyse different energy system technologies under accurate Irish climate and economic conditions.

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
python -m greenhouse_model.MainScript
```
## Getting started

1. Ensure you have climate and solar radiation data in `CSV Inputs/` folder (see MainScript prompts for data sources)
2. Run the main optimisation:
```bash
python -m greenhouse_model.MainScript
```
3. For the interactive dashboard:
```bash
python Dash/interactive_capacity_explorer.py
```

## Testing

Not yet set up

## Contributing

Pull requests welcome. For major changes, open an issue first.

## License
This project is licensed under the [MIT License](https://github.com/FionnOhAilin/greenhouse-energy-model/blob/main/LICENSE)
