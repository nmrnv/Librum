Pattern = str

SEPARATOR = ""
SEPARATOR_RAW = "\n"
RE_SEPARATOR_PATTERN = "^$"

NEW_LINE = "\n"
RE_NEW_LINE_PATTERN = "^\n$"

RE_DAY_PATTERN = r"([0-9]{1,2})"  # Will rely on datetime validation
RE_WEEKDAY_PATTERN = (
    r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
)
RE_WEEKDAY_ABV_PATTERN = r"(MON|TUE|WED|THU|FRI|SAT|SUN)"
RE_MONTH_PATTERN = r"(0[0-9]|1[0-2])"
RE_MONTH_NAME_PATTERN = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
RE_YEAR_PATTERN = r"([2-9][0-9]{3})"
RE_DATE_PATTERN = (
    r"((?:[0-2][0-9]|(?:3)[0-1])/(?:0[0-9]|1[0-2])/(?:[2-9][0-9]{3}))"
)

RE_TITLE_PATTERN = r"[A-Z][\w,-:–'& ]+\w"
RE_SENTENCE_PATTERN = r"[A-Z][\w,-:–'& ]+\w[\.\!\?]"
RE_QUESTION_PATTERN = r"[A-Z][\w,-:–'& ]+\w\?"

RE_FILE_TITLE_PATTERN = r"^## ([A-Z][\w,-:–'& ]+\w)$"
RE_FILE_TAG_PATTERN = r"^([a-z]{2,}_)+file$"

RE_TAG_PATTERN = r"((?:(?:[a-z]+[_]{1})+[a-zA-Z]+)|(?:[a-z]+))"
RE_TAGS_PATTERN = rf"^`(?:\[{RE_TAG_PATTERN}\])+`$"

RE_PAGES_GROUP_PATTERN = r"([0-9ivxlc]+)"
RE_PAGES_TAG_MULTIPLE_PATTERN = (
    rf"(?:{RE_PAGES_GROUP_PATTERN}, )+{RE_PAGES_GROUP_PATTERN}"
)
RE_PAGES_TAG_PATTERN = (
    rf"(?:(pages): (?:(?:{RE_PAGES_TAG_MULTIPLE_PATTERN})"
    rf"|(?:{RE_PAGES_GROUP_PATTERN})))"
)
RE_TAGS_PATTERN_WITH_PAGES = (
    rf"^`(?:\[(?:{RE_PAGES_TAG_PATTERN}|{RE_TAG_PATTERN})\])+`$"
)

RE_ANY_TEXT_PATTERN = r"^(?: +)?((?:[^ #].*)|(?:))$"
RE_ANY_TEXT_EXCEPT_NEW_LINE_PATTERN = r"^(?: +)?((?:[^ #]\w.*))$"

RE_ROMAN_NUMBER_PATTERN = r"([IVXLCDM]+)"
