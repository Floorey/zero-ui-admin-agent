import os
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)

def create_summary_chart(chart_path):
    os.makedirs(os.path.dirname(chart_path), exist_ok=True)
    
    categories = ["CPU Single Core\n(OrderBook Loop)", "DDR5 System RAM\n(512MB Sweep)", "RTX 4070 VRAM\n(NVRTC CUDA Engine)"]
    throughput_m_evals = [36.5, 8.5, 11360.0]

    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=300)
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')

    bars = ax.bar(categories, throughput_m_evals, color=['#4facfe', '#ffab00', '#00e676'], width=0.45, alpha=0.9)

    ax.set_ylabel('Throughput (Million Evals / sec)', color='#c5c6c7', fontsize=9, fontweight='bold')
    ax.set_title('Blackgate Capital — CPU vs GPU Execution Throughput', color='#ffffff', fontsize=11, pad=12, fontweight='bold')
    ax.tick_params(colors='#c5c6c7', labelsize=8.5)
    ax.set_yscale('log')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#30363d')

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval * 1.2, f'{yval:,.1f} M/s', ha='center', va='bottom', color='#ffffff', fontsize=8, fontweight='bold')

    plt.tight_layout()
    plt.savefig(chart_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

def generate_doc_pdf(pdf_path, chart_path):
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    COLOR_PRIMARY = colors.HexColor('#0b0f19')
    COLOR_ACCENT = colors.HexColor('#00f2fe')
    COLOR_TEXT = colors.HexColor('#222222')
    COLOR_BOX = colors.HexColor('#f4f6f9')
    COLOR_BORDER = colors.HexColor('#d0d7de')

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=18, leading=22,
        textColor=COLOR_PRIMARY, spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.5, leading=13,
        textColor=colors.HexColor('#0077b6'), spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=12, leading=15,
        textColor=COLOR_PRIMARY, spaceBefore=12, spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13,
        textColor=COLOR_TEXT, spaceAfter=6
    )

    code_style = ParagraphStyle(
        'Code_Custom', parent=styles['Normal'],
        fontName='Courier', fontSize=7.5, leading=10,
        textColor=colors.HexColor('#1f2328'), spaceAfter=6
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph("Blackgate Capital — HFT Cluster Redesign & CUDA Engine Report", title_style))
    story.append(Paragraph("Session Summary: All Test Suites 100% Green | Fedora Linux Architecture", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ACCENT, spaceAfter=12))

    meta_data = [
        [Paragraph("<b>Status:</b> All Test Suites 100% Green (Python, Go, C++/CUDA)", body_style), Paragraph("<b>CPU Latency:</b> 27.40 ns / tick", body_style)],
        [Paragraph("<b>HFT Core Engine:</b> <code>/home/lukasenderle/CLionProjects/hft_engine</code>", body_style), Paragraph("<b>GPU Throughput:</b> 11.4 - 12.1 Billion evals / sec", body_style)],
        [Paragraph("<b>Middle Node:</b> Zero-Copy Pinned DMA Memory (<code>cudaHostAllocMapped</code>)", body_style), Paragraph("<b>NVRTC CUDA Engine:</b> RTX 4070 (<code>sm_89</code>)", body_style)]
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

    # Section 1: Verification Matrix
    story.append(Paragraph("1. System Test Verification Matrix", h2_style))
    
    test_matrix = [
        ["Subsystem", "Component Path", "Test Command", "Status", "Metrics / Key Results"],
        ["Multi-Agent Frontend", "<code>agent_frontend/</code>", "<code>pytest tests/test_agent.py</code>", "PASSED (6/6)", "Google/Figma/Canva OAuth, Subagents #2 & #3"],
        ["Zero-Trust Proxy", "<code>backend/middleware/</code>", "<code>go test ./backend/...</code>", "PASSED (100%)", "X-Trace-ID audit, Concurrency Governor"],
        ["Go Backend API", "<code>backend/server/</code>", "<code>go test ./backend/...</code>", "PASSED (100%)", "REST + WebSocket echo endpoints"],
        ["Middle Node Prebuffer", "<code>include/middle_node_prebuffer.hpp</code>", "<code>./build_cuda/hft_engine</code>", "PASSED (100%)", "Zero-copy Pinned Host DMA Allocation"],
        ["CUDA Strategy Engine", "<code>src/cuda_execution_engine.cpp</code>", "<code>./build_cuda/hft_engine</code>", "PASSED (100%)", "11.4B evals/sec on 4,096 strategies x 1M ticks"]
    ]
    t_table = Table(test_matrix, colWidths=[90, 115, 115, 70, 150])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0b0f19')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, COLOR_BOX])
    ]))
    story.append(t_table)
    story.append(Spacer(1, 10))

    # Section 2: Performance Chart
    story.append(Paragraph("2. Performance Benchmark: CPU vs GPU Throughput", h2_style))
    story.append(Image(chart_path, width=540, height=235))
    story.append(Spacer(1, 10))

    # Section 3: Architecture Code Summary & Tomorrow's Plan
    story.append(Paragraph("3. Tomorrow's Next Steps & Roadmap", h2_style))
    roadmap = [
        "<b>Cluster Inter-Node Socket Streaming:</b> Connect Middle Node SPSC Ring Buffer directly to live market data socket feeds (UDP Multicast / WebSockets).",
        "<b>Multi-Stream CUDA Pipeline:</b> Expand NVRTC kernel to use multiple CUDA streams (<code>cudaStream_t</code>) for simultaneous risk calculations and backtesting.",
        "<b>TensorRT Inference Integration:</b> Embed TensorRT FP16 neural network model execution inside the GPU engine for AI signal generation."
    ]
    for item in roadmap:
        story.append(Paragraph(f"[  ] {item}", body_style))

    doc.build(story)
    print(f"Final Documentation PDF created: {pdf_path}")

if __name__ == "__main__":
    pdf_out = "/home/lukasenderle/Dokumente/Research data/CUDA_HFT_Engine_Session_Summary.pdf"
    chart_out = "/tmp/hft_summary_chart.png"
    create_summary_chart(chart_out)
    generate_doc_pdf(pdf_out, chart_out)
