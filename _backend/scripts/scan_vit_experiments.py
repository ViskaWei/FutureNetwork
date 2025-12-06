#!/usr/bin/env python3
"""
VIT Experiment Scanner
======================

Scan the VIT repository for experiments and register them to the central index.

Usage:
    python scan_vit_experiments.py --vit-root ~/VIT
    python scan_vit_experiments.py --vit-root ~/VIT --since "2025-11-28"
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


def parse_lightning_log(version_dir: Path) -> dict:
    """Parse a lightning_logs/version_X directory."""
    info = {
        "output_path": str(version_dir),
        "config_path": "",
        "metrics_summary": "",
        "start_time": "",
        "end_time": "",
    }
    
    # Try to get modification time
    try:
        mtime = version_dir.stat().st_mtime
        info["end_time"] = datetime.fromtimestamp(mtime).isoformat()
    except:
        pass
    
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
                    # Extract key metrics
                    metrics = []
                    for key in ['val_r2', 'val_mae', 'val_rmse', 'test_r2', 'test_mae']:
                        if key in last_row and last_row[key]:
                            metrics.append(f"{key}={last_row[key]}")
                    if metrics:
                        info["metrics_summary"] = ", ".join(metrics[:3])
        except Exception as e:
            print(f"  ⚠️ Could not parse {metrics_file}: {e}")
    
    return info


def parse_result_dir(result_dir: Path) -> dict:
    """Parse a results/XXX directory."""
    info = {
        "output_path": str(result_dir),
        "metrics_summary": "",
    }
    
    # Look for summary files
    for fname in ["summary.json", "results.json", "metrics.json"]:
        summary_file = result_dir / fname
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    data = json.load(f)
                    # Try to extract metrics
                    metrics = []
                    for key in ['r2', 'R2', 'mae', 'MAE', 'rmse', 'RMSE', 'best_r2', 'test_r2']:
                        if key in data:
                            val = data[key]
                            if isinstance(val, float):
                                metrics.append(f"{key}={val:.4f}")
                            else:
                                metrics.append(f"{key}={val}")
                    if metrics:
                        info["metrics_summary"] = ", ".join(metrics[:3])
                        break
            except:
                pass
    
    # Look for CSV result files
    for csv_file in result_dir.glob("*.csv"):
        if "results" in csv_file.name.lower():
            try:
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    if rows:
                        # Find best result by R2 if available
                        best_row = rows[-1]
                        for row in rows:
                            if 'r2' in row and row['r2']:
                                try:
                                    if float(row['r2']) > float(best_row.get('r2', 0)):
                                        best_row = row
                                except:
                                    pass
                        
                        metrics = []
                        for key in ['r2', 'R2', 'mae', 'MAE', 'rmse', 'RMSE']:
                            if key in best_row and best_row[key]:
                                metrics.append(f"{key}={best_row[key]}")
                        if metrics and not info["metrics_summary"]:
                            info["metrics_summary"] = ", ".join(metrics[:3])
                            break
            except:
                pass
    
    return info


def infer_topic(path: str, name: str) -> str:
    """Infer topic from path or experiment name."""
    path_lower = path.lower()
    name_lower = name.lower()
    combined = f"{path_lower} {name_lower}"
    
    topic_keywords = {
        "cnn": ["cnn", "conv", "dilated", "kernel"],
        "swin": ["swin", "transformer", "attention", "vit"],
        "noise": ["noise", "snr", "robustness"],
        "pca": ["pca", "principal"],
        "ridge": ["ridge", "linear", "regression", "alpha"],
        "lightgbm": ["lightgbm", "lgbm", "gbm", "boost"],
        "topk": ["topk", "top_k", "feature_selection"],
        "gta": ["global", "tower", "gta", "metadata"],
        "distill": ["distill", "latent", "probe", "encoder"],
        "train": ["train", "val", "sweep", "hyperp"],
    }
    
    for topic, keywords in topic_keywords.items():
        if any(kw in combined for kw in keywords):
            return topic
    
    return "other"


def scan_vit_experiments(
    vit_root: Path,
    since: Optional[datetime] = None,
    dry_run: bool = False
) -> list[dict]:
    """Scan VIT repository for experiments."""
    
    print(f"🔍 Scanning VIT repository: {vit_root}")
    
    experiments = []
    existing_index = load_index()
    existing_ids = {r.get("experiment_id") for r in existing_index}
    
    # 1. Scan lightning_logs/
    lightning_logs = vit_root / "lightning_logs"
    if lightning_logs.exists():
        print(f"\n📁 Scanning {lightning_logs}...")
        for version_dir in sorted(lightning_logs.glob("version_*")):
            if not version_dir.is_dir():
                continue
            
            # Check modification time
            try:
                mtime = datetime.fromtimestamp(version_dir.stat().st_mtime)
                if since and mtime < since:
                    continue
            except:
                pass
            
            version_num = version_dir.name.replace("version_", "")
            exp_id = f"VIT-lightning-v{version_num}"
            
            if exp_id in existing_ids:
                print(f"  ⏭️  Skipping {exp_id} (already exists)")
                continue
            
            info = parse_lightning_log(version_dir)
            topic = infer_topic(str(version_dir), "")
            
            exp = {
                "experiment_id": exp_id,
                "project": "VIT",
                "topic": topic,
                "status": "completed",
                **info
            }
            experiments.append(exp)
            print(f"  ✨ Found: {exp_id} [{topic}]")
    
    # 2. Scan results/
    results_dir = vit_root / "results"
    if results_dir.exists():
        print(f"\n📁 Scanning {results_dir}...")
        for result_subdir in sorted(results_dir.iterdir()):
            if not result_subdir.is_dir():
                continue
            if result_subdir.name.startswith("."):
                continue
            
            # Check modification time
            try:
                mtime = datetime.fromtimestamp(result_subdir.stat().st_mtime)
                if since and mtime < since:
                    continue
            except:
                pass
            
            exp_name = result_subdir.name
            exp_id = f"VIT-results-{exp_name}"
            
            if exp_id in existing_ids:
                print(f"  ⏭️  Skipping {exp_id} (already exists)")
                continue
            
            info = parse_result_dir(result_subdir)
            topic = infer_topic(str(result_subdir), exp_name)
            
            exp = {
                "experiment_id": exp_id,
                "project": "VIT",
                "topic": topic,
                "status": "completed",
                **info
            }
            experiments.append(exp)
            print(f"  ✨ Found: {exp_id} [{topic}] {info.get('metrics_summary', '')[:30]}")
    
    # 3. Scan models/
    models_dir = vit_root / "models"
    if models_dir.exists():
        print(f"\n📁 Scanning {models_dir}...")
        for model_subdir in sorted(models_dir.iterdir()):
            if not model_subdir.is_dir():
                continue
            if model_subdir.name.startswith("."):
                continue
            
            exp_name = model_subdir.name
            exp_id = f"VIT-model-{exp_name}"
            
            if exp_id in existing_ids:
                print(f"  ⏭️  Skipping {exp_id} (already exists)")
                continue
            
            topic = infer_topic(str(model_subdir), exp_name)
            
            exp = {
                "experiment_id": exp_id,
                "project": "VIT",
                "topic": topic,
                "status": "completed",
                "output_path": str(model_subdir),
            }
            experiments.append(exp)
            print(f"  ✨ Found: {exp_id} [{topic}]")
    
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
        description="Scan VIT repository for experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--vit-root", "-v",
        type=Path,
        default=Path.home() / "VIT",
        help="Path to VIT repository root"
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
    
    scan_vit_experiments(
        vit_root=args.vit_root,
        since=since,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

