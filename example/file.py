import typing as t
from pathlib import Path

from example.models import GrammarRule, Task, Word
from example.sections import (
    GrammarSection,
    HeaderSection,
    TasksSection,
    WordSection,
)
from librum.files import File
from librum.sections import Section, SectionDefinition


class SpanishFile(File):
    FILE_TAG = "spanish_file"
    SECTION_DEFINITIONS = [
        SectionDefinition(HeaderSection),
        SectionDefinition(TasksSection, optional=True),
        SectionDefinition(WordSection, ordered=False, count=-1),
        SectionDefinition(GrammarSection, ordered=False, count=-1),
    ]

    tasks: t.List[Task]
    words: t.List[Word]
    grammar_rules: t.List[GrammarRule]

    def __init__(self, path: Path):
        super().__init__(path)
        self.words = []
        self.grammar_rules = []

    def on_match(self, section: Section):
        if isinstance(section, TasksSection):
            self.tasks = section.tasks
        elif isinstance(section, WordSection):
            self.words.append(section.word)
        elif isinstance(section, GrammarSection):
            self.grammar_rules.append(section.grammar_rule)

    def on_complete(self):
        # Perform extra validation
        # or create other objects based on the parsed sections
        ...
