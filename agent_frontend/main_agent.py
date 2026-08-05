import os
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from agent_frontend.auth_service import AuthService
from agent_frontend.subagent_design import DesignLayoutSubagent, SubagentTaskRequest, SubagentTaskResponse
from agent_frontend.subagent_docs import DocumentationSubagent, DocGeneratorRequest, DocGeneratorResponse

class MainAgentRequest(BaseModel):
    cluster_name: str = "k8s-prod-cluster-01"
    theme: str = "dark_cyberpunk"
    figma_file_key: str = "k8s-dashboard-v2"
    auth_provider: str = "google"
    generate_docs: bool = True

class MainAgentResponse(BaseModel):
    status: str
    main_agent_id: str
    main_agent_role: str
    workspace_skills_indexed: List[str]
    subagent_design_execution: Dict[str, Any]
    subagent_docs_execution: Optional[Dict[str, Any]] = None
    oauth_providers_available: List[str]
    rendered_html: str

class MainOrchestratorAgent:
    """
    Main Agent #1: Primary Orchestrator Agent.
    Responsibilities:
    - Index workspace skills in .agents/skills.
    - Receives user requests and manages OAuth authentication (Google, Figma, Canva).
    - Spawns and delegates design tasks to Subagent #2 (DesignLayoutSubagent).
    - Spawns and delegates documentation tasks to Subagent #3 (DocumentationSubagent).
    - Aggregates subagent results and delivers final output to client.
    """
    def __init__(self, agent_id: Optional[str] = None, skills_dir: Optional[str] = None):
        self.agent_id = agent_id or f"main_agent_{str(uuid.uuid4())[:8]}"
        self.role = "Main Orchestrator Agent (Auth, Skill Discovery & Multi-Subagent Delegation)"
        self.auth_service = AuthService()
        self.design_subagent = DesignLayoutSubagent()
        self.docs_subagent = DocumentationSubagent()
        self.skills_dir = skills_dir or os.path.abspath(".agents/skills")
        self.indexed_skills: List[str] = self._discover_workspace_skills()

    def _discover_workspace_skills(self) -> List[str]:
        found_skills = []
        if os.path.exists(self.skills_dir):
            for entry in os.listdir(self.skills_dir):
                skill_path = os.path.join(self.skills_dir, entry, "SKILL.md")
                if os.path.isfile(skill_path):
                    found_skills.append(entry)
        return found_skills

    async def process_user_request(self, req: MainAgentRequest) -> MainAgentResponse:
        task_id = f"task_{str(uuid.uuid4())[:8]}"
        
        design_task = SubagentTaskRequest(
            task_id=task_id,
            cluster_name=req.cluster_name,
            theme=req.theme,
            figma_file_key=req.figma_file_key
        )
        design_res: SubagentTaskResponse = await self.design_subagent.run_task(design_task)
        
        docs_exec_dict = None
        if req.generate_docs:
            doc_task = DocGeneratorRequest(task_id=task_id, project_name=f"K8s Cluster {req.cluster_name}")
            doc_res: DocGeneratorResponse = await self.docs_subagent.run_task(doc_task)
            docs_exec_dict = {
                "subagent_id": doc_res.subagent_id,
                "subagent_role": doc_res.subagent_role,
                "task_id": doc_res.task_id,
                "status": doc_res.status,
                "docs_generated": doc_res.docs_generated
            }

        return MainAgentResponse(
            status="SUCCESS",
            main_agent_id=self.agent_id,
            main_agent_role=self.role,
            workspace_skills_indexed=self.indexed_skills,
            subagent_design_execution={
                "subagent_id": design_res.subagent_id,
                "subagent_role": design_res.subagent_role,
                "task_id": design_res.task_id,
                "status": design_res.status,
                "mcp_servers_used": design_res.mcp_servers_used,
                "figma_tokens_count": design_res.figma_tokens_count,
                "canva_assets_count": design_res.canva_assets_count
            },
            subagent_docs_execution=docs_exec_dict,
            oauth_providers_available=["google", "figma", "canva"],
            rendered_html=design_res.rendered_html
        )
