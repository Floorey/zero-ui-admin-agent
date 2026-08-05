import pytest
import asyncio
from agent_frontend.auth_service import AuthService
from agent_frontend.mcp_connectors import FigmaMCPConnector, CanvaMCPConnector
from agent_frontend.subagent_design import DesignLayoutSubagent, SubagentTaskRequest
from agent_frontend.subagent_docs import DocumentationSubagent, DocGeneratorRequest
from agent_frontend.main_agent import MainOrchestratorAgent, MainAgentRequest

@pytest.mark.asyncio
async def test_auth_service():
    auth = AuthService()
    info = auth.generate_auth_url("google")
    assert info["provider"] == "google"
    assert "accounts.google.com" in info["auth_url"]
    
    session = auth.process_callback("google", "code123", info["state"])
    assert session.provider == "google"
    assert session.access_token.startswith("tok_")

@pytest.mark.asyncio
async def test_figma_mcp():
    figma = FigmaMCPConnector()
    res = await figma.fetch_design_system("test-key")
    assert res["status"] == "connected"
    assert len(res["tokens"]) > 0
    assert len(res["frames"]) > 0

@pytest.mark.asyncio
async def test_canva_mcp():
    canva = CanvaMCPConnector()
    res = await canva.generate_homepage_assets("k8s-test-cluster")
    assert res["status"] == "connected"
    assert len(res["assets"]) > 0

@pytest.mark.asyncio
async def test_subagent_design_execution():
    subagent = DesignLayoutSubagent()
    task = SubagentTaskRequest(
        task_id="task_sub_101",
        cluster_name="k8s-subagent-cluster",
        theme="dark_cyberpunk",
        figma_file_key="k8s-figma-key"
    )
    res = await subagent.run_task(task)
    assert res.status == "COMPLETED"
    assert "figma-mcp" in res.mcp_servers_used
    assert "canva-mcp-server" in res.mcp_servers_used
    assert "<!DOCTYPE html>" in res.rendered_html

@pytest.mark.asyncio
async def test_subagent_docs_execution():
    docs_subagent = DocumentationSubagent()
    task = DocGeneratorRequest(task_id="task_doc_202", project_name="Test Cluster")
    res = await docs_subagent.run_task(task)
    assert res.status == "COMPLETED"
    assert "SYSTEM_ARCHITECTURE.md" in res.docs_generated
    assert "API_REFERENCE.md" in res.docs_generated
    assert "K8S_RUNBOOK.md" in res.docs_generated
    assert "# Test Cluster — System Architecture" in res.architecture_md

@pytest.mark.asyncio
async def test_main_agent_multi_subagent_orchestration():
    main_agent = MainOrchestratorAgent()
    req = MainAgentRequest(cluster_name="gke-main-cluster", theme="glassmorphism", generate_docs=True)
    res = await main_agent.process_user_request(req)
    assert res.status == "SUCCESS"
    assert res.main_agent_id.startswith("main_agent_")
    assert res.subagent_design_execution["subagent_id"].startswith("subagent_design_")
    assert res.subagent_docs_execution["subagent_id"].startswith("subagent_docs_")
    assert res.subagent_docs_execution["status"] == "COMPLETED"
    assert "k8s-cluster-ops" in res.workspace_skills_indexed
    assert "design-system-mcp" in res.workspace_skills_indexed
    assert "zero-trust-proxy" in res.workspace_skills_indexed
    assert "google" in res.oauth_providers_available
    assert "<!DOCTYPE html>" in res.rendered_html
