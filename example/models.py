import typing as t

from pydantic import BaseModel


class Task(BaseModel):
    title: str
    completed: bool


class Example(BaseModel):
    text: str
    translation: str


class Word(BaseModel):
    text: str
    meaning: str
    synonyms: t.Set[str]
    antonyms: t.Set[str]
    examples: t.List[Example]


class GrammarRule(BaseModel):
    text: str
    explanation: str
    examples: t.List[Example]
