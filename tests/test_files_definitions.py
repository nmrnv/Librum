import abc
from pathlib import Path

import pytest

from librum.files import File, FileDefinitionError, FileError
from librum.sections import SectionDefinition, SectionDefinitionError
from tests.conftest import BodySection, FileMock, HeaderSection


class File_(File):
    FILE_TAG = "test_files_test_file"
    SECTION_DEFINITIONS = [SectionDefinition(HeaderSection)]

    def on_match(self, *_):
        pass


def test_file_definition_invalid_file_tag():
    # Then
    with pytest.raises(FileDefinitionError, match="Invalid file tag"):
        # When
        class _(File):
            FILE_TAG = "Invalid file tag"
            SECTION_DEFINITIONS = [SectionDefinition(HeaderSection)]

            def on_match(self, *_): ...


def test_file_definition_duplicate_file_tag():
    # Given
    class _(File):
        FILE_TAG = "test_duplicate_file"
        SECTION_DEFINITIONS = [SectionDefinition(HeaderSection)]

        def on_match(self, *_): ...

    # Then
    with pytest.raises(FileDefinitionError, match="Duplicates file tag"):
        # When
        class __(File):
            FILE_TAG = "test_duplicate_file"
            SECTION_DEFINITIONS = [SectionDefinition(HeaderSection)]

            def on_match(self, *_): ...


def test_file_definition_empty_section_definitions():
    # Then
    with pytest.raises(
        FileDefinitionError, match="Must have at least one section."
    ):
        # When
        class _(File):
            FILE_TAG = "test_empty_sections_file"
            SECTION_DEFINITIONS = []

            def on_match(self, *_): ...


def test_file_definition_ambiguous_section_definitions():
    # Then
    with pytest.raises(
        SectionDefinitionError, match="cannot be duplicated"
    ):
        # When
        class _(File):
            FILE_TAG = "test_ambiguous_file"
            SECTION_DEFINITIONS = [
                SectionDefinition(BodySection),
                SectionDefinition(BodySection),
            ]

            def on_match(self, *_): ...


def test_match(test_file: FileMock):
    # Given
    test_file.write("Header", "`[test_files_test_file]`")

    # Then
    assert File_.match(test_file.path)


def test_abstract_files_are_not_matched():
    # Given
    class AbstractFile(File, abc.ABC): ...

    # With
    with pytest.raises(FileError, match="Cannot match abstract files."):
        # When
        AbstractFile.match(Path())


def test_non_existent_file(tmp_path: Path):
    # Given
    non_existent_path = tmp_path / "non_existent.md"

    # Then
    with pytest.raises(FileError, match="does not exist"):
        # When
        File_.match(non_existent_path)


def test_empty_file(test_file: FileMock):
    # Then
    with pytest.raises(FileError, match="Invalid tags ''"):
        # When
        File_.match(test_file.path)


def test_file_does_not_match_tags(test_file: FileMock):
    # Given
    test_file.write("Header", "invalid tags")

    # Then
    with pytest.raises(FileError, match="Invalid tags 'invalid tags'"):
        # When
        File_.match(test_file.path)


def test_file_invalid_file_tag(test_file: FileMock):
    # Given
    test_file.write("Header", "`[invalid_file]`")

    # Then
    with pytest.raises(
        FileError,
        match="Invalid 'invalid_file' tag for File_.",
    ):
        # When
        File_.match(test_file.path)
