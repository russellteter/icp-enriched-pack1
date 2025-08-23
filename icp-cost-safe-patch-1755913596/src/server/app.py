from fastapi import FastAPI
from pydantic import BaseModel
from src.flows.healthcare_flow import app_graph, HCState

class RunBody(BaseModel):
    segment: str
    targetcount: int = 50
    mode: str = "fast"
    region: str = "both"

app = FastAPI()

@app.post("/run")
def run(body: RunBody):
    if body.segment not in ["healthcare","corporate","provider"]:
        return {"error":"Unsupported segment"}
    # v1: healthcare only
    state = HCState(targetcount=body.targetcount, region=body.region, mode=body.mode)
    result = app_graph.invoke(state)
    return {
        "segment": body.segment,
        "count": len(result.outputs),
        "outputs": result.outputs,
        "budget": result.budget_snapshot,
        "summary": result.summary,
        "message": "OK"
    }
