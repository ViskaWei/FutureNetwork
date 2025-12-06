#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate plots from network anomaly experiment results.
"""

import json
import os
import sys

# Try matplotlib, fall back to simple text output
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("matplotlib not available, generating text summaries only")


def load_results(results_file):
    """Load results from JSON file."""
    with open(results_file, 'r') as f:
        return json.load(f)


def plot_loss_sweep(results, output_dir):
    """Plot TCP throughput vs packet loss rate."""
    if not HAS_MATPLOTLIB:
        return
    
    loss_data = results.get('loss_sweep', [])
    
    loss_rates = [d['loss_percent'] for d in loss_data]
    tcp_throughput = [d['tcp'].get('throughput_mbps', 0) for d in loss_data]
    retransmits = [d['tcp'].get('retransmits', 0) for d in loss_data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # TCP Throughput vs Loss
    ax1.plot(loss_rates, tcp_throughput, 'b-o', linewidth=2, markersize=8)
    ax1.set_xlabel('Packet Loss Rate (%)', fontsize=12)
    ax1.set_ylabel('TCP Throughput (Mbps)', fontsize=12)
    ax1.set_title('TCP Throughput vs Packet Loss Rate', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    
    # Add annotations
    for i, (x, y) in enumerate(zip(loss_rates, tcp_throughput)):
        if y > 0:
            ax1.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                        xytext=(0, 10), ha='center', fontsize=9)
    
    # Retransmits vs Loss
    ax2.bar(loss_rates, retransmits, color='coral', edgecolor='black')
    ax2.set_xlabel('Packet Loss Rate (%)', fontsize=12)
    ax2.set_ylabel('TCP Retransmits', fontsize=12)
    ax2.set_title('TCP Retransmits vs Packet Loss Rate', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tcp_throughput_vs_loss.png'), dpi=150)
    plt.close()
    print(f"  Saved: tcp_throughput_vs_loss.png")


def plot_delay_sweep(results, output_dir):
    """Plot RTT and throughput vs injected delay."""
    if not HAS_MATPLOTLIB:
        return
    
    delay_data = results.get('delay_sweep', [])
    
    delays = [d['delay_ms'] for d in delay_data]
    rtts = [d['ping'].get('rtt_avg_ms', 0) for d in delay_data]
    tcp_throughput = [d['tcp'].get('throughput_mbps', 0) for d in delay_data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # RTT vs Delay
    ax1.plot(delays, rtts, 'g-o', linewidth=2, markersize=8, label='Measured RTT')
    ax1.plot(delays, delays, 'r--', linewidth=1, label='Injected Delay')
    ax1.set_xlabel('Injected Delay (ms)', fontsize=12)
    ax1.set_ylabel('Round-Trip Time (ms)', fontsize=12)
    ax1.set_title('RTT vs Injected Delay', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # TCP Throughput vs Delay
    ax2.plot(delays, tcp_throughput, 'm-s', linewidth=2, markersize=8)
    ax2.set_xlabel('Injected Delay (ms)', fontsize=12)
    ax2.set_ylabel('TCP Throughput (Mbps)', fontsize=12)
    ax2.set_title('TCP Throughput vs Delay', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rtt_vs_delay.png'), dpi=150)
    plt.close()
    print(f"  Saved: rtt_vs_delay.png")


def plot_bandwidth_sweep(results, output_dir):
    """Plot throughput vs bandwidth limit."""
    if not HAS_MATPLOTLIB:
        return
    
    bw_data = results.get('bandwidth_sweep', [])
    
    limits = [d['bandwidth_limit_mbps'] for d in bw_data]
    tcp_throughput = [d['tcp'].get('throughput_mbps', 0) for d in bw_data]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    x = range(len(limits))
    bars = ax.bar(x, tcp_throughput, color='steelblue', edgecolor='black', label='Measured')
    ax.plot(x, limits, 'r--o', linewidth=2, markersize=8, label='Limit')
    
    ax.set_xlabel('Bandwidth Limit (Mbps)', fontsize=12)
    ax.set_ylabel('TCP Throughput (Mbps)', fontsize=12)
    ax.set_title('TCP Throughput vs Bandwidth Limit', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([str(l) for l in limits])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'bandwidth_sweep.png'), dpi=150)
    plt.close()
    print(f"  Saved: bandwidth_sweep.png")


def plot_combined_summary(results, output_dir):
    """Create a combined summary plot."""
    if not HAS_MATPLOTLIB:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Loss vs TCP Throughput
    loss_data = results.get('loss_sweep', [])
    loss_rates = [d['loss_percent'] for d in loss_data]
    tcp_loss = [d['tcp'].get('throughput_mbps', 0) for d in loss_data]
    
    axes[0, 0].semilogy(loss_rates, tcp_loss, 'b-o', linewidth=2, markersize=8)
    axes[0, 0].set_xlabel('Packet Loss Rate (%)')
    axes[0, 0].set_ylabel('TCP Throughput (Mbps)')
    axes[0, 0].set_title('(a) TCP Throughput vs Packet Loss')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=tcp_loss[0]*0.5, color='r', linestyle='--', alpha=0.5, label='50% baseline')
    axes[0, 0].legend()
    
    # 2. Delay vs RTT
    delay_data = results.get('delay_sweep', [])
    delays = [d['delay_ms'] for d in delay_data]
    rtts = [d['ping'].get('rtt_avg_ms', 0) for d in delay_data]
    
    axes[0, 1].plot(delays, rtts, 'g-o', linewidth=2, markersize=8, label='Measured RTT')
    axes[0, 1].plot(delays, delays, 'r--', linewidth=1, label='y=x (ideal)')
    axes[0, 1].set_xlabel('Injected Delay (ms)')
    axes[0, 1].set_ylabel('RTT (ms)')
    axes[0, 1].set_title('(b) RTT vs Injected Delay')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend()
    
    # 3. Delay vs TCP Throughput
    tcp_delay = [d['tcp'].get('throughput_mbps', 0) for d in delay_data]
    
    axes[1, 0].semilogy(delays, tcp_delay, 'm-s', linewidth=2, markersize=8)
    axes[1, 0].set_xlabel('Injected Delay (ms)')
    axes[1, 0].set_ylabel('TCP Throughput (Mbps)')
    axes[1, 0].set_title('(c) TCP Throughput vs Delay')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Bandwidth limiting
    bw_data = results.get('bandwidth_sweep', [])
    limits = [d['bandwidth_limit_mbps'] for d in bw_data]
    tcp_bw = [d['tcp'].get('throughput_mbps', 0) for d in bw_data]
    
    x = range(len(limits))
    axes[1, 1].bar(x, tcp_bw, color='steelblue', edgecolor='black', alpha=0.7, label='Measured')
    axes[1, 1].scatter(x, limits, color='red', s=100, zorder=5, label='Limit')
    axes[1, 1].set_xlabel('Bandwidth Limit (Mbps)')
    axes[1, 1].set_ylabel('TCP Throughput (Mbps)')
    axes[1, 1].set_title('(d) TCP Throughput vs Bandwidth Limit')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels([str(l) for l in limits])
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Network Anomaly Evaluation Results (FN-20251206-network-01)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'combined_summary.png'), dpi=150)
    plt.close()
    print(f"  Saved: combined_summary.png")


def generate_text_summary(results, output_dir):
    """Generate a text summary of results."""
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("Network Anomaly Evaluation - Results Summary")
    summary_lines.append("Experiment: FN-20251206-network-01")
    summary_lines.append("=" * 60)
    
    # Baseline
    baseline = results.get('baseline', {}).get('tests', {})
    summary_lines.append("\n[BASELINE]")
    summary_lines.append(f"  TCP Throughput: {baseline.get('tcp', {}).get('throughput_mbps', 'N/A'):.2f} Mbps")
    summary_lines.append(f"  RTT: {baseline.get('ping', {}).get('rtt_avg_ms', 'N/A'):.3f} ms")
    
    # Loss sweep
    summary_lines.append("\n[PACKET LOSS SWEEP]")
    summary_lines.append(f"  {'Loss%':>6} {'TCP Mbps':>12} {'Retrans':>10} {'Drop%':>10}")
    baseline_tcp = results.get('loss_sweep', [{}])[0].get('tcp', {}).get('throughput_mbps', 1)
    for d in results.get('loss_sweep', []):
        tcp = d.get('tcp', {}).get('throughput_mbps', 0)
        drop = (1 - tcp/baseline_tcp) * 100 if baseline_tcp > 0 else 0
        summary_lines.append(f"  {d['loss_percent']:>6} {tcp:>12.2f} {d.get('tcp', {}).get('retransmits', 0):>10} {drop:>9.1f}%")
    
    # Delay sweep
    summary_lines.append("\n[DELAY SWEEP]")
    summary_lines.append(f"  {'Delay ms':>8} {'RTT ms':>10} {'TCP Mbps':>12}")
    for d in results.get('delay_sweep', []):
        summary_lines.append(f"  {d['delay_ms']:>8} {d.get('ping', {}).get('rtt_avg_ms', 0):>10.3f} {d.get('tcp', {}).get('throughput_mbps', 0):>12.2f}")
    
    # Bandwidth sweep
    summary_lines.append("\n[BANDWIDTH SWEEP]")
    summary_lines.append(f"  {'Limit Mbps':>10} {'TCP Mbps':>12}")
    for d in results.get('bandwidth_sweep', []):
        summary_lines.append(f"  {d['bandwidth_limit_mbps']:>10} {d.get('tcp', {}).get('throughput_mbps', 0):>12.2f}")
    
    summary_text = '\n'.join(summary_lines)
    
    with open(os.path.join(output_dir, 'results_summary.txt'), 'w') as f:
        f.write(summary_text)
    
    print(f"  Saved: results_summary.txt")
    return summary_text


def main():
    # Find most recent results file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(os.path.dirname(script_dir), 'results')
    output_dir = os.path.join(os.path.dirname(script_dir), 'img')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find latest results file
    results_files = [f for f in os.listdir(results_dir) if f.startswith('all_results_') and f.endswith('.json')]
    if not results_files:
        print("No results files found!")
        sys.exit(1)
    
    latest_file = sorted(results_files)[-1]
    results_path = os.path.join(results_dir, latest_file)
    
    print(f"Loading results from: {results_path}")
    results = load_results(results_path)
    
    print(f"\nGenerating plots in: {output_dir}")
    
    if HAS_MATPLOTLIB:
        plot_loss_sweep(results, output_dir)
        plot_delay_sweep(results, output_dir)
        plot_bandwidth_sweep(results, output_dir)
        plot_combined_summary(results, output_dir)
    
    summary = generate_text_summary(results, output_dir)
    print("\n" + summary)


if __name__ == '__main__':
    main()
