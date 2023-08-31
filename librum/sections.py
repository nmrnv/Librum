import abc
import inspect
import re
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum

from librum.errors import SectionDefinitionError, SectionError
from librum.patterns import RE_SEPARATOR_PATTERN, SEPARATOR_RAW, Pattern

Index = Count = int


@dataclass
class Line:
    index: Index
    text: str

    def __init__(self, index: Index, text: str):
        if index < 0:
            raise ValueError("Line indices cannot be negative.")
        self.index = index
        self.text = text.rstrip()

    def __repr__(self) -> str:
        return f"{self.index}:{self.text!r}"


@dataclass
class LineDefinition:
    pattern: Pattern
    optional: bool = False
    ordered: bool = True
    count: Count = 1  # -1 for unlimited


class Section(abc.ABC):
    LINE_DEFINITIONS: t.Sequence[LineDefinition]
    END_PATTERN: t.Optional[Pattern] = None

    starting_line_index: Index
    ending_line_index: t.Optional[Index] = None
    last_consumed_line: Line

    __expected_definitions: t.Sequence[LineDefinition]
    __definition_counts: t.Dict[Index, Count]

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def number_of_lines(self) -> Count:
        return self.last_consumed_line.index - self.starting_line_index + 1

    @property
    def completed(self):
        return self.ending_line_index is not None

    def __init_subclass__(cls, *_, **__):
        if inspect.isabstract(cls):
            return

        header = cls.LINE_DEFINITIONS[0]
        if header.optional:
            raise SectionError("Header definition cannot be optional.")
        if not header.ordered:
            raise SectionError("Header definition cannot be ordered.")

        for index, definition in enumerate(cls.LINE_DEFINITIONS):
            location = f"Definition at index {index}"
            if definition.count == 0:
                raise SectionError(f"{location} cannot have a count of 0.")
            if not definition.ordered:
                previous_section = cls.LINE_DEFINITIONS[index - 1]
                try:
                    next_section = cls.LINE_DEFINITIONS[index + 1]
                except IndexError:
                    next_section = None
                if (
                    # The previous is ordered and the next is ordered
                    (
                        previous_section.ordered
                        and next_section
                        and next_section.ordered
                    )
                    # The previous is ordered and the next does not exist
                    or (previous_section.ordered and not next_section)
                ):
                    raise SectionError(
                        f"{location} must have unordered siblings,"
                        " otherwise it has no effect."
                    )

        if cls.END_PATTERN == "":
            raise SectionError("END_PATTERN cannot be an empty string.")

        last_definition = cls.LINE_DEFINITIONS[-1]
        is_last_definition_unlimited = last_definition.count == -1
        if is_last_definition_unlimited and not re.match(
            last_definition.pattern, SEPARATOR_RAW
        ):
            cls.END_PATTERN = RE_SEPARATOR_PATTERN

        if cls.END_PATTERN and not (
            last_definition.optional or is_last_definition_unlimited
        ):
            raise SectionError(
                "The END_PATTERN has no effect if the last definition is"
                " not optional or has no unlimited repeated count (-1)."
            )

    def __init__(self, starting_line: Line):
        self.starting_line_index = starting_line.index
        self.last_consumed_line = starting_line
        self.__expected_definitions = [self.LINE_DEFINITIONS[0]]
        self.__definition_counts = defaultdict(Count)
        self.consume_line(starting_line)

    def __get_definition_count(self, definition: LineDefinition) -> Count:
        return self.__definition_counts[
            self.LINE_DEFINITIONS.index(definition)
        ]

    def __can_definition_consume_more(
        self, definition: LineDefinition
    ) -> bool:
        if definition.count == -1:
            return True
        return definition.count > self.__get_definition_count(definition)

    def __is_definition_consumed(self, definition: LineDefinition) -> bool:
        definition_count = self.__get_definition_count(definition)
        if definition.optional and definition_count == 0:
            return True
        return (
            definition.count == -1 and definition_count > 0
        ) or definition.count == definition_count

    def has_consumed_all_definitions(self) -> bool:
        return all(
            [
                self.__is_definition_consumed(definition)
                for definition in self.LINE_DEFINITIONS
            ]
        )

    @t.final
    def consume_line(self, line: Line):
        if self.completed:
            raise SectionError(f"{self.name} already completed.")

        if self.END_PATTERN and self.__match_end_pattern(line):
            self.__on_complete(ending_line=self.last_consumed_line)
            return

        match: t.Optional[re.Match] = None
        matched_definition: t.Optional[LineDefinition] = None
        for definition in self.__expected_definitions:
            re_expression = re.compile(definition.pattern)
            if match := re_expression.match(line.text):
                matched_definition = definition
                break
        if not match or not matched_definition:
            expected_patterns = [
                definition.pattern
                for definition in self.__expected_definitions
            ]
            raise SectionError(
                f"{self.name}: Invalid line {line!r}."
                f" Last consumed line: {self.last_consumed_line!r}."
                f" Expected patterns: {expected_patterns}."
            )

        self.last_consumed_line = line
        self.__on_match(matched_definition, match)
        self.__update_expected_definitions(matched_definition)
        if not any(
            [
                self.__can_definition_consume_more(definition)
                for definition in self.__expected_definitions
            ]
        ):
            self.__on_complete(line)

    def __match_end_pattern(self, line: Line) -> bool:
        if not self.has_consumed_all_definitions():
            return False
        if self.END_PATTERN and re.match(self.END_PATTERN, line.text):
            return True
        return False

    def __on_match(
        self,
        matched_definition: LineDefinition,
        match: re.Match,
    ):
        index = self.LINE_DEFINITIONS.index(matched_definition)
        self.__definition_counts[index] += 1
        self.on_match(matched_definition, match)

    @abc.abstractmethod
    def on_match(self, definition: LineDefinition, match: re.Match): ...

    def __on_complete(self, ending_line: Line):
        self.ending_line_index = ending_line.index
        self.on_complete()

    def on_complete(self): ...

    @t.final
    def on_end(self):
        if not self.has_consumed_all_definitions():
            raise SectionError(
                f"{self.name}: End of section reached"
                " before section was completed."
                f" Last consumed line {self.last_consumed_line!r}."
            )
        self.__on_complete(ending_line=self.last_consumed_line)

    def __update_expected_definitions(
        self, matched_definition: LineDefinition
    ):
        index = self.LINE_DEFINITIONS.index(matched_definition)
        if not matched_definition.ordered:
            while not self.LINE_DEFINITIONS[index].ordered:
                index -= 1

        expected_definitions: t.List[LineDefinition] = []
        possible_definitions: t.List[LineDefinition] = list(
            self.LINE_DEFINITIONS[index:]
        )

        has_unconsumed_unordered = False
        for definition in possible_definitions:
            if definition.ordered:
                if has_unconsumed_unordered:
                    break
                if self.__can_definition_consume_more(definition):
                    expected_definitions.append(definition)
                if not self.__is_definition_consumed(definition):
                    break
            else:
                if self.__can_definition_consume_more(definition):
                    expected_definitions.append(definition)
                if (
                    not has_unconsumed_unordered
                    and not self.__is_definition_consumed(definition)
                ):
                    has_unconsumed_unordered = True

        self.__expected_definitions = expected_definitions


