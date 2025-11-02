from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Task(BaseModel):
    id: str
    tool_calls: List[str] = []

class Gate(BaseModel):
    type: Optional[str] = None
    approver: Optional[str] = None
    tools: List[str] = []

class Phase(BaseModel):
    id: str
    entry_prompt: str
    outputs: List[str] = []
    tasks: List[Task] = []
    gate: Optional[Gate] = None
    transitions: Dict[str, str] = {}

class Project(BaseModel):
    id: str
    goal: str
    context: Dict[str, Any] = {}

class Blueprint(BaseModel):
    version: int = Field(1)
    project: Project
    phases: List[Phase]
