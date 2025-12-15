"""Joke content models."""

from pydantic import BaseModel, Field

from joke_emporium.models.enums import ElementType


class JokeElement(BaseModel):
    """A single element of joke content.

    Examples:
        - Setup: "Why did the chicken cross the road?"
        - Punchline: "To get to the other side!"
        - Text: "I told my wife she was drawing her eyebrows too high. She looked surprised."
    """

    type: ElementType = Field(
        ..., description="Type of content element (setup, punchline, text, etc.)"
    )
    text: str = Field(..., min_length=1, description="The actual text content of this element")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"type": "setup", "text": "Why did the scarecrow win an award?"},
                {"type": "punchline", "text": "Because he was outstanding in his field!"},
            ]
        }
    }
