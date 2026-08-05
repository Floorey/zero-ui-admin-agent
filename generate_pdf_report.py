import os
import sys
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)

def create_charts(chart_dir):
    os.makedirs(chart_dir, exist_ok=True)
    chart_path = os.path.join(chart_dir, "cache_latency_chart.png")
    
    buffers = ["8 KB (L1)", "16 KB (L1)", "32 KB (L1)", "64 KB (L2)", "256 KB (L2)", "1 MB (L2)", "16 MB (L3)", "64 MB (DRAM)"]
    cycles_debug = [16, 14, 11, 12, 11, 14, 25, 45]  
    cycles_o3_pc = [4.16, 3.84, 3.33, 11.73, 11.75, 30.56, 61.16, 623.23] 

    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=300)
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    
    x = np.arange(len(buffers))
    width = 0.35

    rects1 = ax.bar(x - width/2, cycles_debug, width, label='Debug -O0 (Baseline Noise)', color='#e55353', alpha=0.85)
    rects2 = ax.bar(x + width/2, cycles_o3_pc, width, label='Real Hardware (O3 Pointer Chasing)', color='#2eb85c', alpha=0.85)

    ax.set_ylabel('Access Latency (CPU Cycles)', color='#c5c6c7', fontsize=9, fontweight='bold')
    ax.set_title('AMD Ryzen 7 7700X — Cache & Memory Latency Profile', color='#ffffff', fontsize=11, pad=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(buffers, rotation=20, color='#c5c6c7', fontsize=8.5)
    ax.tick_params(colors='#c5c6c7')
    ax.set_yscale('log')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#30363d')
    ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='#ffffff', fontsize=8.5)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    return chart_path

