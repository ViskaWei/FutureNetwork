#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Main Orchestrator
===============================================

This script runs all MVP tests in sequence and generates a summary.

Usage:
    sudo python run_all.py [--skip-baseline] [--skip-plots]

Options:
    --skip-baseline  Skip MVP-0.0 baseline tests (use existing results)
    --skip-plots     Skip plot generation
    --dry-run        Run in dry-run mode (no actual tests)

Output:
    results/summary_YYYYMMDD_HHMMSS.json
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def get_script_dir():
    """Get the scripts directory path."""
    return Path(__file__).parent


def get_results_dir():
    """Get the results directory path."""
    script_dir = get_script_dir()
    results_dir = script_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def get_img_dir():
    """Get the img directory path."""
    script_dir = get_script_dir()
    img_dir = script_dir.parent / "img"
    img_dir.mkdir(exist_ok=True)
    return img_dir


def run_script(script_name, description):
    """Run a Python script and return success status."""
    script_path = get_script_dir() / script_name
    
    print(f"\n{'═' * 70}")
    print(f"🚀 Running: {description}")
    print(f"   Script: {script_path}")
    print('═' * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully")
            return True
        else:
            print(f"\n❌ {description} failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏰ {description} timed out (30 min limit)")
        return False
    except Exception as e:
        print(f"\n❌ Error running {description}: {e}")
        return False


def find_latest_result(prefix):
    """Find the latest result file with given prefix."""
    results_dir = get_results_dir()
    pattern = f"{prefix}_*.json"
    files = sorted(results_dir.glob(pattern), reverse=True)
    return files[0] if files else None


def load_latest_results():
    """Load all latest result files."""
    results = {}
    
    prefixes = {
        "baseline": "MVP-0.0",
        "loss_sweep": "MVP-1.0",
        "delay_sweep": "MVP-1.1",
        "bandwidth_sweep": "MVP-1.2",
        "http_test": "MVP-2.0/2.1"
    }
    
    for prefix, mvp in prefixes.items():
        filepath = find_latest_result(prefix)
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    results[prefix] = {
                        "mvp": mvp,
                        "file": str(filepath),
                        "data": json.load(f)
                    }
            except Exception as e:
                print(f"⚠️ Error loading {filepath}: {e}")
    
    return results


def generate_summary(all_results, execution_log):
    """Generate a summary of all test results."""
    summary = {
        "experiment_id": "FN-20251206-network-01",
        "timestamp": datetime.now().isoformat(),
        "execution_log": execution_log,
        "results_files": {},
        "hypothesis_verification": {},
        "key_findings": []
    }
    
    # Add file references
    for name, data in all_results.items():
        summary["results_files"][name] = {
            "mvp": data["mvp"],
            "file": data["file"]
        }
    
    # Extract hypothesis verification
    
    # H1.1: TCP throughput drops >50% at 10% loss
    loss_data = all_results.get("loss_sweep", {}).get("data", {})
    loss_results = loss_data.get("results", [])
    baseline_tcp = None
    tcp_at_10pct = None
    
    for r in loss_results:
        if r.get("loss_rate_percent") == 0:
            baseline_tcp = r.get("tcp", {}).get("throughput_mbps")
        if r.get("loss_rate_percent") == 10:
            tcp_at_10pct = r.get("tcp", {}).get("throughput_mbps")
    
    if baseline_tcp and tcp_at_10pct:
        drop_pct = (1 - tcp_at_10pct / baseline_tcp) * 100
        summary["hypothesis_verification"]["H1.1"] = {
            "description": "TCP throughput drops >50% at 10% loss",
            "baseline_mbps": baseline_tcp,
            "at_10pct_loss_mbps": tcp_at_10pct,
            "drop_percent": drop_pct,
            "confirmed": drop_pct > 50
        }
    
    # H1.2: RTT scales linearly with delay
    delay_data = all_results.get("delay_sweep", {}).get("data", {})
    delay_results = delay_data.get("results", [])
    baseline_rtt = None
    
    for r in delay_results:
        if r.get("delay_ms") == 0:
            baseline_rtt = r.get("ping", {}).get("rtt_avg_ms")
    
    if baseline_rtt:
        errors = []
        for r in delay_results:
            delay = r.get("delay_ms")
            rtt = r.get("ping", {}).get("rtt_avg_ms")
            if rtt and delay > 0:
                expected = baseline_rtt + delay * 2
                error = abs(rtt - expected) / expected * 100
                errors.append(error)
        
        if errors:
            avg_error = sum(errors) / len(errors)
            summary["hypothesis_verification"]["H1.2"] = {
                "description": "RTT scales linearly with delay (RTT = baseline + 2×delay)",
                "baseline_rtt_ms": baseline_rtt,
                "avg_prediction_error_pct": avg_error,
                "confirmed": avg_error < 20
            }
    
    # H2.1: UDP loss matches injected loss rate
    udp_results = []
    for r in loss_results:
        loss = r.get("loss_rate_percent")
        measured = r.get("udp", {}).get("lost_percent")
        if loss is not None and measured is not None:
            udp_results.append({
                "injected_pct": loss,
                "measured_pct": measured,
                "diff": abs(measured - loss)
            })
    
    if udp_results:
        avg_diff = sum(r["diff"] for r in udp_results) / len(udp_results)
        summary["hypothesis_verification"]["H2.1"] = {
            "description": "UDP loss matches injected loss rate",
            "measurements": udp_results,
            "avg_diff_pct": avg_diff,
            "confirmed": avg_diff < 5  # Within 5% is acceptable
        }
    
    # H2.2: HTTP shows compounded effects
    http_data = all_results.get("http_test", {}).get("data", {})
    http_results = http_data.get("results", [])
    
    baseline_http = None
    combined_http = None
    
    for r in http_results:
        if r.get("file_size_mb") == 1:
            if r.get("condition") == "baseline":
                baseline_http = r.get("avg_s")
            elif r.get("condition") == "combined":
                combined_http = r.get("avg_s")
    
    if baseline_http and combined_http:
        ratio = combined_http / baseline_http
        summary["hypothesis_verification"]["H2.2"] = {
            "description": "HTTP shows compounded effects under combined anomalies (>2× slowdown)",
            "baseline_s": baseline_http,
            "combined_s": combined_http,
            "slowdown_ratio": ratio,
            "confirmed": ratio >= 2.0
        }
    
    # Generate key findings
    for h_id, h_data in summary["hypothesis_verification"].items():
        status = "✅ Confirmed" if h_data.get("confirmed") else "❌ Not confirmed"
        summary["key_findings"].append(f"{h_id}: {h_data['description']} - {status}")
    
    return summary


def print_final_summary(summary):
    """Print the final summary."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "📊 EXPERIMENT SUMMARY" + " " * 27 + "║")
    print("║" + " " * 16 + "FN-20251206-network-01" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Execution log
    print("\n📋 Execution Log:")
    for entry in summary.get("execution_log", []):
        status = "✅" if entry["success"] else "❌"
        print(f"   {status} {entry['mvp']}: {entry['script']}")
    
    # Results files
    print("\n📁 Results Files:")
    for name, info in summary.get("results_files", {}).items():
        print(f"   • {info['mvp']}: {info['file']}")
    
    # Hypothesis verification
    print("\n🔬 Hypothesis Verification:")
    for h_id, h_data in summary.get("hypothesis_verification", {}).items():
        status = "✅ CONFIRMED" if h_data.get("confirmed") else "❌ NOT CONFIRMED"
        print(f"\n   {h_id}: {h_data['description']}")
        print(f"      → {status}")
        
        # Print key metrics
        for key, value in h_data.items():
            if key not in ["description", "confirmed", "measurements"]:
                if isinstance(value, float):
                    print(f"      {key}: {value:.2f}")
                else:
                    print(f"      {key}: {value}")
    
    # Key findings
    print("\n💡 Key Findings:")
    for finding in summary.get("key_findings", []):
        print(f"   • {finding}")
    
    print("\n" + "─" * 70)


def main():
    parser = argparse.ArgumentParser(description="Run all network anomaly evaluation tests")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline tests")
    parser.add_argument("--skip-plots", action="store_true", help="Skip plot generation")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (show what would be executed)")
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - Complete Test Suite                    ║
║   Experiment ID: FN-20251206-network-01                               ║
║                                                                       ║
║   MVPs: 0.0 (Baseline) → 1.0 (Loss) → 1.1 (Delay) →                   ║
║         1.2 (Bandwidth) → 2.0/2.1 (HTTP)                              ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Ensure directories exist
    get_results_dir()
    get_img_dir()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - showing execution plan only\n")
    
    # Define test sequence
    tests = [
        ("run_baseline.py", "MVP-0.0: Baseline Tests", args.skip_baseline),
        ("run_loss_sweep.py", "MVP-1.0: Packet Loss Sweep", False),
        ("run_delay_sweep.py", "MVP-1.1: Delay Sweep", False),
        ("run_bandwidth_sweep.py", "MVP-1.2: Bandwidth Limit", False),
        ("run_http_tests.py", "MVP-2.0/2.1: HTTP Tests", False),
    ]
    
    execution_log = []
    start_time = datetime.now()
    
    for script, description, skip in tests:
        if skip:
            print(f"\n⏭️  Skipping: {description}")
            execution_log.append({
                "script": script,
                "mvp": description.split(":")[0],
                "skipped": True,
                "success": None
            })
            continue
        
        if args.dry_run:
            print(f"\n📝 Would run: {script} ({description})")
            execution_log.append({
                "script": script,
                "mvp": description.split(":")[0],
                "dry_run": True,
                "success": None
            })
        else:
            success = run_script(script, description)
            execution_log.append({
                "script": script,
                "mvp": description.split(":")[0],
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            if not success:
                print(f"\n⚠️ Test failed. Continue with remaining tests? (y/n)")
                # In automated mode, we continue
                # response = input().strip().lower()
                # if response != 'y':
                #     break
            
            time.sleep(2)  # Brief pause between tests
    
    # Generate plots
    if not args.skip_plots and not args.dry_run:
        print("\n📊 Generating plots...")
        run_script("plot_results.py", "Visualization")
    elif args.dry_run:
        print("\n📝 Would run: plot_results.py (Visualization)")
    
    # Load and summarize results
    if not args.dry_run:
        print("\n📈 Loading results...")
        all_results = load_latest_results()
        
        summary = generate_summary(all_results, execution_log)
        
        # Save summary
        results_dir = get_results_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = results_dir / f"summary_{timestamp}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Summary saved to: {summary_file}")
        
        print_final_summary(summary)
    
    # Final timing
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n⏱️  Total execution time: {duration}")
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║   ✅ All tests complete!                                              ║
║                                                                       ║
║   Next steps:                                                         ║
║   1. Review results in network/results/                               ║
║   2. Check plots in network/img/                                      ║
║   3. Update exp_network_anomaly_mininet_20251206.md with findings     ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == '__main__':
    main()
