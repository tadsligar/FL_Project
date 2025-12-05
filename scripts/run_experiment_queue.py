#!/usr/bin/env python3
"""
Experiment Queue Runner

Continuously monitors a queue directory for experiment configs and runs them sequentially.
Add new configs while experiments are running - they'll automatically start when ready.

Usage:
    python scripts/run_experiment_queue.py --queue configs/batch/queue

How it works:
    1. Monitors configs/batch/queue/ for .yaml files
    2. Runs oldest config first (by creation time)
    3. Moves completed configs to configs/batch/completed/
    4. Keeps running, checking for new configs every 30 seconds
    5. Stops after 5 minutes of no new configs (configurable)
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ExperimentQueue:
    """Manages a queue of experiment configurations."""

    def __init__(
        self,
        queue_dir: Path,
        completed_dir: Path,
        failed_dir: Path,
        check_interval: int = 30,
        idle_timeout: int = 300
    ):
        self.queue_dir = queue_dir
        self.completed_dir = completed_dir
        self.failed_dir = failed_dir
        self.check_interval = check_interval  # seconds between queue checks
        self.idle_timeout = idle_timeout  # seconds to wait with empty queue before stopping

        # Create directories
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.log_dir = Path('logs/experiment_queue')
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f"queue_run_{timestamp}.log"

        self.total_run = 0
        self.total_success = 0
        self.total_failed = 0

    def log(self, message: str):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] {message}"

        # Print with error handling for Windows encoding
        try:
            print(full_message)
        except UnicodeEncodeError:
            # Fallback to ASCII-safe version
            print(full_message.encode('ascii', errors='replace').decode('ascii'))

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(full_message + '\n')

    def get_next_experiment(self) -> Optional[Path]:
        """Get the oldest experiment config from queue."""
        yaml_files = list(self.queue_dir.glob('*.yaml'))

        if not yaml_files:
            return None

        # Sort by creation time (oldest first)
        yaml_files.sort(key=lambda p: p.stat().st_ctime)

        return yaml_files[0]

    def validate_config(self, config_path: Path) -> bool:
        """Validate experiment config."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            if 'script' not in config:
                self.log(f"ERROR: Config missing 'script' field: {config_path.name}")
                return False

            if 'config' not in config:
                self.log(f"ERROR: Config missing 'config' field: {config_path.name}")
                return False

            # Check script exists
            script_path = Path('scripts') / config['script']
            if not script_path.exists():
                self.log(f"ERROR: Script not found: {script_path}")
                return False

            # Check config exists
            exp_config_path = Path(config['config'])
            if not exp_config_path.exists():
                self.log(f"ERROR: Config not found: {exp_config_path}")
                return False

            return True

        except Exception as e:
            self.log(f"ERROR: Failed to validate config {config_path.name}: {e}")
            return False

    def run_experiment(self, config_path: Path) -> bool:
        """Run a single experiment."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            self.log(f"ERROR: Failed to load config {config_path.name}: {e}")
            return False

        name = config.get('name', config_path.stem)
        script = config['script']
        exp_config = config['config']
        args = config.get('args', '')

        self.log("=" * 80)
        self.log(f"Starting experiment: {name}")
        self.log(f"  Config file: {config_path.name}")
        self.log(f"  Script: {script}")
        self.log(f"  Config: {exp_config}")
        self.log(f"  Args: {args}")
        self.log("=" * 80)

        # Build command
        cmd = f"python scripts/{script} --config {exp_config}"
        if args:
            cmd += f" {args}"

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
                self.log(f"[OK] Experiment completed successfully in {exp_duration:.1f}s ({exp_duration/3600:.2f} hours)")
                return True
            else:
                self.log(f"[X] Experiment failed with return code {result.returncode}")
                return False

        except Exception as e:
            exp_duration = time.time() - exp_start
            self.log(f"[X] Experiment crashed: {e}")
            return False

    def move_to_completed(self, config_path: Path):
        """Move config to completed directory."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{config_path.stem}_{timestamp}.yaml"
        dest = self.completed_dir / new_name

        shutil.move(str(config_path), str(dest))
        self.log(f"Moved config to: {dest}")

    def move_to_failed(self, config_path: Path):
        """Move config to failed directory."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{config_path.stem}_{timestamp}.yaml"
        dest = self.failed_dir / new_name

        shutil.move(str(config_path), str(dest))
        self.log(f"Moved failed config to: {dest}")

    def run_queue(self, stop_when_empty: bool = False):
        """Run the experiment queue continuously."""
        self.log("=" * 80)
        self.log("EXPERIMENT QUEUE STARTED")
        self.log(f"Queue directory: {self.queue_dir}")
        self.log(f"Check interval: {self.check_interval}s")
        self.log(f"Idle timeout: {self.idle_timeout}s")
        self.log(f"Stop when empty: {stop_when_empty}")
        self.log(f"Log file: {self.log_file}")
        self.log("=" * 80)
        self.log("")
        self.log("Add .yaml configs to the queue directory to run experiments.")
        self.log("Press Ctrl+C to stop the queue runner.")
        self.log("")

        last_activity = time.time()

        try:
            while True:
                # Check for next experiment
                next_config = self.get_next_experiment()

                if next_config:
                    last_activity = time.time()

                    # Validate config
                    if not self.validate_config(next_config):
                        self.log(f"Skipping invalid config: {next_config.name}")
                        self.move_to_failed(next_config)
                        continue

                    # Run experiment
                    self.total_run += 1
                    success = self.run_experiment(next_config)

                    if success:
                        self.total_success += 1
                        self.move_to_completed(next_config)
                    else:
                        self.total_failed += 1
                        self.move_to_failed(next_config)

                    self.log("")
                    self.log(f"Queue stats: {self.total_run} run, {self.total_success} success, {self.total_failed} failed")
                    self.log("")

                    # Brief pause before checking for next
                    time.sleep(5)

                else:
                    # Queue is empty
                    idle_time = time.time() - last_activity

                    if stop_when_empty:
                        self.log("Queue is empty and stop_when_empty=True. Exiting.")
                        break

                    if idle_time > self.idle_timeout:
                        self.log(f"Queue has been empty for {idle_time:.0f}s (timeout: {self.idle_timeout}s). Exiting.")
                        break

                    # Show waiting message every minute
                    if int(idle_time) % 60 == 0 and idle_time > 0:
                        remaining = self.idle_timeout - idle_time
                        self.log(f"Waiting for experiments... ({remaining:.0f}s until timeout)")

                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.log("")
            self.log("Received Ctrl+C. Stopping queue runner...")

        # Final summary
        self.print_summary()

    def print_summary(self):
        """Print final summary."""
        self.log("")
        self.log("=" * 80)
        self.log("EXPERIMENT QUEUE SUMMARY")
        self.log("=" * 80)
        self.log(f"Total experiments: {self.total_run}")
        self.log(f"Successful: {self.total_success}")
        self.log(f"Failed: {self.total_failed}")
        self.log("")

        # Check if any experiments left in queue
        remaining = list(self.queue_dir.glob('*.yaml'))
        if remaining:
            self.log(f"WARNING: {len(remaining)} experiments still in queue:")
            for config in remaining:
                self.log(f"  - {config.name}")

        self.log("=" * 80)
        self.log(f"Log saved to: {self.log_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Run experiments from a queue directory'
    )
    parser.add_argument(
        '--queue',
        type=str,
        default='configs/batch/queue',
        help='Queue directory to monitor (default: configs/batch/queue)'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=30,
        help='Seconds between queue checks (default: 30)'
    )
    parser.add_argument(
        '--idle-timeout',
        type=int,
        default=300,
        help='Seconds to wait with empty queue before stopping (default: 300)'
    )
    parser.add_argument(
        '--stop-when-empty',
        action='store_true',
        help='Stop immediately when queue is empty (don\'t wait for new configs)'
    )

    args = parser.parse_args()

    queue_dir = Path(args.queue)
    completed_dir = queue_dir.parent / 'completed'
    failed_dir = queue_dir.parent / 'failed'

    runner = ExperimentQueue(
        queue_dir=queue_dir,
        completed_dir=completed_dir,
        failed_dir=failed_dir,
        check_interval=args.check_interval,
        idle_timeout=args.idle_timeout
    )

    runner.run_queue(stop_when_empty=args.stop_when_empty)


if __name__ == '__main__':
    main()
