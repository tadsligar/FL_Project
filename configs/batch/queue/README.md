# Experiment Queue

Drop experiment configs here - they'll run automatically in order!

## How to Add an Experiment

Create a `.yaml` file with this format:

```yaml
name: "Descriptive name for your experiment"
script: test_script_name.py
config: configs/your_config.yaml
args: --n 1071 --output runs/your_output
```

## Example

```yaml
name: "Zero-shot baseline @ temp 0.3"
script: test_zero_shot.py
config: configs/qwen25_32b_temp03.yaml
args: --n 1071 --output runs/zero_shot_temp03_full
```

Save as: `02_my_experiment.yaml`

## Tips

- Use numbered prefixes (01_, 02_, etc.) to see intended order
- Oldest file runs first (by creation time)
- Check `../completed/` for finished experiments
- Check `../failed/` if something goes wrong

## Currently Queued

Check: `ls *.yaml` or just look at files in this directory