class SectionPriority(IntEnum):
    # An interrupting priority section matches
    # only if the previous section definition
    # is completed. The reason is that a pattern
    # of a section heading can absorb the remaining
    # lines of another section definition.
    INTERRUPTING = 0
    LOWER = 1
    DEFAULT = 2
    HIGHER = 3


@dataclass
class SectionDefinition:
    section: t.Type[Section]
    subsections: t.Sequence["SectionDefinition"]
    parent: t.Optional["SectionDefinition"]
    optional: bool
    ordered: bool
    count: Count  # -1 for unlimited
    priority: SectionPriority
    separator_count: Count

    @property
    def identifier(self) -> str:
        if hasattr(self, "_identifier"):
            return self._identifier

        identifiers = [str(id(self))]
        parent = self.parent
        while parent:
            identifiers.insert(0, str(id(parent)))
            parent = parent.parent

        self._identifier = "_".join(identifiers)
        return self._identifier

    def __init__(
        self,
        section: t.Type[Section],
        *,
        subsections: t.Optional[t.Sequence["SectionDefinition"]] = None,
        parent: t.Optional["SectionDefinition"] = None,
        optional: bool = False,
        ordered: bool = True,
        count: Count = 1,
        priority: SectionPriority = SectionPriority.DEFAULT,
        separator_count: Count = 1,
    ):
        self.section = section
        self.subsections = subsections or []
        self.parent = parent
        self.optional = optional
        self.ordered = ordered
        self.count = count
        self.priority = priority
        self.separator_count = separator_count
        if subsections:
            for subsection in self.subsections:
                subsection.parent = self

    def all_subsection_types(self) -> t.Set[t.Type[Section]]:
        def collect_subsection_definitions(
            definition: "SectionDefinition",
        ) -> t.Set[t.Type[Section]]:
            subsections = set()
            for subsection in definition.subsections:
                subsections.add(subsection.section)
                subsections.update(
                    collect_subsection_definitions(subsection)
                )
            return subsections

        return collect_subsection_definitions(self)


