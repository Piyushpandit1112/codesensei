"""Pydantic schemas for LLM-generated structured content."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --- Solution --------------------------------------------------------------
class ComplexityNote(BaseModel):
    big_o: str
    why: str


class CodeBundle(BaseModel):
    python: str = ""
    java: str = ""
    cpp: str = ""


class Alternative(BaseModel):
    name: str
    big_o: str = ""
    tradeoff: str = ""


class SimilarProblem(BaseModel):
    title: str
    difficulty: str = ""
    why: str = ""
    url: str = ""


class Resource(BaseModel):
    title: str
    url: str = ""
    source: str = ""      # channel name / website
    why: str = ""


class Solution(BaseModel):
    approach_name: str
    intuition: str
    steps: list[str] = Field(default_factory=list)
    code: CodeBundle = Field(default_factory=CodeBundle)
    dry_run: list[str] = Field(default_factory=list)
    time_complexity: ComplexityNote
    space_complexity: ComplexityNote
    pitfalls: list[str] = Field(default_factory=list)
    alternatives: list[Alternative] = Field(default_factory=list)
    # Interview prep additions
    companies: list[str] = Field(default_factory=list)
    similar_problems: list[SimilarProblem] = Field(default_factory=list)
    interview_tips: list[str] = Field(default_factory=list)
    followups: list[str] = Field(default_factory=list)
    # Learning resources
    youtube_recommendations: list[Resource] = Field(default_factory=list)
    articles: list[Resource] = Field(default_factory=list)


# --- Animation -------------------------------------------------------------
class Frame(BaseModel):
    id: int
    state_patch: dict[str, Any] = Field(default_factory=dict)
    # highlights: indices (int) for array-like, or node IDs (str) for tree/graph/recursion
    highlights: list[Any] = Field(default_factory=list)
    # pointers: named labels → index / node-id / [row,col] / code-line, etc.
    pointers: dict[str, Any] = Field(default_factory=dict)
    annotation_en: str = ""
    annotation_hi: str = ""
    duration_ms: int = 1800


class FrameScript(BaseModel):
    template: str = "array"       # v0 supports array only
    initial_state: dict[str, Any] = Field(default_factory=dict)
    frames: list[Frame] = Field(default_factory=list)


# --- Classification --------------------------------------------------------
class Example(BaseModel):
    input: str = ""
    output: str = ""
    explanation: str = ""


class ProblemMeta(BaseModel):
    title: str = ""
    topic: str = ""
    difficulty: str = ""
    # A short hint about which DS best visualises the problem.
    # One of: array, linked_list, tree, graph, grid, stack, queue,
    # hashmap, dp_table, string, heap, generic.
    template_hint: str = "array"
    description: str = ""                       # cleaned, concise problem statement
    examples: list[Example] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
