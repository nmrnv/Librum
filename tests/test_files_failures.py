import pytest

from librum.files import FileError
from librum.patterns import SEPARATOR
from librum.sections import (
    LineDefinition,
    Section,
    SectionDefinition,
    SectionError,
    SectionPriority,
)
from tests.conftest import (
    BodySection,
    CommentSection,
    File_,
    FileMock,
    FooterSection,
    GroupSection,
    HeaderSection,
    NoteSection,
    Section_,
)


def test_parse_failure_last_definition_not_consumed(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header", f"`[{test_file.file_tag}]`", SEPARATOR, "Body"
    )

    # Then
    with pytest.raises(
        FileError,
        match=(
            "TestFile: End of file reached before"
            " all sections were completed."
        ),
    ):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_repeated_optional(
    test_file: FileMock,
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, optional=True, count=2),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Body'\]"):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_repeated_optional_as_last_section(
    test_file: FileMock,
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, optional=True, count=2),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header", f"`[{test_file.file_tag}]`", SEPARATOR, "Body"
    )

    # Then
    with pytest.raises(
        FileError,
        match="End of file reached before all sections were completed",
    ):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_reconsumed_unordered(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False),
            SectionDefinition(CommentSection, ordered=False),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Body",
    )

    # Then
    with pytest.raises(
        FileError, match=r"Expected patterns: \['Comment'\]"
    ):
        # When
        TestFile(test_file.path).parse()


@pytest.mark.parametrize("unexpected_line", ["Comment", "Footer"])
def test_parse_failure_with_previous_unordered_not_consumed(
    test_file: FileMock, unexpected_line: str
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False, count=2),
            SectionDefinition(CommentSection, ordered=False),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        unexpected_line,
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Body'\]"):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_last_unordered_not_consumed(
    test_file: FileMock,
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False),
            SectionDefinition(CommentSection, ordered=False, count=2),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(
        FileError, match=r"Expected patterns: \['Comment'\]"
    ):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_subsection(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(BodySection),
                    SectionDefinition(NoteSection),
                ],
            ),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "BodySection",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Note'\]"):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_repeated_subsection(
    test_file: FileMock,
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(BodySection, count=2),
                ],
            ),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "BodySection",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Body'\]"):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_optional(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(BodySection, optional=True, count=2),
                ],
            ),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Body'\]"):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_unordered(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(BodySection, ordered=False),
                    SectionDefinition(NoteSection, ordered=False),
                ],
            ),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Body'\]"):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_unconsumed_repeated_parent(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                count=2,
                subsections=[SectionDefinition(BodySection)],
            ),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Footer",
    )

    # Then
    with pytest.raises(FileError, match=r"Expected patterns: \['Body'\]"):
        # When
        TestFile(test_file.path).parse()


@pytest.mark.parametrize("count", [0, 1, 3])
def test_parse_failure_with_incorrect_number_of_separators(
    test_file: FileMock, count: int
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(FooterSection, separator_count=2),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        *((SEPARATOR,) * count),
        "Footer",
    )

    # Then
    with pytest.raises(
        FileError, match="Invalid separator count for FooterSection"
    ):
        # When
        TestFile(test_file.path).parse()


def test_parse_failure_with_interrupted_section(test_file: FileMock):
    # Given
    class OverlappingSection(Section_):
        LINE_DEFINITIONS = [
            LineDefinition("# Section"),
            LineDefinition("Overlapping pattern"),
        ]

    class InterruptingSection(Section_):
        LINE_DEFINITIONS = [LineDefinition(r"[a-zA-Z ]+")]

    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(OverlappingSection, ordered=False),
            SectionDefinition(
                InterruptingSection,
                priority=SectionPriority.DEFAULT,
                ordered=False,
            ),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "# Section",
        "Overlapping pattern",
        SEPARATOR,
        "Overlapping pattern",
    )

    # Then
    with pytest.raises(
        SectionError,
        match=(
            "OverlappingSection: End of section reached"
            " before section was completed."
            " Last consumed line 3:'# Section'"
        ),
    ):
        # When
        TestFile(test_file.path).parse()
