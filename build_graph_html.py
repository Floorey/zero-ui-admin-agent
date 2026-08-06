#!/usr/bin/env python3
import json
import os

graph_path = "graphify-out/graph.json"
html_out_path = "graphify-out/graph.html"

if not os.path.exists(graph_path):
    print("graph.json not found")
    exit(1)

with open(graph_path, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data.get("nodes", [])
edges = data.get("edges", [])

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Graphify - Interactive Knowledge Graph Network</title>
    <script src="https://unpkg.com/force-graph"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}
        #header {{
            position: absolute;
            top: 15px;
            left: 20px;
            z-index: 10;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            padding: 12px 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        h1 {{
            margin: 0 0 5px 0;
            font-size: 1.2rem;
            color: #38bdf8;
        }}
        p {{
            margin: 0;
            font-size: 0.85rem;
            color: #94a3b8;
        }}
        #graph {{
            width: 100vw;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🌌 Graphify Knowledge Graph</h1>
        <p><b>{len(nodes)}</b> Nodes · <b>{len(edges)}</b> Edges | Drag, scroll to zoom, click to inspect</p>
    </div>
    <div id="graph"></div>

    <script>
        const graphData = {json.dumps({"nodes": nodes, "links": edges})};

        const Graph = ForceGraph()
            (document.getElementById('graph'))
            .graphData(graphData)
            .nodeId('id')
            .nodeLabel(node => `<b>${{node.id}}</b><br/>Type: ${{node.type || 'Symbol'}}`)
            .nodeColor(node => node.type === 'file' ? '#38bdf8' : node.type === 'function' ? '#4ade80' : '#c084fc')
            .nodeRelSize(6)
            .linkSource('source')
            .linkTarget('target')
            .linkLabel(link => link.relation || 'relates_to')
            .directionalParticles(2)
            .directionalParticleSpeed(0.005)
            .linkColor(() => '#334155')
            .backgroundColor('#0b0f19');
    </script>
</body>
</html>
"""

with open(html_out_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✔ Interactive HTML network graph generated: {html_out_path}")
