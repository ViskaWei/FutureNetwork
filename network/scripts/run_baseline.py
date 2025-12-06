#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Baseline Test Script (MVP-0.0)
============================================================

This script runs baseline performance tests using Mininet.

Requirements:
- Linux (Mininet requires Linux kernel namespaces)
- Mininet installed: sudo apt install mininet
- iperf3 installed: sudo apt install iperf3

Usage:
    sudo python run_baseline.py

Output:
    results/baseline_YYYYMMDD_HHMMSS.json
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Try to import mininet (only works on Linux with mininet installed)
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


def get_results_dir():
    """Get the results directory path."""
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def run_command(host, cmd, timeout=60):
    """Run a command on a Mininet host and return output."""
    if MININET_AVAILABLE:
        output = host.cmd(cmd)
        return output.strip()
    else:
        print(f"[DRY-RUN] Would execute on {host}: {cmd}")
        return "[DRY-RUN]"


def parse_iperf3_json(output):
    """Parse iperf3 JSON output."""
    try:
        data = json.loads(output)
        return {
            "throughput_mbps": data["end"]["sum_received"]["bits_per_second"] / 1e6,
            "retransmits": data["end"]["sum_sent"].get("retransmits", 0),
        }
    except (json.JSONDecodeError, KeyError):
        return {"throughput_mbps": None, "retransmits": None, "raw": output}


def parse_ping(output):
    """Parse ping output for RTT statistics."""
    lines = output.split('\n')
    for line in lines:
        if 'rtt min/avg/max/mdev' in line or 'round-trip min/avg/max' in line:
            # Format: rtt min/avg/max/mdev = 0.123/0.456/0.789/0.012 ms
            parts = line.split('=')[-1].strip().split('/')
            return {
                "rtt_min_ms": float(parts[0]),
                "rtt_avg_ms": float(parts[1]),
                "rtt_max_ms": float(parts[2]),
                "rtt_mdev_ms": float(parts[3].split()[0]) if len(parts) > 3 else None
            }
    return {"raw": output}


def run_baseline_tests():
    """Run baseline performance tests."""
    
    results = {
        "experiment_id": "FN-20251206-network-01",
        "mvp": "MVP-0.0",
        "timestamp": datetime.now().isoformat(),
        "condition": "baseline (no anomaly)",
        "tests": {}
    }
    
    if not MININET_AVAILABLE:
        print("=" * 60)
        print("DRY-RUN MODE (Mininet not available)")
        print("=" * 60)
        print("\nTo run actual tests, execute on a Linux system with Mininet:")
        print("  sudo apt install mininet iperf3")
        print("  sudo python run_baseline.py")
        print("")
        
        # Generate sample data structure
        results["tests"] = {
            "tcp_throughput": {"status": "dry-run"},
            "udp_throughput": {"status": "dry-run"},
            "ping": {"status": "dry-run"},
            "http": {"status": "dry-run"}
        }
        return results
    
    # Initialize Mininet
    setLogLevel('info')
    print("=" * 60)
    print("MVP-0.0: Baseline Performance Tests")
    print("=" * 60)
    
    print("\n📡 Creating network topology: Host1 -- Switch -- Host2")
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, controller=Controller)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    h1_ip = h1.IP()
    
    print(f"   h1 IP: {h1_ip}")
    print(f"   h2 IP: {h2.IP()}")
    
    try:
        # ─────────────────────────────────────────────────────────
        # Test 1: TCP Throughput (iperf3)
        # ─────────────────────────────────────────────────────────
        print("\n🔹 Test 1: TCP Throughput")
        print("   Starting iperf3 server on h1...")
        h1.cmd('iperf3 -s -D')  # Daemon mode
        time.sleep(1)
        
        print("   Running iperf3 client on h2 (30s)...")
        tcp_output = h2.cmd(f'iperf3 -c {h1_ip} -t 30 -J')
        results["tests"]["tcp_throughput"] = parse_iperf3_json(tcp_output)
        print(f"   ✅ TCP Throughput: {results['tests']['tcp_throughput'].get('throughput_mbps', 'N/A')} Mbps")
        
        # ─────────────────────────────────────────────────────────
        # Test 2: UDP Throughput (iperf3)
        # ─────────────────────────────────────────────────────────
        print("\n🔹 Test 2: UDP Throughput")
        print("   Running iperf3 UDP client on h2 (30s, 100Mbps target)...")
        udp_output = h2.cmd(f'iperf3 -c {h1_ip} -u -b 100M -t 30 -J')
        results["tests"]["udp_throughput"] = parse_iperf3_json(udp_output)
        print(f"   ✅ UDP Throughput: {results['tests']['udp_throughput'].get('throughput_mbps', 'N/A')} Mbps")
        
        # Stop iperf3 server
        h1.cmd('pkill iperf3')
        
        # ─────────────────────────────────────────────────────────
        # Test 3: Ping (RTT)
        # ─────────────────────────────────────────────────────────
        print("\n🔹 Test 3: Ping (RTT)")
        print("   Running ping from h2 to h1 (100 packets)...")
        ping_output = h2.cmd(f'ping -c 100 {h1_ip}')
        results["tests"]["ping"] = parse_ping(ping_output)
        print(f"   ✅ RTT avg: {results['tests']['ping'].get('rtt_avg_ms', 'N/A')} ms")
        
        # ─────────────────────────────────────────────────────────
        # Test 4: HTTP Download
        # ─────────────────────────────────────────────────────────
        print("\n🔹 Test 4: HTTP Download")
        
        # Create test file
        h1.cmd('dd if=/dev/zero of=/tmp/testfile_1mb bs=1M count=1 2>/dev/null')
        h1.cmd('cd /tmp && python3 -m http.server 8000 &')
        time.sleep(2)
        
        print("   Downloading 1MB test file...")
        curl_output = h2.cmd(f'curl -o /dev/null -w "%{{time_total}}" http://{h1_ip}:8000/testfile_1mb 2>/dev/null')
        try:
            download_time = float(curl_output.strip())
            results["tests"]["http"] = {
                "download_time_s": download_time,
                "file_size_mb": 1
            }
            print(f"   ✅ HTTP Download Time: {download_time:.3f} s")
        except ValueError:
            results["tests"]["http"] = {"raw": curl_output}
            print(f"   ⚠️  Could not parse curl output: {curl_output}")
        
        # Cleanup
        h1.cmd('pkill -f "http.server"')
        h1.cmd('rm -f /tmp/testfile_1mb')
        
    finally:
        print("\n🧹 Stopping Mininet...")
        net.stop()
    
    return results


