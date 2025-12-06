#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Packet Loss Sweep (MVP-1.0)
=========================================================

This script tests the impact of packet loss on TCP and UDP throughput.

Requirements:
- Linux (Mininet requires Linux kernel namespaces)
- Mininet installed: sudo apt install mininet
- iperf3 installed: sudo apt install iperf3

Usage:
    sudo python run_loss_sweep.py

Output:
    results/loss_sweep_YYYYMMDD_HHMMSS.json
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
LOSS_RATES = [0, 1, 5, 10, 20]  # percent
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


def apply_loss(host, interface, loss_percent):
    """Apply packet loss using tc netem."""
    if loss_percent == 0:
        # Clear any existing qdisc
        host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
    else:
        # First clear, then add netem
        host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')
        host.cmd(f'tc qdisc add dev {interface} root netem loss {loss_percent}%')


def clear_netem(host, interface):
    """Clear tc netem rules."""
    host.cmd(f'tc qdisc del dev {interface} root 2>/dev/null')


def run_loss_sweep():
    """Run packet loss sweep tests."""
    
    results = {
        "experiment_id": "FN-20251206-network-01",
        "mvp": "MVP-1.0",
        "timestamp": datetime.now().isoformat(),
        "test_type": "packet_loss_sweep",
        "parameters": {
            "loss_rates_percent": LOSS_RATES,
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
        print("  sudo python run_loss_sweep.py")
        print("")
        
        # Generate sample data structure
        for loss in LOSS_RATES:
            results["results"].append({
                "loss_rate_percent": loss,
                "tcp": {"status": "dry-run"},
                "udp": {"status": "dry-run"}
            })
        return results
    
    # Initialize Mininet
    setLogLevel('info')
    print("=" * 60)
    print("MVP-1.0: Packet Loss Sweep")
    print("=" * 60)
    
    print("\n📡 Creating network topology: Host1 -- Switch -- Host2")
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, controller=Controller)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    s1 = net.get('s1')
    h1_ip = h1.IP()
    
    # Get interface name (typically s1-eth1)
    switch_intf = 's1-eth1'
    
    print(f"   h1 IP: {h1_ip}")
    print(f"   h2 IP: {h2.IP()}")
    print(f"   Switch interface: {switch_intf}")
    
    try:
        for loss_rate in LOSS_RATES:
            print(f"\n{'─' * 60}")
            print(f"🔹 Testing Loss Rate: {loss_rate}%")
            print('─' * 60)
            
            test_result = {
                "loss_rate_percent": loss_rate,
                "tcp": {},
                "udp": {}
            }
            
            # Apply packet loss
            print(f"   Applying {loss_rate}% packet loss on {switch_intf}...")
            apply_loss(s1, switch_intf, loss_rate)
            time.sleep(1)  # Let settings stabilize
            
            # TCP Test
            print(f"   📶 TCP Throughput Test ({IPERF_DURATION}s)...")
            h1.cmd('pkill iperf3 2>/dev/null')
            h1.cmd('iperf3 -s -D')
            time.sleep(1)
            
            tcp_output = h2.cmd(f'iperf3 -c {h1_ip} -t {IPERF_DURATION} -J')
            test_result["tcp"] = parse_iperf3_json(tcp_output, "tcp")
            
            tcp_mbps = test_result["tcp"].get("throughput_mbps", "N/A")
            tcp_retrans = test_result["tcp"].get("retransmits", "N/A")
            print(f"      TCP: {tcp_mbps:.2f} Mbps, Retransmits: {tcp_retrans}" if isinstance(tcp_mbps, float) else f"      TCP: {tcp_mbps}")
            
            # UDP Test
            print(f"   📶 UDP Throughput Test ({IPERF_DURATION}s, 100Mbps target)...")
            udp_output = h2.cmd(f'iperf3 -c {h1_ip} -u -b 100M -t {IPERF_DURATION} -J')
            test_result["udp"] = parse_iperf3_json(udp_output, "udp")
            
            udp_mbps = test_result["udp"].get("throughput_mbps", "N/A")
            udp_loss = test_result["udp"].get("lost_percent", "N/A")
            print(f"      UDP: {udp_mbps:.2f} Mbps, Measured Loss: {udp_loss:.2f}%" if isinstance(udp_mbps, float) else f"      UDP: {udp_mbps}")
            
            h1.cmd('pkill iperf3')
            results["results"].append(test_result)
            
            # Clear netem before next iteration
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
    filename = f"loss_sweep_{timestamp}.json"
    filepath = results_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filepath}")
    return filepath


def print_summary(results):
    """Print a summary of the results."""
    print("\n" + "=" * 60)
    print("📊 Loss Sweep Results Summary (MVP-1.0)")
    print("=" * 60)
    
    print(f"\n{'Loss %':<10} {'TCP Mbps':<15} {'TCP Retrans':<15} {'UDP Mbps':<15} {'UDP Loss %':<10}")
    print("-" * 65)
    
    baseline_tcp = None
    
    for r in results.get("results", []):
        loss = r["loss_rate_percent"]
        tcp = r.get("tcp", {})
        udp = r.get("udp", {})
        
        tcp_mbps = tcp.get("throughput_mbps")
        tcp_retrans = tcp.get("retransmits", "-")
        udp_mbps = udp.get("throughput_mbps")
        udp_loss = udp.get("lost_percent", "-")
        
        if loss == 0 and tcp_mbps:
            baseline_tcp = tcp_mbps
        
        tcp_str = f"{tcp_mbps:.2f}" if tcp_mbps else "N/A"
        udp_str = f"{udp_mbps:.2f}" if udp_mbps else "N/A"
        udp_loss_str = f"{udp_loss:.2f}" if isinstance(udp_loss, (int, float)) else udp_loss
        
        print(f"{loss:<10} {tcp_str:<15} {tcp_retrans:<15} {udp_str:<15} {udp_loss_str:<10}")
    
    print("-" * 65)
    
    # Hypothesis check
    print("\n📋 Hypothesis Check:")
    for r in results.get("results", []):
        if r["loss_rate_percent"] == 10:
            tcp_mbps = r.get("tcp", {}).get("throughput_mbps")
            if tcp_mbps and baseline_tcp:
                drop_pct = (1 - tcp_mbps / baseline_tcp) * 100
                status = "✅ CONFIRMED" if drop_pct > 50 else "❌ NOT CONFIRMED"
                print(f"   H1.1 (TCP @10% loss drops >50%): {drop_pct:.1f}% drop → {status}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - MVP-1.0 Packet Loss Sweep      ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    results = run_loss_sweep()
    filepath = save_results(results)
    print_summary(results)
    
    print("\n💡 Next Steps:")
    print("   1. Review loss sweep results")
    print("   2. Proceed to MVP-1.1 (Delay Sweep)")
    print("   3. Run: sudo python run_delay_sweep.py")


if __name__ == '__main__':
    main()
