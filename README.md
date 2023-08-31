# Librum

A Python framework for extracting data and validating structured files.

### Installation
Add `librum` to pip or poetry.

# Usage (code with imports can be found in `example/`)
Suppose you're learning Spanish and you've defined your own structured file to write down tasks, words, and grammar rules:
```
Learning Spanish
`[spanish_file]`

Tasks
- [x] Establish a study schedule
- [ ] Find a teacher

W) Feliz
Meaning: Happy
Synonyms: Contento, Alegre
Antonyms: Triste
Examples:
- Estoy muy feliz (I am very happy)

G) Ser vs estar
'Ser' relates to essence or identity, while 'estar' relates to state or condition.
Examples:
- Ella es profesora (She is a teacher)
- Ella está cansada (She is tired)
```

From this file we can see that we have 4 types of sections: HeaderSection, TasksSection, WordSection, and GrammarSection.
Each consisting of predefined lines.

# Defining the HeaderSection
Section:
```
Learning Spanish
`[spanish_file]`
```

Definition:
```
class HeaderSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition("^Learning Spanish$"),
        LineDefinition(RE_TAGS_PATTERN),
    ]

    def on_match(self, *_, **__):
        # Required for non-abstact sections.
        # Explained with TasksSection.
        ...
```

Line definitions describe each line with a regex pattern. Regex groups are used to capture the information.
The second line definition of each header section of every file should be `RE_TAGS_PATTERN`. This way, the framework will know what type of file is being parsed and its tags if any – explained further with the File definitions.

# Defining the TasksSection
Section:
```
Tasks
- [x] Establish a study schedule
- [ ] Find a teacher
```

Definition:
```
class TasksSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition("Tasks"),
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

```
Here, we start with the predefined section line 'Tasks'. Then we define the pattern for completed or uncompleted tasks.
There are some predefined patterns in `librum/patterns.py`. The one used here is `RE_TITLE_PATTERN = r"[A-Z][\w,-:–'& ]+\w"`.
To learn more or test regex patterns visit https://regexr.com .

Every section and file can have properties where we can store the parsed information. Here, we define `tasks` and set it to an empty list in the initialiser.

For every match of a line definition thereafter, `on_match` is called with the definition and the regex match object.
We check which definition was matched, and retrieve the captured data to create a task.

The checking by definition in `on_match` is a bit tedious but can be addressed with decorators in the future:
```
@Section.definition(LineDefinition("Tasks"), index=0)
def match_header(self, definition: LineDefinition, match: re.Match):
  ...
```

# Defining the WordSection
Section:
```
W) Feliz
Meaning: Happy
Synonyms: Contento, Alegre
Antonyms: Triste
Examples:
- Estoy muy feliz (I am very happy)
```
Definition:

We see that the Examples are shared by both the WordSection and GrammarSection, so we can reuse them.
```
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
```
Each WordSection has a word, so we define it as a property of the section.

In `on_match` we extract the information, and validate it, as we do for synonyms and antonyms when checking for duplicates.

Once we have matched all sections, `on_complete` is called. This is where we can use the collected data to build the Word object.


# Defining the GrammarSection
The Grammar section is similar to the WordSection, you can see it in `example/sections.py`.

# Defining the SpanishFile
Once we've defined the sections, we need to define the file.

Every file must have a `FILE_TAG` property, so that the parser knows what type of file it's working with.

Then we define the `SECTION_DEFINITIONS`. They can have a different count (-1 for unlimited), can be optional, and unordered. We define the WordSection and GrammarSection as unordered, because one can come before the other, i.e. in a mixed order. We can have many words and grammar rules in the file, not just one as in the example.
```
class SpanishFile(File):
    FILE_TAG = "spanish_file"
    SECTION_DEFINITIONS = [
        SectionDefinition(HeaderSection),
        SectionDefinition(TasksSection, optional=True),
        SectionDefinition(WordSection, ordered=False, count=-1),
        SectionDefinition(GrammarSection, ordered=False, count=-1),
    ]

    tasks: t.List[Task]
    words: t.List[Word]
    grammar_rules: t.List[GrammarRule]

    def __init__(self, path: Path):
        super().__init__(path)
        self.words = []
        self.grammar_rules = []

    def on_match(self, section: Section):
        if isinstance(section, TasksSection):
            self.tasks = section.tasks
        elif isinstance(section, WordSection):
            self.words.append(section.word)
        elif isinstance(section, GrammarSection):
            self.grammar_rules.append(section.grammar_rule)

    def on_complete(self):
        # Perform extra validation
        # or create other objects with the data collected from `on_match`
        ...
```

Files also have `on_match` and `on_complete`. In `on_match`, we get back the section where we can check which one it is so as to get its data.

# How to parse the file
File types are automatically registered when they are defined.

If you don't know what type of file in a given path, you can use: `file = File.match(path)` This way it will figure out what the file is based on the file tag.

If you do know the file type upfront, you should use `file = SpanishFile(path)`.

Lastly, the file should be parsed:
```
try:
  file.parse()
except (FileError, SectionError) as error:
  print(error)

# Use file.tasks, file.words, file.grammar_rules
```

## Results
To see what the resulting objects look like, see: https://github.com/nmrnv/Librum/blob/main/example/test_parse.py

## Definition options
By definitions we mean LineDefinition when describing sections and SectionDefinition when describing files.
1. Count - How many definitions are expected. For unlimited, use -1.
2. Optional - Whether or not a definition is optional. First definitions cannot be.
3. Unordered - Whether or not different definitions can come one before another, i.e. in a mixed manner. Count and optionality are still respected.

**Section definition options**
1. Subsections - The parser can work with nested sections.
2. Priority - If you have a specific pattern such as `Tasks` it should be set to `SectionPriority.HIGHER` so that it's prioritised over open-regex patterns where we can have any title. `SectionPriority.INTERRUPTING` is when we have a section header pattern which is more generic than the remaining lines of the current parsed sections. Examples can be seen in `tests/test_files.py::test_file_with_higher_priority` and `tests/test_files.py::test_file_with_interrupting_priority`.
3. Separator count - how many empty lines should separate the given section definition.
