import abc
import typing as t
from copy import copy

import pytest

from librum.patterns import RE_SEPARATOR_PATTERN, SEPARATOR
from librum.sections import Line, LineDefinition, Section, SectionError


class SectionMock(Section):
    LINE_DEFINITIONS = [
        LineDefinition("Header"),
        LineDefinition(RE_SEPARATOR_PATTERN),
        LineDefinition("Body", count=2),
    ]

    on_match_calls: int = 0
    on_complete_calls: int = 0

    def on_match(self, *_, **__):
        self.on_match_calls += 1

    def on_complete(self):
        self.on_complete_calls += 1


def make_lines(*lines: str) -> t.List[Line]:
    return [Line(index, text) for index, text in enumerate(lines)]


def consume_lines(section: Section, lines: t.Sequence[Line]):
    for line in lines:
        section.consume_line(line)


Section_ = t.TypeVar("Section_", bound=Section)


def make_section(
    cls: t.Type[Section_],
    lines: t.List[Line],
    until_index: t.Optional[int] = None,
) -> Section_:
    lines = copy(lines)
    section = cls(lines.pop(0))
    consume_lines(
        # -1 because the first line has been popped
        section,
        lines if not until_index else lines[: until_index - 1],
    )
    return section


def assert_consumed_lines(section, lines):
    assert section.last_consumed_line == lines[-1]
    assert section.number_of_lines == len(lines)
    assert section.starting_line_index == lines[0].index

    if section.completed:
        assert section.ending_line_index == lines[-1].index
    else:
        assert not section.ending_line_index

    assert section.on_match_calls == len(lines)
    assert section.on_complete_calls == (1 if section.completed else 0)


@pytest.mark.parametrize(
    "index, text, expected_text",
    [
        (0, "text", "text"),
        (1, " text \n", " text"),
        (2, SEPARATOR, SEPARATOR),
    ],
)
def test_line_initialisation(index: int, text: str, expected_text: str):
    # Given
    line = Line(index, text)

    # Then
    assert line.index == index
    assert line.text == expected_text


def test_line_initialisation_failure():
    # Then
    with pytest.raises(ValueError, match="Line indices cannot be negative"):
        # When
        Line(-1, "invalid_index")


def test_line_representation():
    # Given
    line = Line(0, "text")

    # Then
    assert f"{line!r}" == "0:'text'"


def test_abstract_section_without_line_definitions():
    # Then
    class _(Section, abc.ABC): ...


def test_header_definition_cannot_be_optional():
    # Then
    with pytest.raises(
        SectionError, match="Header definition cannot be optional."
    ):
        # When
        class _(SectionMock):
            LINE_DEFINITIONS = [LineDefinition("Header", optional=True)]


def test_definition_cannot_have_zero_count():
    # Then
    with pytest.raises(
        SectionError,
        match="Definition at index 1 cannot have a count of 0.",
    ):
        # When
        class _(SectionMock):
            LINE_DEFINITIONS = [
                LineDefinition("Header"),
                LineDefinition("Body", count=0),
            ]


def test_definition_cannot_be_standalone_unordered():
    # Then
    with pytest.raises(
        SectionError,
        match=(
            "Definition at index 1 must have unordered siblings,"
            " otherwise it has no effect."
        ),
    ):
        # When
        class _(SectionMock):
            LINE_DEFINITIONS = [
                LineDefinition("Header"),
                LineDefinition("Body", ordered=False),
                LineDefinition("Footer"),
            ]


def test_definition_cannot_be_last_and_standalone_unordered():
    # Then
    with pytest.raises(
        SectionError,
        match=(
            "Definition at index 1 must have unordered siblings,"
            " otherwise it has no effect."
        ),
    ):
        # When
        class _(SectionMock):
            LINE_DEFINITIONS = [
                LineDefinition("Header"),
                LineDefinition("Body", ordered=False),
            ]


