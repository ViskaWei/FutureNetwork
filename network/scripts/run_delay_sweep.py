#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Delay Sweep (MVP-1.1)
==================================================

This script tests the impact of network delay on RTT and throughput.

Requirements:
- Linux (Mininet requires Linux kernel namespaces)
- Mininet installed: sudo apt install mininet
- iperf3 installed: sudo apt install iperf3

Usage:
    sudo python run_delay_sweep.py

Output:
    results/delay_sweep_YYYYMMDD_HHMMSS.json
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
DELAYS_MS = [0, 10, 25, 50, 100]  # milliseconds
PING_COUNT = 100
IPERF_DURATION = 30  # seconds


def get_results_dir():
    """Get the results directory path."""
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def parse_iperf3_json(output):
    """Parse iperf3 JSON output."""
    try:
        data = json.loads(output)
        return {
            "throughput_mbps": data["end"]["sum_received"]["bits_per_second"] / 1e6,
            "retransmits": data["end"]["sum_sent"].get("retransmits", 0),
        }
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": str(e), "raw": output[:500]}


def parse_ping(output):
    """Parse ping output for RTT statistics."""
    lines = output.split('\n')
    result = {}
    
    for line in lines:
        if 'rtt min/avg/max/mdev' in line or 'round-trip min/avg/max' in line:
            parts = line.split('=')[-1].strip().split('/')
            result = {
                "rtt_min_ms": float(parts[0]),
                "rtt_avg_ms": float(parts[1]),
                "rtt_max_ms": float(parts[2]),
                "rtt_mdev_ms": float(parts[3].split()[0]) if len(parts) > 3 else None
            }
        elif 'packets transmitted' in line:
            # Parse: X packets transmitted, Y received, Z% packet loss
            import re
            match = re.search(r'(\d+) packets transmitted, (\d+) received', line)
            if match:
                result["packets_sent"] = int(match.group(1))
                result["packets_received"] = int(match.group(2))
    
    return result if result else {"raw": output}


def apply_delay(host, interface, delay_ms):
    """Apply network delay using tc netem."""
    if delay_ms == 0:
        host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
    else:
        host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
        host.cmd(f'tc qdisc add dev {interface} root netem delay {delay_ms}ms')


def clear_netem(host, interface):
    """Clear tc netem rules."""
    host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')


