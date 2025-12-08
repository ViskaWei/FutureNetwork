#!/usr/bin/env python3
"""
Network Anomaly Evaluation - Final Figures
==========================================

Generates publication-quality figures from Mininet+netem experiments.
Experiment ID: FN-20251206-network-01

Figures:
1. TCP Throughput vs Packet Loss (Log-Scale)
2. TCP Retransmissions vs Packet Loss
3. RTT vs Injected Delay with Linear Regression
4. TCP Throughput vs Injected Delay (Log-Scale)
5. RTT Variation (mdev) vs Injected Delay
6. Bandwidth Ceiling Accuracy (Measured vs Configured)
7. HTTP Download Time Sensitivity (Optional)

Usage:
    python plot_final_figures.py

Output:
    img/fig1_tcp_throughput_vs_loss.png
    img/fig2_tcp_retransmits_vs_loss.png
    img/fig3_rtt_vs_delay_regression.png
    img/fig4_tcp_throughput_vs_delay.png
    img/fig5_rtt_mdev_vs_delay.png
    img/fig6_bandwidth_accuracy.png
    img/fig7_http_download_time.png

Author: Viska Wei
Date: 2025-12-08
"""

import os
from pathlib import Path
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def linregress(x, y):
    """Simple linear regression using numpy (scipy-free)."""
    x = np.array(x)
    y = np.array(y)
    n = len(x)
    
    # Calculate slope and intercept
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    
    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    r_value = np.sqrt(r_squared) if r_squared >= 0 else 0
    
    return slope, intercept, r_value, None, None

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 10

# Color palette
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#E94F37',    # Coral/Red
    'accent': '#A23B72',       # Purple
    'success': '#44AF69',      # Green
    'warning': '#F18F01',      # Orange
    'gray': '#6C757D'
}

# ============================================================================
# DATA
# ============================================================================

# Figure 1 & 2: Packet Loss Sweep
LOSS_RATES = [0, 1, 5, 10, 20]  # %
TCP_THROUGHPUT_LOSS = [42583.80, 6143.15, 144.69, 4.95, 0.49]  # Mbps
TCP_RETRANSMITS = [0, 54397, 6302, 591, 108]  # counts

# Figure 3, 4, 5: Delay Sweep
DELAYS = [0, 10, 25, 50, 100]  # ms
RTT_MEASURED = [0.040, 10.080, 25.083, 50.082, 100.079]  # ms
TCP_THROUGHPUT_DELAY = [42256.20, 3005.44, 668.29, 89.31, 7.64]  # Mbps
RTT_MDEV = [0.012, 0.119, 0.123, 0.126, 0.329]  # ms

# Figure 6: Bandwidth Ceiling
BW_CONFIGURED = [1, 5, 10]  # Mbps
BW_MEASURED = [1.23, 5.18, 10.05]  # Mbps

# Figure 7: HTTP Download Times
HTTP_CONDITIONS = ["baseline", "5% loss", "50ms delay", "5%+50ms"]
HTTP_DOWNLOAD_TIMES = [0.0001, 0.0001, 0.001, 0.001]  # seconds (approximate)


def get_output_dir():
    """Get output directory for figures."""
    script_dir = Path(__file__).parent
    img_dir = script_dir.parent / "img"
    img_dir.mkdir(exist_ok=True)
    return img_dir


