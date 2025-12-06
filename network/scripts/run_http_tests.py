#!/usr/bin/env python3
"""
Network Anomaly Evaluation - HTTP Tests (MVP-2.0 & MVP-2.1)
============================================================

This script tests HTTP download performance under various network anomalies.

MVP-2.0: HTTP tests under individual anomalies
MVP-2.1: HTTP tests under combined anomalies

Requirements:
- Linux (Mininet requires Linux kernel namespaces)
- Mininet installed: sudo apt install mininet
- curl installed

Usage:
    sudo python run_http_tests.py

Output:
    results/http_test_YYYYMMDD_HHMMSS.json
"""

import json
import time
from datetime import datetime
from pathlib import Path

# Try to import mininet
try:
    from mininet.net import Mininet
    from mininet.node import Controller
    from mininet.topo import SingleSwitchTopo
    from mininet.link import TCLink
    from mininet.log import setLogLevel
    MININET_AVAILABLE = True
except ImportError:
    MININET_AVAILABLE = False
    print("⚠️  Mininet not available. Running in dry-run mode.")


# Test conditions
TEST_CONDITIONS = [
    {"name": "baseline", "loss": 0, "delay": 0, "description": "No anomaly"},
    {"name": "loss_5pct", "loss": 5, "delay": 0, "description": "5% packet loss"},
    {"name": "delay_50ms", "loss": 0, "delay": 50, "description": "50ms delay"},
    {"name": "combined", "loss": 5, "delay": 50, "description": "5% loss + 50ms delay"},
]

# Test file sizes
TEST_FILE_SIZES_MB = [1, 5]  # 1MB and 5MB files
DOWNLOAD_REPEATS = 3  # Repeat each download for stability


def get_results_dir():
    """Get the results directory path."""
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def apply_anomaly(host, interface, loss=0, delay=0):
    """Apply network anomaly using tc netem."""
    host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
    
    if loss == 0 and delay == 0:
        return
    
    netem_args = []
    if loss > 0:
        netem_args.append(f"loss {loss}%")
    if delay > 0:
        netem_args.append(f"delay {delay}ms")
    
    if netem_args:
        cmd = f"tc qdisc add dev {interface} root netem {' '.join(netem_args)}"
        host.cmd(cmd)


def clear_netem(host, interface):
    """Clear tc netem rules."""
    host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')


def download_file(client_host, server_ip, filename, repeats=3):
    """Download a file multiple times and return statistics."""
    times = []
    
    for i in range(repeats):
        output = client_host.cmd(
            f'curl -o /dev/null -s -w "%{{time_total}}\\n%{{http_code}}\\n%{{size_download}}" '
            f'http://{server_ip}:8000/{filename}'
        )
        lines = output.strip().split('\n')
        
        try:
            time_total = float(lines[0])
            http_code = int(lines[1])
            size = int(lines[2])
            
            if http_code == 200:
                times.append(time_total)
        except (ValueError, IndexError):
            pass
        
        time.sleep(0.5)
    
    if times:
        return {
            "download_count": len(times),
            "download_times_s": times,
            "min_s": min(times),
            "max_s": max(times),
            "avg_s": sum(times) / len(times),
        }
    else:
        return {"error": "All downloads failed", "raw": output}


