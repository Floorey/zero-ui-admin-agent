import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ClusterNode(BaseModel):
    name: str
    role: str
    status: str
    cpu_usage: str
    mem_usage: str
    pod_count: int

class PodStatus(BaseModel):
    name: str
    namespace: str
    status: str
    restarts: int
    uptime: str

class HomepageLayoutConfig(BaseModel):
    title: str
    theme: str
    cluster_name: str
    hero_title: str
    hero_description: str
    figma_file_key: str
    canva_asset_ids: List[str]
    nodes: List[ClusterNode]
    pods: List[PodStatus]

class HomepageLayoutEngine:
    def __init__(self):
        pass

    def get_default_k8s_state(self) -> Dict[str, Any]:
        nodes = [
            ClusterNode(name="k8s-node-01-master", role="control-plane", status="Ready", cpu_usage="18%", mem_usage="42%", pod_count=14),
            ClusterNode(name="k8s-node-02-worker", role="worker", status="Ready", cpu_usage="34%", mem_usage="58%", pod_count=28),
            ClusterNode(name="k8s-node-03-worker", role="worker", status="Ready", cpu_usage="29%", mem_usage="51%", pod_count=26),
        ]
        pods = [
            PodStatus(name="proxy-zero-trust-7d8b5c9f-x82m", namespace="ingress-system", status="Running", restarts=0, uptime="14d 6h"),
            PodStatus(name="backend-server-6a4f128c-k91p", namespace="default", status="Running", restarts=0, uptime="14d 6h"),
            PodStatus(name="postgres-db-0", namespace="database", status="Running", restarts=0, uptime="30d 12h"),
            PodStatus(name="frontend-agent-5c91a0b1-m44z", namespace="agent-system", status="Running", restarts=0, uptime="2d 4h"),
        ]
        return {"nodes": nodes, "pods": pods}

    def render_html_homepage(
        self,
        config: HomepageLayoutConfig,
        figma_data: Dict[str, Any],
        canva_data: Dict[str, Any]
    ) -> str:
        tokens_map = {t["name"]: t["value"] for t in figma_data.get("tokens", [])}
        bg_color = tokens_map.get("k8s-bg-dark", "#0b0f19")
        card_bg = tokens_map.get("k8s-surface-card", "rgba(18, 26, 43, 0.75)")
        cyan_accent = tokens_map.get("k8s-accent-cyan", "#00f2fe")
        
        assets = canva_data.get("assets", [])
        hero_img = assets[0]["thumbnail_url"] if len(assets) > 0 else "/content/canva_k8s_hero.png"
        pdf_url = assets[0]["download_pdf_url"] if len(assets) > 0 else "/content/k8s_cluster_architecture.pdf"

        node_rows_html = "".join([
            f"""
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 1rem; font-weight: 500;">{node.name}</td>
                <td style="padding: 1rem;"><span style="background: rgba(0, 242, 254, 0.1); color: {cyan_accent}; padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem;">{node.role}</span></td>
                <td style="padding: 1rem;"><span style="color: #00e676;">● {node.status}</span></td>
                <td style="padding: 1rem;">{node.cpu_usage}</td>
                <td style="padding: 1rem;">{node.mem_usage}</td>
                <td style="padding: 1rem;">{node.pod_count}</td>
            </tr>
            """
            for node in config.nodes
        ])

        pod_cards_html = "".join([
            f"""
            <div style="background: {card_bg}; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 1.5rem; backdrop-filter: blur(10px);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #9e9992;">{pod.namespace}</span>
                    <span style="background: rgba(0, 230, 118, 0.15); color: #00e676; padding: 0.2rem 0.5rem; border-radius: 20px; font-size: 0.75rem;">{pod.status}</span>
                </div>
                <h4 style="font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem; word-break: break-all;">{pod.name}</h4>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #9e9992;">
                    <span>Restarts: {pod.restarts}</span>
                    <span>Uptime: {pod.uptime}</span>
                </div>
            </div>
            """
            for pod in config.pods
        ])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.title} — Kubernetes Cluster Control</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: {bg_color};
            color: #f2eee9;
            font-family: 'Outfit', sans-serif;
            line-height: 1.6;
            background-image: 
                radial-gradient(circle at 20% 10%, rgba(0, 242, 254, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 80% 90%, rgba(79, 172, 254, 0.05) 0%, transparent 50%);
            min-height: 100vh;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 4rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(11, 15, 25, 0.8);
        }}
        .logo {{ font-size: 1.4rem; font-weight: 700; letter-spacing: 0.1em; color: #fff; text-decoration: none; }}
        .logo span {{ color: {cyan_accent}; }}
        nav a {{
            color: #9e9992;
            text-decoration: none;
            margin-left: 2rem;
            font-size: 0.9rem;
            font-weight: 400;
            transition: color 0.3s;
        }}
        nav a:hover {{ color: {cyan_accent}; }}
        .hero {{
            padding: 5rem 4rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .hero-badge {{
            display: inline-block;
            padding: 0.3rem 1rem;
            background: rgba(0, 242, 254, 0.1);
            border: 1px solid rgba(0, 242, 254, 0.2);
            color: {cyan_accent};
            border-radius: 20px;
            font-size: 0.8rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 1.5rem;
        }}
        .hero-title {{
            font-size: 3.5rem;
            font-weight: 700;
            line-height: 1.15;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #ffffff 0%, #a5f3fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .hero-desc {{ font-size: 1.1rem; color: #9e9992; margin-bottom: 2rem; }}
        .btn {{
            display: inline-block;
            padding: 0.9rem 2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            color: #0b0f19;
            box-shadow: 0 4px 20px rgba(0, 242, 254, 0.3);
        }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 6px 25px rgba(0, 242, 254, 0.4); }}
        .btn-secondary {{
            background: transparent;
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.15);
            margin-left: 1rem;
        }}
        .btn-secondary:hover {{ border-color: {cyan_accent}; color: {cyan_accent}; }}
        .hero-preview {{
            background: {card_bg};
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        .hero-preview img {{ width: 100%; border-radius: 12px; display: block; }}
        .section {{ padding: 4rem; max-width: 1400px; margin: 0 auto; }}
        .section-title {{ font-size: 2rem; font-weight: 600; margin-bottom: 2rem; border-left: 4px solid {cyan_accent}; padding-left: 1rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        table {{ width: 100%; border-collapse: collapse; background: {card_bg}; border-radius: 12px; overflow: hidden; }}
        th {{ background: rgba(255,255,255,0.03); padding: 1rem; text-align: left; font-size: 0.85rem; color: #9e9992; text-transform: uppercase; }}
        footer {{ text-align: center; padding: 3rem; border-top: 1px solid rgba(255,255,255,0.05); color: #9e9992; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <header>
        <a href="#" class="logo">K8S<span>.AGENT</span></a>
        <nav>
            <a href="#nodes">Cluster Nodes</a>
            <a href="#pods">Active Pods</a>
            <a href="{pdf_url}" target="_blank">Canva Architecture PDF</a>
            <a href="/api/v1/health">Proxy Health</a>
            <a href="/api/auth/login/google">Login</a>
        </nav>
    </header>

    <main>
        <section class="hero">
            <div>
                <span class="hero-badge">Cluster Orchestrator • {config.cluster_name}</span>
                <h1 class="hero-title">{config.hero_title}</h1>
                <p class="hero-desc">{config.hero_description}</p>
                <div>
                    <a href="#pods" class="btn btn-primary">Inspect Pod Health</a>
                    <a href="{pdf_url}" target="_blank" class="btn btn-secondary">Export Canva Report</a>
                </div>
            </div>
            <div class="hero-preview">
                <img src="{hero_img}" alt="Canva Generated Hero Banner" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80';">
            </div>
        </section>

        <section id="nodes" class="section">
            <h2 class="section-title">Node Topology & Capacity</h2>
            <table>
                <thead>
                    <tr>
                        <th>Node Name</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>CPU Alloc</th>
                        <th>Mem Alloc</th>
                        <th>Active Pods</th>
                    </tr>
                </thead>
                <tbody>
                    {node_rows_html}
                </tbody>
            </table>
        </section>

        <section id="pods" class="section">
            <h2 class="section-title">Microservice Pod Mesh</h2>
            <div class="grid">
                {pod_cards_html}
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 KUBERNETES FRONTEND AGENT. FIGMA-MCP & CANVA-MCP-SERVER INTEGRATED.</p>
    </footer>
</body>
</html>
"""
