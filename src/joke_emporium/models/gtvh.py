"""GTVH (General Theory of Verbal Humor) annotation models.

These are optional advanced annotations based on academic humor research.
"""

from pydantic import BaseModel, Field

from joke_emporium.models.enums import (
    LogicalMechanism,
    NarrativeStrategy,
    OppositionType,
    TargetType,
)


class ScriptOpposition(BaseModel):
    """Script opposition from GTVH framework.

    Represents the cognitive incongruity that creates humor.
    """

    opposition_type: OppositionType = Field(..., description="Type of script opposition")
    script_1: str = Field(..., description="Description of the first script/interpretation")
    script_2: str = Field(..., description="Description of the second script/interpretation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "opposition_type": "actual_non_actual",
                    "script_1": "Literal understanding of 'outstanding in his field'",
                    "script_2": "Metaphorical meaning (excellent at his job)",
                }
            ]
        }
    }


class Target(BaseModel):
    """Target of the joke (who/what is being made fun of)."""

    target_type: TargetType = Field(..., description="Type of target")
    description: str | None = Field(default=None, description="Description of the specific target")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"target_type": "profession", "description": "Scarecrows/farmers"},
                {"target_type": "universal", "description": None},
            ]
        }
    }


class GTVHAnnotation(BaseModel):
    """Complete GTVH annotation for advanced humor analysis.

    Based on the General Theory of Verbal Humor (Attardo & Raskin).
    All fields are optional - annotate what's relevant.
    """

    script_opposition: ScriptOpposition | None = Field(
        default=None, description="The central script opposition (semantic incongruity)"
    )
    logical_mechanism: LogicalMechanism | None = Field(
        default=None, description="How the opposition is resolved logically"
    )
    narrative_strategy: NarrativeStrategy | None = Field(
        default=None, description="Narrative structure used"
    )
    target: Target | None = Field(default=None, description="Who/what the joke targets")
    situation: str | None = Field(default=None, description="The situational context of the joke")
    notes: str | None = Field(default=None, description="Additional analytical notes")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "script_opposition": {
                        "opposition_type": "actual_non_actual",
                        "script_1": "Literal: standing out in a field",
                        "script_2": "Metaphorical: being exceptionally good at one's job",
                    },
                    "logical_mechanism": "garden_path",
                    "narrative_strategy": "riddle",
                    "target": {"target_type": "profession", "description": "Scarecrows"},
                    "situation": "Award ceremony / recognition scenario",
                    "notes": "Classic pun relying on ambiguity of 'outstanding'",
                }
            ]
        }
    }
