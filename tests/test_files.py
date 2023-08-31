import pytest

from librum.files import File
from librum.patterns import SEPARATOR
from librum.sections import (
    LineDefinition,
    Section,
    SectionDefinition,
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
    assert_calls,
)


def test_file_hashing_and_equality(test_file: FileMock):
    # Given
    file_tag = test_file.file_tag

    class _(File):
        FILE_TAG = file_tag
        SECTION_DEFINITIONS = [SectionDefinition(HeaderSection)]

        def on_match(self, section: Section): ...

    # Two files of the same file type
    directory = test_file.path.parent
    filepath = directory / "file_one"
    filepath.write_text(f"# File\n`[{file_tag}]`\n")
    another_filepath = directory / "file_two"
    another_filepath.write_text(f"# File\n`[{file_tag}]`\n")

    # When
    file = File.match(filepath)
    same_file = File.match(filepath)
    another_file = File.match(another_filepath)

    # Then
    assert hash(file) == hash(filepath)
    assert file == same_file
    assert file != another_file


def test_file_full_parse(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, count=-1),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(section=NoteSection, count=-1)
                ],
                count=-1,
                optional=True,
                ordered=False,
            ),
            SectionDefinition(
                section=CommentSection, count=2, ordered=False
            ),
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
        "Body",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=13)
    assert file.matched_sections == [
        HeaderSection,
        BodySection,
        BodySection,
        GroupSection,
        NoteSection,
        NoteSection,
        CommentSection,
        GroupSection,
        NoteSection,
        CommentSection,
        GroupSection,
        NoteSection,
        FooterSection,
    ]


def test_file_with_two_optionals(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, optional=True),
            SectionDefinition(CommentSection, optional=True),
            SectionDefinition(FooterSection),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=2)
    assert file.matched_sections == [HeaderSection, FooterSection]


@pytest.mark.parametrize("count", [2, -1])
def test_file_with_repeated_optional(test_file: FileMock, count: int):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, optional=True, count=count),
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
        "Body",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=4)
    assert file.matched_sections == [
        HeaderSection,
        BodySection,
        BodySection,
        FooterSection,
    ]


def test_file_with_optional_as_last_section(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection),
            SectionDefinition(FooterSection, optional=True),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header", f"`[{test_file.file_tag}]`", SEPARATOR, "Body"
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=2)
    assert file.matched_sections == [HeaderSection, BodySection]


def test_file_with_unlimited_optional_as_last_section(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, optional=True, count=-1),
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

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=3)
    assert file.matched_sections == [
        HeaderSection,
        BodySection,
        BodySection,
    ]


def test_file_with_unordered(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False, count=2),
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
        "Comment",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=6)
    assert file.matched_sections == [
        HeaderSection,
        CommentSection,
        BodySection,
        CommentSection,
        BodySection,
        FooterSection,
    ]


def test_file_with_unordered_consumed_as_ordered(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False, count=2),
            SectionDefinition(CommentSection, ordered=False, count=2),
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
        "Body",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=6)
    assert file.matched_sections == [
        HeaderSection,
        BodySection,
        BodySection,
        CommentSection,
        CommentSection,
        FooterSection,
    ]


def test_file_with_unordered_as_last(test_file: FileMock):
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
        "Comment",
        SEPARATOR,
        "Body",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=3)
    assert file.matched_sections == [
        HeaderSection,
        CommentSection,
        BodySection,
    ]


def test_file_with_unlimited_ordered(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False, count=-1),
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
        "Body",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=5)
    assert file.matched_sections == [
        HeaderSection,
        BodySection,
        CommentSection,
        BodySection,
        FooterSection,
    ]


def test_file_with_optional_after_unordered(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False),
            SectionDefinition(CommentSection, ordered=False),
            SectionDefinition(NoteSection, optional=True),
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
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=4)
    assert file.matched_sections == [
        HeaderSection,
        BodySection,
        CommentSection,
        FooterSection,
    ]


def test_file_with_unlimited_unordered_after_optionals(
    test_file: FileMock,
):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, optional=True),
            SectionDefinition(CommentSection, optional=True),
            SectionDefinition(NoteSection, ordered=False, count=-1),
            SectionDefinition(FooterSection, ordered=False, count=-1),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Footer",
        SEPARATOR,
        "Footer",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=6)
    assert file.matched_sections == [
        HeaderSection,
        NoteSection,
        FooterSection,
        FooterSection,
        NoteSection,
        FooterSection,
    ]


def test_file_with_unlimited_unordered_as_last_line(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False),
            SectionDefinition(CommentSection, ordered=False, count=-1),
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
        "Comment",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=4)
    assert file.matched_sections == [
        HeaderSection,
        CommentSection,
        BodySection,
        CommentSection,
    ]