def generate_pdf(output_pdf_path, chart_path):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    COLOR_PRIMARY = colors.HexColor('#0b0f19')
    COLOR_ACCENT = colors.HexColor('#00f2fe')
    COLOR_TEXT = colors.HexColor('#222222')
    COLOR_MUTED = colors.HexColor('#555555')
    COLOR_BOX = colors.HexColor('#f4f6f9')
    COLOR_BORDER = colors.HexColor('#d0d7de')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0b0f19'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#0077b6'),
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0b0f19'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1f2328'),
        spaceAfter=6
    )

    story = []

    # Title Banner
    story.append(Paragraph("HFT & Automated Trading Hardware Engineering Report", title_style))
    story.append(Paragraph("System Evaluation: AMD Ryzen 7 7700X, NVIDIA RTX 4070 & DDR5-6000 | Hybrid CUDA Architecture", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ACCENT, spaceAfter=12))

    # Executive Metadata Table
    meta_data = [
        [Paragraph("<b>Target System:</b> AMD Ryzen 7 7700X (Zen 4, 8C/16T, 32MB L3)", body_style), Paragraph("<b>GPU:</b> MSI GeForce RTX 4070 (12GB GDDR6X)", body_style)],
        [Paragraph("<b>Memory:</b> DDR5-6000 MHz EXPO (CL30 / UCLK:MCLK 1:1)", body_style), Paragraph("<b>OS:</b> Fedora Linux (Kernel 6.x Low-Latency)", body_style)],
        [Paragraph("<b>Primary Bottleneck:</b> CPU L3 Thrashing & Memory Bandwidth Starvation during 512MB Backtests", body_style), Paragraph("<b>Evaluation Scope:</b> Hardware Profiling & CUDA Hybrid Switch", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_BOX),
        ('BOX', (0,0), (-1,-1), 1, COLOR_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section 1: Hardware Profiling & Anomaly Analysis
    story.append(Paragraph("1. Hardware Profiling & Anomaly Diagnosis", h2_style))
    story.append(Paragraph(
        "Initial hardware benchmark logs from C++ (<code>cache_probe_latency</code>) reported counter-intuitive latency spikes for small buffer sizes (e.g., 4 KB showing 16 cycles, 8 KB showing 14 cycles, vs. 16 KB showing 11 cycles). Architectural investigation revealed three key root causes:",
        body_style
    ))

    anomaly_bullets = [
        "<b>Debug Build Overhead (-O0):</b> Executing in <code>cmake-build-debug</code> mode forces unoptimized stack frame allocations (<code>mov [rbp-8], rax</code>) on every array access, adding ~4–8 stack cycles of noise per iteration.",
        "<b>Heap Allocation Cold Cache:</b> Instantiating <code>std::vector&lt;int&gt; data(...)</code> immediately prior to <code>__rdtscp()</code> causes memory allocation and page table warming overhead for small buffers.",
        "<b>Fixed Loop Span Bug:</b> The original benchmark loop was bounded to <code>i &lt; 64</code> with stride 8, measuring only the first 2,016 bytes (~2 KB) regardless of the configured vector size parameter."
    ]
    for bullet in anomaly_bullets:
        story.append(Paragraph(f"• {bullet}", body_style))

    story.append(Spacer(1, 6))
    story.append(Image(chart_path, width=540, height=255))
    story.append(Spacer(1, 8))

    # Section 2: Re-compiled Pointer Chasing Hardware Results
    story.append(Paragraph("2. True Zen 4 Hardware Cache Hierarchy Latency", h2_style))
    story.append(Paragraph(
        "Re-compiling with <b>Pointer Chasing</b> (randomized index stride linked-list) under <code>-O3 -march=native</code> eliminated prefetcher predictions and compiler artifacts, revealing the actual hardware capabilities of the Ryzen 7 7700X:",
        body_style
    ))

    latency_table_data = [
        ["Buffer Size", "Cache Level", "Measured Latency (Cycles)", "Effective Latency (ns)", "HFT Allocation Guidance"],
        ["8 KB - 32 KB", "L1 Data Cache (32K/core)", "3.33 - 4.16 cycles", "~0.62 - 0.77 ns", "Ultra-hot OrderBook Ring-Buffers & Execution Loops"],
        ["64 KB - 512 KB", "L2 Cache (1MB/core)", "11.73 - 11.75 cycles", "~2.17 ns", "Active Tick Windows & Recent Order Maps"],
        ["1024 KB (1 MB)", "L2 Top Boundary", "30.56 cycles", "~5.65 ns", "Maximum budget for single-thread core working set"],
        ["16 MB - 32 MB", "L3 Shared Cache (32MB)", "61.16 - 363.14 cycles", "~11.3 - 67.2 ns", "Multi-core shared data structures (Inter-thread communication)"],
        ["64 MB+", "DDR5-6000 RAM (EXPO)", "623.23 cycles", "~115.0 ns", "Exceeds L3 capacity! Thrashes CPU cache lines!"]
    ]
    lat_table = Table(latency_table_data, colWidths=[75, 95, 110, 95, 165])
    lat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0b0f19')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, COLOR_BOX])
    ]))
    story.append(lat_table)
    story.append(Spacer(1, 10))

    # Page Break for Architectural Design
    story.append(PageBreak())

    # Section 3: The 512 MB Backtesting Bottleneck & CUDA Switch
    story.append(Paragraph("3. Bottleneck Analysis: CPU Backtesting vs. CUDA Switch", h2_style))
    story.append(Paragraph(
        "The system bottleneck occurs when running <b>2x 256 MB (512 MB) backtesting simulations</b> in parallel via Go goroutines. Because 512 MB is <b>16x larger than the Ryzen 7700X 32MB L3 cache</b>, execution is constrained by dual-channel DDR5 bandwidth (~55-65 GB/s) and completely evicts the live HFT order book from CPU L1/L2/L3 caches.",
        body_style
    ))

    dispatch_data = [
        ["Architectural Dimension", "CPU-Only Execution (Ryzen 7700X)", "GPU Hybrid Offload (RTX 4070 CUDA)", "Performance Gain / Impact"],
        ["Compute Units", "8 Cores / 16 Threads", "5,888 CUDA Cores", "368x more execution threads"],
        ["Memory Bandwidth", "~55 - 65 GB/s (DDR5 Dual Channel)", "504 GB/s (GDDR6X VRAM)", "9.2x memory throughput acceleration"],
        ["512 MB Dataset Fit", "Exceeds 32MB L3; 100% Cache Thrashing", "Fits 100% inside 12GB VRAM", "Zero L3 eviction; zero DRAM bottleneck"],
        ["Impact on Real-time HFT", "High cache pollution & latency spikes", "Zero interference with live CPU execution", "Real-time order book stays < 1 µs"]
    ]
    disp_table = Table(dispatch_data, colWidths=[115, 135, 145, 145])
    disp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0077b6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, COLOR_BOX])
    ]))
    story.append(disp_table)
    story.append(Spacer(1, 10))

    # Section 4: Code Architecture & Implementation Blueprint
    story.append(Paragraph("4. Recommended Code Architecture Blueprint", h2_style))
    story.append(Paragraph(
        "To implement the hybrid switch without requiring a major codebase overhaul, introduce a <b>Dynamic Dispatch Offloader</b> in Go using Cgo to bridge CUDA kernel executions:",
        body_style
    ))

    cgo_code = """// Go Cgo Dynamic Offload Switch (offloader.go)
package main

/*
#cgo LDFLAGS: -L/usr/local/cuda/lib64 -lcudart
void launch_cuda_backtest(const float* ticks, float* results, int total_ticks, int num_params);
*/
import "C"
import "unsafe"

func ExecuteSimulation(ticks []float32, numParams int) []float32 {
    dataSizeMB := float64(len(ticks) * 4) / (1024 * 1024)
    results := make([]float32, numParams)

    // DYNAMIC DISPATCH SWITCH
    if dataSizeMB >= 1.0 || numParams > 1000 {
        // Route heavy backtests to RTX 4070 (504 GB/s VRAM)
        C.launch_cuda_backtest(
            (*C.float)(unsafe.Pointer(&ticks[0])),
            (*C.float)(unsafe.Pointer(&results[0])),
            C.int(len(ticks)), C.int(numParams),
        )
    } else {
        // Execute low-latency SIMD AVX-512 on CPU
        executeCPU_AVX512(ticks, results)
    }
    return results
}"""
    
    story.append(Paragraph("<font color='#0077b6'><b>Go / Cgo Dynamic Dispatch Blueprint:</b></font>", body_style))
    story.append(Paragraph(cgo_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
    story.append(Spacer(1, 10))

    # Section 5: Actionable Implementation Checklist
    story.append(Paragraph("5. Next Steps & Low-Friction Execution Checklist", h2_style))

    checklist = [
        "<b>BIOS DDR5 Configuration:</b> Verify EXPO Profile 1 is enabled and set UCLK Ratio to <code>UCLK = MCLK</code> (1:1 ratio at 3000 MHz) with FCLK at 2000 MHz.",
        "<b>Fedora Kernel Isolation:</b> Set kernel parameters <code>isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7</code> to reserve Cores 2-7 exclusively for HFT execution.",
        "<b>Lock Process C-States:</b> Run <code>cpupower frequency-set -g performance</code> and disable C-states (<code>cpupower idle-set -d 1</code>) to eliminate 15 µs wake-up delays.",
        "<b>Compile CUDA Backtest Engine:</b> Compile CUDA backtesting kernels using <code>nvcc -O3 -arch=sm_89</code> for Ada Lovelace RTX 4070 optimization.",
        "<b>Integrate Async Audit Logger:</b> Replace synchronous logging on hot paths with lock-free channel ring-buffers (<code>auditChan &lt;- event</code>)."
    ]

    for item in checklist:
        story.append(Paragraph(f"[  ] {item}", body_style))

    doc.build(story)
    print(f"PDF generated successfully at: {output_pdf_path}")

if __name__ == "__main__":
    pdf_dest_dir = "/home/lukasenderle/Dokumente/Research data"
    chart_dir = "/tmp/hft_report_charts"
    
    chart_path = create_charts(chart_dir)
    pdf_path = os.path.join(pdf_dest_dir, "HFT_Ryzen7700X_CUDA_Evaluation_Report.pdf")
    generate_pdf(pdf_path, chart_path)
