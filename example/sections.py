import re
import typing as t

from example.models import Example, GrammarRule, Task, Word
from librum.patterns import (
    RE_ANY_TEXT_EXCEPT_NEW_LINE_PATTERN,
    RE_CAPITALISED_WORD_PATTERN,
    RE_TAGS_PATTERN,
    RE_TITLE_PATTERN,
)
from librum.sections import LineDefinition, Section, SectionError


class HeaderSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition("^Learning Spanish$"),
        LineDefinition(RE_TAGS_PATTERN),
    ]

    def on_match(self, *_, **__): ...


class TasksSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition("^Tasks$"),
        LineDefinition(rf"- \[(x| )\] ({RE_TITLE_PATTERN})", count=-1),
    ]

    tasks: t.List[Task]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = []

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[1]:
            tick, title = match.groups()
            self.tasks.append(Task(title=title, completed=tick == "x"))


EXAMPLES_LINE_DEFINITIONS = [
    LineDefinition("^Examples:$"),
    LineDefinition(
        rf"- ({RE_TITLE_PATTERN}) \(({RE_TITLE_PATTERN})\)", count=-1
    ),
]


class WordSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(rf"^W\) ({RE_CAPITALISED_WORD_PATTERN})$"),
        LineDefinition(rf"^Meaning: ({RE_CAPITALISED_WORD_PATTERN})$"),
        LineDefinition(
            rf"^Synonyms: ({RE_CAPITALISED_WORD_PATTERN})(?:, ({RE_CAPITALISED_WORD_PATTERN}))*$",
            optional=True,
        ),
        LineDefinition(
            rf"^Antonyms: ({RE_CAPITALISED_WORD_PATTERN})(?:, ({RE_CAPITALISED_WORD_PATTERN}))*$",
            optional=True,
        ),
        *EXAMPLES_LINE_DEFINITIONS,
    ]

    word: Word

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._synonyms: t.Set[str] = set()
        self._antonyms: t.Set[str] = set()
        self._examples: t.List[Example] = []

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            self._text = match.groups()[0]
        elif definition == self.LINE_DEFINITIONS[1]:
            self._meaning = match.groups()[0]
        elif definition == self.LINE_DEFINITIONS[2]:
            groups = [g for g in match.groups() if g]
            if (synonyms := set(groups)) and len(synonyms) > len(groups):
                raise SectionError("Cannot have duplicate synonyms")
            self._synonyms = synonyms
        elif definition == self.LINE_DEFINITIONS[3]:
            groups = [g for g in match.groups() if g]
            if (antonyms := set(groups)) and len(antonyms) > len(groups):
                raise SectionError("Cannot have duplicate antonyms")
            self._antonyms = antonyms
        elif definition == self.LINE_DEFINITIONS[5]:
            text, translation = match.groups()
            self._examples.append(
                Example(text=text, translation=translation)
            )

    def on_complete(self):
        self.word = Word(
            text=self._text,
            meaning=self._meaning,
            synonyms=self._synonyms,
            antonyms=self._antonyms,
            examples=self._examples,
        )


class GrammarSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(rf"^G\) ({RE_TITLE_PATTERN})$"),
        LineDefinition(RE_ANY_TEXT_EXCEPT_NEW_LINE_PATTERN),
        *EXAMPLES_LINE_DEFINITIONS,
    ]

    grammar_rule: GrammarRule

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._examples: t.List[Example] = []

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            self._text = match.groups()[0]
        elif definition == self.LINE_DEFINITIONS[1]:
            self._explanation = match.groups()[0]
        elif definition == self.LINE_DEFINITIONS[3]:
            text, translation = match.groups()
            self._examples.append(
                Example(text=text, translation=translation)
            )

    def on_complete(self):
        self.grammar_rule = GrammarRule(
            text=self._text,
            explanation=self._explanation,
            examples=self._examples,
        )
