from pathlib import Path
import typing as t

from librum.files import File
from librum.sections import Section, SectionDefinition

from example.models import Task, Word, GrammarRule
from example.sections import (
    HeaderSection,
    TasksSection,
    WordSection,
    GrammarSection,
)


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