def save_results(results):
    """Save results to JSON file."""
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"baseline_{timestamp}.json"
    filepath = results_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filepath}")
    return filepath


def print_summary(results):
    """Print a summary of the results."""
    print("\n" + "=" * 60)
    print("📊 Baseline Results Summary (MVP-0.0)")
    print("=" * 60)
    
    tests = results.get("tests", {})
    
    print(f"\n{'Metric':<25} {'Value':<20} {'Status'}")
    print("-" * 60)
    
    # TCP
    tcp = tests.get("tcp_throughput", {})
    if "throughput_mbps" in tcp and tcp["throughput_mbps"]:
        print(f"{'TCP Throughput':<25} {tcp['throughput_mbps']:.2f} Mbps{'':<8} ✅")
    else:
        print(f"{'TCP Throughput':<25} {'N/A':<20} ⏳")
    
    # UDP
    udp = tests.get("udp_throughput", {})
    if "throughput_mbps" in udp and udp["throughput_mbps"]:
        print(f"{'UDP Throughput':<25} {udp['throughput_mbps']:.2f} Mbps{'':<8} ✅")
    else:
        print(f"{'UDP Throughput':<25} {'N/A':<20} ⏳")
    
    # RTT
    ping = tests.get("ping", {})
    if "rtt_avg_ms" in ping:
        print(f"{'RTT (avg)':<25} {ping['rtt_avg_ms']:.3f} ms{'':<11} ✅")
    else:
        print(f"{'RTT (avg)':<25} {'N/A':<20} ⏳")
    
    # HTTP
    http = tests.get("http", {})
    if "download_time_s" in http:
        print(f"{'HTTP Download (1MB)':<25} {http['download_time_s']:.3f} s{'':<12} ✅")
    else:
        print(f"{'HTTP Download (1MB)':<25} {'N/A':<20} ⏳")
    
    print("-" * 60)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - MVP-0.0 Baseline Tests         ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    results = run_baseline_tests()
    filepath = save_results(results)
    print_summary(results)
    
    print("\n💡 Next Steps:")
    print("   1. Review baseline results")
    print("   2. If stable, proceed to MVP-1.0 (Packet Loss)")
    print("   3. Run: sudo python run_loss_sweep.py")


if __name__ == '__main__':
    main()
