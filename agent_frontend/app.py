import os
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agent_frontend.main_agent import MainOrchestratorAgent, MainAgentRequest

app = FastAPI(
    title="Kubernetes Main Agent & Multi-Subagent Architecture API",
    description="Main Agent #1 (Orchestrator) delegating tasks to Subagent #2 (Design) and Subagent #3 (Docs)",
    version="3.0.0"
)

main_agent = MainOrchestratorAgent()

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "UP",
        "service": "main-orchestrator-agent",
        "main_agent_id": main_agent.agent_id,
        "subagent_design_id": main_agent.design_subagent.subagent_id,
        "subagent_docs_id": main_agent.docs_subagent.subagent_id,
        "mcp_integrations": ["figma-mcp", "canva-mcp-server"],
        "oauth_providers": ["google", "figma", "canva"]
    }

@app.get("/api/auth/login/{provider}")
async def oauth_login(provider: str):
    try:
        url_info = main_agent.auth_service.generate_auth_url(provider)
        return JSONResponse(content=url_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/callback/{provider}")
async def oauth_callback(provider: str, code: str = "mock-code", state: str = "mock-state"):
    try:
        if state not in main_agent.auth_service.pending_states:
            main_agent.auth_service.pending_states[state] = provider
        session = main_agent.auth_service.process_callback(provider, code, state)
        return JSONResponse(content={"status": "authenticated", "session": session.model_dump()})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/agent/generate")
async def generate_homepage(req: MainAgentRequest):
    res = await main_agent.process_user_request(req)
    return JSONResponse(content=res.model_dump())

@app.get("/", response_class=HTMLResponse)
async def serve_homepage(cluster: str = "k8s-prod-cluster-01"):
    req = MainAgentRequest(cluster_name=cluster)
    res = await main_agent.process_user_request(req)
    return HTMLResponse(content=res.rendered_html)
