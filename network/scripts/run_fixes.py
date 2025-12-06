#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Fix UDP and HTTP tests - FN-20251206-network-01
================================================

Fixes:
1. UDP parsing for iperf3 3.0.11 (uses 'sum' not 'sum_received')
2. HTTP tests with bandwidth-limited baseline for meaningful results
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


IPERF_DURATION = 10
LOSS_RATES = [0, 1, 5, 10, 20]


def get_results_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(os.path.dirname(script_dir), 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    return results_dir


def parse_udp_iperf3(output):
    """Parse iperf3 UDP output - compatible with 3.0.11."""
    try:
        data = json.loads(output)
        # iperf3 3.0.11 UDP uses 'sum' at end
        end_data = data.get("end", {})
        
        # Try sum first (for UDP sender stats)
        sum_data = end_data.get("sum", {})
        if sum_data:
            return {
                "throughput_mbps": sum_data.get("bits_per_second", 0) / 1e6,
                "jitter_ms": sum_data.get("jitter_ms", None),
                "lost_packets": sum_data.get("lost_packets", 0),
                "total_packets": sum_data.get("packets", 0),
                "lost_percent": sum_data.get("lost_percent", 0),
            }
        
        # Fallback to streams
        streams = end_data.get("streams", [])
        if streams:
            udp_data = streams[0].get("udp", {})
            return {
                "throughput_mbps": udp_data.get("bits_per_second", 0) / 1e6,
                "jitter_ms": udp_data.get("jitter_ms", None),
                "lost_packets": udp_data.get("lost_packets", 0),
                "total_packets": udp_data.get("packets", 0),
                "lost_percent": udp_data.get("lost_percent", 0),
            }
        
        return {"error": "No UDP data found", "raw": str(data)[:500]}
    except (ValueError, KeyError) as e:
        return {"error": str(e), "raw": output[:500] if output else "empty"}


def apply_netem(net, interface, loss=0, delay=0, bw=0):
    """Apply tc netem rules."""
    s1 = net.get('s1')
    s1.cmd('tc qdisc del dev {} root 2>/dev/null'.format(interface))
    
    if loss == 0 and delay == 0 and bw == 0:
        return
    
    if bw > 0:
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


def run_udp_loss_sweep(net, h1, h2, h1_ip, interface):
    """Run UDP loss sweep with fixed parsing."""
    print("\n" + "=" * 60)
    print("UDP Loss Sweep (Fixed Parsing)")
    print("=" * 60)
    
    results = []
    
    for loss in LOSS_RATES:
        print("\n  [LOSS {}%]".format(loss))
        apply_netem(net, interface, loss=loss)
        time.sleep(1)
        
        test = {"loss_percent": loss, "udp": {}}
        
        # Run UDP server (need to restart for each test)
        h1.cmd('pkill iperf3 2>/dev/null')
        h1.cmd('iperf3 -s -D')
        time.sleep(1)
        
        # UDP test - use lower bitrate for more reliable results
        udp_out = h2.cmd('iperf3 -c {} -u -b 50M -t {} -J'.format(h1_ip, IPERF_DURATION))
        test["udp"] = parse_udp_iperf3(udp_out)
        
        udp_mbps = test["udp"].get("throughput_mbps", "N/A")
        udp_loss = test["udp"].get("lost_percent", "N/A")
        lost_pkts = test["udp"].get("lost_packets", "-")
        total_pkts = test["udp"].get("total_packets", "-")
        
        if isinstance(udp_mbps, float):
            print("    UDP: {:.2f} Mbps".format(udp_mbps))
            print("    Lost: {}/{} packets ({:.2f}%)".format(lost_pkts, total_pkts, udp_loss if isinstance(udp_loss, float) else 0))
        else:
            print("    UDP: {}".format(test["udp"].get("error", "Unknown error")))
        
        h1.cmd('pkill iperf3')
        results.append(test)
        clear_netem(net, interface)
        time.sleep(1)
    
    return results


def run_http_with_bandwidth_limit(net, h1, h2, h1_ip, interface):
    """Run HTTP tests with bandwidth-limited baseline for meaningful comparison."""
    print("\n" + "=" * 60)
    print("HTTP Tests (10 Mbps Bandwidth Limit)")
    print("=" * 60)
    
    results = []
    
    # Create larger test file (10MB)
    print("\n  Creating 10MB test file...")
    h1.cmd('dd if=/dev/zero of=/tmp/testfile_10mb bs=1M count=10 2>/dev/null')
    h1.cmd('cd /tmp && python -m SimpleHTTPServer 8000 &')
    time.sleep(2)
    
    conditions = [
        {"name": "baseline (10Mbps)", "loss": 0, "delay": 0, "bw": 10},
        {"name": "5% loss", "loss": 5, "delay": 0, "bw": 10},
        {"name": "50ms delay", "loss": 0, "delay": 50, "bw": 10},
        {"name": "5% loss + 50ms delay", "loss": 5, "delay": 50, "bw": 10},
        {"name": "10% loss + 100ms delay", "loss": 10, "delay": 100, "bw": 10},
    ]
    
    for cond in conditions:
        print("\n  [HTTP] Condition: {}".format(cond["name"]))
        apply_netem(net, interface, loss=cond["loss"], delay=cond["delay"], bw=cond["bw"])
        time.sleep(1)
        
        test = {
            "condition": cond["name"],
            "loss_percent": cond["loss"],
            "delay_ms": cond["delay"],
            "bandwidth_mbps": cond["bw"]
        }
        
        # Download 10MB file
        curl_out = h2.cmd('curl -o /dev/null -w "%{{time_total}}\\n%{{speed_download}}" http://{}:8000/testfile_10mb 2>/dev/null'.format(h1_ip))
        lines = curl_out.strip().split('\n')
        
        try:
            download_time = float(lines[0])
            speed = float(lines[1]) / 1e6 if len(lines) > 1 else None  # MB/s
            test["download_time_s"] = download_time
            test["speed_mbps"] = speed * 8 if speed else None  # Convert MB/s to Mbps
            print("    Download time: {:.3f} s".format(download_time))
            if speed:
                print("    Speed: {:.2f} Mbps".format(speed * 8))
        except (ValueError, IndexError):
            test["download_time_s"] = None
            test["raw"] = curl_out
            print("    Download: Could not parse")
        
        results.append(test)
        clear_netem(net, interface)
        time.sleep(1)
    
    h1.cmd('pkill -f SimpleHTTPServer')
    h1.cmd('rm -f /tmp/testfile_10mb')
    
    return results


def main():
    print("""
======================================================================
   Network Anomaly Evaluation - Fix Tests
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
        "test_type": "fixes"
    }
    
    try:
        # Run fixed tests
        results["udp_loss_sweep"] = run_udp_loss_sweep(net, h1, h2, h1_ip, interface)
        results["http_bandwidth_limited"] = run_http_with_bandwidth_limit(net, h1, h2, h1_ip, interface)
        
    finally:
        print("\n[CLEANUP] Stopping network...")
        clear_netem(net, interface)
        net.stop()
    
    # Save results
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(results_dir, "fixes_{}.json".format(timestamp))
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("RESULTS SAVED: {}".format(filepath))
    print("=" * 60)
    
    # Print summary
    print("\n[UDP LOSS SWEEP SUMMARY]")
    print("  {:>8} {:>12} {:>12} {:>12}".format("Loss%", "UDP Mbps", "Lost Pkts", "Lost%"))
    for r in results.get("udp_loss_sweep", []):
        udp = r.get("udp", {})
        print("  {:>8} {:>12} {:>12} {:>12}".format(
            r["loss_percent"],
            "{:.2f}".format(udp.get("throughput_mbps", 0)) if udp.get("throughput_mbps") else "N/A",
            udp.get("lost_packets", "-"),
            "{:.2f}".format(udp.get("lost_percent", 0)) if udp.get("lost_percent") is not None else "-"
        ))
    
    print("\n[HTTP BANDWIDTH-LIMITED SUMMARY]")
    print("  {:>30} {:>12} {:>12}".format("Condition", "Time (s)", "Speed Mbps"))
    baseline_time = None
    for r in results.get("http_bandwidth_limited", []):
        t = r.get("download_time_s")
        if r["condition"].startswith("baseline") and t:
            baseline_time = t
        ratio = ""
        if baseline_time and t:
            ratio = " ({:.1f}x)".format(t / baseline_time)
        print("  {:>30} {:>12}{} {:>12}".format(
            r["condition"],
            "{:.3f}".format(t) if t else "N/A",
            ratio,
            "{:.2f}".format(r.get("speed_mbps", 0)) if r.get("speed_mbps") else "-"
        ))
    
    # Hypothesis verification
    print("\n[HYPOTHESIS VERIFICATION]")
    
    # H2.1: UDP loss = injected loss
    print("\n  H2.1: UDP measured loss matches injected loss")
    for r in results.get("udp_loss_sweep", []):
        injected = r["loss_percent"]
        measured = r.get("udp", {}).get("lost_percent", None)
        if measured is not None and injected > 0:
            diff = abs(measured - injected)
            status = "CONFIRMED" if diff <= injected * 0.5 else "DEVIATION"
            print("    @{}% injected: {:.2f}% measured (diff: {:.2f}%) -> {}".format(
                injected, measured, diff, status))
    
    # H2.2: HTTP shows compounding
    print("\n  H2.2: HTTP shows compounded effects (>2x baseline)")
    for r in results.get("http_bandwidth_limited", []):
        if "loss" in r["condition"].lower() and "delay" in r["condition"].lower():
            t = r.get("download_time_s")
            if t and baseline_time:
                ratio = t / baseline_time
                status = "CONFIRMED" if ratio > 2 else "NOT CONFIRMED"
                print("    {}: {:.2f}x baseline -> {}".format(r["condition"], ratio, status))


if __name__ == '__main__':
    main()
