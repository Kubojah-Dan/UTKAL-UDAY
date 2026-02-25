from typing import Dict, List, Optional

from pydantic import BaseModel, Field

class InteractionIn(BaseModel):
    quest_id: str
    interaction_id: Optional[str] = None
    problem_id: Optional[str] = None
    timestamp: int
    outcome: bool
    time_ms: Optional[int] = 0
    hints: Optional[int] = 0
    path_steps: Optional[int] = 0
    steps_json: Optional[str] = None
    skill_id: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[int] = None
    school: Optional[str] = None
    class_grade: Optional[int] = None
    xp_awarded: Optional[int] = 0

class SyncPayload(BaseModel):
    student_id: str
    device_info: Dict = Field(default_factory=dict)
    interactions: List[InteractionIn]
