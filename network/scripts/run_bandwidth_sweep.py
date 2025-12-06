#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Bandwidth Limit Sweep (MVP-1.2)
=============================================================

This script tests the impact of bandwidth limits on throughput.

Requirements:
- Linux (Mininet requires Linux kernel namespaces)
- Mininet installed: sudo apt install mininet
- iperf3 installed: sudo apt install iperf3

Usage:
    sudo python run_bandwidth_sweep.py

Output:
    results/bandwidth_sweep_YYYYMMDD_HHMMSS.json
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


# Test parameters
BANDWIDTHS_MBPS = [1, 5, 10]  # Mbps
IPERF_DURATION = 30  # seconds


def get_results_dir():
    """Get the results directory path."""
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def parse_iperf3_json(output, protocol="tcp"):
    """Parse iperf3 JSON output."""
    try:
        data = json.loads(output)
        result = {
            "throughput_mbps": data["end"]["sum_received"]["bits_per_second"] / 1e6,
        }
        if protocol == "tcp":
            result["retransmits"] = data["end"]["sum_sent"].get("retransmits", 0)
        if protocol == "udp":
            result["lost_packets"] = data["end"]["sum"].get("lost_packets", 0)
            result["lost_percent"] = data["end"]["sum"].get("lost_percent", 0)
        return result
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": str(e), "raw": output[:500]}


def apply_bandwidth_limit(host, interface, bw_mbps):
    """Apply bandwidth limit using tc tbf."""
    if bw_mbps is None:
        host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
    else:
        host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
        # tbf: rate + burst + latency
        # burst should be at least rate/HZ, typically 32kbit is safe
        # latency controls max queue delay
        host.cmd(f'tc qdisc add dev {interface} root tbf rate {bw_mbps}mbit burst 32kbit latency 400ms')


def clear_qdisc(host, interface):
    """Clear tc qdisc rules."""
    host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')


def run_bandwidth_sweep():
    """Run bandwidth limit sweep tests."""
    
    results = {
        "experiment_id": "FN-20251206-network-01",
        "mvp": "MVP-1.2",
        "timestamp": datetime.now().isoformat(),
        "test_type": "bandwidth_sweep",
        "parameters": {
            "bandwidths_mbps": BANDWIDTHS_MBPS,
            "iperf_duration_s": IPERF_DURATION
        },
        "results": []
    }
    
    if not MININET_AVAILABLE:
        print("=" * 60)
        print("DRY-RUN MODE (Mininet not available)")
        print("=" * 60)
        print("\nTo run actual tests, execute on a Linux system with Mininet:")
        print("  sudo apt install mininet iperf3")
        print("  sudo python run_bandwidth_sweep.py")
        print("")
        
        for bw in BANDWIDTHS_MBPS:
            results["results"].append({
                "bandwidth_limit_mbps": bw,
                "expected_throughput_mbps": bw,
                "tcp": {"status": "dry-run"},
                "udp": {"status": "dry-run"}
            })
        return results
    
    # Initialize Mininet
    setLogLevel('info')
    print("=" * 60)
    print("MVP-1.2: Bandwidth Limit Sweep")
    print("=" * 60)
    
    print("\n📡 Creating network topology: Host1 -- Switch -- Host2")
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, controller=Controller)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    s1 = net.get('s1')
    h1_ip = h1.IP()
    
    switch_intf = 's1-eth1'
    
    print(f"   h1 IP: {h1_ip}")
    print(f"   h2 IP: {h2.IP()}")
    print(f"   Switch interface: {switch_intf}")
    
    # First, get baseline (unlimited)
    print(f"\n{'─' * 60}")
    print("🔹 Testing Baseline (No Bandwidth Limit)")
    print('─' * 60)
    
    baseline_result = {
        "bandwidth_limit_mbps": None,
        "expected_throughput_mbps": "unlimited",
        "tcp": {},
        "udp": {}
    }
    
    h1.cmd('pkill iperf3 2>/dev/null')
    h1.cmd('iperf3 -s -D')
    time.sleep(1)
    
    print(f"   📶 TCP Throughput Test (Baseline, {IPERF_DURATION}s)...")
    tcp_output = h2.cmd(f'iperf3 -c {h1_ip} -t {IPERF_DURATION} -J')
    baseline_result["tcp"] = parse_iperf3_json(tcp_output, "tcp")
    
    print(f"   📶 UDP Throughput Test (Baseline, {IPERF_DURATION}s)...")
    udp_output = h2.cmd(f'iperf3 -c {h1_ip} -u -b 100M -t {IPERF_DURATION} -J')
    baseline_result["udp"] = parse_iperf3_json(udp_output, "udp")
    
    tcp_mbps = baseline_result["tcp"].get("throughput_mbps", "N/A")
    udp_mbps = baseline_result["udp"].get("throughput_mbps", "N/A")
    print(f"      TCP: {tcp_mbps:.2f} Mbps" if isinstance(tcp_mbps, float) else f"      TCP: {tcp_mbps}")
    print(f"      UDP: {udp_mbps:.2f} Mbps" if isinstance(udp_mbps, float) else f"      UDP: {udp_mbps}")
    
    h1.cmd('pkill iperf3')
    results["results"].append(baseline_result)
    
    try:
        for bw_mbps in BANDWIDTHS_MBPS:
            print(f"\n{'─' * 60}")
            print(f"🔹 Testing Bandwidth Limit: {bw_mbps} Mbps")
            print('─' * 60)
            
            test_result = {
                "bandwidth_limit_mbps": bw_mbps,
                "expected_throughput_mbps": bw_mbps,
                "tcp": {},
                "udp": {}
            }
            
            # Apply bandwidth limit
            print(f"   Applying {bw_mbps} Mbps limit on {switch_intf}...")
            apply_bandwidth_limit(s1, switch_intf, bw_mbps)
            time.sleep(1)
            
            # TCP Test
            print(f"   📶 TCP Throughput Test ({IPERF_DURATION}s)...")
            h1.cmd('pkill iperf3 2>/dev/null')
            h1.cmd('iperf3 -s -D')
            time.sleep(1)
            
            tcp_output = h2.cmd(f'iperf3 -c {h1_ip} -t {IPERF_DURATION} -J')
            test_result["tcp"] = parse_iperf3_json(tcp_output, "tcp")
            
            tcp_mbps = test_result["tcp"].get("throughput_mbps", "N/A")
            efficiency = (tcp_mbps / bw_mbps * 100) if isinstance(tcp_mbps, float) else None
            print(f"      TCP: {tcp_mbps:.2f} Mbps ({efficiency:.1f}% of limit)" if efficiency else f"      TCP: {tcp_mbps}")
            
            # UDP Test
            print(f"   📶 UDP Throughput Test ({IPERF_DURATION}s, target: {bw_mbps * 2}Mbps)...")
            udp_output = h2.cmd(f'iperf3 -c {h1_ip} -u -b {bw_mbps * 2}M -t {IPERF_DURATION} -J')
            test_result["udp"] = parse_iperf3_json(udp_output, "udp")
            
            udp_mbps = test_result["udp"].get("throughput_mbps", "N/A")
            udp_eff = (udp_mbps / bw_mbps * 100) if isinstance(udp_mbps, float) else None
            print(f"      UDP: {udp_mbps:.2f} Mbps ({udp_eff:.1f}% of limit)" if udp_eff else f"      UDP: {udp_mbps}")
            
            h1.cmd('pkill iperf3')
            results["results"].append(test_result)
            
            clear_qdisc(s1, switch_intf)
            time.sleep(1)
            
    finally:
        print("\n🧹 Cleaning up...")
        clear_qdisc(s1, switch_intf)
        net.stop()
    
    return results


