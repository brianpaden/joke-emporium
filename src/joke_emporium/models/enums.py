"""Enumerations for joke categorization and classification."""

from enum import Enum


class Category(str, Enum):
    """Primary topic categories for jokes."""

    # People & Relationships
    RELATIONSHIPS = "relationships"
    MARRIAGE = "marriage"
    DATING = "dating"
    FAMILY = "family"
    PARENTING = "parenting"
    FRIENDSHIP = "friendship"

    # Professions
    WORK = "work"
    DOCTOR = "doctor"
    LAWYER = "lawyer"
    TEACHER = "teacher"
    ENGINEER = "engineer"
    PROGRAMMER = "programmer"

    # Topics
    TECHNOLOGY = "technology"
    COMPUTERS = "computers"
    SCIENCE = "science"
    MATHEMATICS = "math"
    ANIMALS = "animals"
    FOOD = "food"
    SPORTS = "sports"
    MUSIC = "music"
    POLITICS = "politics"
    RELIGION = "religion"

    # Situations
    TRAVEL = "travel"
    SCHOOL = "school"
    MEDICAL = "medical"
    SHOPPING = "shopping"
    DRIVING = "driving"

    # Meta
    META = "meta"  # Jokes about jokes
    OBSERVATIONAL = "observational"
    ABSURD = "absurd"
    WORDPLAY = "wordplay"

    # Demographics & Stereotypes
    KIDS = "kids"
    ELDERLY = "elderly"
    BLONDE = "blonde"  # Blonde jokes (stereotype-based)
    CHUCK_NORRIS = "chuck_norris"  # Chuck Norris jokes

    # Humor Styles
    DARK = "dark"  # Dark humor
    OFFENSIVE = "offensive"  # Potentially offensive content

    # Miscellaneous
    MISCELLANEOUS = "miscellaneous"


class StructureType(str, Enum):
    """Narrative structure of the joke."""

    ONE_LINER = "one_liner"
    QA = "qa"  # Question & answer
    RIDDLE = "riddle"
    STORY = "story"
    DIALOGUE = "dialogue"
    LIST = "list"  # Top 10, etc.
    OBSERVATION = "observation"
    KNOCK_KNOCK = "knock_knock"
    ANTI_JOKE = "anti_joke"
    MISDIRECTION = "misdirection"
    CALLBACK = "callback"  # References earlier setup


class LinguisticMechanism(str, Enum):
    """Linguistic mechanisms used in the joke."""

    # Wordplay
    PUN_HOMOPHONIC = "pun_homophonic"  # prophet/profit
    PUN_HOMOGRAPHIC = "pun_homographic"  # read (present) vs read (past)
    PUN_HOMONYMIC = "pun_homonymic"  # bank (river) vs bank (money)
    PUN_COMPOUND = "pun_compound"

    DOUBLE_ENTENDRE = "double_entendre"
    MALAPROPISM = "malapropism"
    SPOONERISM = "spoonerism"

    # Rhetorical
    IRONY = "irony"
    SARCASM = "sarcasm"
    EXAGGERATION = "exaggeration"
    UNDERSTATEMENT = "understatement"
    HYPERBOLE = "hyperbole"

    # Logic
    PARAPROSDOKIAN = "paraprosdokian"  # Unexpected ending
    NON_SEQUITUR = "non_sequitur"
    ABSURDISM = "absurdism"
    REVERSAL = "reversal"

    # Reference
    ALLUSION = "allusion"
    PARODY = "parody"

    # Sound
    ALLITERATION = "alliteration"
    RHYME = "rhyme"

    # Other
    ANTHROPOMORPHISM = "anthropomorphism"
    JUXTAPOSITION = "juxtaposition"


class MaturityRating(str, Enum):
    """Maturity/content rating."""

    G = "g"  # General - all ages
    PG = "pg"  # Parental guidance - may reference adult themes mildly
    PG13 = "pg13"  # Parents strongly cautioned - mild profanity, innuendo
    R = "r"  # Restricted - strong profanity, explicit themes
    X = "x"  # Adults only - extremely explicit