def test_section_end_pattern_cannot_be_an_empty_string():
    # Then
    with pytest.raises(
        SectionError, match="END_PATTERN cannot be an empty string."
    ):
        # When
        class _(SectionMock):
            LINE_DEFINITIONS = [
                LineDefinition("Header"),
                LineDefinition("Body"),
            ]
            END_PATTERN = SEPARATOR


def test_section_which_cannot_have_an_end_pattern():
    # Then
    with pytest.raises(
        SectionError,
        match="The END_PATTERN has no effect",
    ):
        # When
        class _(SectionMock):
            LINE_DEFINITIONS = [
                LineDefinition("Header"),
                LineDefinition("Body"),
            ]
            END_PATTERN = RE_SEPARATOR_PATTERN


def test_section_name():
    # Given
    section = SectionMock(starting_line=Line(0, "Header"))

    # Then
    assert section.name == "SectionMock"


def test_section_full_parse():
    # Given
    header = Line(0, "Header")
    separator = Line(1, SEPARATOR)
    body_1 = Line(2, "Body")
    invalid_line = Line(2, "Invalid line")
    body_2 = Line(3, "Body")
    section = SectionMock(starting_line=header)

    # Then: Assert initialisation parameters
    with pytest.raises(
        SectionError,
        match=(
            r"SectionMock: Invalid line 0:'Header'."
            r" Last consumed line: 0:'Header'."
            r" Expected patterns: \['\^\$'\]."
        ),
    ):
        # When
        section.consume_line(header)
    assert not section.completed
    assert_consumed_lines(section, [header])

    # When
    section.consume_line(separator)

    # Then
    assert not section.completed
    assert_consumed_lines(section, [header, separator])

    # When
    section.consume_line(body_1)

    # Then
    assert not section.completed
    assert_consumed_lines(section, [header, separator, body_1])

    # Then
    with pytest.raises(
        SectionError,
        match="SectionMock: Invalid line 2:'Invalid line'.",
    ):
        # When
        section.consume_line(invalid_line)
    assert not section.completed
    assert_consumed_lines(section, [header, separator, body_1])

    # When
    section.consume_line(body_2)

    # Then
    assert section.completed
    assert_consumed_lines(section, [header, separator, body_1, body_2])

    # Then
    with pytest.raises(
        SectionError, match="SectionMock already completed."
    ):
        # When
        section.consume_line(body_2)
    assert section.completed
    assert_consumed_lines(section, [header, separator, body_1, body_2])


def test_section_with_unlimited():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", count=-1),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Body", "Footer")
    section = SectionMock_(starting_line=lines[0])

    # When
    for line in lines[1:]:
        section.consume_line(line)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_optional():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Sub-header", optional=True),
            LineDefinition("Body"),
        ]

    lines = make_lines("Header", "Body")
    section = SectionMock_(starting_line=lines[0])

    # When
    section.consume_line(lines[1])

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_two_optionals():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Sub-header", optional=True),
            LineDefinition("Comment", optional=True),
            LineDefinition("Body"),
        ]

    lines = make_lines("Header", "Body")
    section = SectionMock_(starting_line=lines[0])

    # When
    section.consume_line(lines[1])

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


@pytest.mark.parametrize("count", [2, -1])
def test_section_with_repeated_optional(count: int):
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True, count=count),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Body", "Body", "Footer")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_optional_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    header = Line(0, "Header")
    separator = Line(1, SEPARATOR)
    section = SectionMock_(starting_line=header)

    # When
    section.consume_line(separator)

    # Then
    assert section.completed
    assert_consumed_lines(section, [header])


def test_section_with_repeated_optional_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True, count=2),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Body", "Body")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unlimited_optional_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True, count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Body", "Body", SEPARATOR)

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines[:-1])


def test_section_failure_with_unconsumed_repeated_optional():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True, count=2),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Body", "Footer")
    section = SectionMock_(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="SectionMock_: Invalid line 2:'Footer'.",
    ):
        # When
        consume_lines(section, lines[1:])
    assert not section.completed


