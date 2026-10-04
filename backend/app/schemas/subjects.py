from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    subject_name: str = Field(min_length=1, max_length=100)
    difficulty: int = Field(ge=1, le=5)
    priority: int = Field(ge=1, le=5)


class SubjectResponse(BaseModel):
    subject_id: str
    subject_name: str
    difficulty: int
    priority: int


class SubjectListResponse(BaseModel):
    subjects: list[SubjectResponse]
