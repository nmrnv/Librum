import pytest

from librum.sections import (
    SectionDefinition,
    SectionDefinitionError,
    SectionDefinitionsValidator,
)
from tests.conftest import (
    BodySection,
    CommentSection,
    FooterSection,
    GroupSection,
    HeaderSection,
)


def test_all_subsection_definitions():
    # Given
    definition = SectionDefinition(
        section=GroupSection,
        subsections=[
            SectionDefinition(HeaderSection),
            SectionDefinition(
                BodySection,
                subsections=[
                    SectionDefinition(CommentSection),
                    SectionDefinition(FooterSection),
                    SectionDefinition(CommentSection),
                ],
            ),
            SectionDefinition(FooterSection),
        ],
    )

    # Then
    assert definition.all_subsection_types() == {
        HeaderSection,
        BodySection,
        CommentSection,
        FooterSection,
    }


def test_subsection_definition_over_non_optional_in_parent():
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(BodySection),
                SectionDefinition(CommentSection),
            ],
        ),
        SectionDefinition(BodySection),
    ]

    # Then
    SectionDefinitionsValidator.validate(definitions)


def test_definition_cannot_be_defined_as_subsection():
    # Given
    definition = SectionDefinition(
        section=HeaderSection,
        subsections=[SectionDefinition(HeaderSection)],
    )

    # Then
    with pytest.raises(
        SectionDefinitionError,
        match="HeaderSection cannot be defined as a subsection of itself.",
    ):
        # When
        SectionDefinitionsValidator.validate([definition])


@pytest.mark.parametrize(
    "optional, count", [(True, 1), (True, -1), (False, -1)]
)
def test_definition_ambiguity(optional: bool, count: int):
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(
                    CommentSection, optional=optional, count=count
                ),
            ],
        ),
        SectionDefinition(CommentSection),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_over_optional():
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(CommentSection, count=-1),
            ],
        ),
        SectionDefinition(BodySection, optional=True),
        SectionDefinition(CommentSection),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_over_level_optional():
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(
                    section=CommentSection,
                    subsections=[
                        SectionDefinition(BodySection, optional=True)
                    ],
                ),
            ],
        ),
        SectionDefinition(BodySection),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_in_unordered_block():
    # Given
    definitions = [
        SectionDefinition(BodySection, ordered=False),
        SectionDefinition(CommentSection, ordered=False),
        SectionDefinition(BodySection, ordered=False),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_with_unlimited_unordered_last():
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(CommentSection, ordered=False),
                SectionDefinition(BodySection, ordered=False, count=-1),
            ],
        ),
        SectionDefinition(BodySection),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_with_unlimited_unordered_previous():
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(BodySection, ordered=False, count=-1),
                SectionDefinition(CommentSection, ordered=False),
            ],
        ),
        SectionDefinition(BodySection),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_with_unlimited_unordered_over_one():
    # Given
    definitions = [
        SectionDefinition(
            section=GroupSection,
            subsections=[
                SectionDefinition(CommentSection, ordered=False),
                SectionDefinition(FooterSection, ordered=False, count=-1),
            ],
        ),
        SectionDefinition(BodySection, ordered=False),
        SectionDefinition(FooterSection, ordered=False),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_with_duplicate_following_unordered():
    # Given
    definitions = [
        SectionDefinition(BodySection, ordered=False),
        SectionDefinition(CommentSection, ordered=False),
        SectionDefinition(BodySection),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)


def test_definition_ambiguity_with_unlimited_subsection_duplicating_unordered():
    # Given
    definitions = [
        SectionDefinition(BodySection, ordered=False),
        SectionDefinition(
            section=GroupSection,
            subsections=[SectionDefinition(BodySection, count=-1)],
            ordered=False,
        ),
    ]

    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        SectionDefinitionsValidator.validate(definitions)
