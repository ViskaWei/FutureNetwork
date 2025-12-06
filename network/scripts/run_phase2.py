#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Phase 2: Application Layer & Combined Anomalies
================================================

MVP-2.0: HTTP Performance (Fixed with bandwidth limit)
MVP-2.1: Combined Anomalies Analysis

This script creates a realistic scenario by:
1. Limiting baseline bandwidth to 10 Mbps (realistic WAN)
2. Testing HTTP with larger files (10MB, 50MB)
3. Testing combined anomalies (loss + delay + bandwidth)
"""

from __future__ import print_function

import json
import os
import time
from datetime import datetime

from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.topo import SingleSwitchTopo
from mininet.link import TCLink
from mininet.log import setLogLevel


def get_results_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(os.path.dirname(script_dir), 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    return results_dir


def apply_netem(net, interface, loss=0, delay=0, bw=0):
    """Apply tc netem/tbf rules."""
    s1 = net.get('s1')
    s1.cmd('tc qdisc del dev {} root 2>/dev/null'.format(interface))
    
    if loss == 0 and delay == 0 and bw == 0:
        return
    
    if bw > 0:
        # HTB for bandwidth + netem for loss/delay
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
        netem_opts = ''
        if delay > 0:
            netem_opts += ' delay {}ms'.format(delay)
        if loss > 0:
            netem_opts += ' loss {}%'.format(loss)
        if netem_opts:
            s1.cmd('tc qdisc add dev {} root netem{}'.format(interface, netem_opts))


def clear_netem(net, interface):
    s1 = net.get('s1')
    s1.cmd('tc qdisc del dev {} root 2>/dev/null'.format(interface))


def parse_tcp_iperf3(output):
    """Parse iperf3 TCP JSON output."""
    try:
        data = json.loads(output)
        return {
            "throughput_mbps": data["end"]["sum_received"]["bits_per_second"] / 1e6,
            "retransmits": data["end"]["sum_sent"].get("retransmits", 0),
        }
    except (ValueError, KeyError) as e:
        return {"error": str(e)}


def run_http_test(h1, h2, h1_ip, file_size_mb):
    """Run HTTP download test and return time."""
    # Use wget with timing (more reliable than curl for large files)
    start_time = time.time()
    h2.cmd('wget -q -O /dev/null http://{}:8000/testfile_{}mb 2>/dev/null'.format(h1_ip, file_size_mb))
    elapsed = time.time() - start_time
    return elapsed


def run_mvp_2_0_http_fixed(net, h1, h2, h1_ip, interface):
    """
    MVP-2.0: HTTP Performance Tests (Fixed)
    
    Use 10 Mbps baseline to simulate realistic WAN conditions.
    """
    print("\n" + "=" * 60)
    print("MVP-2.0: HTTP Performance (Fixed - 10 Mbps Baseline)")
    print("=" * 60)
    
    results = []
    file_size = 10  # MB
    baseline_bw = 10  # Mbps
    
    # Create test file
    print("\n  Creating {}MB test file...".format(file_size))
    h1.cmd('dd if=/dev/zero of=/tmp/testfile_{}mb bs=1M count={} 2>/dev/null'.format(file_size, file_size))
    h1.cmd('cd /tmp && python -m SimpleHTTPServer 8000 &')
    time.sleep(2)
    
    # Test conditions
    conditions = [
        {"name": "baseline (10Mbps, no anomaly)", "loss": 0, "delay": 0, "bw": baseline_bw},
        {"name": "1% loss", "loss": 1, "delay": 0, "bw": baseline_bw},
        {"name": "5% loss", "loss": 5, "delay": 0, "bw": baseline_bw},
        {"name": "10% loss", "loss": 10, "delay": 0, "bw": baseline_bw},
        {"name": "50ms delay", "loss": 0, "delay": 50, "bw": baseline_bw},
        {"name": "100ms delay", "loss": 0, "delay": 100, "bw": baseline_bw},
        {"name": "5% loss + 50ms delay", "loss": 5, "delay": 50, "bw": baseline_bw},
        {"name": "10% loss + 100ms delay", "loss": 10, "delay": 100, "bw": baseline_bw},
    ]
    
    baseline_time = None
    
    for cond in conditions:
        print("\n  [HTTP {}MB] {}".format(file_size, cond["name"]))
        apply_netem(net, interface, loss=cond["loss"], delay=cond["delay"], bw=cond["bw"])
        time.sleep(1)
        
        download_time = run_http_test(h1, h2, h1_ip, file_size)
        
        test = {
            "condition": cond["name"],
            "loss_percent": cond["loss"],
            "delay_ms": cond["delay"],
            "bandwidth_mbps": cond["bw"],
            "file_size_mb": file_size,
            "download_time_s": download_time,
        }
        
        if cond["name"].startswith("baseline"):
            baseline_time = download_time
            test["ratio"] = 1.0
        elif baseline_time and baseline_time > 0:
            test["ratio"] = download_time / baseline_time
        
        # Calculate effective throughput
        if download_time > 0:
            test["effective_throughput_mbps"] = (file_size * 8) / download_time
        
        print("    Download time: {:.2f} s".format(download_time))
        if "ratio" in test and test["ratio"] != 1.0:
            print("    Ratio vs baseline: {:.2f}x".format(test["ratio"]))
        if "effective_throughput_mbps" in test:
            print("    Effective throughput: {:.2f} Mbps".format(test["effective_throughput_mbps"]))
        
        results.append(test)
        clear_netem(net, interface)
        time.sleep(1)
    
    h1.cmd('pkill -f SimpleHTTPServer')
    h1.cmd('rm -f /tmp/testfile_{}mb'.format(file_size))
    
    return results


def run_mvp_2_1_combined(net, h1, h2, h1_ip, interface):
    """
    MVP-2.1: Combined Anomalies Analysis
    
    Test interaction effects of multiple anomalies.
    """
    print("\n" + "=" * 60)
    print("MVP-2.1: Combined Anomalies Analysis")
    print("=" * 60)
    
    results = []
    
    # Test matrix: Loss x Delay x Bandwidth combinations
    test_matrix = [
        # Baseline comparisons
        {"name": "baseline (no limit)", "loss": 0, "delay": 0, "bw": 0},
        {"name": "10 Mbps only", "loss": 0, "delay": 0, "bw": 10},
        {"name": "5 Mbps only", "loss": 0, "delay": 0, "bw": 5},
        
        # Single anomaly at 10 Mbps
        {"name": "10Mbps + 5% loss", "loss": 5, "delay": 0, "bw": 10},
        {"name": "10Mbps + 50ms delay", "loss": 0, "delay": 50, "bw": 10},
        
        # Combined anomalies
        {"name": "10Mbps + 5% loss + 50ms delay", "loss": 5, "delay": 50, "bw": 10},
        {"name": "10Mbps + 10% loss + 100ms delay", "loss": 10, "delay": 100, "bw": 10},
        {"name": "5Mbps + 5% loss + 50ms delay", "loss": 5, "delay": 50, "bw": 5},
        
        # Extreme conditions
        {"name": "5Mbps + 10% loss + 200ms delay", "loss": 10, "delay": 200, "bw": 5},
    ]
    
    for config in test_matrix:
        print("\n  [Combined] {}".format(config["name"]))
        apply_netem(net, interface, loss=config["loss"], delay=config["delay"], bw=config["bw"])
        time.sleep(1)
        
        test = {
            "config": config["name"],
            "loss_percent": config["loss"],
            "delay_ms": config["delay"],
            "bandwidth_mbps": config["bw"],
            "tcp": {},
            "ping": {}
        }
        
        # TCP test
        h1.cmd('pkill iperf3 2>/dev/null')
        h1.cmd('iperf3 -s -D')
        time.sleep(1)
        
        tcp_out = h2.cmd('iperf3 -c {} -t 10 -J'.format(h1_ip))
        test["tcp"] = parse_tcp_iperf3(tcp_out)
        
        tcp_mbps = test["tcp"].get("throughput_mbps", "N/A")
        retrans = test["tcp"].get("retransmits", "-")
        
        if isinstance(tcp_mbps, float):
            print("    TCP: {:.2f} Mbps, Retransmits: {}".format(tcp_mbps, retrans))
        else:
            print("    TCP: Error - {}".format(test["tcp"].get("error", "unknown")))
        
        # Ping test (RTT)
        ping_out = h2.cmd('ping -c 20 {}'.format(h1_ip))
        for line in ping_out.split('\n'):
            if 'rtt min/avg/max' in line or 'round-trip' in line:
                parts = line.split('=')[-1].strip().split('/')
                test["ping"] = {
                    "rtt_min_ms": float(parts[0]),
                    "rtt_avg_ms": float(parts[1]),
                    "rtt_max_ms": float(parts[2]),
                }
                print("    RTT: {:.2f} ms (avg)".format(test["ping"]["rtt_avg_ms"]))
                break
        
        h1.cmd('pkill iperf3')
        results.append(test)
        clear_netem(net, interface)
        time.sleep(1)
    
    return results


def main():
    print("""