def test_section_failure_with_unconsumed_repeated_optional_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True, count=2),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Body", SEPARATOR)
    section = SectionMock_(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="SectionMock_: Invalid line 2:''.",
    ):
        # When
        consume_lines(section, lines[1:])
    assert not section.completed


def test_section_on_end_with_optional_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", optional=True),
        ]

    header = Line(0, "Header")
    section = SectionMock_(starting_line=header)

    # When
    section.on_end()

    # Then
    assert section.completed
    assert_consumed_lines(section, [header])


def test_section_failure_on_end_with_multiline_optional_failure():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Footer", optional=True, count=2),
        ]

    section = SectionMock_(Line(0, "Header"))
    footer = Line(1, "Footer")
    section.consume_line(footer)

    # When
    with pytest.raises(
        SectionError,
        match=(
            "SectionMock_: End of section reached before"
            " section was completed. Last consumed line 1:'Footer'."
        ),
    ):
        section.on_end()
    assert not section.completed


def test_section_with_unordered():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False, count=2),
            LineDefinition("Comment", ordered=False, count=2),
            LineDefinition("Footer"),
        ]

    lines = make_lines(
        "Header", "Comment", "Body", "Body", "Comment", "Footer"
    )

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unordered_consumed_as_ordered():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False, count=2),
            LineDefinition("Comment", ordered=False, count=2),
            LineDefinition("Footer"),
        ]

    lines = make_lines(
        "Header", "Body", "Body", "Comment", "Comment", "Footer"
    )

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unordered_as_last():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition("Comment", ordered=False),
        ]

    lines = make_lines("Header", "Comment", "Body")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unlimited_unordered():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False, count=-1),
            LineDefinition("Comment", ordered=False),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Body", "Comment", "Body", "Footer")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_optional_after_unordered():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition("Comment", ordered=False),
            LineDefinition("Optional", optional=True),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Comment", "Body", "Footer")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unlimited_unordered_after_optionals():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Comment", optional=True),
            LineDefinition("Optional", optional=True),
            LineDefinition("Body", ordered=False, count=-1),
            LineDefinition("Footer", ordered=False, count=-1),
        ]

    lines = make_lines(
        "Header", "Body", "Footer", "Footer", "Body", "Footer"
    )

    # When
    section = make_section(SectionMock_, lines)
    section.on_end()

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unlimited_unordered_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition("Comment", ordered=False, count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Comment", "Body", "Comment", SEPARATOR)

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines[:-1])


def test_section_failure_with_previous_unordered_not_consumed():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False, count=2),
            LineDefinition("Comment", ordered=False),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Body", "Comment", "Comment", "Footer")
    comment_2, footer = lines[3:]

    section = make_section(SectionMock_, lines, until_index=3)

    # Then
    with pytest.raises(
        SectionError,
        match=(
            r"SectionMock_: Invalid line 3:'Comment'."
            r" Last consumed line: 2:'Comment'."
            r" Expected patterns: \['Body'\]."
        ),
    ):
        # When
        section.consume_line(comment_2)

    # Then
    with pytest.raises(
        SectionError,
        match=(
            r"SectionMock_: Invalid line 4:'Footer'."
            r" Last consumed line: 2:'Comment'."
            r" Expected patterns: \['Body'\]."
        ),
    ):
        # When
        section.consume_line(footer)
    assert not section.completed


def test_section_failure_with_last_unordered_not_consumed():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition("Comment", ordered=False, count=2),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Comment", "Body", "Footer")
    section = SectionMock_(lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match=(
            r"SectionMock_: Invalid line 3:'Footer'."
            r" Last consumed line: 2:'Body'."
            r" Expected patterns: \['Comment'\]."
        ),
    ):
        # When
        consume_lines(section, lines[1:])
    assert not section.completed