def test_file_with_unordered_optional(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False),
            SectionDefinition(FooterSection, ordered=False, optional=True),
            SectionDefinition(CommentSection, ordered=False),
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

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=4)
    assert file.matched_sections == [
        HeaderSection,
        CommentSection,
        BodySection,
        FooterSection,
    ]


def test_file_with_unlimited_unordered_optional(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(BodySection, ordered=False),
            SectionDefinition(
                CommentSection, ordered=False, optional=True, count=-1
            ),
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
        "Comment",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=5)
    assert file.matched_sections == [
        HeaderSection,
        CommentSection,
        BodySection,
        CommentSection,
        FooterSection,
    ]


def test_file_with_subsections_full_parse(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[SectionDefinition(section=NoteSection)],
                ordered=False,
                count=2,
            ),
            SectionDefinition(CommentSection, ordered=False),
            SectionDefinition(BodySection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(section=NoteSection),
                    SectionDefinition(section=CommentSection),
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
        "Comment",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Body",
        SEPARATOR,
        "Group",
        SEPARATOR,
        "Note",
        SEPARATOR,
        "Comment",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=11)
    assert file.matched_sections == [
        HeaderSection,
        GroupSection,
        NoteSection,
        CommentSection,
        GroupSection,
        NoteSection,
        BodySection,
        GroupSection,
        NoteSection,
        CommentSection,
        FooterSection,
    ]


def test_file_exits_subsections_with_optional(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(section=NoteSection),
                    SectionDefinition(
                        section=CommentSection, optional=True
                    ),
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

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=4)
    assert file.matched_sections == [
        HeaderSection,
        GroupSection,
        NoteSection,
        FooterSection,
    ]


def test_file_exits_subsections_with_unlimited(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(BodySection, count=-1),
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
        "BodySection",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=5)
    assert file.matched_sections == [
        HeaderSection,
        GroupSection,
        BodySection,
        BodySection,
        FooterSection,
    ]


def test_file_exits_subsections_with_unordered(test_file: FileMock):
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
        "NoteSection",
        SEPARATOR,
        "BodySection",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=5)
    assert file.matched_sections == [
        HeaderSection,
        GroupSection,
        NoteSection,
        BodySection,
        FooterSection,
    ]


def test_full_parse_with_three_levels(test_file: FileMock):
    # Given
    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(
                section=GroupSection,
                subsections=[
                    SectionDefinition(BodySection, ordered=False),
                    SectionDefinition(
                        CommentSection,
                        ordered=False,
                        subsections=[SectionDefinition(NoteSection)],
                        count=2,
                    ),
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
        "CommentSection",
        SEPARATOR,
        "NoteSection",
        SEPARATOR,
        "BodySection",
        SEPARATOR,
        "CommentSection",
        SEPARATOR,
        "NoteSection",
        SEPARATOR,
        "Footer",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=8)
    assert file.matched_sections == [
        HeaderSection,
        GroupSection,
        CommentSection,
        NoteSection,
        BodySection,
        CommentSection,
        NoteSection,
        FooterSection,
    ]


def test_file_with_higher_priority(test_file: FileMock):
    # Given
    class GenericSection(Section_):
        LINE_DEFINITIONS = [LineDefinition(r"# [a-zA-Z]+")]

    class SpecificSection(Section_):
        LINE_DEFINITIONS = [LineDefinition("# Specific")]

    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(GenericSection, ordered=False),
            SectionDefinition(
                SpecificSection,
                ordered=False,
                priority=SectionPriority.HIGHER,
            ),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "# Specific",
        SEPARATOR,
        "# Generic",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=3)
    assert file.matched_sections == [
        HeaderSection,
        SpecificSection,
        GenericSection,
    ]


def test_file_with_interrupting_priority(test_file: FileMock):
    # Given
    class InterruptingSection(Section_):
        LINE_DEFINITIONS = [LineDefinition(r"[a-zA-Z ]+")]

    class OverlngSection(Section_):
        LINE_DEFINITIONS = [
            LineDefinition("# Section"),
            LineDefinition("Overlng pattern"),
        ]

    class TestFile(File_):
        FILE_TAG = test_file.file_tag
        SECTION_DEFINITIONS = [
            SectionDefinition(HeaderSection),
            SectionDefinition(OverlngSection),
            SectionDefinition(
                InterruptingSection, priority=SectionPriority.INTERRUPTING
            ),
        ]

        def on_match(self, section: Section):
            self.match_(section)

    test_file.write(
        "Header",
        f"`[{test_file.file_tag}]`",
        SEPARATOR,
        "# Section",
        "Overlng pattern",
        SEPARATOR,
        "Overlng pattern",
    )

    # When
    file = TestFile(test_file.path)
    file.parse()

    # Then
    assert_calls(file, number_of_sections=3, number_of_lines=7)
    assert file.matched_sections == [
        HeaderSection,
        OverlngSection,
        InterruptingSection,
    ]