class ElementType(str, Enum):
    """Type of joke content element."""

    TITLE = "title"  # Optional title
    TEXT = "text"  # Generic text (for one-liners, stories)
    SETUP = "setup"  # Question, premise
    BUILD = "build"  # Additional setup/context
    PUNCHLINE = "punchline"  # The payoff
    CALLBACK = "callback"  # References earlier setup
    TAG = "tag"  # Additional punchline/kicker


class CognitiveType(str, Enum):
    """Cognitive joke taxonomy (Chalmers)."""

    # Main types
    ALLUSIVE = "allusive"
    PARADOXICAL = "paradoxical"
    INFERENTIAL = "inferential"

    # Interpretational subtypes
    INTERPRETATIONAL_SDS = "interpretational_sds"
    INTERPRETATIONAL_DSS = "interpretational_dss"
    INTERPRETATIONAL_SDD = "interpretational_sdd"
    INTERPRETATIONAL_SD = "interpretational_sd"
    INTERPRETATIONAL_DS = "interpretational_ds"


class SourcePlatform(str, Enum):
    """Platform where the joke originated."""

    REDDIT = "reddit"
    TWITTER = "twitter"
    WEBSITE = "website"
    BOOK = "book"
    API = "api"
    ORIGINAL = "original"
    MANUAL_ENTRY = "manual_entry"
    SCRAPED = "scraped"
    CROWDSOURCED = "crowdsourced"
    COMEDY_SPECIAL = "comedy_special"
    UNKNOWN = "unknown"


class OppositionType(str, Enum):
    """Script opposition types (GTVH)."""

    ACTUAL_NON_ACTUAL = "actual_non_actual"
    NORMAL_ABNORMAL = "normal_abnormal"
    POSSIBLE_IMPOSSIBLE = "possible_impossible"
    GOOD_BAD = "good_bad"
    LIFE_DEATH = "life_death"
    OBSCENE_NON_OBSCENE = "obscene_non_obscene"
    MONEY_NO_MONEY = "money_no_money"
    HIGH_LOW_STATURE = "high_low_stature"
    EXPECTED_UNEXPECTED = "expected_unexpected"


class LogicalMechanism(str, Enum):
    """Logical mechanisms (GTVH)."""

    FIGURE_GROUND_REVERSAL = "figure_ground_reversal"
    FALSE_ANALOGY = "false_analogy"
    ROLE_REVERSAL = "role_reversal"
    IGNORANCE_OF_OBVIOUS = "ignorance_of_obvious"
    JUXTAPOSITION = "juxtaposition"
    CHIASMUS = "chiasmus"
    EXAGGERATION = "exaggeration"
    GARDEN_PATH = "garden_path"


class NarrativeStrategy(str, Enum):
    """Narrative strategy (GTVH)."""

    SIMPLE_NARRATIVE = "simple_narrative"
    DIALOGUE = "dialogue"
    RIDDLE = "riddle"
    BEFORE_AFTER = "before_after"
    META_HUMOR = "meta_humor"
    FRAME_STORY = "frame_story"


class TargetType(str, Enum):
    """Type of joke target (GTVH)."""

    SELF = "self"
    PERSON = "person"
    PROFESSION = "profession"
    GROUP_NATIONALITY = "group_nationality"
    GROUP_GENDER = "group_gender"
    GROUP_AGE = "group_age"
    GROUP_RELIGION = "group_religion"
    GROUP_POLITICAL = "group_political"
    CONCEPT = "concept"
    INSTITUTION = "institution"
    UNIVERSAL = "universal"  # No specific target


class AuthorType(str, Enum):
    """Type of author/persona."""

    INDIVIDUAL = "individual"
    GROUP = "group"
    ANONYMOUS = "anonymous"
    UNKNOWN = "unknown"


class AgeRange(str, Enum):
    """Age range for demographic data."""

    UNDER_18 = "under_18"
    AGE_18_24 = "18_24"
    AGE_25_34 = "25_34"
    AGE_35_44 = "35_44"
    AGE_45_54 = "45_54"
    AGE_55_64 = "55_64"
    AGE_65_PLUS = "65_plus"
