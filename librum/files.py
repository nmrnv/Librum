import abc
import inspect
import re
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from librum.errors import FileDefinitionError, FileError
from librum.patterns import (
    NEW_LINE,
    RE_FILE_TAG_PATTERN,
    RE_TAG_PATTERN,
    RE_TAGS_PATTERN,
    SEPARATOR,
    SEPARATOR_RAW,
)
from librum.sections import (
    Line,
    Section,
    SectionDefinition,
    SectionDefinitionsValidator,
    SectionError,
    SectionPriority,
)

Index = Count = int
File_ = t.TypeVar("File_", bound="File")


@dataclass
class SectionInfo:
    section: Section
    definition: SectionDefinition
    has_updated_count: bool = False
    has_been_completed: bool = False

    def can_interrupt(self, section_info: "SectionInfo") -> bool:
        if (
            self.definition.priority == SectionPriority.INTERRUPTING
            and not section_info.has_been_completed
        ):
            return False
        return True


@dataclass
class SectionCount:
    count: int
    subsections_counts: t.Mapping[str, "SectionCount"]


class File(abc.ABC):
    FILE_TAG: str
    SECTION_DEFINITIONS: t.Sequence[SectionDefinition] = []

    __FILE_TYPES: t.ClassVar[t.List[t.Type]] = []

    __definition_counts: t.Dict[str, Count]
    number_of_lines: Count = 0

    @property
    @t.final
    def name(self):
        return self.__class__.__name__

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, other) -> bool:
        return self.path == other.path

    def __is_definition_consumed(
        self, definition: SectionDefinition
    ) -> bool:
        definition_count = self.__definition_counts.get(
            definition.identifier, 0
        )
        if definition.optional and definition_count == 0:
            return True

        return (  # is count sufficient
            definition.count == -1 and definition_count > 0
        ) or definition.count == definition_count

    def __can_definition_consume_more(
        self, definition: SectionDefinition
    ) -> bool:
        if definition.count == -1:
            return True
        return definition.count > self.__definition_counts.get(
            definition.identifier, 0
        )

    def __is_file_consumed(self) -> bool:
        return all(
            [
                self.__is_definition_consumed(definition)
                for definition in self.SECTION_DEFINITIONS
            ]
        )

    def __init_subclass__(cls, **_):
        if inspect.isabstract(cls):
            return
        if not re.match(RE_FILE_TAG_PATTERN, cls.FILE_TAG):
            raise FileDefinitionError("Invalid file tag.")
        if cls.FILE_TAG in {cls_.FILE_TAG for cls_ in cls.__FILE_TYPES}:
            raise FileDefinitionError("Duplicates file tag.")
        cls.__FILE_TYPES.append(cls)

        if not cls.SECTION_DEFINITIONS:
            raise FileDefinitionError("Must have at least one section.")
        SectionDefinitionsValidator.validate(cls.SECTION_DEFINITIONS)

    @classmethod
    @t.final
    def match(cls: t.Type[File_], path: Path) -> File_:
        if cls is not File and inspect.isabstract(cls):
            raise FileError("Cannot match abstract files.")

        try:
            with open(path, mode="r") as file:
                lines = [file.readline().rstrip(NEW_LINE) for _ in range(2)]
        except FileNotFoundError:
            raise FileError("File does not exist")

        # Match tag
        _, tags_line = tuple(lines)
        if not re.compile(RE_TAGS_PATTERN).match(tags_line):
            raise FileError(f"Invalid tags {tags_line!r}.")
        file_tag = re.findall(RE_TAG_PATTERN, tags_line)[0]

        file_types = cls.__FILE_TYPES if cls is File else [cls]
        matched_file_type = None
        for file_type in file_types:
            if file_tag == file_type.FILE_TAG:
                matched_file_type = file_type
                break
        if not matched_file_type:
            raise FileError(f"Invalid {file_tag!r} tag for {cls.__name__}.")
        return matched_file_type(path)

    def __init__(self, path: Path):
        self.path = path
        self.__definition_counts = defaultdict(int)
        self.__update_expected_definitions()

    @t.final
    def parse(self):
        self.__parse_sections()

    def on_complete(self): ...

    def __on_complete(self):
        if not self.__is_file_consumed():
            raise FileError(
                f"{self.name}: End of file reached "
                "before all sections were completed."
            )
        self.__expected_definitions = []
        self.on_complete()

    @abc.abstractmethod
    def on_match(self, section: Section): ...

    def __on_match(self, section_info: SectionInfo):
        self.__update_count(section_info)
        section_info.has_been_completed = True
        self.on_match(section_info.section)

    def __update_count(self, section_info: SectionInfo):
        if not section_info.has_updated_count:
            key = section_info.definition.identifier
            self.__definition_counts[key] += 1
            section_info.has_updated_count = True

    def __clear_subsections_count(self, section_info: SectionInfo):
        # The count is cleared for newly-matched sections with subsections,
        # because we keep count only for the latest subsections.
        for subsection in section_info.definition.subsections:
            if subsection.identifier in self.__definition_counts:
                del self.__definition_counts[subsection.identifier]

    def __update_expected_definitions(
        self, matched_definition: t.Optional[SectionDefinition] = None
    ):
        self.__expected_definitions = self.__select_expected_definitions(
            definition=matched_definition or self.SECTION_DEFINITIONS[0]
        )

    def __select_expected_definitions(
        self, definition: SectionDefinition, selecting_upwards: bool = False
    ) -> t.Sequence[SectionDefinition]:
        expected_definitions: t.List[SectionDefinition] = []

        if selecting_upwards or not definition.subsections:
            siblings = (
                self.SECTION_DEFINITIONS
                if not definition.parent
                else definition.parent.subsections
            )
            index = siblings.index(definition)

            if not definition.ordered:
                while not siblings[index].ordered and index > 0:
                    index -= 1

            possible_definitions = list(siblings[index:])
        else:
            possible_definitions = list(definition.subsections)

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
            if (
                definition == possible_definitions[-1]
                and definition.parent
                and not has_unconsumed_unordered
            ):
                expected_definitions.extend(
                    self.__select_expected_definitions(
                        definition.parent, selecting_upwards=True
                    )
                )
        return sorted(
            expected_definitions,
            key=lambda d: d.priority,
            reverse=True,
        )

    def __match_definition(
        self, line: Line
    ) -> t.Tuple[t.Optional[SectionInfo], t.Sequence[SectionError]]:
        section_info: t.Optional[SectionInfo] = None
        errors: t.List[SectionError] = []
        for definition in self.__expected_definitions:
            try:
                section = definition.section(line)
                section_info = SectionInfo(section, definition)
                break
            except SectionError as error:
                errors.append(error)
        return section_info, errors

    @t.final
    def __parse_sections(self):
        section_info: t.Optional[SectionInfo] = None

        with open(self.path.as_posix(), "r") as raw_file:
            raw_lines = raw_file.readlines()
        self.number_of_lines = len(raw_lines)

        for index, raw_line in enumerate(raw_lines):
            line = Line(index, raw_line)

            # Always start by trying to match a new section
            matched_section_info, errors = self.__match_definition(line)
            if matched_section_info and (
                matched_section_info.can_interrupt(section_info)
                if section_info
                else True
            ):
                if section_info:
                    if not section_info.section.completed:
                        section_info.section.on_end()
                        self.__on_match(section_info)
                    self.__validate_separators(
                        matched_section_info, raw_lines
                    )

                section_info = matched_section_info
                # Check if one-line sections are completed
                if section_info.section.completed:
                    self.__on_match(section_info)
                if section_info.definition.subsections:
                    self.__clear_subsections_count(section_info)
                self.__update_expected_definitions(section_info.definition)
                continue

            elif section_info and not section_info.section.completed:
                section_info.section.consume_line(line)
                if (
                    not section_info.has_updated_count
                    and section_info.section.has_consumed_all_definitions()
                ):
                    self.__update_count(section_info)
                    self.__update_expected_definitions(
                        section_info.definition
                    )
                if section_info.section.completed:
                    self.__on_match(section_info)
                continue

            elif line.text == SEPARATOR:
                continue

            # Error if no section has been matched
            errors_str = "\n".join([f"– {str(error)}" for error in errors])
            raise FileError(
                f"{self.name}: Could not match any section.\n"
                f"Errors:\n{errors_str}"
            )

        if section_info and not section_info.section.completed:
            section_info.section.on_end()
            self.__on_match(section_info)
        self.__on_complete()

    def __validate_separators(
        self, section_info: SectionInfo, raw_lines: t.Sequence[str]
    ):
        to_index = section_info.section.starting_line_index
        from_index = to_index - section_info.definition.separator_count
        if (
            set(raw_lines[from_index:to_index]) != {SEPARATOR_RAW}
            or raw_lines[from_index - 1] == SEPARATOR_RAW
        ):
            raise FileError(
                f"{self.name}: Invalid separator count for"
                f" {section_info.section.name} at line {to_index}."
            )