def test_section_with_unordered_optional():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition("Footer", ordered=False, optional=True),
            LineDefinition("Comment", ordered=False),
        ]

    lines = make_lines("Header", "Comment", "Body", "Footer")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unlimited_unordered_optional():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition(
                "Comment", ordered=False, optional=True, count=-1
            ),
            LineDefinition("Footer"),
        ]

    lines = make_lines("Header", "Comment", "Body", "Comment", "Footer")

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_with_unlimited_unordered_optional_as_last_line():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition(
                "Comment", ordered=False, optional=True, count=-1
            ),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Comment", "Body", "Comment", SEPARATOR)

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines[:-1])


@pytest.mark.parametrize("count", [1, 2, -1])
def test_section_on_end_with_unordered_optional(count: int):
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body", ordered=False),
            LineDefinition(
                "Footer", ordered=False, optional=True, count=count
            ),
            LineDefinition("Comment", ordered=False),
        ]

    lines = make_lines("Header", "Comment", "Body")

    # When
    section = make_section(SectionMock_, lines)
    section.on_end()

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_failure_initialisation_with_unmatched_header():
    # Then
    with pytest.raises(
        SectionError, match="SectionMock: Invalid line 0:'Non-header'."
    ):
        # When
        SectionMock(starting_line=Line(0, "Non-header"))


def test_section_completion_on_end_pattern():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body"),
            LineDefinition("Footer", count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Body", "Footer", SEPARATOR)

    # When
    section = make_section(SectionMock_, lines)

    # Then
    assert section.completed
    assert_consumed_lines(section, lines[:-1])


def test_section_failure_on_end_pattern_when_not_on_last_definition():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body"),
            LineDefinition("Footer", count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    header = Line(0, "Header")
    separator = Line(1, SEPARATOR)

    section = SectionMock_(starting_line=header)

    # Then
    with pytest.raises(
        SectionError, match="SectionMock_: Invalid line 1:''."
    ):
        # When
        section.consume_line(separator)
    assert not section.completed


def test_section_failure_on_end_pattern_when_last_definition_not_consumed():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body"),
            LineDefinition("Footer", count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Body", SEPARATOR)
    section = SectionMock_(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError, match="SectionMock_: Invalid line 2:''."
    ):
        # When
        consume_lines(section, lines[1:])
    assert not section.completed


def test_section_completion_on_file_end_with_unlimited():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body"),
            LineDefinition("Footer", count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    lines = make_lines("Header", "Body", "Footer")

    # When
    section = make_section(SectionMock_, lines)
    section.on_end()

    # Then
    assert section.completed
    assert_consumed_lines(section, lines)


def test_section_failure_on_file_end_with_unlimited():
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Footer", count=-1),
        ]
        END_PATTERN = RE_SEPARATOR_PATTERN

    section = SectionMock_(starting_line=Line(0, "Header"))

    # Then
    with pytest.raises(
        SectionError,
        match=(
            "SectionMock_: End of section reached"
            " before section was completed."
            " Last consumed line 0:'Header'."
        ),
    ):
        # When
        section.on_end()
    assert not section.completed


@pytest.mark.parametrize("previous_count, last_count", [(1, 2), (2, 1)])
def test_section_failure_on_file_end_with_unordered(
    previous_count: int, last_count: int
):
    # Given
    class SectionMock_(SectionMock):
        LINE_DEFINITIONS = [
            LineDefinition("Header"),
            LineDefinition("Body"),
            LineDefinition("Comment", ordered=False, count=previous_count),
            LineDefinition("Footer", ordered=False, count=last_count),
        ]

    lines = make_lines("Header", "Body", "Comment", "Footer")
    section = make_section(SectionMock_, lines)

    # Then
    with pytest.raises(
        SectionError,
        match=(
            "SectionMock_: End of section reached"
            " before section was completed."
            " Last consumed line 3:'Footer'."
        ),
    ):
        # When
        section.on_end()
    assert not section.completed