def fig1_tcp_throughput_vs_loss():
    """
    Figure 1: TCP Throughput vs Packet Loss (Log-Scale)
    
    Line plot with markers showing TCP throughput degradation across
    injected packet loss rates. Uses log10 y-axis.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot with log scale
    ax.semilogy(LOSS_RATES, TCP_THROUGHPUT_LOSS, 'o-', 
                color=COLORS['primary'], linewidth=2.5, markersize=12,
                markerfacecolor='white', markeredgewidth=2.5)
    
    # Calculate degradation and annotate each point
    baseline = TCP_THROUGHPUT_LOSS[0]
    for i, (loss, throughput) in enumerate(zip(LOSS_RATES, TCP_THROUGHPUT_LOSS)):
        ratio = throughput / baseline
        degradation = (1 - ratio) * 100
        
        # Position annotations
        if loss == 0:
            label = f"{throughput:,.1f} Mbps\n(baseline)"
            offset = (10, 15)
        else:
            label = f"{throughput:,.2f} Mbps\n({ratio:.4f}× baseline)\n({degradation:.1f}% drop)"
            if loss <= 5:
                offset = (10, -10)
            else:
                offset = (10, 10)
        
        ax.annotate(label, xy=(loss, throughput),
                   xytext=offset, textcoords='offset points',
                   fontsize=9, ha='left',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='gray', alpha=0.9))
    
    # Formatting
    ax.set_xlabel('Injected Packet Loss Rate (%)', fontsize=12)
    ax.set_ylabel('TCP Throughput (Mbps)', fontsize=12)
    ax.set_title('TCP Throughput Degradation under Packet Loss (Mininet+netem)',
                fontsize=14, fontweight='bold')
    
    ax.set_xlim(-1, 22)
    ax.set_xticks(LOSS_RATES)
    ax.grid(True, alpha=0.4, which='both')
    ax.set_ylim(0.1, 100000)
    
    # Add note about 5 orders of magnitude
    ax.text(0.98, 0.02, 
            'Note: Y-axis spans ~5 orders of magnitude\n'
            '1% loss → 85.6% throughput drop\n'
            '5% loss → 99.7% throughput drop',
            transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig1_tcp_throughput_vs_loss.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def fig2_tcp_retransmits_vs_loss():
    """
    Figure 2: TCP Retransmissions vs Packet Loss
    
    Bar chart showing retransmission counts with throughput annotations.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(LOSS_RATES))
    bars = ax.bar(x, TCP_RETRANSMITS, color=COLORS['secondary'], 
                  edgecolor='black', linewidth=1.2, alpha=0.85)
    
    # Annotate each bar with throughput
    for i, (bar, retrans, throughput) in enumerate(zip(bars, TCP_RETRANSMITS, TCP_THROUGHPUT_LOSS)):
        height = bar.get_height()
        
        # Retransmit count label
        if retrans > 0:
            ax.annotate(f'{retrans:,}',
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 5), textcoords='offset points',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Throughput annotation (secondary)
        if throughput >= 1000:
            tp_label = f'{throughput/1000:.1f} Gbps'
        else:
            tp_label = f'{throughput:.1f} Mbps'
        
        ax.annotate(f'TCP: {tp_label}',
                   xy=(bar.get_x() + bar.get_width()/2, height + 2500),
                   ha='center', va='bottom', fontsize=9, color=COLORS['gray'],
                   style='italic')
    
    # Formatting
    ax.set_xlabel('Injected Packet Loss Rate (%)', fontsize=12)
    ax.set_ylabel('TCP Retransmissions (count)', fontsize=12)
    ax.set_title('TCP Retransmissions vs Packet Loss Rate\n'
                 '(with corresponding TCP throughput)',
                fontsize=14, fontweight='bold')
    
    ax.set_xticks(x)
    ax.set_xticklabels([f'{r}%' for r in LOSS_RATES])
    ax.grid(True, axis='y', alpha=0.4)
    ax.set_ylim(0, max(TCP_RETRANSMITS) * 1.25)
    
    # Insight annotation
    ax.text(0.98, 0.98,
            'Key insight: Retransmissions peak at 1% loss\n'
            'where sending rate is still high.\n'
            'At higher loss, throughput collapse\n'
            'limits total retransmissions.',
            transform=ax.transAxes, fontsize=9, ha='right', va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig2_tcp_retransmits_vs_loss.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def fig3_rtt_vs_delay_regression():
    """
    Figure 3: RTT vs Injected Delay with Linear Regression
    
    Scatter plot with linear regression overlay showing RTT response
    to unidirectional delay injection.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    delays = np.array(DELAYS)
    rtts = np.array(RTT_MEASURED)
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = linregress(delays, rtts)
    r_squared = r_value ** 2
    
    # Plot scatter points
    ax.scatter(delays, rtts, s=150, c=COLORS['primary'], alpha=0.9, 
              edgecolors='white', linewidths=2, zorder=5, label='Measured RTT')
    
    # Connected line
    ax.plot(delays, rtts, '--', color=COLORS['primary'], alpha=0.4, linewidth=1.5)
    
    # Regression line
    x_fit = np.linspace(-5, 110, 100)
    y_fit = slope * x_fit + intercept
    ax.plot(x_fit, y_fit, '-', color=COLORS['secondary'], linewidth=2.5,
            label=f'Linear fit: RTT = {slope:.4f}×delay + {intercept:.4f}')
    
    # Perfect y=x line for reference
    ax.plot(x_fit, x_fit, ':', color=COLORS['gray'], linewidth=1.5,
            label='Reference: y = x', alpha=0.7)
    
    # Annotate each point
    for delay, rtt in zip(delays, rtts):
        ax.annotate(f'({delay}, {rtt:.3f})',
                   xy=(delay, rtt), xytext=(5, 8),
                   textcoords='offset points', fontsize=9, color=COLORS['gray'])
    
    # Regression statistics box
    stats_text = (f'Linear Regression Results:\n'
                  f'  Slope: {slope:.6f}\n'
                  f'  Intercept: {intercept:.6f} ms\n'
                  f'  R² = {r_squared:.8f}\n\n'
                  f'Note: Delay injected unidirectionally.\n'
                  f'Near-unit slope ({slope:.4f} ≈ 1.0) confirms\n'
                  f'RTT ≈ baseline + injected_delay')
    
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes, fontsize=10, va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.95),
            family='monospace')
    
    # Formatting
    ax.set_xlabel('Injected Delay (ms)', fontsize=12)
    ax.set_ylabel('Measured RTT (ms)', fontsize=12)
    ax.set_title('RTT vs Injected Delay with Linear Regression\n'
                 '(Unidirectional delay injection via netem)',
                fontsize=14, fontweight='bold')
    
    ax.set_xlim(-5, 110)
    ax.set_ylim(-5, 110)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.4)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig3_rtt_vs_delay_regression.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def fig4_tcp_throughput_vs_delay():
    """
    Figure 4: TCP Throughput vs Injected Delay (Log-Scale)
    
    Line plot showing TCP throughput sensitivity to latency.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot with log scale
    ax.semilogy(DELAYS, TCP_THROUGHPUT_DELAY, 'o-',
                color=COLORS['accent'], linewidth=2.5, markersize=12,
                markerfacecolor='white', markeredgewidth=2.5)
    
    # Annotate each point
    for i, (delay, throughput) in enumerate(zip(DELAYS, TCP_THROUGHPUT_DELAY)):
        if throughput >= 1000:
            label = f'{throughput/1000:.1f} Gbps'
        else:
            label = f'{throughput:.1f} Mbps'
        
        if delay == 0:
            offset = (10, 10)
        elif delay <= 25:
            offset = (10, -5)
        else:
            offset = (10, 10)
        
        ax.annotate(label, xy=(delay, throughput),
                   xytext=offset, textcoords='offset points',
                   fontsize=9, ha='left',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                            edgecolor='gray', alpha=0.9))
    
    # Calculate drop factors
    baseline = TCP_THROUGHPUT_DELAY[0]
    final = TCP_THROUGHPUT_DELAY[-1]
    drop_factor = baseline / final
    
    # Add drop annotation
    ax.annotate('', xy=(100, final), xytext=(0, baseline),
               arrowprops=dict(arrowstyle='<->', color=COLORS['secondary'], 
                              lw=2, ls='--'))
    ax.text(50, np.sqrt(baseline * final), f'{drop_factor:,.0f}× drop',
            fontsize=11, ha='center', va='center', color=COLORS['secondary'],
            fontweight='bold', rotation=-35)
    
    # Formatting
    ax.set_xlabel('Injected Delay (ms)', fontsize=12)
    ax.set_ylabel('TCP Throughput (Mbps)', fontsize=12)
    ax.set_title('TCP Throughput vs Injected Delay (Mininet+netem)',
                fontsize=14, fontweight='bold')
    
    ax.set_xlim(-5, 110)
    ax.set_xticks(DELAYS)
    ax.grid(True, alpha=0.4, which='both')
    
    # Caption/note
    ax.text(0.98, 0.02,
            'TCP is highly sensitive to RTT due to:\n'
            '• Window-limited throughput (BDP)\n'
            '• ACK pacing constraints\n'
            '• Congestion control dynamics\n\n'
            f'0ms → 100ms: {drop_factor:,.0f}× throughput reduction',
            transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig4_tcp_throughput_vs_delay.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def fig5_rtt_mdev_vs_delay():
    """
    Figure 5: RTT Variation (mdev) vs Injected Delay
    
    Line plot showing ping mdev (RTT standard deviation) remains
    sub-millisecond, indicating deterministic delay behavior.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(DELAYS, RTT_MDEV, 'o-',
            color=COLORS['success'], linewidth=2.5, markersize=12,
            markerfacecolor='white', markeredgewidth=2.5)
    
    # Annotate each point
    for delay, mdev in zip(DELAYS, RTT_MDEV):
        ax.annotate(f'{mdev:.3f} ms',
                   xy=(delay, mdev), xytext=(5, 8),
                   textcoords='offset points', fontsize=9)
    
    # Horizontal reference line at 1ms
    ax.axhline(y=1.0, color=COLORS['secondary'], linestyle='--', 
               linewidth=1.5, alpha=0.7, label='1 ms reference')
    
    # Fill area to show sub-millisecond region
    ax.fill_between([-5, 110], [0, 0], [1, 1], 
                    color=COLORS['success'], alpha=0.1)
    ax.text(55, 0.5, 'Sub-millisecond region', fontsize=10, 
            ha='center', va='center', color=COLORS['success'], alpha=0.7)
    
    # Formatting
    ax.set_xlabel('Injected Delay (ms)', fontsize=12)
    ax.set_ylabel('RTT Variation / mdev (ms)', fontsize=12)
    ax.set_title('RTT Variation (mdev) vs Injected Delay',
                fontsize=14, fontweight='bold')
    
    ax.set_xlim(-5, 110)
    ax.set_xticks(DELAYS)
    ax.set_ylim(0, 0.5)
    ax.grid(True, alpha=0.4)
    ax.legend(loc='upper left')
    
    # Annotation
    ax.text(0.98, 0.98,
            'Observation: RTT variation (mdev)\n'
            'remains sub-millisecond throughout,\n'
            'indicating stable deterministic delay\n'
            'in the absence of explicit jitter injection.\n\n'
            'Max mdev: 0.329 ms @ 100ms delay',
            transform=ax.transAxes, fontsize=9, ha='right', va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig5_rtt_mdev_vs_delay.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def fig6_bandwidth_accuracy():
    """
    Figure 6: Bandwidth Ceiling Accuracy (Measured vs Configured)
    
    Scatter plot comparing configured bandwidth limits to measured throughput,
    with y=x reference line.
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    
    configured = np.array(BW_CONFIGURED)
    measured = np.array(BW_MEASURED)
    efficiency = (measured / configured) * 100
    
    # y=x reference line (dashed)
    max_val = max(max(configured), max(measured)) * 1.2
    ax.plot([0, max_val], [0, max_val], '--', color=COLORS['gray'], 
            linewidth=2, label='Perfect accuracy (y=x)', alpha=0.7)
    
    # Scatter plot
    ax.scatter(configured, measured, s=250, c=COLORS['primary'], 
              alpha=0.9, edgecolors='white', linewidths=3, zorder=5)
    
    # Annotate each point with efficiency
    for i, (cfg, meas, eff) in enumerate(zip(configured, measured, efficiency)):
        ax.annotate(f'{meas:.2f} Mbps\n({eff:.0f}% of limit)',
                   xy=(cfg, meas), xytext=(15, 0),
                   textcoords='offset points', fontsize=10, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='gray', alpha=0.9))
    
    # Formatting
    ax.set_xlabel('Configured Bandwidth Limit (Mbps)', fontsize=12)
    ax.set_ylabel('Measured TCP Throughput (Mbps)', fontsize=12)
    ax.set_title('Bandwidth Ceiling Accuracy: Measured vs Configured\n'
                 '(Mininet HTB rate limiting)',
                fontsize=14, fontweight='bold')
    
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)
    ax.set_xticks(BW_CONFIGURED + [12])
    ax.set_yticks([0, 1, 2, 5, 10, 12])
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.4)
    ax.legend(loc='upper left')
    
    # Explanation
    ax.text(0.98, 0.02,
            'Overshoot explanation:\n'
            '• Token bucket burst allowance\n'
            '• Measurement window effects\n'
            '• All within ~23% of configured\n'
            '• Accuracy improves at higher limits',
            transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig6_bandwidth_accuracy.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def fig7_http_download_time():
    """
    Figure 7 (Optional): HTTP Download Time Sensitivity
    
    Bar chart demonstrating measurement visibility limitations
    with small files on fast emulated links.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(HTTP_CONDITIONS))
    
    # Convert to milliseconds for better visibility
    times_ms = [t * 1000 for t in HTTP_DOWNLOAD_TIMES]
    
    colors = [COLORS['primary'] if c == "baseline" else COLORS['secondary'] 
              for c in HTTP_CONDITIONS]
    
    bars = ax.bar(x, times_ms, color=colors, edgecolor='black', 
                  linewidth=1.2, alpha=0.85)
    
    # Annotate bars
    for bar, time_s, time_ms in zip(bars, HTTP_DOWNLOAD_TIMES, times_ms):
        height = bar.get_height()
        if time_s < 0.001:
            label = f'<1 ms\n({time_s:.4f}s)'
        else:
            label = f'{time_ms:.1f} ms\n({time_s:.3f}s)'
        
        ax.annotate(label,
                   xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 5), textcoords='offset points',
                   ha='center', va='bottom', fontsize=10)
    
    # Formatting
    ax.set_xlabel('Network Condition', fontsize=12)
    ax.set_ylabel('HTTP Download Time (ms)', fontsize=12)
    ax.set_title('HTTP Download Time Sensitivity\n'
                 '(Measurement Visibility Demonstration)',
                fontsize=14, fontweight='bold')
    
    ax.set_xticks(x)
    ax.set_xticklabels(HTTP_CONDITIONS)
    ax.grid(True, axis='y', alpha=0.4)
    ax.set_ylim(0, max(times_ms) * 1.5)
    
    # Warning/explanation
    ax.text(0.98, 0.98,
            '⚠️ Measurement Limitation:\n\n'
            'Small files on very fast emulated links\n'
            'compress timing differences below\n'
            'measurement resolution.\n\n'
            'Recommendation:\n'
            '• Use larger test objects (10MB+)\n'
            '• Apply bandwidth ceilings\n'
            '• Multiple iterations for statistics',
            transform=ax.transAxes, fontsize=9, ha='right', va='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', 
                     edgecolor=COLORS['warning'], linewidth=2, alpha=0.95))
    
    plt.tight_layout()
    
    output_path = get_output_dir() / "fig7_http_download_time.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def create_combined_figure():
    """
    Create a combined 2x3 figure with the key plots.
    """
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle('Network Anomaly Evaluation Summary\n'
                 'Experiment: FN-20251206-network-01 (Mininet+netem)',
                 fontsize=16, fontweight='bold')
    
    # 2x3 layout
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. TCP Throughput vs Loss (log)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.semilogy(LOSS_RATES, TCP_THROUGHPUT_LOSS, 'o-', 
                color=COLORS['primary'], linewidth=2, markersize=8)
    ax1.set_xlabel('Packet Loss (%)')
    ax1.set_ylabel('TCP Throughput (Mbps)')
    ax1.set_title('(a) TCP Throughput vs Packet Loss')
    ax1.grid(True, alpha=0.4, which='both')
    ax1.set_xticks(LOSS_RATES)
    
    # 2. Retransmits vs Loss
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(LOSS_RATES, TCP_RETRANSMITS, color=COLORS['secondary'], 
            edgecolor='black', width=3)
    ax2.set_xlabel('Packet Loss (%)')
    ax2.set_ylabel('Retransmissions')
    ax2.set_title('(b) TCP Retransmissions vs Packet Loss')
    ax2.grid(True, axis='y', alpha=0.4)
    
    # 3. RTT vs Delay (regression)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.scatter(DELAYS, RTT_MEASURED, s=100, c=COLORS['primary'])
    ax3.plot([0, 100], [0, 100], '--', color=COLORS['secondary'], 
             label='y=x reference')
    slope, intercept, r_value, _, _ = linregress(DELAYS, RTT_MEASURED)
    ax3.plot(DELAYS, [slope*d + intercept for d in DELAYS], '-', 
             color=COLORS['success'], linewidth=2, label=f'Fit (R²={r_value**2:.4f})')
    ax3.set_xlabel('Injected Delay (ms)')
    ax3.set_ylabel('Measured RTT (ms)')
    ax3.set_title('(c) RTT vs Injected Delay')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.4)
    
    # 4. TCP Throughput vs Delay (log)
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.semilogy(DELAYS, TCP_THROUGHPUT_DELAY, 'o-', 
                color=COLORS['accent'], linewidth=2, markersize=8)
    ax4.set_xlabel('Injected Delay (ms)')
    ax4.set_ylabel('TCP Throughput (Mbps)')
    ax4.set_title('(d) TCP Throughput vs Delay')
    ax4.grid(True, alpha=0.4, which='both')
    ax4.set_xticks(DELAYS)
    
    # 5. RTT mdev vs Delay
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.plot(DELAYS, RTT_MDEV, 'o-', color=COLORS['success'], 
             linewidth=2, markersize=8)
    ax5.axhline(y=1.0, color=COLORS['secondary'], linestyle='--', 
                alpha=0.5, label='1ms reference')
    ax5.set_xlabel('Injected Delay (ms)')
    ax5.set_ylabel('RTT mdev (ms)')
    ax5.set_title('(e) RTT Variation vs Delay')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.4)
    ax5.set_ylim(0, 0.5)
    
    # 6. Bandwidth Accuracy
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.scatter(BW_CONFIGURED, BW_MEASURED, s=150, c=COLORS['primary'])
    ax6.plot([0, 12], [0, 12], '--', color=COLORS['gray'], label='y=x')
    ax6.set_xlabel('Configured BW (Mbps)')
    ax6.set_ylabel('Measured BW (Mbps)')
    ax6.set_title('(f) Bandwidth Ceiling Accuracy')
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.4)
    ax6.set_xlim(0, 12)
    ax6.set_ylim(0, 12)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    output_path = get_output_dir() / "fig_combined_summary.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {output_path}")
    return output_path


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Network Anomaly Evaluation - Final Figures                  ║
║   Experiment ID: FN-20251206-network-01                       ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    output_dir = get_output_dir()
    print(f"📁 Output directory: {output_dir}\n")
    print("📊 Generating figures...\n")
    
    figures = []
    
    # Generate all individual figures
    figures.append(fig1_tcp_throughput_vs_loss())
    figures.append(fig2_tcp_retransmits_vs_loss())
    figures.append(fig3_rtt_vs_delay_regression())
    figures.append(fig4_tcp_throughput_vs_delay())
    figures.append(fig5_rtt_mdev_vs_delay())
    figures.append(fig6_bandwidth_accuracy())
    figures.append(fig7_http_download_time())
    
    # Generate combined summary
    figures.append(create_combined_figure())
    
    # Summary
    print("\n" + "═" * 60)
    print(f"📈 Generated {len(figures)} figures:")
    for fig_path in figures:
        print(f"   • {fig_path.name}")
    print("═" * 60)
    
    print("\n✅ All figures generated successfully!")
    print(f"   View at: {output_dir}")


if __name__ == '__main__':
    main()
