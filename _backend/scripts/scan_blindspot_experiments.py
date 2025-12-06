#!/usr/bin/env python3
"""
BlindSpotDenoiser Experiment Scanner
====================================

Scan the BlindSpotDenoiser repository for experiments and register them to the central index.

Usage:
    python scan_blindspot_experiments.py --blindspot-root ~/BlindSpotDenoiser
    python scan_blindspot_experiments.py --blindspot-root ~/BlindSpotDenoiser --since "2025-11-28"
"""

import argparse
import os
import re
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import the register function
from register_experiment import register_experiment, load_index


def parse_evals_dir(evals_dir: Path) -> list[dict]:
    """Parse the evals/ directory for experiment results."""
    experiments = []
    
    # Look for specific result files
    result_patterns = [
        ("*_results*.json", "json"),
        ("*_results*.csv", "csv"),
        ("*_report*.md", "md"),
    ]
    
    for pattern, ftype in result_patterns:
        for result_file in evals_dir.glob(pattern):
            exp_name = result_file.stem.replace("_results", "").replace("_report", "")
            
            info = {
                "output_path": str(result_file.parent),
                "log_path": str(result_file),
                "metrics_summary": "",
            }
            
            # Try to extract metrics
            if ftype == "json":
                try:
                    with open(result_file, 'r') as f:
                        data = json.load(f)
                        metrics = []
                        for key in ['r2', 'R2', 'mae', 'MAE', 'rmse', 'RMSE', 'mse', 'MSE']:
                            if key in data:
                                val = data[key]
                                if isinstance(val, float):
                                    metrics.append(f"{key}={val:.4f}")
                                else:
                                    metrics.append(f"{key}={val}")
                        if metrics:
                            info["metrics_summary"] = ", ".join(metrics[:3])
                except:
                    pass
            elif ftype == "csv":
                try:
                    with open(result_file, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            last_row = rows[-1]
                            metrics = []
                            for key in ['r2', 'R2', 'mae', 'MAE', 'rmse', 'RMSE']:
                                if key in last_row and last_row[key]:
                                    metrics.append(f"{key}={last_row[key]}")
                            if metrics:
                                info["metrics_summary"] = ", ".join(metrics[:3])
                except:
                    pass
            
            experiments.append({
                "name": exp_name,
                **info
            })
    
    return experiments


def parse_logs_dir(logs_dir: Path) -> list[dict]:
    """Parse the logs/ directory for training logs."""
    experiments = []
    
    for log_subdir in logs_dir.iterdir():
        if not log_subdir.is_dir():
            continue
        
        exp_name = log_subdir.name
        
        # Look for version subdirs
        for version_dir in sorted(log_subdir.glob("version_*")):
            version_num = version_dir.name.replace("version_", "")
            
            info = {
                "output_path": str(version_dir),
                "config_path": "",
                "metrics_summary": "",
            }
            
            # Look for hparams.yaml
            hparams_file = version_dir / "hparams.yaml"
            if hparams_file.exists():
                info["config_path"] = str(hparams_file)
            
            # Look for metrics.csv
            metrics_file = version_dir / "metrics.csv"
            if metrics_file.exists():
                try:
                    with open(metrics_file, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            last_row = rows[-1]
                            metrics = []
                            for key in ['val_r2', 'val_mae', 'val_loss', 'train_loss']:
                                if key in last_row and last_row[key]:
                                    metrics.append(f"{key}={last_row[key]}")
                            if metrics:
                                info["metrics_summary"] = ", ".join(metrics[:3])
                except:
                    pass
            
            experiments.append({
                "name": f"{exp_name}-v{version_num}",
                **info
            })
    
    return experiments


def parse_checkpoints_dir(checkpoints_dir: Path) -> list[dict]:
    """Parse the checkpoints/ directory for saved models."""
    experiments = []
    
    for exp_dir in checkpoints_dir.iterdir():
        if not exp_dir.is_dir():
            continue
        
        exp_name = exp_dir.name
        
        # Look for checkpoint files with metrics in name
        for ckpt_file in exp_dir.glob("**/*.ckpt"):
            # Try to extract metrics from filename
            # e.g., "r2=0.5979.ckpt"
            metrics_match = re.search(r'r2=([0-9.]+)', ckpt_file.name)
            metrics_summary = ""
            if metrics_match:
                metrics_summary = f"r2={metrics_match.group(1)}"
            
            experiments.append({
                "name": exp_name,
                "output_path": str(exp_dir),
                "metrics_summary": metrics_summary,
            })
            break  # Only take first checkpoint per experiment
    
    return experiments


def infer_topic(name: str) -> str:
    """Infer topic from experiment name."""
    name_lower = name.lower()
    
    topic_keywords = {
        "distill": ["encoder", "latent", "probe", "frozen", "distill"],
        "noise": ["noise", "denois", "blindspot", "snr"],
        "train": ["train", "sweep", "hyperp"],
        "gta": ["global", "tower", "pool"],
    }
    
    for topic, keywords in topic_keywords.items():
        if any(kw in name_lower for kw in keywords):
            return topic
    
    return "distill"  # Default for BlindSpot


def scan_blindspot_experiments(
    blindspot_root: Path,
    since: Optional[datetime] = None,
    dry_run: bool = False
) -> list[dict]:
    """Scan BlindSpotDenoiser repository for experiments."""
    
    print(f"🔍 Scanning BlindSpotDenoiser repository: {blindspot_root}")
    
    experiments = []
    existing_index = load_index()
    existing_ids = {r.get("experiment_id") for r in existing_index}
    
    # 1. Scan evals/
    evals_dir = blindspot_root / "evals"
    if evals_dir.exists():
        print(f"\n📁 Scanning {evals_dir}...")
        for exp_info in parse_evals_dir(evals_dir):
            exp_name = exp_info.pop("name")
            exp_id = f"BS-evals-{exp_name}"
            
            if exp_id in existing_ids:
                print(f"  ⏭️  Skipping {exp_id} (already exists)")
                continue
            
            topic = infer_topic(exp_name)
            
            exp = {
                "experiment_id": exp_id,
                "project": "BlindSpot",
                "topic": topic,
                "status": "completed",
                **exp_info
            }
            experiments.append(exp)
            print(f"  ✨ Found: {exp_id} [{topic}] {exp_info.get('metrics_summary', '')[:30]}")
    
    # 2. Scan logs/
    logs_dir = blindspot_root / "logs"
    if logs_dir.exists():
        print(f"\n📁 Scanning {logs_dir}...")
        for exp_info in parse_logs_dir(logs_dir):
            exp_name = exp_info.pop("name")
            exp_id = f"BS-logs-{exp_name}"
            
            if exp_id in existing_ids:
                print(f"  ⏭️  Skipping {exp_id} (already exists)")
                continue
            
            topic = infer_topic(exp_name)
            
            exp = {
                "experiment_id": exp_id,
                "project": "BlindSpot",
                "topic": topic,
                "status": "completed",
                **exp_info
            }
            experiments.append(exp)
            print(f"  ✨ Found: {exp_id} [{topic}]")
    
    # 3. Scan checkpoints/
    checkpoints_dir = blindspot_root / "checkpoints"
    if checkpoints_dir.exists():
        print(f"\n📁 Scanning {checkpoints_dir}...")
        for exp_info in parse_checkpoints_dir(checkpoints_dir):
            exp_name = exp_info.pop("name")
            exp_id = f"BS-ckpt-{exp_name}"
            
            if exp_id in existing_ids:
                print(f"  ⏭️  Skipping {exp_id} (already exists)")
                continue
            
            topic = infer_topic(exp_name)
            
            exp = {
                "experiment_id": exp_id,
                "project": "BlindSpot",
                "topic": topic,
                "status": "completed",
                **exp_info
            }
            experiments.append(exp)
            print(f"  ✨ Found: {exp_id} [{topic}] {exp_info.get('metrics_summary', '')[:30]}")
    
    print(f"\n📊 Found {len(experiments)} new experiments")
    
    # Register experiments
    if not dry_run and experiments:
        print("\n📝 Registering experiments...")
        for exp in experiments:
            register_experiment(**exp, update=False)
    elif dry_run:
        print("\n🔍 Dry run - no changes made")
    
    return experiments


def main():
    parser = argparse.ArgumentParser(
        description="Scan BlindSpotDenoiser repository for experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--blindspot-root", "-b",
        type=Path,
        default=Path.home() / "BlindSpotDenoiser",
        help="Path to BlindSpotDenoiser repository root"
    )
    parser.add_argument(
        "--since", "-s",
        type=str,
        help="Only include experiments modified since this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be registered without actually doing it"
    )
    
    args = parser.parse_args()
    
    since = None
    if args.since:
        since = datetime.fromisoformat(args.since)
    
    scan_blindspot_experiments(
        blindspot_root=args.blindspot_root,
        since=since,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

