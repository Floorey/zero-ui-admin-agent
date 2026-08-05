import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agent_frontend.mcp_connectors import FigmaMCPConnector, CanvaMCPConnector
from agent_frontend.layout_engine import HomepageLayoutEngine, HomepageLayoutConfig

class SubagentTaskRequest(BaseModel):
    task_id: str
    cluster_name: str
    theme: str
    figma_file_key: str

class SubagentTaskResponse(BaseModel):
    subagent_id: str
    subagent_role: str
    task_id: str
    status: str
    mcp_servers_used: List[str]
    figma_tokens_count: int
    canva_assets_count: int
    rendered_html: str

class DesignLayoutSubagent:
    """
    Subagent #2: Specialized Design & Layout Subagent.
    Responsible for executing figma-mcp and canva-mcp-server asset generation and HTML rendering.
    """
    def __init__(self, subagent_id: Optional[str] = None):
        self.subagent_id = subagent_id or f"subagent_design_{str(uuid.uuid4())[:8]}"
        self.role = "Design & MCP Asset Generator Subagent"
        self.figma_mcp = FigmaMCPConnector()
        self.canva_mcp = CanvaMCPConnector()
        self.layout_engine = HomepageLayoutEngine()

    async def run_task(self, req: SubagentTaskRequest) -> SubagentTaskResponse:
        figma_data = await self.figma_mcp.fetch_design_system(req.figma_file_key)
        canva_data = await self.canva_mcp.generate_homepage_assets(req.cluster_name)
        state = self.layout_engine.get_default_k8s_state()
        
        config = HomepageLayoutConfig(
            title=f"{req.cluster_name} — Control Center",
            theme=req.theme,
            cluster_name=req.cluster_name,
            hero_title="Autonomous Kubernetes UI & Subagent Orchestrator",
            hero_description="Real-time cluster topology, pod health mesh, and dynamic design assets synchronized via Figma MCP & Canva MCP Subagent.",
            figma_file_key=req.figma_file_key,
            canva_asset_ids=[a["id"] for a in canva_data.get("assets", [])],
            nodes=state["nodes"],
            pods=state["pods"]
        )
        
        html_output = self.layout_engine.render_html_homepage(config, figma_data, canva_data)
        
        return SubagentTaskResponse(
            subagent_id=self.subagent_id,
            subagent_role=self.role,
            task_id=req.task_id,
            status="COMPLETED",
            mcp_servers_used=["figma-mcp", "canva-mcp-server"],
            figma_tokens_count=len(figma_data.get("tokens", [])),
            canva_assets_count=len(canva_data.get("assets", [])),
            rendered_html=html_output
        )