def run_http_tests():
    """Run HTTP download tests under various conditions."""
    
    results = {
        "experiment_id": "FN-20251206-network-01",
        "mvp": ["MVP-2.0", "MVP-2.1"],
        "timestamp": datetime.now().isoformat(),
        "test_type": "http_download",
        "parameters": {
            "test_conditions": TEST_CONDITIONS,
            "file_sizes_mb": TEST_FILE_SIZES_MB,
            "download_repeats": DOWNLOAD_REPEATS
        },
        "results": []
    }
    
    if not MININET_AVAILABLE:
        print("=" * 60)
        print("DRY-RUN MODE (Mininet not available)")
        print("=" * 60)
        print("\nTo run actual tests, execute on a Linux system with Mininet:")
        print("  sudo apt install mininet curl")
        print("  sudo python run_http_tests.py")
        print("")
        
        for condition in TEST_CONDITIONS:
            for size in TEST_FILE_SIZES_MB:
                results["results"].append({
                    "condition": condition["name"],
                    "file_size_mb": size,
                    "status": "dry-run"
                })
        return results
    
    # Initialize Mininet
    setLogLevel('info')
    print("=" * 60)
    print("MVP-2.0 & MVP-2.1: HTTP Download Tests")
    print("=" * 60)
    
    print("\n📡 Creating network topology: Host1 (Server) -- Switch -- Host2 (Client)")
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, controller=Controller)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    s1 = net.get('s1')
    h1_ip = h1.IP()
    
    switch_intf = 's1-eth1'
    
    print(f"   Server (h1) IP: {h1_ip}")
    print(f"   Client (h2) IP: {h2.IP()}")
    
    # Create test files and start HTTP server
    print("\n📁 Creating test files on server...")
    for size in TEST_FILE_SIZES_MB:
        h1.cmd(f'dd if=/dev/zero of=/tmp/testfile_{size}mb bs=1M count={size} 2>/dev/null')
        print(f"   Created: testfile_{size}mb")
    
    print("🌐 Starting HTTP server on h1:8000...")
    h1.cmd('cd /tmp && python3 -m http.server 8000 &')
    time.sleep(2)
    
    # Verify server is running
    check = h2.cmd(f'curl -s -o /dev/null -w "%{{http_code}}" http://{h1_ip}:8000/')
    if "200" in check:
        print("   ✅ Server is running")
    else:
        print(f"   ⚠️ Server check returned: {check}")
    
    try:
        for condition in TEST_CONDITIONS:
            print(f"\n{'─' * 60}")
            print(f"🔹 Condition: {condition['description']}")
            print(f"   Loss: {condition['loss']}%, Delay: {condition['delay']}ms")
            print('─' * 60)
            
            # Apply anomaly
            apply_anomaly(s1, switch_intf, condition['loss'], condition['delay'])
            time.sleep(1)
            
            for size in TEST_FILE_SIZES_MB:
                print(f"\n   📥 Downloading {size}MB file ({DOWNLOAD_REPEATS} times)...")
                
                test_result = {
                    "condition": condition["name"],
                    "condition_description": condition["description"],
                    "loss_percent": condition["loss"],
                    "delay_ms": condition["delay"],
                    "file_size_mb": size,
                }
                
                download_stats = download_file(
                    h2, h1_ip, f"testfile_{size}mb", DOWNLOAD_REPEATS
                )
                test_result.update(download_stats)
                
                if "avg_s" in download_stats:
                    print(f"      Avg time: {download_stats['avg_s']:.3f}s "
                          f"(min: {download_stats['min_s']:.3f}s, max: {download_stats['max_s']:.3f}s)")
                else:
                    print(f"      ⚠️ Download failed: {download_stats.get('error', 'unknown')}")
                
                results["results"].append(test_result)
            
            clear_netem(s1, switch_intf)
            time.sleep(1)
            
    finally:
        print("\n🧹 Cleaning up...")
        h1.cmd('pkill -f "http.server"')
        for size in TEST_FILE_SIZES_MB:
            h1.cmd(f'rm -f /tmp/testfile_{size}mb')
        clear_netem(s1, switch_intf)
        net.stop()
    
    return results


def save_results(results):
    """Save results to JSON file."""
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"http_test_{timestamp}.json"
    filepath = results_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filepath}")
    return filepath


def print_summary(results):
    """Print a summary of the results."""
    print("\n" + "=" * 60)
    print("📊 HTTP Download Results Summary (MVP-2.0 & MVP-2.1)")
    print("=" * 60)
    
    # Group by file size
    for size in TEST_FILE_SIZES_MB:
        print(f"\n📁 {size}MB File Downloads:")
        print(f"{'Condition':<20} {'Avg Time':<12} {'Min':<10} {'Max':<10} {'vs Baseline'}")
        print("-" * 65)
        
        baseline_time = None
        
        for r in results.get("results", []):
            if r.get("file_size_mb") == size:
                cond = r.get("condition", "unknown")
                avg = r.get("avg_s")
                min_t = r.get("min_s")
                max_t = r.get("max_s")
                
                if cond == "baseline" and avg:
                    baseline_time = avg
                
                avg_str = f"{avg:.3f}s" if avg else "N/A"
                min_str = f"{min_t:.3f}s" if min_t else "-"
                max_str = f"{max_t:.3f}s" if max_t else "-"
                
                if baseline_time and avg:
                    ratio = avg / baseline_time
                    ratio_str = f"{ratio:.2f}×"
                else:
                    ratio_str = "-"
                
                print(f"{cond:<20} {avg_str:<12} {min_str:<10} {max_str:<10} {ratio_str}")
    
    print("-" * 65)
    
    # Hypothesis check
    print("\n📋 Hypothesis Check:")
    
    # Find baseline and combined results
    baseline_1mb = None
    combined_1mb = None
    
    for r in results.get("results", []):
        if r.get("file_size_mb") == 1:
            if r.get("condition") == "baseline":
                baseline_1mb = r.get("avg_s")
            elif r.get("condition") == "combined":
                combined_1mb = r.get("avg_s")
    
    print(f"   H2.2 (HTTP shows compounded effects under combined anomalies):")
    if baseline_1mb and combined_1mb:
        ratio = combined_1mb / baseline_1mb
        status = "✅ CONFIRMED" if ratio >= 2.0 else "❌ NOT CONFIRMED"
        print(f"      Baseline: {baseline_1mb:.3f}s, Combined: {combined_1mb:.3f}s")
        print(f"      Ratio: {ratio:.2f}× (expected >2×) → {status}")
    else:
        print("      ⏳ Insufficient data")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - MVP-2.0/2.1 HTTP Tests         ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    results = run_http_tests()
    filepath = save_results(results)
    print_summary(results)
    
    print("\n💡 Next Steps:")
    print("   1. Review HTTP test results")
    print("   2. All MVP tests complete!")
    print("   3. Run: python plot_results.py (to generate visualizations)")
    print("   4. Update exp.md with results and conclusions")


if __name__ == '__main__':
    main()
