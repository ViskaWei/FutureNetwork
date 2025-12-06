#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Network Anomaly Evaluation - All Tests (Python 2 Compatible)
============================================================

Runs all MVP tests: Baseline, Loss Sweep, Delay Sweep, Bandwidth, HTTP

Requirements:
- Linux with Mininet
- iperf3 installed

Usage:
    sudo python2 run_all_py2.py
"""

from __future__ import print_function

import json
import os
import time
from datetime import datetime

from mininet.net import Mininet
from mininet.node import Controller, OVSBridge
from mininet.topo import SingleSwitchTopo
from mininet.link import TCLink
from mininet.log import setLogLevel


# ============================================================
# Configuration
# ============================================================

LOSS_RATES = [0, 1, 5, 10, 20]  # percent
DELAYS = [0, 10, 25, 50, 100]   # ms
BANDWIDTHS = [1, 5, 10]         # Mbps
IPERF_DURATION = 10             # seconds (reduced for faster testing)
PING_COUNT = 50                 # packets


def get_results_dir():
    """Get the results directory path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(os.path.dirname(script_dir), 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
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
    except (ValueError, KeyError) as e:
        return {"error": str(e), "raw": output[:500] if output else "empty"}


def parse_ping(output):
    """Parse ping output for RTT statistics."""
    lines = output.split('\n')
    for line in lines:
        if 'rtt min/avg/max/mdev' in line or 'round-trip min/avg/max' in line:
            parts = line.split('=')[-1].strip().split('/')
            return {
                "rtt_min_ms": float(parts[0]),
                "rtt_avg_ms": float(parts[1]),
                "rtt_max_ms": float(parts[2]),
                "rtt_mdev_ms": float(parts[3].split()[0]) if len(parts) > 3 else None
            }
    # Try to extract packet loss
    for line in lines:
        if 'packet loss' in line:
            return {"raw": line, "error": "Could not parse RTT"}
    return {"raw": output, "error": "Could not parse"}


def apply_netem(net, interface, loss=0, delay=0, bw=0):
    """Apply tc netem rules."""
    s1 = net.get('s1')
    # Clear existing rules
    s1.cmd('tc qdisc del dev {} root 2>/dev/null'.format(interface))
    
    if loss == 0 and delay == 0 and bw == 0:
        return
    
    if bw > 0:
        # Use HTB for bandwidth limiting with netem for loss/delay
        s1.cmd('tc qdisc add dev {} root handle 1: htb default 1'.format(interface))
        s1.cmd('tc class add dev {} parent 1: classid 1:1 htb rate {}mbit'.format(interface, bw))
        if loss > 0 or delay > 0:
            netem_opts = ''
            if delay > 0:
                netem_opts += ' delay {}ms'.format(delay)
            if loss > 0:
                netem_opts += ' loss {}%'.format(loss)
            s1.cmd('tc qdisc add dev {} parent 1:1 handle 10: netem{}'.format(interface, netem_opts))
    else:
        # Just netem for loss/delay
        netem_opts = ''
        if delay > 0:
            netem_opts += ' delay {}ms'.format(delay)
        if loss > 0:
            netem_opts += ' loss {}%'.format(loss)
        if netem_opts:
            s1.cmd('tc qdisc add dev {} root netem{}'.format(interface, netem_opts))


def clear_netem(net, interface):
    """Clear tc netem rules."""
    s1 = net.get('s1')
    s1.cmd('tc qdisc del dev {} root 2>/dev/null'.format(interface))


# ============================================================
# Test Functions
# ============================================================

def run_baseline(net, h1, h2, h1_ip):
    """MVP-0.0: Baseline tests."""
    print("\n" + "=" * 60)
    print("MVP-0.0: Baseline Performance Tests")
    print("=" * 60)
    
    results = {"condition": "baseline", "tests": {}}
    
    # TCP
    print("\n  [TCP] Running iperf3 for {}s...".format(IPERF_DURATION))
    h1.cmd('pkill iperf3 2>/dev/null')
    h1.cmd('iperf3 -s -D')
    time.sleep(1)
    tcp_out = h2.cmd('iperf3 -c {} -t {} -J'.format(h1_ip, IPERF_DURATION))
    results["tests"]["tcp"] = parse_iperf3_json(tcp_out, "tcp")
    tcp_mbps = results["tests"]["tcp"].get("throughput_mbps", "N/A")
    print("        TCP Throughput: {:.2f} Mbps".format(tcp_mbps) if isinstance(tcp_mbps, float) else "        TCP: {}".format(tcp_mbps))
    
    # UDP
    print("\n  [UDP] Running iperf3 for {}s (100Mbps target)...".format(IPERF_DURATION))
    udp_out = h2.cmd('iperf3 -c {} -u -b 100M -t {} -J'.format(h1_ip, IPERF_DURATION))
    results["tests"]["udp"] = parse_iperf3_json(udp_out, "udp")
    udp_mbps = results["tests"]["udp"].get("throughput_mbps", "N/A")
    print("        UDP Throughput: {:.2f} Mbps".format(udp_mbps) if isinstance(udp_mbps, float) else "        UDP: {}".format(udp_mbps))
    
    h1.cmd('pkill iperf3')
    
    # Ping
    print("\n  [PING] Running {} packets...".format(PING_COUNT))
    ping_out = h2.cmd('ping -c {} {}'.format(PING_COUNT, h1_ip))
    results["tests"]["ping"] = parse_ping(ping_out)
    rtt = results["tests"]["ping"].get("rtt_avg_ms", "N/A")
    print("        RTT avg: {:.3f} ms".format(rtt) if isinstance(rtt, float) else "        RTT: {}".format(rtt))
    
    # HTTP
    print("\n  [HTTP] Creating test file and downloading...")
    h1.cmd('dd if=/dev/zero of=/tmp/testfile_1mb bs=1M count=1 2>/dev/null')
    h1.cmd('cd /tmp && python -m SimpleHTTPServer 8000 &')
    time.sleep(2)
    curl_out = h2.cmd('curl -o /dev/null -w "%{{time_total}}" http://{}:8000/testfile_1mb 2>/dev/null'.format(h1_ip))
    try:
        download_time = float(curl_out.strip())
        results["tests"]["http"] = {"download_time_s": download_time, "file_size_mb": 1}
        print("        Download time: {:.3f} s".format(download_time))
    except ValueError:
        results["tests"]["http"] = {"raw": curl_out}
        print("        HTTP: Could not parse")
    h1.cmd('pkill -f SimpleHTTPServer')
    h1.cmd('rm -f /tmp/testfile_1mb')
    
    return results


def run_loss_sweep(net, h1, h2, h1_ip, interface):
    """MVP-1.0: Packet Loss Sweep."""
    print("\n" + "=" * 60)
    print("MVP-1.0: Packet Loss Sweep")
    print("=" * 60)
    
    results = []
    
    for loss in LOSS_RATES:
        print("\n  [LOSS {}%]".format(loss))
        apply_netem(net, interface, loss=loss)
        time.sleep(1)
        
        test = {"loss_percent": loss, "tcp": {}, "udp": {}}
        
        # TCP
        h1.cmd('pkill iperf3 2>/dev/null')
        h1.cmd('iperf3 -s -D')
        time.sleep(1)
        tcp_out = h2.cmd('iperf3 -c {} -t {} -J'.format(h1_ip, IPERF_DURATION))
        test["tcp"] = parse_iperf3_json(tcp_out, "tcp")
        tcp_mbps = test["tcp"].get("throughput_mbps", "N/A")
        retrans = test["tcp"].get("retransmits", "-")
        print("    TCP: {:.2f} Mbps, Retransmits: {}".format(tcp_mbps, retrans) if isinstance(tcp_mbps, float) else "    TCP: {}".format(tcp_mbps))
        
        # UDP
        udp_out = h2.cmd('iperf3 -c {} -u -b 100M -t {} -J'.format(h1_ip, IPERF_DURATION))
        test["udp"] = parse_iperf3_json(udp_out, "udp")
        udp_mbps = test["udp"].get("throughput_mbps", "N/A")
        udp_loss = test["udp"].get("lost_percent", "-")
        print("    UDP: {:.2f} Mbps, Measured Loss: {:.2f}%".format(udp_mbps, udp_loss) if isinstance(udp_mbps, float) and isinstance(udp_loss, float) else "    UDP: {}".format(udp_mbps))
        
        h1.cmd('pkill iperf3')
        results.append(test)
        clear_netem(net, interface)
    
    return results


def run_delay_sweep(net, h1, h2, h1_ip, interface):
    """MVP-1.1: Delay Sweep."""
    print("\n" + "=" * 60)
    print("MVP-1.1: Delay Sweep")
    print("=" * 60)
    
    results = []
    
    for delay in DELAYS:
        print("\n  [DELAY {}ms]".format(delay))
        apply_netem(net, interface, delay=delay)
        time.sleep(1)
        
        test = {"delay_ms": delay, "ping": {}, "tcp": {}}
        
        # Ping
        ping_out = h2.cmd('ping -c {} {}'.format(PING_COUNT, h1_ip))
        test["ping"] = parse_ping(ping_out)
        rtt = test["ping"].get("rtt_avg_ms", "N/A")
        print("    RTT avg: {:.3f} ms".format(rtt) if isinstance(rtt, float) else "    RTT: {}".format(rtt))
        
        # TCP
        h1.cmd('pkill iperf3 2>/dev/null')
        h1.cmd('iperf3 -s -D')
        time.sleep(1)
        tcp_out = h2.cmd('iperf3 -c {} -t {} -J'.format(h1_ip, IPERF_DURATION))
        test["tcp"] = parse_iperf3_json(tcp_out, "tcp")
        tcp_mbps = test["tcp"].get("throughput_mbps", "N/A")
        print("    TCP: {:.2f} Mbps".format(tcp_mbps) if isinstance(tcp_mbps, float) else "    TCP: {}".format(tcp_mbps))
        
        h1.cmd('pkill iperf3')
        results.append(test)
        clear_netem(net, interface)
    
    return results


def run_bandwidth_sweep(net, h1, h2, h1_ip, interface):
    """MVP-1.2: Bandwidth Limit Sweep."""
    print("\n" + "=" * 60)
    print("MVP-1.2: Bandwidth Limit Sweep")
    print("=" * 60)
    
    results = []
    
    for bw in BANDWIDTHS:
        print("\n  [BW LIMIT {}Mbps]".format(bw))
        apply_netem(net, interface, bw=bw)
        time.sleep(1)
        
        test = {"bandwidth_limit_mbps": bw, "tcp": {}, "udp": {}}
        
        # TCP
        h1.cmd('pkill iperf3 2>/dev/null')
        h1.cmd('iperf3 -s -D')
        time.sleep(1)
        tcp_out = h2.cmd('iperf3 -c {} -t {} -J'.format(h1_ip, IPERF_DURATION))
        test["tcp"] = parse_iperf3_json(tcp_out, "tcp")
        tcp_mbps = test["tcp"].get("throughput_mbps", "N/A")
        print("    TCP: {:.2f} Mbps".format(tcp_mbps) if isinstance(tcp_mbps, float) else "    TCP: {}".format(tcp_mbps))
        
        # UDP
        udp_out = h2.cmd('iperf3 -c {} -u -b 100M -t {} -J'.format(h1_ip, IPERF_DURATION))
        test["udp"] = parse_iperf3_json(udp_out, "udp")
        udp_mbps = test["udp"].get("throughput_mbps", "N/A")
        print("    UDP: {:.2f} Mbps".format(udp_mbps) if isinstance(udp_mbps, float) else "    UDP: {}".format(udp_mbps))
        
        h1.cmd('pkill iperf3')
        results.append(test)
        clear_netem(net, interface)
    
    return results


def run_http_tests(net, h1, h2, h1_ip, interface):
    """MVP-2.0: HTTP Performance under Anomalies."""
    print("\n" + "=" * 60)
    print("MVP-2.0: HTTP Performance Tests")
    print("=" * 60)
    
    results = []
    
    # Create test file
    h1.cmd('dd if=/dev/zero of=/tmp/testfile_1mb bs=1M count=1 2>/dev/null')
    h1.cmd('cd /tmp && python -m SimpleHTTPServer 8000 &')
    time.sleep(2)
    
    conditions = [
        {"name": "baseline", "loss": 0, "delay": 0},
        {"name": "5% loss", "loss": 5, "delay": 0},
        {"name": "50ms delay", "loss": 0, "delay": 50},
        {"name": "5% loss + 50ms delay", "loss": 5, "delay": 50},
    ]
    
    for cond in conditions:
        print("\n  [HTTP] Condition: {}".format(cond["name"]))
        apply_netem(net, interface, loss=cond["loss"], delay=cond["delay"])
        time.sleep(1)
        
        test = {"condition": cond["name"], "loss_percent": cond["loss"], "delay_ms": cond["delay"]}
        
        curl_out = h2.cmd('curl -o /dev/null -w "%{{time_total}}" http://{}:8000/testfile_1mb 2>/dev/null'.format(h1_ip))
        try:
            download_time = float(curl_out.strip())
            test["download_time_s"] = download_time
            print("    Download time: {:.3f} s".format(download_time))
        except ValueError:
            test["download_time_s"] = None
            test["raw"] = curl_out
            print("    Download: Could not parse")
        
        results.append(test)
        clear_netem(net, interface)
    
    h1.cmd('pkill -f SimpleHTTPServer')
    h1.cmd('rm -f /tmp/testfile_1mb')
    
    return results


# ============================================================
# Main
# ============================================================

def main():
    print("""
======================================================================
   Network Anomaly Evaluation - FN-20251206-network-01
   Running all MVPs: 0.0, 1.0, 1.1, 1.2, 2.0
======================================================================
""")
    
    setLogLevel('warning')
    
    # Create network
    print("[SETUP] Creating network topology: h1 -- s1 -- h2")
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    h1_ip = h1.IP()
    interface = 's1-eth1'
    
    print("         h1 IP: {}".format(h1_ip))
    print("         h2 IP: {}".format(h2.IP()))
    print("         Interface: {}".format(interface))
    
    all_results = {
        "experiment_id": "FN-20251206-network-01",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "iperf_duration_s": IPERF_DURATION,
            "ping_count": PING_COUNT,
            "loss_rates": LOSS_RATES,
            "delays": DELAYS,
            "bandwidths": BANDWIDTHS
        }
    }
    
    try:
        # Run all tests
        all_results["baseline"] = run_baseline(net, h1, h2, h1_ip)
        all_results["loss_sweep"] = run_loss_sweep(net, h1, h2, h1_ip, interface)
        all_results["delay_sweep"] = run_delay_sweep(net, h1, h2, h1_ip, interface)
        all_results["bandwidth_sweep"] = run_bandwidth_sweep(net, h1, h2, h1_ip, interface)
        all_results["http_tests"] = run_http_tests(net, h1, h2, h1_ip, interface)
        
    finally:
        print("\n[CLEANUP] Stopping network...")
        clear_netem(net, interface)
        net.stop()
    
    # Save results
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(results_dir, "all_results_{}.json".format(timestamp))
    
    with open(filepath, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("RESULTS SAVED: {}".format(filepath))
    print("=" * 60)
    
    # Print summary
    print_summary(all_results)
    
    return all_results


def print_summary(results):
    """Print summary of all results."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Baseline
    baseline = results.get("baseline", {}).get("tests", {})
    tcp_base = baseline.get("tcp", {}).get("throughput_mbps", "N/A")
    udp_base = baseline.get("udp", {}).get("throughput_mbps", "N/A")
    rtt_base = baseline.get("ping", {}).get("rtt_avg_ms", "N/A")
    http_base = baseline.get("http", {}).get("download_time_s", "N/A")
    
    print("\n[Baseline (MVP-0.0)]")
    print("  TCP Throughput: {} Mbps".format("{:.2f}".format(tcp_base) if isinstance(tcp_base, float) else tcp_base))
    print("  UDP Throughput: {} Mbps".format("{:.2f}".format(udp_base) if isinstance(udp_base, float) else udp_base))
    print("  RTT: {} ms".format("{:.3f}".format(rtt_base) if isinstance(rtt_base, float) else rtt_base))
    print("  HTTP Download: {} s".format("{:.3f}".format(http_base) if isinstance(http_base, float) else http_base))
    
    # Loss Sweep Summary
    print("\n[Loss Sweep (MVP-1.0)]")
    print("  {:>8} {:>12} {:>12} {:>12}".format("Loss%", "TCP Mbps", "Retrans", "UDP Loss%"))
    for r in results.get("loss_sweep", []):
        tcp = r.get("tcp", {})
        udp = r.get("udp", {})
        print("  {:>8} {:>12} {:>12} {:>12}".format(
            r["loss_percent"],
            "{:.2f}".format(tcp.get("throughput_mbps", 0)) if tcp.get("throughput_mbps") else "N/A",
            tcp.get("retransmits", "-"),
            "{:.2f}".format(udp.get("lost_percent", 0)) if udp.get("lost_percent") is not None else "-"
        ))
    
    # Delay Sweep Summary
    print("\n[Delay Sweep (MVP-1.1)]")
    print("  {:>10} {:>12} {:>12}".format("Delay ms", "RTT ms", "TCP Mbps"))
    for r in results.get("delay_sweep", []):
        ping = r.get("ping", {})
        tcp = r.get("tcp", {})
        print("  {:>10} {:>12} {:>12}".format(
            r["delay_ms"],
            "{:.3f}".format(ping.get("rtt_avg_ms", 0)) if ping.get("rtt_avg_ms") else "N/A",
            "{:.2f}".format(tcp.get("throughput_mbps", 0)) if tcp.get("throughput_mbps") else "N/A"
        ))
    
    # Bandwidth Sweep Summary
    print("\n[Bandwidth Sweep (MVP-1.2)]")
    print("  {:>10} {:>12} {:>12}".format("BW Limit", "TCP Mbps", "UDP Mbps"))
    for r in results.get("bandwidth_sweep", []):
        tcp = r.get("tcp", {})
        udp = r.get("udp", {})
        print("  {:>10} {:>12} {:>12}".format(
            r["bandwidth_limit_mbps"],
            "{:.2f}".format(tcp.get("throughput_mbps", 0)) if tcp.get("throughput_mbps") else "N/A",
            "{:.2f}".format(udp.get("throughput_mbps", 0)) if udp.get("throughput_mbps") else "N/A"
        ))
    
    # HTTP Tests Summary
    print("\n[HTTP Tests (MVP-2.0)]")
    print("  {:>25} {:>12}".format("Condition", "Time (s)"))
    for r in results.get("http_tests", []):
        print("  {:>25} {:>12}".format(
            r["condition"],
            "{:.3f}".format(r.get("download_time_s", 0)) if r.get("download_time_s") else "N/A"
        ))
    
    # Hypothesis verification
    print("\n" + "=" * 60)
    print("HYPOTHESIS VERIFICATION")
    print("=" * 60)
    
    # H1.1: TCP @10% loss drops >50%
    if isinstance(tcp_base, float):
        for r in results.get("loss_sweep", []):
            if r["loss_percent"] == 10:
                tcp_10 = r.get("tcp", {}).get("throughput_mbps")
                if tcp_10:
                    drop = (1 - tcp_10 / tcp_base) * 100
                    status = "CONFIRMED" if drop > 50 else "NOT CONFIRMED"
                    print("\n  H1.1: TCP throughput drops >50% at 10% loss")
                    print("        Baseline: {:.2f} Mbps, @10% loss: {:.2f} Mbps".format(tcp_base, tcp_10))
                    print("        Drop: {:.1f}% -> {}".format(drop, status))
    
    # H1.2: RTT scales linearly with delay
    print("\n  H1.2: RTT scales linearly with delay")
    for r in results.get("delay_sweep", []):
        delay = r["delay_ms"]
        rtt = r.get("ping", {}).get("rtt_avg_ms")
        if rtt and delay > 0:
            expected = rtt_base + 2 * delay if isinstance(rtt_base, float) else 2 * delay
            print("        @{}ms delay: RTT={:.3f}ms (expected ~{:.1f}ms)".format(delay, rtt, expected))
    
    # H2.2: HTTP shows compounded effects
    baseline_http = None
    combined_http = None
    for r in results.get("http_tests", []):
        if r["condition"] == "baseline":
            baseline_http = r.get("download_time_s")
        if r["condition"] == "5% loss + 50ms delay":
            combined_http = r.get("download_time_s")
    
    if baseline_http and combined_http:
        ratio = combined_http / baseline_http
        status = "CONFIRMED" if ratio > 2 else "NOT CONFIRMED"
        print("\n  H2.2: HTTP shows compounded effects (>2x baseline)")
        print("        Baseline: {:.3f}s, Combined: {:.3f}s".format(baseline_http, combined_http))
        print("        Ratio: {:.2f}x -> {}".format(ratio, status))
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