def save_results(results):
    """Save results to JSON file."""
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bandwidth_sweep_{timestamp}.json"
    filepath = results_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filepath}")
    return filepath


def print_summary(results):
    """Print a summary of the results."""
    print("\n" + "=" * 60)
    print("📊 Bandwidth Limit Results Summary (MVP-1.2)")
    print("=" * 60)
    
    print(f"\n{'BW Limit':<12} {'TCP Mbps':<12} {'TCP Eff %':<12} {'UDP Mbps':<12} {'UDP Eff %':<12}")
    print("-" * 60)
    
    for r in results.get("results", []):
        bw = r["bandwidth_limit_mbps"]
        tcp = r.get("tcp", {})
        udp = r.get("udp", {})
        
        tcp_mbps = tcp.get("throughput_mbps")
        udp_mbps = udp.get("throughput_mbps")
        
        bw_str = f"{bw} Mbps" if bw else "Unlimited"
        tcp_str = f"{tcp_mbps:.2f}" if tcp_mbps else "N/A"
        udp_str = f"{udp_mbps:.2f}" if udp_mbps else "N/A"
        
        if bw and tcp_mbps:
            tcp_eff = f"{tcp_mbps / bw * 100:.1f}%"
        else:
            tcp_eff = "-"
        
        if bw and udp_mbps:
            udp_eff = f"{udp_mbps / bw * 100:.1f}%"
        else:
            udp_eff = "-"
        
        print(f"{bw_str:<12} {tcp_str:<12} {tcp_eff:<12} {udp_str:<12} {udp_eff:<12}")
    
    print("-" * 60)
    
    # Hypothesis check
    print("\n📋 Hypothesis Check:")
    print("   Expected: Throughput ≈ Bandwidth Limit")
    
    matched = 0
    total = 0
    for r in results.get("results", []):
        bw = r["bandwidth_limit_mbps"]
        if bw:  # Skip baseline
            tcp_mbps = r.get("tcp", {}).get("throughput_mbps")
            if tcp_mbps:
                ratio = tcp_mbps / bw
                if 0.7 <= ratio <= 1.1:  # Within 70-110% of limit
                    matched += 1
                total += 1
    
    if total > 0:
        pct = matched / total * 100
        status = "✅ CONFIRMED" if pct >= 80 else "❌ NOT CONFIRMED"
        print(f"   Results: {matched}/{total} tests within 70-110% of limit → {status}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - MVP-1.2 Bandwidth Sweep        ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    results = run_bandwidth_sweep()
    filepath = save_results(results)
    print_summary(results)
    
    print("\n💡 Next Steps:")
    print("   1. Review bandwidth sweep results")
    print("   2. Proceed to MVP-2.0 (HTTP Tests)")
    print("   3. Run: sudo python run_http_tests.py")


if __name__ == '__main__':
    main()