class SectionDefinitionsValidator:
    root_definitions: t.Sequence[SectionDefinition]

    @classmethod
    def validate(cls, root_definitions: t.Sequence[SectionDefinition]):
        cls.root_definitions = root_definitions
        cls._validate_definitions(root_definitions)

    @classmethod
    def _validate_definitions(
        cls, definitions: t.Sequence[SectionDefinition]
    ):
        for definition in definitions:
            next_possible_sections = cls._next_possible_sections(definition)
            if definition.section in next_possible_sections:
                raise SectionDefinitionError(
                    f"{definition.section.__name__} cannot be duplicated"
                    " by the next possible section definitions."
                )
            if definition.subsections:
                if definition.section in definition.all_subsection_types():
                    raise SectionDefinitionError(
                        f"{definition.section.__name__} cannot be"
                        " defined as a subsection of itself."
                    )
                cls._validate_definitions(definition.subsections)

    @classmethod
    def _next_possible_sections(
        cls, definition: SectionDefinition, selecting_upwards: bool = False
    ) -> t.Sequence[t.Type[Section]]:
        siblings = (
            cls.root_definitions
            if not definition.parent
            else definition.parent.subsections
        )
        index = siblings.index(definition)

        if selecting_upwards and not definition.ordered:
            while not siblings[index].ordered and index > 0:
                index -= 1

        possible_sections = []
        possible_definitions = siblings[index:]
        last_continued_definition = None

        for possible_definition in possible_definitions:
            # Whenever we select upwards, we always add the definition
            # If at root however, we do not add the definition we're validating
            if selecting_upwards or possible_definition is not definition:
                possible_sections.append(possible_definition.section)
            else:
                last_continued_definition = possible_definition
                continue

            # If we're checking upwards, we must move past the
            # parent definition, even if it's not optional or unordered
            if selecting_upwards and possible_definition is definition:
                last_continued_definition = possible_definition
                continue

            if (
                possible_definition.optional
                or not possible_definition.ordered
            ):
                last_continued_definition = possible_definition
                continue

            break

        if (
            last_continued_definition
            and last_continued_definition == possible_definitions[-1]
            and last_continued_definition.parent
        ):
            possible_sections.extend(
                cls._next_possible_sections(
                    definition=last_continued_definition.parent,
                    selecting_upwards=True,
                )
            )

        return possible_sections
