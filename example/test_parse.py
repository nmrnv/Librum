from pathlib import Path

from example.file import SpanishFile


def test_parse():
    # Given
    path = Path() / "example" / "learning_spanish.txt"
    file = SpanishFile(path)

    # When
    file.parse()

    # Then
    assert len(file.tasks) == 2
    task_1, task_2 = file.tasks
    assert dict(task_1) == {
        "title": "Establish a study schedule",
        "completed": True,
    }
    assert dict(task_2) == {"title": "Find a teacher", "completed": False}

    assert len(file.words) == 1
    assert file.words[0].model_dump() == {
        "text": "Feliz",
        "meaning": "Happy",
        "synonyms": {"Alegre", "Contento"},
        "antonyms": {"Triste"},
        "examples": [
            {"text": "Estoy muy feliz", "translation": "I am very happy"}
        ],
    }

    assert len(file.grammar_rules) == 1
    assert file.grammar_rules[0].model_dump() == {
        "text": "Ser vs estar",
        "explanation": (
            "'Ser' relates to essence or identity, while 'estar' relates to state or condition."
        ),
        "examples": [
            {
                "text": "Ella es profesora",
                "translation": "She is a teacher",
            },
            {"text": "Ella está cansada", "translation": "She is tired"},
        ],
    }