======================================================================
   Network Anomaly Evaluation - Phase 2
   MVP-2.0: HTTP Performance (Fixed)
   MVP-2.1: Combined Anomalies Analysis
   FN-20251206-network-01
======================================================================
""")
    
    setLogLevel('warning')
    
    print("[SETUP] Creating network...")
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    h1_ip = h1.IP()
    interface = 's1-eth1'
    
    print("         h1 IP: {}".format(h1_ip))
    print("         h2 IP: {}".format(h2.IP()))
    
    results = {
        "experiment_id": "FN-20251206-network-01",
        "timestamp": datetime.now().isoformat(),
        "phase": 2
    }
    
    try:
        results["mvp_2_0_http"] = run_mvp_2_0_http_fixed(net, h1, h2, h1_ip, interface)
        results["mvp_2_1_combined"] = run_mvp_2_1_combined(net, h1, h2, h1_ip, interface)
        
    finally:
        print("\n[CLEANUP] Stopping network...")
        clear_netem(net, interface)
        net.stop()
    
    # Save results
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(results_dir, "phase2_{}.json".format(timestamp))
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("RESULTS SAVED: {}".format(filepath))
    print("=" * 60)
    
    # Print summary
    print("\n" + "=" * 60)
    print("MVP-2.0: HTTP PERFORMANCE SUMMARY")
    print("=" * 60)
    print("\n{:>35} {:>12} {:>10} {:>12}".format("Condition", "Time (s)", "Ratio", "Throughput"))
    print("-" * 75)
    for r in results.get("mvp_2_0_http", []):
        print("{:>35} {:>12.2f} {:>10.2f}x {:>10.2f} Mbps".format(
            r["condition"][:35],
            r.get("download_time_s", 0),
            r.get("ratio", 1.0),
            r.get("effective_throughput_mbps", 0)
        ))
    
    # H2.2 verification
    print("\n[HYPOTHESIS H2.2 VERIFICATION]")
    baseline_time = None
    for r in results.get("mvp_2_0_http", []):
        if r["condition"].startswith("baseline"):
            baseline_time = r.get("download_time_s")
        if "loss" in r["condition"].lower() and "delay" in r["condition"].lower():
            ratio = r.get("ratio", 0)
            status = "CONFIRMED" if ratio > 2 else "NOT CONFIRMED"
            print("  {}: {:.2f}x baseline -> {}".format(r["condition"], ratio, status))
    
    print("\n" + "=" * 60)
    print("MVP-2.1: COMBINED ANOMALIES SUMMARY")
    print("=" * 60)
    print("\n{:>40} {:>12} {:>10} {:>10}".format("Config", "TCP Mbps", "Retrans", "RTT ms"))
    print("-" * 75)
    for r in results.get("mvp_2_1_combined", []):
        tcp = r.get("tcp", {})
        ping = r.get("ping", {})
        print("{:>40} {:>12} {:>10} {:>10}".format(
            r["config"][:40],
            "{:.2f}".format(tcp.get("throughput_mbps", 0)) if tcp.get("throughput_mbps") else "N/A",
            tcp.get("retransmits", "-"),
            "{:.2f}".format(ping.get("rtt_avg_ms", 0)) if ping.get("rtt_avg_ms") else "-"
        ))
    
    return results


if __name__ == '__main__':
    main()
