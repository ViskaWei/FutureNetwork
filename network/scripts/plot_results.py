#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Results Visualization
===================================================

This script generates plots from the experiment results.

Requirements:
- matplotlib
- numpy (optional, for better formatting)

Usage:
    python plot_results.py

Output:
    img/tcp_throughput_vs_loss.png
    img/rtt_vs_delay.png
    img/udp_loss_correlation.png
    img/http_download_time.png
"""

import json
from datetime import datetime
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib not available. Install with: pip install matplotlib")


def get_results_dir():
    """Get the results directory path."""
    script_dir = Path(__file__).parent
    return script_dir.parent / "results"


def get_img_dir():
    """Get the img directory path."""
    script_dir = Path(__file__).parent
    img_dir = script_dir.parent / "img"
    img_dir.mkdir(exist_ok=True)
    return img_dir


def find_latest_result(prefix):
    """Find the latest result file with given prefix."""
    results_dir = get_results_dir()
    pattern = f"{prefix}_*.json"
    files = sorted(results_dir.glob(pattern), reverse=True)
    return files[0] if files else None


def load_json(filepath):
    """Load JSON file."""
    if filepath and filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


def plot_tcp_throughput_vs_loss():
    """Plot TCP throughput vs packet loss rate."""
    filepath = find_latest_result("loss_sweep")
    data = load_json(filepath)
    
    if not data:
        print("⚠️  No loss sweep data found")
        return None
    
    results = data.get("results", [])
    
    loss_rates = []
    tcp_throughputs = []
    retransmits = []
    
    for r in results:
        loss = r.get("loss_rate_percent")
        tcp = r.get("tcp", {}).get("throughput_mbps")
        retrans = r.get("tcp", {}).get("retransmits", 0)
        
        if loss is not None and tcp is not None:
            loss_rates.append(loss)
            tcp_throughputs.append(tcp)
            retransmits.append(retrans)
    
    if not loss_rates:
        print("⚠️  No valid loss sweep results")
        return None
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Primary axis: Throughput
    color1 = '#2E86AB'
    ax1.set_xlabel('Packet Loss Rate (%)', fontsize=12)
    ax1.set_ylabel('TCP Throughput (Mbps)', color=color1, fontsize=12)
    line1 = ax1.plot(loss_rates, tcp_throughputs, 'o-', color=color1, 
                     linewidth=2, markersize=10, label='TCP Throughput')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(bottom=0)
    ax1.grid(True, alpha=0.3)
    
    # Secondary axis: Retransmits
    ax2 = ax1.twinx()
    color2 = '#E94F37'
    ax2.set_ylabel('Retransmits', color=color2, fontsize=12)
    line2 = ax2.plot(loss_rates, retransmits, 's--', color=color2, 
                     linewidth=2, markersize=8, label='Retransmits')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(bottom=0)
    
    # Add annotations for key points
    if len(loss_rates) >= 4:
        baseline = tcp_throughputs[0]
        for i, (loss, tcp) in enumerate(zip(loss_rates, tcp_throughputs)):
            if loss in [10, 20]:
                drop = (1 - tcp/baseline) * 100
                ax1.annotate(f'{drop:.0f}% drop', 
                            xy=(loss, tcp), 
                            xytext=(loss+1, tcp+baseline*0.1),
                            fontsize=9, color='gray',
                            arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
    
    # Legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')
    
    # Title
    plt.title('TCP Throughput vs Packet Loss Rate\n(MVP-1.0: Packet Loss Sweep)', 
              fontsize=14, fontweight='bold')
    
    # Add hypothesis annotation
    fig.text(0.5, 0.02, 
             'H1.1: TCP throughput should drop >50% at 10% loss', 
             ha='center', fontsize=10, style='italic', color='gray')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    
    # Save
    img_path = get_img_dir() / "tcp_throughput_vs_loss.png"
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {img_path}")
    return img_path


def plot_rtt_vs_delay():
    """Plot RTT vs injected delay."""
    filepath = find_latest_result("delay_sweep")
    data = load_json(filepath)
    
    if not data:
        print("⚠️  No delay sweep data found")
        return None
    
    results = data.get("results", [])
    
    delays = []
    rtts = []
    expected_rtts = []
    
    baseline_rtt = None
    
    for r in results:
        delay = r.get("delay_ms")
        rtt = r.get("ping", {}).get("rtt_avg_ms")
        
        if delay == 0 and rtt:
            baseline_rtt = rtt
        
        if delay is not None and rtt is not None:
            delays.append(delay)
            rtts.append(rtt)
    
    if not delays or not baseline_rtt:
        print("⚠️  No valid delay sweep results")
        return None
    
    # Calculate expected RTT
    for delay in delays:
        expected_rtts.append(baseline_rtt + delay * 2)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Measured RTT
    ax.plot(delays, rtts, 'o-', color='#2E86AB', linewidth=2, markersize=10, 
            label='Measured RTT')
    
    # Expected RTT (linear model)
    ax.plot(delays, expected_rtts, 's--', color='#E94F37', linewidth=2, markersize=8,
            label=f'Expected (baseline + 2×delay)')
    
    # Annotations
    for delay, rtt, exp in zip(delays, rtts, expected_rtts):
        if delay > 0:
            diff = rtt - exp
            color = 'green' if abs(diff) < exp * 0.2 else 'red'
            ax.annotate(f'{rtt:.1f}ms', xy=(delay, rtt), 
                       xytext=(delay+2, rtt+5), fontsize=9, color='gray')
    
    ax.set_xlabel('Injected Delay (ms)', fontsize=12)
    ax.set_ylabel('Round-Trip Time (ms)', fontsize=12)
    ax.set_title('RTT vs Injected Network Delay\n(MVP-1.1: Delay Sweep)', 
                 fontsize=14, fontweight='bold')
    
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=-5)
    ax.set_ylim(bottom=0)
    
    # Add hypothesis annotation
    fig.text(0.5, 0.02, 
             'H1.2: RTT should scale linearly with delay (RTT = baseline + 2×delay)', 
             ha='center', fontsize=10, style='italic', color='gray')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    
    # Save
    img_path = get_img_dir() / "rtt_vs_delay.png"
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {img_path}")
    return img_path


def plot_udp_loss_correlation():
    """Plot UDP measured loss vs injected loss."""
    filepath = find_latest_result("loss_sweep")
    data = load_json(filepath)
    
    if not data:
        print("⚠️  No loss sweep data found")
        return None
    
    results = data.get("results", [])
    
    injected = []
    measured = []
    
    for r in results:
        loss = r.get("loss_rate_percent")
        udp_loss = r.get("udp", {}).get("lost_percent")
        
        if loss is not None and udp_loss is not None:
            injected.append(loss)
            measured.append(udp_loss)
    
    if not injected:
        print("⚠️  No valid UDP loss results")
        return None
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Scatter plot
    ax.scatter(injected, measured, s=150, c='#2E86AB', alpha=0.8, 
               edgecolors='white', linewidth=2, zorder=5)
    
    # Perfect correlation line (y=x)
    max_val = max(max(injected), max(measured)) * 1.1
    ax.plot([0, max_val], [0, max_val], '--', color='#E94F37', linewidth=2,
            label='Perfect correlation (y=x)')
    
    # Add data labels
    for x, y in zip(injected, measured):
        ax.annotate(f'({x}, {y:.1f})', xy=(x, y), 
                   xytext=(x+0.5, y+0.5), fontsize=9, color='gray')
    
    ax.set_xlabel('Injected Packet Loss (%)', fontsize=12)
    ax.set_ylabel('Measured UDP Loss (%)', fontsize=12)
    ax.set_title('UDP Loss: Injected vs Measured\n(MVP-1.0: Packet Loss Sweep)', 
                 fontsize=14, fontweight='bold')
    
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-1, max_val)
    ax.set_ylim(-1, max_val)
    ax.set_aspect('equal')
    
    # Add hypothesis annotation
    fig.text(0.5, 0.02, 
             'H2.1: UDP measured loss should match injected loss rate', 
             ha='center', fontsize=10, style='italic', color='gray')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # Save
    img_path = get_img_dir() / "udp_loss_correlation.png"
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {img_path}")
    return img_path


def plot_http_download_time():
    """Plot HTTP download times under different conditions."""
    filepath = find_latest_result("http_test")
    data = load_json(filepath)
    
    if not data:
        print("⚠️  No HTTP test data found")
        return None
    
    results = data.get("results", [])
    
    # Group by file size
    data_1mb = {}
    data_5mb = {}
    
    for r in results:
        cond = r.get("condition")
        size = r.get("file_size_mb")
        avg = r.get("avg_s")
        
        if avg:
            if size == 1:
                data_1mb[cond] = avg
            elif size == 5:
                data_5mb[cond] = avg
    
    if not data_1mb:
        print("⚠️  No valid HTTP results")
        return None
    
    # Order conditions
    condition_order = ["baseline", "loss_5pct", "delay_50ms", "combined"]
    condition_labels = ["Baseline", "5% Loss", "50ms Delay", "Combined"]
    
    # Get values in order
    values_1mb = [data_1mb.get(c, 0) for c in condition_order]
    values_5mb = [data_5mb.get(c, 0) for c in condition_order if c in data_5mb]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(condition_order))
    width = 0.35
    
    # Plot bars
    bars1 = ax.bar([i - width/2 for i in x], values_1mb, width, 
                   label='1MB File', color='#2E86AB', alpha=0.8)
    
    if len(values_5mb) == len(condition_order):
        bars2 = ax.bar([i + width/2 for i in x], values_5mb, width,
                       label='5MB File', color='#E94F37', alpha=0.8)
    
    # Add value labels on bars
    for bar, val in zip(bars1, values_1mb):
        if val > 0:
            ax.annotate(f'{val:.2f}s',
                       xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       ha='center', va='bottom', fontsize=9)
    
    # Calculate and annotate slowdown vs baseline
    if values_1mb[0] > 0:  # baseline exists
        baseline = values_1mb[0]
        for i, val in enumerate(values_1mb[1:], 1):
            if val > 0:
                ratio = val / baseline
                ax.annotate(f'{ratio:.1f}×',
                           xy=(i - width/2, val + 0.1),
                           ha='center', va='bottom', fontsize=10, fontweight='bold',
                           color='gray')
    
    ax.set_xlabel('Network Condition', fontsize=12)
    ax.set_ylabel('Download Time (seconds)', fontsize=12)
    ax.set_title('HTTP Download Time Under Various Conditions\n(MVP-2.0/2.1: HTTP Tests)', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(condition_labels)
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_ylim(bottom=0)
    
    # Add hypothesis annotation
    fig.text(0.5, 0.02, 
             'H2.2: HTTP under combined anomalies should show >2× slowdown vs baseline', 
             ha='center', fontsize=10, style='italic', color='gray')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    
    # Save
    img_path = get_img_dir() / "http_download_time.png"
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {img_path}")
    return img_path


def plot_combined_dashboard():
    """Generate a combined dashboard with all plots."""
    # Load all data
    loss_data = load_json(find_latest_result("loss_sweep"))
    delay_data = load_json(find_latest_result("delay_sweep"))
    http_data = load_json(find_latest_result("http_test"))
    
    if not any([loss_data, delay_data, http_data]):
        print("⚠️  No data available for dashboard")
        return None
    
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Network Anomaly Evaluation Dashboard\nExperiment: FN-20251206-network-01',
                 fontsize=16, fontweight='bold')
    
    # Create 2x2 grid
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    # Plot 1: TCP vs Loss (top-left)
    ax1 = fig.add_subplot(gs[0, 0])
    if loss_data:
        results = loss_data.get("results", [])
        loss_rates = [r.get("loss_rate_percent") for r in results if r.get("loss_rate_percent") is not None]
        tcp_tp = [r.get("tcp", {}).get("throughput_mbps") for r in results]
        tcp_tp = [t if t else 0 for t in tcp_tp]
        
        if loss_rates:
            ax1.plot(loss_rates, tcp_tp, 'o-', color='#2E86AB', linewidth=2, markersize=8)
            ax1.set_xlabel('Packet Loss (%)')
            ax1.set_ylabel('TCP Throughput (Mbps)')
            ax1.set_title('TCP Throughput vs Loss')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(bottom=0)
    
    # Plot 2: RTT vs Delay (top-right)
    ax2 = fig.add_subplot(gs[0, 1])
    if delay_data:
        results = delay_data.get("results", [])
        delays = [r.get("delay_ms") for r in results if r.get("delay_ms") is not None]
        rtts = [r.get("ping", {}).get("rtt_avg_ms") for r in results]
        rtts = [r if r else 0 for r in rtts]
        
        if delays:
            ax2.plot(delays, rtts, 'o-', color='#2E86AB', linewidth=2, markersize=8,
                    label='Measured')
            
            # Expected line
            baseline = rtts[0] if rtts else 0
            expected = [baseline + d * 2 for d in delays]
            ax2.plot(delays, expected, 's--', color='#E94F37', linewidth=2, markersize=6,
                    label='Expected')
            
            ax2.set_xlabel('Delay (ms)')
            ax2.set_ylabel('RTT (ms)')
            ax2.set_title('RTT vs Injected Delay')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(bottom=0)
    
    # Plot 3: UDP Loss Correlation (bottom-left)
    ax3 = fig.add_subplot(gs[1, 0])
    if loss_data:
        results = loss_data.get("results", [])
        injected = [r.get("loss_rate_percent") for r in results if r.get("loss_rate_percent") is not None]
        measured = [r.get("udp", {}).get("lost_percent", 0) for r in results]
        
        if injected:
            ax3.scatter(injected, measured, s=100, c='#2E86AB', alpha=0.8)
            max_val = max(max(injected), max(measured)) * 1.1
            ax3.plot([0, max_val], [0, max_val], '--', color='#E94F37', linewidth=2)
            ax3.set_xlabel('Injected Loss (%)')
            ax3.set_ylabel('Measured Loss (%)')
            ax3.set_title('UDP Loss: Injected vs Measured')
            ax3.grid(True, alpha=0.3)
            ax3.set_xlim(-1, max_val)
            ax3.set_ylim(-1, max_val)
    
    # Plot 4: HTTP Download Time (bottom-right)
    ax4 = fig.add_subplot(gs[1, 1])
    if http_data:
        results = http_data.get("results", [])
        
        data_1mb = {}
        for r in results:
            if r.get("file_size_mb") == 1:
                data_1mb[r.get("condition")] = r.get("avg_s", 0)
        
        if data_1mb:
            conditions = ["baseline", "loss_5pct", "delay_50ms", "combined"]
            labels = ["Baseline", "5% Loss", "50ms Delay", "Combined"]
            values = [data_1mb.get(c, 0) for c in conditions]
            
            colors = ['#2E86AB' if c == 'baseline' else '#E94F37' for c in conditions]
            ax4.bar(labels, values, color=colors, alpha=0.8)
            ax4.set_xlabel('Condition')
            ax4.set_ylabel('Download Time (s)')
            ax4.set_title('HTTP Download Time (1MB)')
            ax4.grid(True, axis='y', alpha=0.3)
            
            # Add value labels
            for i, v in enumerate(values):
                if v > 0:
                    ax4.annotate(f'{v:.2f}s', xy=(i, v), ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    # Save
    img_path = get_img_dir() / "dashboard.png"
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {img_path}")
    return img_path


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - Results Visualization          ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    if not MATPLOTLIB_AVAILABLE:
        print("\n❌ matplotlib is required for plot generation")
        print("   Install with: pip install matplotlib")
        return
    
    # Set matplotlib style
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    
    print("\n📊 Generating plots...")
    
    plots_generated = []
    
    # Generate individual plots
    if plot_tcp_throughput_vs_loss():
        plots_generated.append("tcp_throughput_vs_loss.png")
    
    if plot_rtt_vs_delay():
        plots_generated.append("rtt_vs_delay.png")
    
    if plot_udp_loss_correlation():
        plots_generated.append("udp_loss_correlation.png")
    
    if plot_http_download_time():
        plots_generated.append("http_download_time.png")
    
    # Generate dashboard
    if plot_combined_dashboard():
        plots_generated.append("dashboard.png")
    
    # Summary
    print("\n" + "═" * 50)
    print(f"📈 Generated {len(plots_generated)} plots:")
    for plot in plots_generated:
        print(f"   • {get_img_dir() / plot}")
    
    if not plots_generated:
        print("\n⚠️  No plots generated. Make sure result files exist in:")
        print(f"   {get_results_dir()}")
        print("\n   Run the test scripts first:")
        print("   sudo python run_all.py")


if __name__ == '__main__':
    main()