def run_delay_sweep():
    """Run delay sweep tests."""
    
    results = {
        "experiment_id": "FN-20251206-network-01",
        "mvp": "MVP-1.1",
        "timestamp": datetime.now().isoformat(),
        "test_type": "delay_sweep",
        "parameters": {
            "delays_ms": DELAYS_MS,
            "ping_count": PING_COUNT,
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
        print("  sudo python run_delay_sweep.py")
        print("")
        
        for delay in DELAYS_MS:
            results["results"].append({
                "delay_ms": delay,
                "expected_rtt_ms": delay * 2,  # Round-trip
                "ping": {"status": "dry-run"},
                "tcp": {"status": "dry-run"}
            })
        return results
    
    # Initialize Mininet
    setLogLevel('info')
    print("=" * 60)
    print("MVP-1.1: Delay Sweep")
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
    
    try:
        for delay_ms in DELAYS_MS:
            print(f"\n{'─' * 60}")
            print(f"🔹 Testing Delay: {delay_ms}ms")
            print('─' * 60)
            
            test_result = {
                "delay_ms": delay_ms,
                "expected_rtt_increase_ms": delay_ms * 2,  # Round-trip delay
                "ping": {},
                "tcp": {}
            }
            
            # Apply delay
            print(f"   Applying {delay_ms}ms delay on {switch_intf}...")
            apply_delay(s1, switch_intf, delay_ms)
            time.sleep(1)
            
            # Ping Test
            print(f"   📶 Ping Test ({PING_COUNT} packets)...")
            ping_output = h2.cmd(f'ping -c {PING_COUNT} {h1_ip}')
            test_result["ping"] = parse_ping(ping_output)
            
            rtt_avg = test_result["ping"].get("rtt_avg_ms")
            if rtt_avg:
                print(f"      RTT avg: {rtt_avg:.3f} ms (expected ~{delay_ms * 2}+ ms)")
            
            # TCP Throughput Test
            print(f"   📶 TCP Throughput Test ({IPERF_DURATION}s)...")
            h1.cmd('pkill iperf3 2>/dev/null')
            h1.cmd('iperf3 -s -D')
            time.sleep(1)
            
            tcp_output = h2.cmd(f'iperf3 -c {h1_ip} -t {IPERF_DURATION} -J')
            test_result["tcp"] = parse_iperf3_json(tcp_output)
            
            tcp_mbps = test_result["tcp"].get("throughput_mbps", "N/A")
            print(f"      TCP: {tcp_mbps:.2f} Mbps" if isinstance(tcp_mbps, float) else f"      TCP: {tcp_mbps}")
            
            h1.cmd('pkill iperf3')
            results["results"].append(test_result)
            
            clear_netem(s1, switch_intf)
            time.sleep(1)
            
    finally:
        print("\n🧹 Cleaning up...")
        clear_netem(s1, switch_intf)
        net.stop()
    
    return results


def save_results(results):
    """Save results to JSON file."""
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"delay_sweep_{timestamp}.json"
    filepath = results_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filepath}")
    return filepath


def print_summary(results):
    """Print a summary of the results."""
    print("\n" + "=" * 60)
    print("📊 Delay Sweep Results Summary (MVP-1.1)")
    print("=" * 60)
    
    print(f"\n{'Delay ms':<12} {'Expected RTT':<15} {'Measured RTT':<15} {'TCP Mbps':<12} {'Match':<8}")
    print("-" * 65)
    
    baseline_rtt = None
    
    for r in results.get("results", []):
        delay = r["delay_ms"]
        expected_increase = delay * 2
        ping = r.get("ping", {})
        tcp = r.get("tcp", {})
        
        rtt_avg = ping.get("rtt_avg_ms")
        tcp_mbps = tcp.get("throughput_mbps")
        
        if delay == 0 and rtt_avg:
            baseline_rtt = rtt_avg
        
        expected_rtt = (baseline_rtt or 0) + expected_increase
        
        rtt_str = f"{rtt_avg:.3f}" if rtt_avg else "N/A"
        tcp_str = f"{tcp_mbps:.2f}" if tcp_mbps else "N/A"
        expected_str = f"~{expected_rtt:.1f}" if baseline_rtt else f"+{expected_increase}"
        
        # Check if measured RTT is within 20% of expected
        if rtt_avg and baseline_rtt:
            ratio = rtt_avg / expected_rtt if expected_rtt > 0 else 0
            match = "✅" if 0.8 <= ratio <= 1.2 else "⚠️"
        else:
            match = "⏳"
        
        print(f"{delay:<12} {expected_str:<15} {rtt_str:<15} {tcp_str:<12} {match:<8}")
    
    print("-" * 65)
    
    # Hypothesis check
    print("\n📋 Hypothesis Check:")
    if baseline_rtt:
        print(f"   H1.2 (RTT scales linearly with delay):")
        print(f"      Baseline RTT: {baseline_rtt:.3f} ms")
        print(f"      Expected: RTT = baseline + 2×delay (round-trip)")
        
        # Check linearity
        errors = []
        for r in results.get("results", []):
            delay = r["delay_ms"]
            rtt = r.get("ping", {}).get("rtt_avg_ms")
            if rtt and delay > 0:
                expected = baseline_rtt + delay * 2
                error = abs(rtt - expected) / expected * 100
                errors.append(error)
        
        if errors:
            avg_error = sum(errors) / len(errors)
            status = "✅ CONFIRMED" if avg_error < 20 else "❌ NOT CONFIRMED"
            print(f"      Average prediction error: {avg_error:.1f}% → {status}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - MVP-1.1 Delay Sweep            ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    results = run_delay_sweep()
    filepath = save_results(results)
    print_summary(results)
    
    print("\n💡 Next Steps:")
    print("   1. Review delay sweep results")
    print("   2. Proceed to MVP-1.2 (Bandwidth Limit)")
    print("   3. Run: sudo python run_bandwidth_sweep.py")


if __name__ == '__main__':
    main()
