#!/usr/bin/env python3
"""
Batch Experiment Runner

Runs multiple experiments sequentially from a batch configuration file.
This allows you to queue up experiments and run them unattended.

Usage:
    python scripts/run_batch_experiments.py --batch configs/batch/my_experiments.yaml

Example batch config:
    experiments:
      - name: "Zero-shot baseline temp 0.3"
        script: test_zero_shot.py
        config: configs/qwen25_32b_temp03.yaml
        args: --n 1071 --output runs/zero_shot_temp03_full
      - name: "Physician role debate temp 0.3"
        script: test_debate_physician_role.py
        config: configs/qwen25_32b_temp03.yaml
        args: --n 1071 --output runs/debate_physician_role_temp03_full
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml


class ExperimentRunner:
    """Runs a batch of experiments sequentially."""

    def __init__(self, batch_file: Path, dry_run: bool = False):
        self.batch_file = batch_file
        self.dry_run = dry_run
        self.start_time = None
        self.results = []

        # Load batch configuration
        with open(batch_file, 'r') as f:
            self.config = yaml.safe_load(f)

        self.experiments = self.config.get('experiments', [])

        # Setup logging
        self.log_dir = Path('logs/batch_runs')
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_name = batch_file.stem
        self.log_file = self.log_dir / f"{batch_name}_{timestamp}.log"

    def log(self, message: str):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] {message}"

        print(full_message)

        with open(self.log_file, 'a') as f:
            f.write(full_message + '\n')

    def validate_experiments(self) -> bool:
        """Validate that all experiments are properly configured."""
        if not self.experiments:
            self.log("ERROR: No experiments found in batch configuration")
            return False

        for i, exp in enumerate(self.experiments):
            if 'script' not in exp:
                self.log(f"ERROR: Experiment {i+1} missing 'script' field")
                return False

            if 'config' not in exp:
                self.log(f"ERROR: Experiment {i+1} missing 'config' field")
                return False

            # Check script exists
            script_path = Path('scripts') / exp['script']
            if not script_path.exists():
                self.log(f"ERROR: Script not found: {script_path}")
                return False

            # Check config exists
            config_path = Path(exp['config'])
            if not config_path.exists():
                self.log(f"ERROR: Config not found: {config_path}")
                return False

        return True

    def run_experiment(self, exp: Dict, exp_num: int, total: int) -> bool:
        """Run a single experiment."""
        name = exp.get('name', f"Experiment {exp_num}")
        script = exp['script']
        config = exp['config']
        args = exp.get('args', '')

        self.log("=" * 80)
        self.log(f"Starting experiment {exp_num}/{total}: {name}")
        self.log(f"  Script: {script}")
        self.log(f"  Config: {config}")
        self.log(f"  Args: {args}")
        self.log("=" * 80)

        # Build command
        cmd = f"python scripts/{script} --config {config}"
        if args:
            cmd += f" {args}"

        if self.dry_run:
            self.log(f"DRY RUN: Would execute: {cmd}")
            return True

        # Run experiment
        exp_start = time.time()

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=False,  # Show output in real-time
                text=True,
                cwd=Path.cwd()
            )

            exp_duration = time.time() - exp_start

            if result.returncode == 0:
                self.log(f"✓ Experiment completed successfully in {exp_duration:.1f}s")
                self.results.append({
                    'name': name,
                    'status': 'success',
                    'duration': exp_duration
                })
                return True
            else:
                self.log(f"✗ Experiment failed with return code {result.returncode}")
                self.results.append({
                    'name': name,
                    'status': 'failed',
                    'duration': exp_duration,
                    'error': f"Return code {result.returncode}"
                })
                return False

        except Exception as e:
            exp_duration = time.time() - exp_start
            self.log(f"✗ Experiment crashed: {e}")
            self.results.append({
                'name': name,
                'status': 'error',
                'duration': exp_duration,
                'error': str(e)
            })
            return False

    def run_all(self, continue_on_error: bool = True):
        """Run all experiments in the batch."""
        self.start_time = time.time()

        self.log("=" * 80)
        self.log(f"BATCH EXPERIMENT RUN")
        self.log(f"Batch file: {self.batch_file}")
        self.log(f"Total experiments: {len(self.experiments)}")
        self.log(f"Continue on error: {continue_on_error}")
        self.log(f"Dry run: {self.dry_run}")
        self.log(f"Log file: {self.log_file}")
        self.log("=" * 80)

        # Validate
        if not self.validate_experiments():
            self.log("ERROR: Validation failed. Aborting.")
            return False

        # Run each experiment
        total = len(self.experiments)
        for i, exp in enumerate(self.experiments, 1):
            success = self.run_experiment(exp, i, total)

            if not success and not continue_on_error:
                self.log(f"ERROR: Experiment failed and continue_on_error=False. Stopping.")
                break

            # Brief pause between experiments
            if i < total:
                self.log(f"Pausing 5 seconds before next experiment...")
                if not self.dry_run:
                    time.sleep(5)

        # Summary
        self.print_summary()

        return True

    def print_summary(self):
        """Print summary of all experiments."""
        total_duration = time.time() - self.start_time

        self.log("")
        self.log("=" * 80)
        self.log("BATCH EXPERIMENT SUMMARY")
        self.log("=" * 80)

        success_count = sum(1 for r in self.results if r['status'] == 'success')
        failed_count = sum(1 for r in self.results if r['status'] in ['failed', 'error'])

        self.log(f"Total experiments: {len(self.results)}")
        self.log(f"Successful: {success_count}")
        self.log(f"Failed: {failed_count}")
        self.log(f"Total time: {total_duration:.1f}s ({total_duration/3600:.2f} hours)")

        self.log("")
        self.log("Individual Results:")
        for i, result in enumerate(self.results, 1):
            status_symbol = "✓" if result['status'] == 'success' else "✗"
            self.log(f"  {i}. {status_symbol} {result['name']}: {result['status']} ({result['duration']:.1f}s)")
            if 'error' in result:
                self.log(f"     Error: {result['error']}")

        self.log("=" * 80)
        self.log(f"Log saved to: {self.log_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Run multiple experiments sequentially from a batch configuration'
    )
    parser.add_argument(
        '--batch',
        type=str,
        required=True,
        help='Path to batch configuration YAML file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would be run without actually running experiments'
    )
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop batch if any experiment fails (default: continue)'
    )

    args = parser.parse_args()

    batch_file = Path(args.batch)
    if not batch_file.exists():
        print(f"ERROR: Batch file not found: {batch_file}")
        sys.exit(1)

    runner = ExperimentRunner(batch_file, dry_run=args.dry_run)
    success = runner.run_all(continue_on_error=not args.stop_on_error)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
