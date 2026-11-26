from typing import Literal
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(min_length=3,max_length=120)
    account: str = Field(min_length=1,max_length=64)
    notes: str = Field(default="",max_length=4000)
    evidence: list[str] = Field(default_factory=list,max_length=100)


class CaseUpdate(BaseModel):
    status: Literal["Open","In review","Closed"]
    notes: str = Field(default="",max_length=4000)
    evidence: list[str] = Field(default_factory=list,max_length=100)
    revision: int = Field(ge=1)

