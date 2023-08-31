import typing as t
from pathlib import Path

import pytest

from librum.files import File
from librum.patterns import RE_TAGS_PATTERN
from librum.sections import LineDefinition, Section


class File_(File):
    matched_sections = []
    on_match_calls = 0
    on_complete_calls = 0

    def __init__(self, *args, **kwargs):
        self.matched_sections = []
        super().__init__(*args, **kwargs)

    def match_(self, section: Section):
        self.matched_sections.append(section.__class__)
        self.on_match_calls += 1

    def on_complete(self):
        self.on_complete_calls += 1


class Section_(Section):
    LINE_DEFINITIONS = [LineDefinition("Header")]

    def on_match(self, *_):
        pass


class HeaderSection(Section_):
    LINE_DEFINITIONS = [
        LineDefinition("Header"),
        LineDefinition(RE_TAGS_PATTERN),
    ]


class BodySection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Body")]


class GroupSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Group")]


class NoteSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Note")]


class CommentSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Comment")]


class FooterSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Footer")]


def assert_calls(
    file: File_,
    number_of_sections: int,
    number_of_lines: t.Optional[int] = None,
):
    assert file.number_of_lines == number_of_lines or number_of_sections * 2
    assert file.on_match_calls == number_of_sections
    assert file.on_complete_calls == 1


class FileMock:
    unique_counter = 26

    @property
    def file_tag(self) -> str:
        file_tag = ""
        self.__class__.unique_counter += 1
        integer = self.__class__.unique_counter
        while integer > 0:
            integer, remainder = divmod(integer - 1, 26)
            file_tag = chr(ord("a") + remainder) + file_tag
        return f"{file_tag}_file"

    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self.path.touch()

    def write(self, *lines):
        self.path.write_text("\n".join(lines))


@pytest.fixture
def test_file(tmp_path: Path) -> FileMock:
    return FileMock(tmp_path / "test_file.md")
