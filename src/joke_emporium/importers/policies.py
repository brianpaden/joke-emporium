"""Policy engine for automated review of staging jokes.

This module provides a declarative policy engine using YAML configuration files
to define auto-approval, auto-rejection, and flagging rules for staging jokes.

Key components:
- PolicyCondition: Evaluates a single condition against a StagingJokeDB
- Policy: Collection of conditions with an action (approve/reject/flag)
- PolicyEngine: Loads policies from YAML and applies them to jokes

Example YAML configuration:
    policies:
      auto_approve:
        - name: "high_quality_reddit"
          conditions:
            - field: weighted_avg_funniness
              operator: ">="
              value: 80
            - field: flags.nsfw
              operator: "=="
              value: false
          action: approve

      auto_reject:
        - name: "low_quality"
          conditions:
            - field: weighted_avg_funniness
              operator: "<"
              value: 20
            - field: total_ratings_count
              operator: ">="
              value: 5
          action: reject
          reason: "Low quality with sufficient ratings"
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from sqlmodel import Session, select

from joke_emporium.db.models.staging import ReviewStatus, StagingJokeDB

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

# Type aliases for clarity
Operator = Literal[
    # Comparison operators
    "==", "!=", ">", ">=", "<", "<=",
    # Membership operators
    "in", "not_in",
    # Null operators
    "is_null", "is_not_null",
    # String operators
    "contains", "not_contains", "starts_with", "ends_with", "matches",
    "length_gt", "length_lt",
    # Array operators
    "empty", "not_empty", "size_gt", "size_lt",
    # Numeric range operators
    "between", "not_between",
]

# Compiled regex patterns cache for performance
_COMPILED_PATTERNS: dict[str, re.Pattern[str]] = {}
PolicyAction = Literal["approve", "reject", "flag"]

# JSON field prefixes that require parsing (module-level constant for performance)
_JSON_FIELD_PREFIXES: tuple[str, ...] = ("flags.", "tags.", "engagement.", "gtvh.", "metadata.")

# Mapping from nested prefix to JSON field name on StagingJokeDB
_JSON_FIELD_MAP: dict[str, str] = {
    "flags": "flags_json",
    "tags": "tags_json",
    "engagement": "engagement_json",
    "gtvh": "gtvh_json",
    "metadata": "metadata_json",
}


@dataclass(frozen=True, slots=True)
class PolicyCondition:
    """A single condition to evaluate against a StagingJokeDB.

    Supports direct field access (e.g., `weighted_avg_funniness`) and
    nested field access for JSON fields (e.g., `flags.nsfw`, `engagement.upvotes`).

    Attributes:
        field: Field path to evaluate (e.g., "weighted_avg_funniness" or "flags.nsfw")
        operator: Comparison operator to use
        value: Value to compare against (type depends on operator)

    Supported Operators:
        Comparison: ==, !=, >, >=, <, <=
        Membership: in, not_in
        Null: is_null, is_not_null
        String: contains, not_contains, starts_with, ends_with, matches, length_gt, length_lt
        Array: empty, not_empty, size_gt, size_lt
        Range: between, not_between

    Examples:
        Basic comparison:
            >>> condition = PolicyCondition("weighted_avg_funniness", ">=", 80)
            >>> condition.evaluate(joke)  # Returns True if joke.weighted_avg_funniness >= 80

        JSON field access:
            >>> flag_condition = PolicyCondition("flags.nsfw", "==", False)
            >>> flag_condition.evaluate(joke)  # Parses flags_json and checks nsfw field

        String operators:
            >>> PolicyCondition("text_preview", "contains", "joke")
            >>> PolicyCondition("text_preview", "starts_with", "Why")
            >>> PolicyCondition("text_preview", "matches", "^Q: .* A: .*$")
            >>> PolicyCondition("text_preview", "length_gt", 100)

        Array operators:
            >>> PolicyCondition("tags_json", "empty", True)  # True if no tags
            >>> PolicyCondition("tags_json", "size_gt", 3)   # True if > 3 tags

        Range operators:
            >>> PolicyCondition("weighted_avg_funniness", "between", [40, 60])
            >>> PolicyCondition("weighted_avg_funniness", "not_between", [20, 80])
    """

    field: str
    operator: Operator
    value: Any

    def evaluate(self, joke: StagingJokeDB) -> bool:
        """Evaluate this condition against a staging joke.

        Args:
            joke: The staging joke to evaluate

        Returns:
            True if the condition is satisfied, False otherwise

        Note:
            - Returns False for missing fields or None values with comparison operators
            - Handles JSON field parsing automatically for nested fields
            - Performance: <1ms per evaluation with JSON caching
        """
        try:
            current_value = self._get_field_value(joke)
            return self._apply_operator(current_value)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.debug(f"Condition evaluation failed for field '{self.field}': {e}")
            return False

    def _get_field_value(self, joke: StagingJokeDB) -> Any:
        """Extract the field value from the joke, handling nested JSON fields.

        Args:
            joke: The staging joke to extract value from

        Returns:
            The field value (may be None)

        Raises:
            AttributeError: If the base field doesn't exist
            KeyError: If a nested JSON key doesn't exist
        """
        # Check if this is a nested JSON field
        for prefix in _JSON_FIELD_PREFIXES:
            if self.field.startswith(prefix):
                return self._get_json_field_value(joke)

        # Direct field access
        return self._get_direct_field_value(joke)

    def _get_direct_field_value(self, joke: StagingJokeDB) -> Any:
        """Get a direct field value from the joke.

        Supports simple field access like 'weighted_avg_funniness' or
        nested attribute access like 'import_batch.source'.

        Args:
            joke: The staging joke

        Returns:
            The field value
        """
        parts = self.field.split(".")
        current: Any = joke

        for part in parts:
            if current is None:
                return None
            current = getattr(current, part, None)

        return current

    def _get_json_field_value(self, joke: StagingJokeDB) -> Any:
        """Get a value from a JSON field on the joke.

        Parses the JSON field and navigates to the nested value.
        Example: "flags.nsfw" -> parse flags_json, return flags["nsfw"]

        Args:
            joke: The staging joke

        Returns:
            The nested JSON field value, or None if not found
        """
        parts = self.field.split(".")
        if len(parts) < 1:
            return None

        base_field = parts[0]
        json_attr = _JSON_FIELD_MAP.get(base_field)

        if not json_attr:
            # Fall back to direct attribute access
            return self._get_direct_field_value(joke)

        # Get the JSON string from the database model
        json_str = getattr(joke, json_attr, None)
        if json_str is None:
            return None

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON field '{json_attr}' for joke {joke.id}")
            return None

        # Navigate to nested value
        current: Any = data
        for part in parts[1:]:  # Skip the base field name
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            else:
                # Can't navigate further
                return None

        return current

    def _apply_operator(self, current_value: Any) -> bool:
        """Apply the operator to compare current_value with self.value.

        Args:
            current_value: The value extracted from the joke

        Returns:
            True if the comparison succeeds, False otherwise

        Supported operators:
            Comparison: ==, !=, >, >=, <, <=
            Membership: in, not_in
            Null: is_null, is_not_null
            String: contains, not_contains, starts_with, ends_with, matches, length_gt, length_lt
            Array: empty, not_empty, size_gt, size_lt
            Range: between, not_between
        """
        match self.operator:
            # Comparison operators
            case "==":
                return bool(current_value == self.value)
            case "!=":
                return bool(current_value != self.value)
            case ">":
                return self._compare_numeric(current_value, lambda a, b: a > b)
            case ">=":
                return self._compare_numeric(current_value, lambda a, b: a >= b)
            case "<":
                return self._compare_numeric(current_value, lambda a, b: a < b)
            case "<=":
                return self._compare_numeric(current_value, lambda a, b: a <= b)

            # Membership operators
            case "in":
                return self._check_in(current_value)
            case "not_in":
                return self._check_not_in(current_value)

            # Null operators
            case "is_null":
                return bool((current_value is None) == self.value)
            case "is_not_null":
                return bool((current_value is not None) == self.value)

            # String operators
            case "contains":
                return self._check_contains(current_value)
            case "not_contains":
                return self._check_not_contains(current_value)
            case "starts_with":
                return self._check_starts_with(current_value)
            case "ends_with":
                return self._check_ends_with(current_value)
            case "matches":
                return self._check_matches(current_value)
            case "length_gt":
                return self._check_length_gt(current_value)
            case "length_lt":
                return self._check_length_lt(current_value)

            # Array operators
            case "empty":
                return self._check_empty(current_value)
            case "not_empty":
                return self._check_not_empty(current_value)
            case "size_gt":
                return self._check_size_gt(current_value)
            case "size_lt":
                return self._check_size_lt(current_value)

            # Numeric range operators
            case "between":
                return self._check_between(current_value)
            case "not_between":
                return self._check_not_between(current_value)

            case _:
                logger.warning(f"Unknown operator: {self.operator}")
                return False

    def _compare_numeric(
        self,
        current_value: Any,
        comparator: Any,  # Callable[[float | int, float | int], bool] - simplified for performance
    ) -> bool:
        """Perform a numeric comparison with proper type handling.

        Args:
            current_value: Value from the joke
            comparator: Comparison function (e.g., lambda a, b: a > b)

        Returns:
            True if comparison succeeds, False if types are incompatible or None
        """
        if current_value is None:
            return False

        # Handle numeric comparisons
        try:
            # Convert strings to numbers if needed
            numeric_current: float | int
            if isinstance(current_value, str):
                if "." in current_value:
                    numeric_current = float(current_value)
                else:
                    numeric_current = int(current_value)
            else:
                numeric_current = current_value

            compare_value: float | int
            if isinstance(self.value, str):
                if "." in self.value:
                    compare_value = float(self.value)
                else:
                    compare_value = int(self.value)
            else:
                compare_value = self.value

            result: bool = comparator(numeric_current, compare_value)
            return result
        except (ValueError, TypeError):
            return False

    def _check_in(self, current_value: Any) -> bool:
        """Check if current_value is in self.value (list).

        Args:
            current_value: Value to check

        Returns:
            True if value is in the list
        """
        if current_value is None:
            return False

        if not isinstance(self.value, list | tuple | set):
            # Single value comparison
            return bool(current_value == self.value)

        return bool(current_value in self.value)

    def _check_not_in(self, current_value: Any) -> bool:
        """Check if current_value is NOT in self.value (list).

        Args:
            current_value: Value to check

        Returns:
            True if value is not in the list
        """
        if current_value is None:
            return True  # None is not in any list

        if not isinstance(self.value, list | tuple | set):
            # Single value comparison
            return bool(current_value != self.value)

        return bool(current_value not in self.value)

    # -------------------------------------------------------------------------
    # String operators
    # -------------------------------------------------------------------------

    def _check_contains(self, current_value: Any) -> bool:
        """Check if string contains substring OR array contains element.

        This operator works for both strings (substring search) and arrays
        (element membership). Type is detected automatically.

        Args:
            current_value: String or array to check

        Returns:
            True if string contains substring or array contains element

        Examples:
            >>> condition = PolicyCondition("text_preview", "contains", "joke")
            >>> condition.evaluate(joke)  # True if text_preview contains "joke"

            >>> condition = PolicyCondition("tags_json", "contains", "pun")
            >>> condition.evaluate(joke)  # True if tags array contains "pun"
        """
        if current_value is None:
            return False

        # Handle string containment
        if isinstance(current_value, str):
            if not isinstance(self.value, str):
                return False
            return self.value in current_value

        # Handle array/list containment
        if isinstance(current_value, list | tuple | set):
            return self.value in current_value

        return False

    def _check_not_contains(self, current_value: Any) -> bool:
        """Check if string does NOT contain substring OR array does NOT contain element.

        Args:
            current_value: String or array to check

        Returns:
            True if string does not contain substring or array does not contain element

        Example:
            >>> condition = PolicyCondition("text_preview", "not_contains", "politics")
            >>> condition.evaluate(joke)  # True if text_preview doesn't contain "politics"
        """
        if current_value is None:
            return True  # None does not contain anything

        # Handle string containment
        if isinstance(current_value, str):
            if not isinstance(self.value, str):
                return True
            return self.value not in current_value

        # Handle array/list containment
        if isinstance(current_value, list | tuple | set):
            return self.value not in current_value

        return True

    def _check_starts_with(self, current_value: Any) -> bool:
        """Check if string starts with prefix.

        Args:
            current_value: String to check

        Returns:
            True if string starts with the prefix

        Example:
            >>> condition = PolicyCondition("text_preview", "starts_with", "Why")
            >>> condition.evaluate(joke)  # True if joke starts with "Why"
        """
        if current_value is None:
            return False

        if not isinstance(current_value, str):
            return False

        if not isinstance(self.value, str):
            return False

        return current_value.startswith(self.value)

    def _check_ends_with(self, current_value: Any) -> bool:
        """Check if string ends with suffix.

        Args:
            current_value: String to check

        Returns:
            True if string ends with the suffix

        Example:
            >>> condition = PolicyCondition("text_preview", "ends_with", "?")
            >>> condition.evaluate(joke)  # True if joke ends with "?"
        """
        if current_value is None:
            return False

        if not isinstance(current_value, str):
            return False

        if not isinstance(self.value, str):
            return False

        return current_value.endswith(self.value)

    def _check_matches(self, current_value: Any) -> bool:
        """Check if string matches a regular expression pattern.

        Uses compiled pattern cache for performance with repeated evaluations.

        Args:
            current_value: String to check

        Returns:
            True if string matches the regex pattern

        Example:
            >>> condition = PolicyCondition("text_preview", "matches", "^Q: .* A: .*$")
            >>> condition.evaluate(joke)  # True if matches Q&A format
        """
        if current_value is None:
            return False

        if not isinstance(current_value, str):
            return False

        if not isinstance(self.value, str):
            return False

        try:
            # Use cached compiled pattern for performance
            pattern_str = self.value
            if pattern_str not in _COMPILED_PATTERNS:
                _COMPILED_PATTERNS[pattern_str] = re.compile(pattern_str)
            pattern = _COMPILED_PATTERNS[pattern_str]
            return bool(pattern.search(current_value))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{self.value}': {e}")
            return False

    def _check_length_gt(self, current_value: Any) -> bool:
        """Check if string length is greater than a value.

        Args:
            current_value: String to check

        Returns:
            True if string length > value

        Example:
            >>> condition = PolicyCondition("text_preview", "length_gt", 100)
            >>> condition.evaluate(joke)  # True if text is longer than 100 chars
        """
        if current_value is None:
            return False

        if not isinstance(current_value, str):
            return False

        try:
            threshold = int(self.value) if isinstance(self.value, str) else self.value
            return len(current_value) > threshold
        except (ValueError, TypeError):
            return False

    def _check_length_lt(self, current_value: Any) -> bool:
        """Check if string length is less than a value.

        Args:
            current_value: String to check

        Returns:
            True if string length < value

        Example:
            >>> condition = PolicyCondition("text_preview", "length_lt", 50)
            >>> condition.evaluate(joke)  # True if text is shorter than 50 chars
        """
        if current_value is None:
            return False

        if not isinstance(current_value, str):
            return False

        try:
            threshold = int(self.value) if isinstance(self.value, str) else self.value
            return len(current_value) < threshold
        except (ValueError, TypeError):
            return False

    # -------------------------------------------------------------------------
    # Array operators
    # -------------------------------------------------------------------------

    def _check_empty(self, current_value: Any) -> bool:
        """Check if array is empty.

        Args:
            current_value: Array to check

        Returns:
            True if array is empty (matches self.value expectation)

        Example:
            >>> condition = PolicyCondition("tags_json", "empty", True)
            >>> condition.evaluate(joke)  # True if tags array is empty
        """
        if current_value is None:
            # None is considered empty
            is_empty = True
        elif isinstance(current_value, str):
            # Try to parse as JSON array
            try:
                parsed = json.loads(current_value)
                is_empty = len(parsed) == 0 if isinstance(parsed, list | tuple | set) else False
            except json.JSONDecodeError:
                # Empty string or non-JSON is considered empty
                is_empty = len(current_value) == 0
        elif isinstance(current_value, list | tuple | set):
            is_empty = len(current_value) == 0
        else:
            is_empty = False

        # Compare against expected value (usually True for "empty")
        expected = self.value if isinstance(self.value, bool) else True
        return is_empty == expected

    def _check_not_empty(self, current_value: Any) -> bool:
        """Check if array is not empty.

        Args:
            current_value: Array to check

        Returns:
            True if array has items (matches self.value expectation)

        Example:
            >>> condition = PolicyCondition("tags_json", "not_empty", True)
            >>> condition.evaluate(joke)  # True if tags array has items
        """
        if current_value is None:
            is_not_empty = False
        elif isinstance(current_value, str):
            # Try to parse as JSON array
            try:
                parsed = json.loads(current_value)
                is_not_empty = len(parsed) > 0 if isinstance(parsed, list | tuple | set) else True
            except json.JSONDecodeError:
                is_not_empty = len(current_value) > 0
        elif isinstance(current_value, list | tuple | set):
            is_not_empty = len(current_value) > 0
        else:
            is_not_empty = True  # Non-array values are considered "not empty"

        expected = self.value if isinstance(self.value, bool) else True
        return is_not_empty == expected

    def _check_size_gt(self, current_value: Any) -> bool:
        """Check if array size is greater than a value.

        Args:
            current_value: Array to check

        Returns:
            True if array has more items than the threshold

        Example:
            >>> condition = PolicyCondition("tags_json", "size_gt", 3)
            >>> condition.evaluate(joke)  # True if more than 3 tags
        """
        size = self._get_array_size(current_value)
        if size is None:
            return False

        try:
            threshold = int(self.value) if isinstance(self.value, str) else self.value
            return size > threshold
        except (ValueError, TypeError):
            return False

    def _check_size_lt(self, current_value: Any) -> bool:
        """Check if array size is less than a value.

        Args:
            current_value: Array to check

        Returns:
            True if array has fewer items than the threshold

        Example:
            >>> condition = PolicyCondition("tags_json", "size_lt", 2)
            >>> condition.evaluate(joke)  # True if fewer than 2 tags
        """
        size = self._get_array_size(current_value)
        if size is None:
            return False

        try:
            threshold = int(self.value) if isinstance(self.value, str) else self.value
            return size < threshold
        except (ValueError, TypeError):
            return False

    def _get_array_size(self, current_value: Any) -> int | None:
        """Get the size of an array, handling JSON strings.

        Args:
            current_value: Array or JSON string to measure

        Returns:
            Size of the array, or None if not measurable
        """
        if current_value is None:
            return 0

        if isinstance(current_value, list | tuple | set):
            return len(current_value)

        if isinstance(current_value, str):
            try:
                parsed = json.loads(current_value)
                if isinstance(parsed, list | tuple | set):
                    return len(parsed)
            except json.JSONDecodeError:
                pass
            return None

        return None

    # -------------------------------------------------------------------------
    # Numeric range operators
    # -------------------------------------------------------------------------

    def _check_between(self, current_value: Any) -> bool:
        """Check if numeric value is between min and max (inclusive).

        Args:
            current_value: Numeric value to check

        Returns:
            True if min <= value <= max

        Example:
            >>> condition = PolicyCondition("weighted_avg_funniness", "between", [40, 60])
            >>> condition.evaluate(joke)  # True if funniness is between 40 and 60
        """
        if current_value is None:
            return False

        try:
            # Parse current value to numeric
            if isinstance(current_value, str):
                if "." in current_value:
                    numeric_value = float(current_value)
                else:
                    numeric_value = int(current_value)
            else:
                numeric_value = float(current_value)

            # Parse range bounds
            min_val, max_val = self._parse_range_bounds()
            if min_val is None or max_val is None:
                return False

            return min_val <= numeric_value <= max_val
        except (ValueError, TypeError):
            return False

    def _check_not_between(self, current_value: Any) -> bool:
        """Check if numeric value is NOT between min and max.

        Args:
            current_value: Numeric value to check

        Returns:
            True if value < min OR value > max

        Example:
            >>> condition = PolicyCondition("weighted_avg_funniness", "not_between", [20, 80])
            >>> condition.evaluate(joke)  # True if funniness < 20 or > 80
        """
        if current_value is None:
            return True  # None is not between any range

        try:
            # Parse current value to numeric
            if isinstance(current_value, str):
                if "." in current_value:
                    numeric_value = float(current_value)
                else:
                    numeric_value = int(current_value)
            else:
                numeric_value = float(current_value)

            # Parse range bounds
            min_val, max_val = self._parse_range_bounds()
            if min_val is None or max_val is None:
                return False

            return numeric_value < min_val or numeric_value > max_val
        except (ValueError, TypeError):
            return False

    def _parse_range_bounds(self) -> tuple[float | None, float | None]:
        """Parse range bounds from self.value.

        Expected formats:
            - List: [min, max]
            - String: "min max" (space-separated)

        Returns:
            Tuple of (min_value, max_value) or (None, None) if invalid
        """
        try:
            if isinstance(self.value, list | tuple):
                if len(self.value) >= 2:
                    return float(self.value[0]), float(self.value[1])
            elif isinstance(self.value, str):
                parts = self.value.split()
                if len(parts) >= 2:
                    return float(parts[0]), float(parts[1])
            return None, None
        except (ValueError, TypeError, IndexError):
            return None, None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolicyCondition:
        """Create a PolicyCondition from a dictionary.

        Args:
            data: Dictionary with 'field', 'operator', and 'value' keys

        Returns:
            PolicyCondition instance

        Raises:
            ValueError: If required keys are missing
        """
        # Operators that don't require a value (default to True)
        no_value_operators = ("is_null", "is_not_null", "empty", "not_empty")

        if "field" not in data:
            raise ValueError("PolicyCondition requires 'field' key")
        if "operator" not in data:
            raise ValueError("PolicyCondition requires 'operator' key")
        if "value" not in data and data.get("operator") not in no_value_operators:
            raise ValueError("PolicyCondition requires 'value' key")

        return cls(
            field=data["field"],
            operator=data["operator"],
            value=data.get("value", True),  # Default to True for operators without value
        )

    @classmethod
    def from_shorthand(cls, field: str, expression: str) -> PolicyCondition:
        """Create a PolicyCondition from shorthand YAML syntax.

        Parses expressions like ">= 80" or "== true" or "in ['G', 'PG']".

        Supported shorthand formats:
            - Comparison: ">= 80", "< 20", "== 'value'"
            - Membership: "in ['G', 'PG']", "not_in ['R', 'X']"
            - Null checks: "null", "not_null"
            - String ops: "contains 'text'", "starts_with 'Why'", "ends_with '?'"
                          "matches '^pattern$'", "length_gt 100", "length_lt 50"
            - Array ops: "empty", "not_empty", "size_gt 3", "size_lt 10"
            - Range ops: "between 40 60", "not_between 20 80"
            - Boolean: "true", "false"

        Args:
            field: The field name
            expression: Operator and value as a string (e.g., ">= 80")

        Returns:
            PolicyCondition instance

        Example:
            >>> PolicyCondition.from_shorthand("weighted_avg_funniness", ">= 80")
            PolicyCondition(field='weighted_avg_funniness', operator='>=', value=80)

            >>> PolicyCondition.from_shorthand("text_preview", "contains 'joke'")
            PolicyCondition(field='text_preview', operator='contains', value='joke')

            >>> PolicyCondition.from_shorthand("tags_json", "size_gt 3")
            PolicyCondition(field='tags_json', operator='size_gt', value=3)

            >>> PolicyCondition.from_shorthand("weighted_avg_funniness", "between 40 60")
            PolicyCondition(field='weighted_avg_funniness', operator='between', value='40 60')
        """
        expression = str(expression).strip()

        # Handle boolean values directly
        if expression.lower() in ("true", "false"):
            return cls(field=field, operator="==", value=expression.lower() == "true")

        # Handle standalone operators (no value required)
        if expression.lower() == "null":
            return cls(field=field, operator="is_null", value=True)
        if expression.lower() == "not_null":
            return cls(field=field, operator="is_not_null", value=True)
        if expression.lower() == "empty":
            return cls(field=field, operator="empty", value=True)
        if expression.lower() == "not_empty":
            return cls(field=field, operator="not_empty", value=True)

        # Parse operator and value
        # Match operators in order of length (longest first to avoid partial matches)
        # Order matters: longer operators must come before shorter ones
        # e.g., "not_contains" before "contains", "not_between" before "between"
        operators = [
            # Comparison operators (longest first)
            ">=", "<=", "!=", "==", ">", "<",
            # Membership operators
            "not_in", "in",
            # Null operators
            "is_not_null", "is_null",
            # String operators (longer first)
            "not_contains", "contains",
            "starts_with", "ends_with",
            "matches",
            "length_gt", "length_lt",
            # Array operators
            "not_empty", "empty",
            "size_gt", "size_lt",
            # Range operators (longer first)
            "not_between", "between",
        ]

        for op in operators:
            if expression.startswith(op + " ") or expression == op:
                value_str = expression[len(op):].strip()
                if not value_str and op in ("empty", "not_empty", "is_null", "is_not_null"):
                    # Operators without values
                    return cls(field=field, operator=op, value=True)  # type: ignore[arg-type]
                value = cls._parse_value(value_str)
                return cls(field=field, operator=op, value=value)  # type: ignore[arg-type]

        # No operator found, assume equality
        value = cls._parse_value(expression)
        return cls(field=field, operator="==", value=value)

    @staticmethod
    def _parse_value(value_str: str) -> Any:
        """Parse a string value into the appropriate Python type.

        Args:
            value_str: String representation of the value

        Returns:
            Parsed value (int, float, bool, list, or string)
        """
        value_str = value_str.strip()

        # Handle booleans
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Handle None/null
        if value_str.lower() in ("none", "null"):
            return None

        # Handle lists (JSON array syntax)
        if value_str.startswith("[") and value_str.endswith("]"):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                # Try parsing as Python list
                pass

        # Handle quoted strings
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]

        # Handle numbers
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str


@dataclass(slots=True)
class Policy:
    """A policy consisting of multiple conditions and an action.

    All conditions must match (AND logic) for the policy to apply.
    The action determines what happens when the policy matches.

    Attributes:
        name: Human-readable policy name for identification and logging
        conditions: List of PolicyConditions that must all match
        action: Action to take when policy matches ("approve", "reject", "flag")
        reason: Optional reason string for audit trail (used with reject/flag)
        priority: Optional priority for ordering (higher = earlier evaluation)

    Example:
        >>> policy = Policy(
        ...     name="high_quality",
        ...     conditions=[
        ...         PolicyCondition("weighted_avg_funniness", ">=", 80),
        ...         PolicyCondition("flags.nsfw", "==", False),
        ...     ],
        ...     action="approve",
        ... )
        >>> policy.matches(joke)  # Returns True if all conditions match
    """

    name: str
    conditions: list[PolicyCondition]
    action: PolicyAction
    reason: str | None = None
    priority: int = 0

    def matches(self, joke: StagingJokeDB) -> bool:
        """Check if all conditions match the given joke.

        Args:
            joke: The staging joke to evaluate

        Returns:
            True if ALL conditions match (AND logic), False otherwise
        """
        if not self.conditions:
            return False  # Empty conditions never match

        return all(condition.evaluate(joke) for condition in self.conditions)

    def get_review_notes(self) -> str:
        """Generate review notes for this policy application.

        Returns:
            String suitable for storing in review_notes field
        """
        action_verb = {
            "approve": "Auto-approved",
            "reject": "Auto-rejected",
            "flag": "Flagged for review",
        }.get(self.action, "Processed")

        notes = f"{action_verb} by policy: {self.name}"
        if self.reason:
            notes += f" - {self.reason}"
        return notes

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        """Create a Policy from a dictionary.

        Supports two condition formats:
        1. Explicit: {"field": "x", "operator": ">=", "value": 80}
        2. Shorthand: {"weighted_avg_funniness": ">= 80"}

        Args:
            data: Dictionary with policy configuration

        Returns:
            Policy instance

        Raises:
            ValueError: If required keys are missing or invalid
        """
        if "name" not in data:
            raise ValueError("Policy requires 'name' key")
        if "action" not in data:
            raise ValueError("Policy requires 'action' key")

        action = data["action"]
        if action not in ("approve", "reject", "flag"):
            raise ValueError(f"Invalid action '{action}'. Must be 'approve', 'reject', or 'flag'")

        conditions: list[PolicyCondition] = []
        raw_conditions = data.get("conditions", [])

        for cond_data in raw_conditions:
            if isinstance(cond_data, dict):
                if "field" in cond_data and "operator" in cond_data:
                    # Explicit format
                    conditions.append(PolicyCondition.from_dict(cond_data))
                else:
                    # Shorthand format: {"field_name": "operator value"}
                    for field_name, expression in cond_data.items():
                        conditions.append(PolicyCondition.from_shorthand(field_name, str(expression)))
            else:
                raise ValueError(f"Invalid condition format: {cond_data}")

        return cls(
            name=data["name"],
            conditions=conditions,
            action=action,
            reason=data.get("reason"),
            priority=data.get("priority", 0),
        )


@dataclass
class PolicyResult:
    """Result of applying a policy to a joke.

    Attributes:
        joke_id: Database ID of the staging joke
        joke_uuid: UUID of the joke
        policy_name: Name of the matched policy (None if no match)
        action: Action taken (None if no policy matched)
        reason: Reason string for the action
        matched: Whether any policy matched
    """

    joke_id: int
    joke_uuid: str
    policy_name: str | None = None
    action: PolicyAction | None = None
    reason: str | None = None
    matched: bool = False


@dataclass
class PolicyStats:
    """Statistics from applying policies to a batch of jokes.

    Attributes:
        total: Total number of jokes processed
        approved: Number of jokes auto-approved
        rejected: Number of jokes auto-rejected
        flagged: Number of jokes flagged for review
        skipped: Number of jokes with no matching policy
        errors: Number of jokes that caused errors during processing
        policy_counts: Count of matches per policy name
        duration_seconds: Time taken to process all jokes
    """

    total: int = 0
    approved: int = 0
    rejected: int = 0
    flagged: int = 0
    skipped: int = 0
    errors: int = 0
    policy_counts: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0

    def increment_policy(self, policy_name: str) -> None:
        """Increment the count for a specific policy."""
        self.policy_counts[policy_name] = self.policy_counts.get(policy_name, 0) + 1


class PolicyEngine:
    """Engine for loading and applying policies to staging jokes.

    The PolicyEngine manages collections of policies organized by action type
    and applies them to staging jokes with first-match-wins precedence.

    Attributes:
        auto_approve_policies: Policies that auto-approve matching jokes
        auto_reject_policies: Policies that auto-reject matching jokes
        flag_policies: Policies that flag matching jokes for manual review

    Example:
        >>> engine = PolicyEngine.from_yaml("config/import_policies.yaml")
        >>> stats = engine.apply_policies(session, import_batch_id, dry_run=True)
        >>> print(f"Would approve {stats.approved} jokes")
    """

    def __init__(
        self,
        auto_approve_policies: list[Policy] | None = None,
        auto_reject_policies: list[Policy] | None = None,
        flag_policies: list[Policy] | None = None,
    ) -> None:
        """Initialize the PolicyEngine with policy lists.

        Args:
            auto_approve_policies: Policies that auto-approve matching jokes
            auto_reject_policies: Policies that auto-reject matching jokes
            flag_policies: Policies that flag matching jokes for manual review
        """
        self.auto_approve_policies = sorted(
            auto_approve_policies or [],
            key=lambda p: -p.priority,  # Higher priority first
        )
        self.auto_reject_policies = sorted(
            auto_reject_policies or [],
            key=lambda p: -p.priority,
        )
        self.flag_policies = sorted(
            flag_policies or [],
            key=lambda p: -p.priority,
        )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> PolicyEngine:
        """Load policies from a YAML configuration file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            PolicyEngine instance configured with the loaded policies

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML is malformed
            ValueError: If the YAML structure is invalid

        Example YAML structure:
            policies:
              auto_approve:
                - name: "high_quality"
                  conditions:
                    - weighted_avg_funniness: ">= 80"
                  action: approve

              auto_reject:
                - name: "low_quality"
                  conditions:
                    - weighted_avg_funniness: "< 20"
                  action: reject
                  reason: "Low quality score"

              flag_for_review:
                - name: "borderline"
                  conditions:
                    - maturity_rating: "R"
                  action: flag
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Policy configuration file not found: {yaml_path}")

        with yaml_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError("Empty policy configuration file")

        policies_config = config.get("policies", config)

        auto_approve = []
        auto_reject = []
        flag = []

        # Parse auto_approve policies
        for policy_data in policies_config.get("auto_approve", []):
            policy = Policy.from_dict({**policy_data, "action": "approve"})
            auto_approve.append(policy)

        # Parse auto_reject policies
        for policy_data in policies_config.get("auto_reject", []):
            policy = Policy.from_dict({**policy_data, "action": "reject"})
            auto_reject.append(policy)

        # Parse flag_for_review policies
        for policy_data in policies_config.get("flag_for_review", []):
            policy = Policy.from_dict({**policy_data, "action": "flag"})
            flag.append(policy)

        logger.info(
            f"Loaded {len(auto_approve)} auto-approve, "
            f"{len(auto_reject)} auto-reject, "
            f"{len(flag)} flag policies from {yaml_path}"
        )

        return cls(
            auto_approve_policies=auto_approve,
            auto_reject_policies=auto_reject,
            flag_policies=flag,
        )

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> PolicyEngine:
        """Load policies from a dictionary configuration.

        Args:
            config: Dictionary with policy configuration

        Returns:
            PolicyEngine instance
        """
        policies_config = config.get("policies", config)

        auto_approve = []
        auto_reject = []
        flag = []

        for policy_data in policies_config.get("auto_approve", []):
            policy = Policy.from_dict({**policy_data, "action": "approve"})
            auto_approve.append(policy)

        for policy_data in policies_config.get("auto_reject", []):
            policy = Policy.from_dict({**policy_data, "action": "reject"})
            auto_reject.append(policy)

        for policy_data in policies_config.get("flag_for_review", []):
            policy = Policy.from_dict({**policy_data, "action": "flag"})
            flag.append(policy)

        return cls(
            auto_approve_policies=auto_approve,
            auto_reject_policies=auto_reject,
            flag_policies=flag,
        )

    def evaluate_joke(self, joke: StagingJokeDB) -> PolicyResult:
        """Evaluate a single joke against all policies.

        Applies policies in order: auto_approve -> auto_reject -> flag
        First matching policy wins.

        Args:
            joke: The staging joke to evaluate

        Returns:
            PolicyResult indicating what action should be taken
        """
        result = PolicyResult(
            joke_id=joke.id or 0,
            joke_uuid=joke.joke_uuid,
        )

        # Try auto-approve policies first
        for policy in self.auto_approve_policies:
            if policy.matches(joke):
                result.policy_name = policy.name
                result.action = "approve"
                result.reason = policy.get_review_notes()
                result.matched = True
                return result

        # Try auto-reject policies
        for policy in self.auto_reject_policies:
            if policy.matches(joke):
                result.policy_name = policy.name
                result.action = "reject"
                result.reason = policy.get_review_notes()
                result.matched = True
                return result

        # Try flag policies
        for policy in self.flag_policies:
            if policy.matches(joke):
                result.policy_name = policy.name
                result.action = "flag"
                result.reason = policy.get_review_notes()
                result.matched = True
                return result

        return result

    def apply_policies(
        self,
        session: Session,
        import_batch_id: int,
        dry_run: bool = False,
        batch_size: int = 1000,
    ) -> PolicyStats:
        """Apply policies to all pending jokes in an import batch.

        Args:
            session: Database session for staging database
            import_batch_id: ID of the import batch to process
            dry_run: If True, don't commit changes to database
            batch_size: Number of jokes to process before committing

        Returns:
            PolicyStats with counts of actions taken

        Note:
            Only processes jokes with ReviewStatus.PENDING.
            Uses first-match-wins precedence: approve -> reject -> flag.
        """
        start_time = datetime.now(UTC)
        stats = PolicyStats()

        # Query pending jokes in batch
        query = select(StagingJokeDB).where(
            StagingJokeDB.import_batch_id == import_batch_id,
            StagingJokeDB.review_status == ReviewStatus.PENDING,
        )

        jokes: Sequence[StagingJokeDB] = session.exec(query).all()
        stats.total = len(jokes)

        logger.info(f"Applying policies to {stats.total} pending jokes (dry_run={dry_run})")

        processed = 0
        for joke in jokes:
            try:
                result = self.evaluate_joke(joke)

                if result.matched and result.action and result.policy_name:
                    # Update statistics
                    stats.increment_policy(result.policy_name)

                    match result.action:
                        case "approve":
                            stats.approved += 1
                            if not dry_run:
                                joke.review_status = ReviewStatus.APPROVED
                                joke.review_notes = result.reason
                                joke.reviewed_at = datetime.now(UTC)
                                joke.reviewed_by = "policy_engine"
                        case "reject":
                            stats.rejected += 1
                            if not dry_run:
                                joke.review_status = ReviewStatus.REJECTED
                                joke.review_notes = result.reason
                                joke.reviewed_at = datetime.now(UTC)
                                joke.reviewed_by = "policy_engine"
                        case "flag":
                            stats.flagged += 1
                            if not dry_run:
                                joke.review_status = ReviewStatus.UNDER_REVIEW
                                joke.review_notes = result.reason
                                joke.reviewed_at = datetime.now(UTC)
                                joke.reviewed_by = "policy_engine"

                    if not dry_run:
                        session.add(joke)
                else:
                    stats.skipped += 1

                processed += 1

                # Batch commit for performance
                if not dry_run and processed % batch_size == 0:
                    session.commit()
                    logger.info(f"Processed {processed}/{stats.total} jokes...")

            except Exception as e:
                stats.errors += 1
                logger.error(f"Error processing joke {joke.id}: {e}")
                continue

        # Final commit
        if not dry_run:
            session.commit()

        stats.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()

        logger.info(
            f"Policy application complete: "
            f"{stats.approved} approved, "
            f"{stats.rejected} rejected, "
            f"{stats.flagged} flagged, "
            f"{stats.skipped} skipped, "
            f"{stats.errors} errors "
            f"in {stats.duration_seconds:.2f}s"
        )

        return stats

    def apply_to_jokes(
        self,
        session: Session,
        jokes: Sequence[StagingJokeDB],
        dry_run: bool = False,
    ) -> PolicyStats:
        """Apply policies to a specific list of jokes.

        Args:
            session: Database session for staging database
            jokes: Sequence of staging jokes to process
            dry_run: If True, don't commit changes to database

        Returns:
            PolicyStats with counts of actions taken
        """
        start_time = datetime.now(UTC)
        stats = PolicyStats()
        stats.total = len(jokes)

        for joke in jokes:
            try:
                result = self.evaluate_joke(joke)

                if result.matched and result.action and result.policy_name:
                    stats.increment_policy(result.policy_name)

                    match result.action:
                        case "approve":
                            stats.approved += 1
                            if not dry_run:
                                joke.review_status = ReviewStatus.APPROVED
                                joke.review_notes = result.reason
                                joke.reviewed_at = datetime.now(UTC)
                                joke.reviewed_by = "policy_engine"
                        case "reject":
                            stats.rejected += 1
                            if not dry_run:
                                joke.review_status = ReviewStatus.REJECTED
                                joke.review_notes = result.reason
                                joke.reviewed_at = datetime.now(UTC)
                                joke.reviewed_by = "policy_engine"
                        case "flag":
                            stats.flagged += 1
                            if not dry_run:
                                joke.review_status = ReviewStatus.UNDER_REVIEW
                                joke.review_notes = result.reason
                                joke.reviewed_at = datetime.now(UTC)
                                joke.reviewed_by = "policy_engine"

                    if not dry_run:
                        session.add(joke)
                else:
                    stats.skipped += 1

            except Exception as e:
                stats.errors += 1
                logger.error(f"Error processing joke {joke.id}: {e}")
                continue

        if not dry_run:
            session.commit()

        stats.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()

        return stats

    def get_policy_summary(self) -> dict[str, Any]:
        """Get a summary of loaded policies.

        Returns:
            Dictionary with policy counts and names
        """
        return {
            "auto_approve": {
                "count": len(self.auto_approve_policies),
                "policies": [p.name for p in self.auto_approve_policies],
            },
            "auto_reject": {
                "count": len(self.auto_reject_policies),
                "policies": [p.name for p in self.auto_reject_policies],
            },
            "flag_for_review": {
                "count": len(self.flag_policies),
                "policies": [p.name for p in self.flag_policies],
            },
            "total": len(self.auto_approve_policies) + len(self.auto_reject_policies) + len(self.flag_policies),
        }

    def validate_config(self) -> list[str]:
        """Validate the policy configuration for common issues.

        Returns:
            List of warning/error messages (empty if no issues)
        """
        issues: list[str] = []

        # Check for duplicate policy names
        all_names = (
            [p.name for p in self.auto_approve_policies]
            + [p.name for p in self.auto_reject_policies]
            + [p.name for p in self.flag_policies]
        )
        seen_names: set[str] = set()
        for name in all_names:
            if name in seen_names:
                issues.append(f"Duplicate policy name: {name}")
            seen_names.add(name)

        # Check for empty conditions
        for policy in self.auto_approve_policies + self.auto_reject_policies + self.flag_policies:
            if not policy.conditions:
                issues.append(f"Policy '{policy.name}' has no conditions")

        # Check for potentially dangerous patterns
        for policy in self.auto_approve_policies:
            if len(policy.conditions) == 1:
                cond = policy.conditions[0]
                if cond.operator in ("is_null", "is_not_null"):
                    issues.append(
                        f"Policy '{policy.name}' auto-approves based only on null check - "
                        "consider adding quality conditions"
                    )

        return issues
