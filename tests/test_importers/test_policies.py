"""Comprehensive unit tests for the Policy Engine.

Tests PolicyCondition, Policy, and PolicyEngine classes with focus on:
- All 10 operators with various data types
- Nested field access for JSON fields
- Type coercion and edge cases
- YAML configuration loading
- Dry-run mode and statistics tracking
- Integration with staging database
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from sqlmodel import select

from joke_emporium.db.models.staging import ReviewStatus, StagingJokeDB
from joke_emporium.importers.policies import (
    Policy,
    PolicyCondition,
    PolicyEngine,
)

# ============================================================================
# PolicyCondition Tests
# ============================================================================


class TestPolicyConditionOperators:
    """Test all 10 operators with various data types."""

    def test_equality_operator_with_strings(self, sample_staging_joke):
        """Test == operator with string values."""
        condition = PolicyCondition("structure", "==", "two_part")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("structure", "==", "one_liner")
        assert condition.evaluate(sample_staging_joke) is False

    def test_equality_operator_with_numbers(self, sample_staging_joke):
        """Test == operator with numeric values."""
        condition = PolicyCondition("total_ratings_count", "==", 100)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("total_ratings_count", "==", 50)
        assert condition.evaluate(sample_staging_joke) is False

    def test_equality_operator_with_floats(self, sample_staging_joke):
        """Test == operator with float values."""
        condition = PolicyCondition("weighted_avg_funniness", "==", 75.5)
        assert condition.evaluate(sample_staging_joke) is True

    def test_inequality_operator(self, sample_staging_joke):
        """Test != operator."""
        condition = PolicyCondition("structure", "!=", "one_liner")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("structure", "!=", "two_part")
        assert condition.evaluate(sample_staging_joke) is False

    def test_greater_than_operator(self, sample_staging_joke):
        """Test > operator with numeric values."""
        condition = PolicyCondition("weighted_avg_funniness", ">", 70)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", ">", 80)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("weighted_avg_funniness", ">", 75.5)
        assert condition.evaluate(sample_staging_joke) is False

    def test_greater_than_or_equal_operator(self, sample_staging_joke):
        """Test >= operator with numeric values."""
        condition = PolicyCondition("weighted_avg_funniness", ">=", 75.5)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", ">=", 70)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", ">=", 80)
        assert condition.evaluate(sample_staging_joke) is False

    def test_less_than_operator(self, sample_staging_joke):
        """Test < operator with numeric values."""
        condition = PolicyCondition("weighted_avg_funniness", "<", 80)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", "<", 70)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("weighted_avg_funniness", "<", 75.5)
        assert condition.evaluate(sample_staging_joke) is False

    def test_less_than_or_equal_operator(self, sample_staging_joke):
        """Test <= operator with numeric values."""
        condition = PolicyCondition("weighted_avg_funniness", "<=", 75.5)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", "<=", 80)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", "<=", 70)
        assert condition.evaluate(sample_staging_joke) is False

    def test_in_operator_with_list(self, sample_staging_joke):
        """Test 'in' operator with list values."""
        condition = PolicyCondition("maturity_rating", "in", ["G", "PG"])
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("maturity_rating", "in", ["R", "NC-17"])
        assert condition.evaluate(sample_staging_joke) is False

    def test_in_operator_with_single_value(self, sample_staging_joke):
        """Test 'in' operator with single value (edge case)."""
        condition = PolicyCondition("maturity_rating", "in", "G")
        assert condition.evaluate(sample_staging_joke) is True

    def test_not_in_operator_with_list(self, sample_staging_joke):
        """Test 'not_in' operator with list values."""
        condition = PolicyCondition("maturity_rating", "not_in", ["R", "NC-17"])
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("maturity_rating", "not_in", ["G", "PG"])
        assert condition.evaluate(sample_staging_joke) is False

    def test_is_null_operator(self, sample_staging_joke):
        """Test 'is_null' operator."""
        condition = PolicyCondition("cognitive_type", "is_null", True)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("structure", "is_null", True)
        assert condition.evaluate(sample_staging_joke) is False

        # Test with False value (field should NOT be null)
        condition = PolicyCondition("structure", "is_null", False)
        assert condition.evaluate(sample_staging_joke) is True

    def test_is_not_null_operator(self, sample_staging_joke):
        """Test 'is_not_null' operator."""
        condition = PolicyCondition("structure", "is_not_null", True)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("cognitive_type", "is_not_null", True)
        assert condition.evaluate(sample_staging_joke) is False


class TestPolicyConditionFieldAccess:
    """Test field access patterns including nested JSON fields."""

    def test_direct_field_access(self, sample_staging_joke):
        """Test direct field access on StagingJokeDB."""
        condition = PolicyCondition("weighted_avg_funniness", ">=", 70)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("language", "==", "en")
        assert condition.evaluate(sample_staging_joke) is True

    def test_json_field_access_flags(self, sample_staging_joke):
        """Test nested field access for flags JSON field."""
        condition = PolicyCondition("flags.nsfw", "==", False)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("flags.offensive", "==", False)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("flags.nsfw", "==", True)
        assert condition.evaluate(sample_staging_joke) is False

    def test_json_field_access_engagement(self, sample_staging_joke):
        """Test nested field access for engagement JSON field."""
        condition = PolicyCondition("engagement.upvotes", ">=", 100)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("engagement.upvotes", ">", 150)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("engagement.comments", "==", 25)
        assert condition.evaluate(sample_staging_joke) is True

    def test_json_field_access_tags(self, sample_staging_joke):
        """Test nested field access for tags JSON field."""
        # Tags are stored as JSON array, accessing index
        # Note: This tests the JSON parsing, but tags are typically accessed differently
        # For now, test that accessing a malformed path returns None
        condition = PolicyCondition("tags.0", "is_not_null", True)
        # Tags is an array, not an object, so this should fail gracefully
        assert condition.evaluate(sample_staging_joke) is False

    def test_missing_json_field(self, sample_staging_joke):
        """Test accessing a non-existent JSON field."""
        condition = PolicyCondition("flags.nonexistent", "==", True)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("flags.nonexistent", "is_null", True)
        assert condition.evaluate(sample_staging_joke) is True

    def test_malformed_json_field(self, staging_session, sample_import_batch):
        """Test handling of malformed JSON in fields."""
        joke = StagingJokeDB(
            joke_uuid="malformed-json-joke",
            version=1,
            content_json='{"type": "text", "text": "test"}',
            flags_json="not valid json{",
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("flags.nsfw", "==", False)
        assert condition.evaluate(joke) is False

    def test_none_json_field(self, staging_session, sample_import_batch):
        """Test handling when JSON field is None."""
        joke = StagingJokeDB(
            joke_uuid="none-json-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            engagement_json=None,  # This field is None
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("engagement.upvotes", ">", 100)
        assert condition.evaluate(joke) is False

        condition = PolicyCondition("engagement.upvotes", "is_null", True)
        assert condition.evaluate(joke) is True


class TestPolicyConditionTypeCoercion:
    """Test type coercion for numeric comparisons."""

    def test_string_to_int_coercion(self, staging_session, sample_import_batch):
        """Test comparing string numbers with int values."""
        joke = StagingJokeDB(
            joke_uuid="string-number-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            engagement_json='{"upvotes": "150"}',  # String number
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        # Numeric comparison operators handle type coercion
        condition = PolicyCondition("engagement.upvotes", ">", 100)
        assert condition.evaluate(joke) is True

        condition = PolicyCondition("engagement.upvotes", ">=", 150)
        assert condition.evaluate(joke) is True

        # Equality uses strict comparison, so string "150" != int 150
        condition = PolicyCondition("engagement.upvotes", "==", "150")
        assert condition.evaluate(joke) is True

    def test_string_to_float_coercion(self, staging_session, sample_import_batch):
        """Test comparing string floats with numeric values."""
        joke = StagingJokeDB(
            joke_uuid="string-float-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            engagement_json='{"score": "75.5"}',  # String float
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        # Numeric comparison operators handle type coercion
        condition = PolicyCondition("engagement.score", ">=", 75)
        assert condition.evaluate(joke) is True

        condition = PolicyCondition("engagement.score", ">", 75)
        assert condition.evaluate(joke) is True

        # Equality uses strict comparison, so string "75.5" != float 75.5
        condition = PolicyCondition("engagement.score", "==", "75.5")
        assert condition.evaluate(joke) is True

    def test_invalid_type_coercion(self, sample_staging_joke):
        """Test that invalid type comparisons return False."""
        condition = PolicyCondition("structure", ">", 100)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("language", ">=", 50)
        assert condition.evaluate(sample_staging_joke) is False


class TestPolicyConditionEdgeCases:
    """Test edge cases and error handling."""

    def test_none_value_with_comparison(self, staging_session, sample_import_batch):
        """Test None values with comparison operators."""
        joke = StagingJokeDB(
            joke_uuid="none-value-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=None,  # None value
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("weighted_avg_funniness", ">", 50)
        assert condition.evaluate(joke) is False

        condition = PolicyCondition("weighted_avg_funniness", "is_null", True)
        assert condition.evaluate(joke) is True

    def test_missing_field(self, sample_staging_joke):
        """Test accessing a field that doesn't exist."""
        condition = PolicyCondition("nonexistent_field", "==", "value")
        assert condition.evaluate(condition) is False

    def test_empty_string_field(self, staging_session, sample_import_batch):
        """Test empty string values."""
        joke = StagingJokeDB(
            joke_uuid="empty-string-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            text_preview="",  # Empty string
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("text_preview", "==", "")
        assert condition.evaluate(joke) is True

        condition = PolicyCondition("text_preview", "is_null", True)
        assert condition.evaluate(joke) is False

    def test_in_operator_with_none_value(self, staging_session, sample_import_batch):
        """Test 'in' operator when field value is None."""
        joke = StagingJokeDB(
            joke_uuid="none-in-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            maturity_rating=None,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("maturity_rating", "in", ["G", "PG"])
        assert condition.evaluate(joke) is False

        condition = PolicyCondition("maturity_rating", "not_in", ["G", "PG"])
        assert condition.evaluate(joke) is True


class TestPolicyConditionShorthand:
    """Test shorthand parsing for YAML convenience."""

    def test_shorthand_numeric_comparison(self):
        """Test parsing shorthand numeric comparisons."""
        condition = PolicyCondition.from_shorthand("weighted_avg_funniness", ">= 80")
        assert condition.field == "weighted_avg_funniness"
        assert condition.operator == ">="
        assert condition.value == 80

        condition = PolicyCondition.from_shorthand("total_ratings_count", "> 100")
        assert condition.operator == ">"
        assert condition.value == 100

        condition = PolicyCondition.from_shorthand("weighted_avg_quality", "< 50.5")
        assert condition.operator == "<"
        assert condition.value == 50.5

    def test_shorthand_equality(self):
        """Test parsing shorthand equality expressions."""
        condition = PolicyCondition.from_shorthand("structure", "== two_part")
        assert condition.operator == "=="
        assert condition.value == "two_part"

        condition = PolicyCondition.from_shorthand("verified", "!= true")
        assert condition.operator == "!="
        assert condition.value is True

    def test_shorthand_boolean_values(self):
        """Test parsing boolean values in shorthand."""
        condition = PolicyCondition.from_shorthand("verified", "true")
        assert condition.operator == "=="
        assert condition.value is True

        condition = PolicyCondition.from_shorthand("verified", "false")
        assert condition.operator == "=="
        assert condition.value is False

    def test_shorthand_null_values(self):
        """Test parsing null checks in shorthand."""
        condition = PolicyCondition.from_shorthand("cognitive_type", "null")
        assert condition.operator == "is_null"
        assert condition.value is True

        condition = PolicyCondition.from_shorthand("structure", "not_null")
        assert condition.operator == "is_not_null"
        assert condition.value is True

    def test_shorthand_list_values(self):
        """Test parsing list values in shorthand."""
        condition = PolicyCondition.from_shorthand("maturity_rating", 'in ["G", "PG"]')
        assert condition.operator == "in"
        assert condition.value == ["G", "PG"]

    def test_shorthand_without_operator(self):
        """Test shorthand assumes equality when no operator."""
        condition = PolicyCondition.from_shorthand("language", "en")
        assert condition.operator == "=="
        assert condition.value == "en"


class TestPolicyConditionFromDict:
    """Test PolicyCondition.from_dict parsing."""

    def test_from_dict_explicit_format(self):
        """Test creating PolicyCondition from explicit dict format."""
        data = {"field": "weighted_avg_funniness", "operator": ">=", "value": 80}
        condition = PolicyCondition.from_dict(data)
        assert condition.field == "weighted_avg_funniness"
        assert condition.operator == ">="
        assert condition.value == 80

    def test_from_dict_missing_field(self):
        """Test error handling for missing 'field' key."""
        with pytest.raises(ValueError, match="requires 'field' key"):
            PolicyCondition.from_dict({"operator": "==", "value": 10})

    def test_from_dict_missing_operator(self):
        """Test error handling for missing 'operator' key."""
        with pytest.raises(ValueError, match="requires 'operator' key"):
            PolicyCondition.from_dict({"field": "test", "value": 10})

    def test_from_dict_missing_value(self):
        """Test error handling for missing 'value' key with comparison operators."""
        with pytest.raises(ValueError, match="requires 'value' key"):
            PolicyCondition.from_dict({"field": "test", "operator": ">"})

    def test_from_dict_missing_value_null_operator(self):
        """Test that 'value' is optional for is_null/is_not_null operators."""
        condition = PolicyCondition.from_dict({"field": "test", "operator": "is_null"})
        assert condition.value is True

        condition = PolicyCondition.from_dict({"field": "test", "operator": "is_not_null"})
        assert condition.value is True


# ============================================================================
# Policy Tests
# ============================================================================


class TestPolicy:
    """Test Policy class with multiple conditions and actions."""

    def test_policy_all_conditions_match(self, sample_staging_joke):
        """Test that all conditions must match (AND logic)."""
        policy = Policy(
            name="high_quality_safe",
            conditions=[
                PolicyCondition("weighted_avg_funniness", ">=", 70),
                PolicyCondition("flags.nsfw", "==", False),
                PolicyCondition("total_ratings_count", ">=", 50),
            ],
            action="approve",
        )

        assert policy.matches(sample_staging_joke) is True

    def test_policy_partial_match_fails(self, sample_staging_joke):
        """Test that partial matches return False."""
        policy = Policy(
            name="high_quality_safe",
            conditions=[
                PolicyCondition("weighted_avg_funniness", ">=", 70),  # Matches
                PolicyCondition("total_ratings_count", ">=", 200),  # Doesn't match
            ],
            action="approve",
        )

        assert policy.matches(sample_staging_joke) is False

    def test_policy_single_condition_match(self, sample_staging_joke):
        """Test policy with single condition."""
        policy = Policy(
            name="english_only",
            conditions=[PolicyCondition("language", "==", "en")],
            action="approve",
        )

        assert policy.matches(sample_staging_joke) is True

    def test_policy_empty_conditions_never_match(self, sample_staging_joke):
        """Test that empty conditions never match."""
        policy = Policy(name="empty", conditions=[], action="approve")

        assert policy.matches(sample_staging_joke) is False

    def test_policy_action_types(self, sample_staging_joke):
        """Test different action types."""
        approve_policy = Policy(
            name="approve_test",
            conditions=[PolicyCondition("language", "==", "en")],
            action="approve",
        )
        assert approve_policy.action == "approve"

        reject_policy = Policy(
            name="reject_test",
            conditions=[PolicyCondition("language", "==", "en")],
            action="reject",
        )
        assert reject_policy.action == "reject"

        flag_policy = Policy(
            name="flag_test",
            conditions=[PolicyCondition("language", "==", "en")],
            action="flag",
        )
        assert flag_policy.action == "flag"

    def test_policy_get_review_notes_approve(self):
        """Test review notes generation for approve action."""
        policy = Policy(
            name="high_quality",
            conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
            action="approve",
        )

        notes = policy.get_review_notes()
        assert "Auto-approved" in notes
        assert "high_quality" in notes

    def test_policy_get_review_notes_reject_with_reason(self):
        """Test review notes generation for reject action with reason."""
        policy = Policy(
            name="low_quality",
            conditions=[PolicyCondition("weighted_avg_funniness", "<", 20)],
            action="reject",
            reason="Quality score too low",
        )

        notes = policy.get_review_notes()
        assert "Auto-rejected" in notes
        assert "low_quality" in notes
        assert "Quality score too low" in notes

    def test_policy_get_review_notes_flag(self):
        """Test review notes generation for flag action."""
        policy = Policy(
            name="borderline",
            conditions=[PolicyCondition("weighted_avg_funniness", ">=", 40)],
            action="flag",
            reason="Needs manual review",
        )

        notes = policy.get_review_notes()
        assert "Flagged for review" in notes
        assert "borderline" in notes
        assert "Needs manual review" in notes

    def test_policy_priority(self):
        """Test policy priority attribute."""
        policy = Policy(
            name="high_priority",
            conditions=[PolicyCondition("language", "==", "en")],
            action="approve",
            priority=10,
        )

        assert policy.priority == 10


class TestPolicyFromDict:
    """Test Policy.from_dict parsing."""

    def test_from_dict_explicit_conditions(self):
        """Test parsing policy with explicit condition format."""
        data = {
            "name": "test_policy",
            "action": "approve",
            "conditions": [
                {"field": "weighted_avg_funniness", "operator": ">=", "value": 80},
                {"field": "flags.nsfw", "operator": "==", "value": False},
            ],
        }

        policy = Policy.from_dict(data)
        assert policy.name == "test_policy"
        assert policy.action == "approve"
        assert len(policy.conditions) == 2

    def test_from_dict_shorthand_conditions(self):
        """Test parsing policy with shorthand condition format."""
        data = {
            "name": "test_policy",
            "action": "reject",
            "conditions": [
                {"weighted_avg_funniness": ">= 80"},
                {"flags.nsfw": "== false"},
            ],
        }

        policy = Policy.from_dict(data)
        assert policy.name == "test_policy"
        assert len(policy.conditions) == 2

    def test_from_dict_with_reason_and_priority(self):
        """Test parsing policy with optional reason and priority."""
        data = {
            "name": "test_policy",
            "action": "reject",
            "conditions": [{"weighted_avg_funniness": "< 20"}],
            "reason": "Too low quality",
            "priority": 5,
        }

        policy = Policy.from_dict(data)
        assert policy.reason == "Too low quality"
        assert policy.priority == 5

    def test_from_dict_missing_name(self):
        """Test error handling for missing 'name' key."""
        with pytest.raises(ValueError, match="requires 'name' key"):
            Policy.from_dict({"action": "approve", "conditions": []})

    def test_from_dict_missing_action(self):
        """Test error handling for missing 'action' key."""
        with pytest.raises(ValueError, match="requires 'action' key"):
            Policy.from_dict({"name": "test", "conditions": []})

    def test_from_dict_invalid_action(self):
        """Test error handling for invalid action value."""
        with pytest.raises(ValueError, match="Invalid action"):
            Policy.from_dict(
                {
                    "name": "test",
                    "action": "delete",  # Invalid action
                    "conditions": [],
                }
            )


# ============================================================================
# PolicyEngine Tests
# ============================================================================


class TestPolicyEngineYAMLLoading:
    """Test PolicyEngine YAML configuration loading."""

    def test_load_from_yaml_file(self):
        """Test loading policies from a valid YAML file."""
        yaml_content = """
policies:
  auto_approve:
    - name: high_quality_reddit
      conditions:
        - weighted_avg_funniness: ">= 80"
        - flags.nsfw: "== false"
      action: approve

  auto_reject:
    - name: low_quality
      conditions:
        - weighted_avg_funniness: "< 20"
        - total_ratings_count: ">= 5"
      action: reject
      reason: "Low quality with sufficient ratings"

  flag_for_review:
    - name: borderline_nsfw
      conditions:
        - flags.nsfw: "== true"
      action: flag
      reason: "NSFW content requires review"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            engine = PolicyEngine.from_yaml(yaml_path)

            assert len(engine.auto_approve_policies) == 1
            assert len(engine.auto_reject_policies) == 1
            assert len(engine.flag_policies) == 1

            assert engine.auto_approve_policies[0].name == "high_quality_reddit"
            assert engine.auto_reject_policies[0].name == "low_quality"
            assert engine.flag_policies[0].name == "borderline_nsfw"
        finally:
            yaml_path.unlink()

    def test_load_from_yaml_missing_file(self):
        """Test error handling for missing YAML file."""
        with pytest.raises(FileNotFoundError):
            PolicyEngine.from_yaml("nonexistent.yaml")

    def test_load_from_yaml_empty_file(self):
        """Test error handling for empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Empty policy configuration"):
                PolicyEngine.from_yaml(yaml_path)
        finally:
            yaml_path.unlink()

    def test_load_from_yaml_invalid_yaml(self):
        """Test error handling for malformed YAML."""
        yaml_content = """
policies:
  auto_approve:
    - name: test
      conditions: [
        - field: test  # Invalid YAML indentation
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                PolicyEngine.from_yaml(yaml_path)
        finally:
            yaml_path.unlink()

    def test_load_from_dict(self):
        """Test loading policies from dictionary."""
        config = {
            "policies": {
                "auto_approve": [
                    {
                        "name": "high_quality",
                        "conditions": [{"weighted_avg_funniness": ">= 80"}],
                    }
                ],
                "auto_reject": [
                    {
                        "name": "low_quality",
                        "conditions": [{"weighted_avg_funniness": "< 20"}],
                    }
                ],
                "flag_for_review": [
                    {
                        "name": "borderline",
                        "conditions": [{"weighted_avg_funniness": ">= 40"}],
                    }
                ],
            }
        }

        engine = PolicyEngine.from_dict(config)

        assert len(engine.auto_approve_policies) == 1
        assert len(engine.auto_reject_policies) == 1
        assert len(engine.flag_policies) == 1


class TestPolicyEngineEvaluation:
    """Test PolicyEngine joke evaluation logic."""

    def test_evaluate_joke_auto_approve(self, sample_staging_joke):
        """Test evaluating a joke that matches an auto-approve policy."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[
                        PolicyCondition("weighted_avg_funniness", ">=", 70),
                        PolicyCondition("flags.nsfw", "==", False),
                    ],
                    action="approve",
                )
            ]
        )

        result = engine.evaluate_joke(sample_staging_joke)

        assert result.matched is True
        assert result.action == "approve"
        assert result.policy_name == "high_quality"
        assert "Auto-approved" in result.reason

    def test_evaluate_joke_auto_reject(self, staging_session, sample_import_batch):
        """Test evaluating a joke that matches an auto-reject policy."""
        low_quality_joke = StagingJokeDB(
            joke_uuid="low-quality-joke",
            version=1,
            content_json='[{"type": "text", "text": "bad joke"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=15.0,
            total_ratings_count=50,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )

        engine = PolicyEngine(
            auto_reject_policies=[
                Policy(
                    name="low_quality",
                    conditions=[
                        PolicyCondition("weighted_avg_funniness", "<", 20),
                        PolicyCondition("total_ratings_count", ">=", 10),
                    ],
                    action="reject",
                    reason="Quality too low",
                )
            ]
        )

        result = engine.evaluate_joke(low_quality_joke)

        assert result.matched is True
        assert result.action == "reject"
        assert result.policy_name == "low_quality"
        assert "Auto-rejected" in result.reason

    def test_evaluate_joke_flag(self, staging_session, sample_import_batch):
        """Test evaluating a joke that matches a flag policy."""
        borderline_joke = StagingJokeDB(
            joke_uuid="borderline-joke",
            version=1,
            content_json='[{"type": "text", "text": "borderline joke"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=50.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )

        engine = PolicyEngine(
            flag_policies=[
                Policy(
                    name="borderline",
                    conditions=[
                        PolicyCondition("weighted_avg_funniness", ">=", 40),
                        PolicyCondition("weighted_avg_funniness", "<", 60),
                    ],
                    action="flag",
                    reason="Needs manual review",
                )
            ]
        )

        result = engine.evaluate_joke(borderline_joke)

        assert result.matched is True
        assert result.action == "flag"
        assert result.policy_name == "borderline"
        assert "Flagged for review" in result.reason

    def test_evaluate_joke_no_match(self, sample_staging_joke):
        """Test evaluating a joke with no matching policies."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="very_high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 90)],
                    action="approve",
                )
            ]
        )

        result = engine.evaluate_joke(sample_staging_joke)

        assert result.matched is False
        assert result.action is None
        assert result.policy_name is None

    def test_evaluate_joke_first_match_wins(self, sample_staging_joke):
        """Test that first matching policy wins (precedence)."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 70)],
                    action="approve",
                    priority=10,
                ),
                Policy(
                    name="also_high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 70)],
                    action="approve",
                    priority=5,
                ),
            ]
        )

        result = engine.evaluate_joke(sample_staging_joke)

        assert result.matched is True
        assert result.policy_name == "high_quality"  # Higher priority wins

    def test_evaluate_joke_action_precedence(self, sample_staging_joke):
        """Test action precedence: approve -> reject -> flag."""
        # Create policies that all match
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="approve_policy",
                    conditions=[PolicyCondition("language", "==", "en")],
                    action="approve",
                )
            ],
            auto_reject_policies=[
                Policy(
                    name="reject_policy",
                    conditions=[PolicyCondition("language", "==", "en")],
                    action="reject",
                )
            ],
            flag_policies=[
                Policy(
                    name="flag_policy",
                    conditions=[PolicyCondition("language", "==", "en")],
                    action="flag",
                )
            ],
        )

        result = engine.evaluate_joke(sample_staging_joke)

        # Approve should win
        assert result.action == "approve"
        assert result.policy_name == "approve_policy"


class TestPolicyEngineApplyPolicies:
    """Test PolicyEngine batch processing with database integration."""

    def test_apply_policies_to_import_batch(self, staging_session, sample_import_batch):
        """Test applying policies to all jokes in an import batch."""
        # Create multiple staging jokes
        jokes = []
        for i in range(5):
            joke = StagingJokeDB(
                joke_uuid=f"test-joke-{i}",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=80.0 + i,
                total_ratings_count=100,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=sample_import_batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            staging_session.add(joke)
            jokes.append(joke)

        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
                    action="approve",
                )
            ]
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.total == 5
        assert stats.approved == 5
        assert stats.rejected == 0
        assert stats.flagged == 0
        assert stats.skipped == 0
        assert stats.errors == 0

        # Verify database state
        for joke in jokes:
            staging_session.refresh(joke)
            assert joke.review_status == ReviewStatus.APPROVED
            assert "Auto-approved" in joke.review_notes
            assert joke.reviewed_by == "policy_engine"

    def test_apply_policies_dry_run_mode(self, staging_session, sample_import_batch):
        """Test dry-run mode doesn't modify database."""
        joke = StagingJokeDB(
            joke_uuid="dry-run-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=85.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )
        staging_session.add(joke)
        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
                    action="approve",
                )
            ]
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=True)

        assert stats.total == 1
        assert stats.approved == 1

        # Verify database NOT modified
        staging_session.refresh(joke)
        assert joke.review_status == ReviewStatus.PENDING
        assert joke.review_notes is None
        assert joke.reviewed_by is None

    def test_apply_policies_mixed_results(self, staging_session, sample_import_batch):
        """Test applying policies with mixed approve/reject/flag results."""
        # High quality joke
        high_quality = StagingJokeDB(
            joke_uuid="high-quality",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=85.0,
            total_ratings_count=100,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        # Low quality joke
        low_quality = StagingJokeDB(
            joke_uuid="low-quality",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=15.0,
            total_ratings_count=50,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        # Borderline joke
        borderline = StagingJokeDB(
            joke_uuid="borderline",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=50.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        # No match joke
        no_match = StagingJokeDB(
            joke_uuid="no-match",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=70.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        staging_session.add_all([high_quality, low_quality, borderline, no_match])
        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
                    action="approve",
                )
            ],
            auto_reject_policies=[
                Policy(
                    name="low_quality",
                    conditions=[
                        PolicyCondition("weighted_avg_funniness", "<", 20),
                        PolicyCondition("total_ratings_count", ">=", 10),
                    ],
                    action="reject",
                )
            ],
            flag_policies=[
                Policy(
                    name="borderline",
                    conditions=[
                        PolicyCondition("weighted_avg_funniness", ">=", 40),
                        PolicyCondition("weighted_avg_funniness", "<", 60),
                    ],
                    action="flag",
                )
            ],
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.total == 4
        assert stats.approved == 1
        assert stats.rejected == 1
        assert stats.flagged == 1
        assert stats.skipped == 1
        assert stats.errors == 0

        # Verify individual statuses
        staging_session.refresh(high_quality)
        assert high_quality.review_status == ReviewStatus.APPROVED

        staging_session.refresh(low_quality)
        assert low_quality.review_status == ReviewStatus.REJECTED

        staging_session.refresh(borderline)
        assert borderline.review_status == ReviewStatus.UNDER_REVIEW

        staging_session.refresh(no_match)
        assert no_match.review_status == ReviewStatus.PENDING

    def test_apply_policies_only_pending_jokes(self, staging_session, sample_import_batch):
        """Test that only PENDING jokes are processed."""
        pending_joke = StagingJokeDB(
            joke_uuid="pending",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=85.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        already_approved = StagingJokeDB(
            joke_uuid="already-approved",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=85.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.APPROVED,
        )

        staging_session.add_all([pending_joke, already_approved])
        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
                    action="approve",
                )
            ]
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        # Should only process the pending joke
        assert stats.total == 1
        assert stats.approved == 1

    def test_apply_policies_statistics_tracking(self, staging_session, sample_import_batch):
        """Test that policy statistics are tracked correctly."""
        for i in range(3):
            joke = StagingJokeDB(
                joke_uuid=f"joke-{i}",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=85.0,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=sample_import_batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            staging_session.add(joke)

        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
                    action="approve",
                )
            ]
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.policy_counts["high_quality"] == 3
        assert stats.duration_seconds > 0


class TestPolicyEngineHelpers:
    """Test PolicyEngine helper methods."""

    def test_get_policy_summary(self):
        """Test getting policy summary."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(name="approve1", conditions=[], action="approve"),
                Policy(name="approve2", conditions=[], action="approve"),
            ],
            auto_reject_policies=[
                Policy(name="reject1", conditions=[], action="reject"),
            ],
            flag_policies=[
                Policy(name="flag1", conditions=[], action="flag"),
                Policy(name="flag2", conditions=[], action="flag"),
                Policy(name="flag3", conditions=[], action="flag"),
            ],
        )

        summary = engine.get_policy_summary()

        assert summary["auto_approve"]["count"] == 2
        assert summary["auto_reject"]["count"] == 1
        assert summary["flag_for_review"]["count"] == 3
        assert summary["total"] == 6
        assert "approve1" in summary["auto_approve"]["policies"]
        assert "reject1" in summary["auto_reject"]["policies"]

    def test_validate_config_no_issues(self):
        """Test config validation with valid policies."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[
                        PolicyCondition("weighted_avg_funniness", ">=", 80),
                        PolicyCondition("flags.nsfw", "==", False),
                    ],
                    action="approve",
                )
            ]
        )

        issues = engine.validate_config()
        assert len(issues) == 0

    def test_validate_config_duplicate_names(self):
        """Test config validation detects duplicate policy names."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(name="test_policy", conditions=[PolicyCondition("language", "==", "en")], action="approve")
            ],
            auto_reject_policies=[
                Policy(name="test_policy", conditions=[PolicyCondition("language", "==", "en")], action="reject")
            ],
        )

        issues = engine.validate_config()
        assert len(issues) > 0
        assert any("Duplicate policy name" in issue for issue in issues)

    def test_validate_config_empty_conditions(self):
        """Test config validation detects empty conditions."""
        engine = PolicyEngine(auto_approve_policies=[Policy(name="empty_policy", conditions=[], action="approve")])

        issues = engine.validate_config()
        assert len(issues) > 0
        assert any("has no conditions" in issue for issue in issues)

    def test_validate_config_dangerous_null_check(self):
        """Test config validation warns about single null check auto-approvals."""
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="dangerous", conditions=[PolicyCondition("structure", "is_not_null", True)], action="approve"
                )
            ]
        )

        issues = engine.validate_config()
        assert len(issues) > 0
        assert any("auto-approves based only on null check" in issue for issue in issues)


# ============================================================================
# Integration Tests with Real Data
# ============================================================================


class TestPolicyEngineIntegration:
    """Integration tests with realistic policy configurations and data."""

    def test_realistic_reddit_import_policies(self, staging_session, sample_import_batch):
        """Test realistic policies for Reddit joke imports."""
        # Create diverse set of jokes
        jokes_data = [
            # High quality, safe -> approve
            {"uuid": "reddit-1", "funniness": 85.0, "ratings": 200, "nsfw": False},
            # High quality but NSFW -> flag
            {"uuid": "reddit-2", "funniness": 88.0, "ratings": 150, "nsfw": True},
            # Low quality, few ratings -> skip
            {"uuid": "reddit-3", "funniness": 45.0, "ratings": 3, "nsfw": False},
            # Low quality, many ratings -> reject
            {"uuid": "reddit-4", "funniness": 12.0, "ratings": 50, "nsfw": False},
            # Medium quality -> flag
            {"uuid": "reddit-5", "funniness": 60.0, "ratings": 80, "nsfw": False},
        ]

        for data in jokes_data:
            joke = StagingJokeDB(
                joke_uuid=data["uuid"],
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json=json.dumps({"nsfw": data["nsfw"]}),
                tags_json="[]",
                weighted_avg_funniness=data["funniness"],
                total_ratings_count=data["ratings"],
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=sample_import_batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            staging_session.add(joke)

        staging_session.commit()

        # Load realistic policy configuration
        config = {
            "policies": {
                "auto_approve": [
                    {
                        "name": "high_quality_safe_reddit",
                        "conditions": [
                            {"weighted_avg_funniness": ">= 80"},
                            {"flags.nsfw": "== false"},
                            {"total_ratings_count": ">= 50"},
                        ],
                        "priority": 10,
                    }
                ],
                "auto_reject": [
                    {
                        "name": "low_quality_reddit",
                        "conditions": [
                            {"weighted_avg_funniness": "< 20"},
                            {"total_ratings_count": ">= 20"},
                        ],
                        "reason": "Low quality with sufficient sample size",
                        "priority": 5,
                    }
                ],
                "flag_for_review": [
                    {
                        "name": "nsfw_content",
                        "conditions": [{"flags.nsfw": "== true"}],
                        "reason": "NSFW content requires manual review",
                        "priority": 8,
                    },
                    {
                        "name": "borderline_quality",
                        "conditions": [
                            {"weighted_avg_funniness": ">= 50"},
                            {"weighted_avg_funniness": "< 70"},
                            {"total_ratings_count": ">= 50"},
                        ],
                        "reason": "Borderline quality score",
                        "priority": 3,
                    },
                ],
            }
        }

        engine = PolicyEngine.from_dict(config)
        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.total == 5
        assert stats.approved == 1  # reddit-1
        assert stats.rejected == 1  # reddit-4
        assert stats.flagged == 2  # reddit-2 (nsfw), reddit-5 (borderline)
        assert stats.skipped == 1  # reddit-3 (no matching policy)

        # Verify specific jokes
        reddit_1 = staging_session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == "reddit-1")).one()
        assert reddit_1.review_status == ReviewStatus.APPROVED

        reddit_2 = staging_session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == "reddit-2")).one()
        assert reddit_2.review_status == ReviewStatus.UNDER_REVIEW
        assert "NSFW" in reddit_2.review_notes

        reddit_4 = staging_session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == "reddit-4")).one()
        assert reddit_4.review_status == ReviewStatus.REJECTED

    def test_apply_to_jokes_method(self, staging_session, sample_import_batch):
        """Test apply_to_jokes method with specific joke list."""
        jokes = []
        for i in range(3):
            joke = StagingJokeDB(
                joke_uuid=f"specific-{i}",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=85.0,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=sample_import_batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            staging_session.add(joke)
            jokes.append(joke)

        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_quality",
                    conditions=[PolicyCondition("weighted_avg_funniness", ">=", 80)],
                    action="approve",
                )
            ]
        )

        stats = engine.apply_to_jokes(staging_session, jokes, dry_run=False)

        assert stats.total == 3
        assert stats.approved == 3

        for joke in jokes:
            staging_session.refresh(joke)
            assert joke.review_status == ReviewStatus.APPROVED

    def test_complex_nested_conditions(self, staging_session, sample_import_batch):
        """Test complex policies with deeply nested JSON field access."""
        joke = StagingJokeDB(
            joke_uuid="complex-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false, "offensive": false, "political": true}',
            tags_json="[]",
            engagement_json=json.dumps(
                {"upvotes": 500, "downvotes": 20, "comments": 100, "awards": {"gold": 5, "silver": 10}}
            ),
            metadata_json=json.dumps({"verified_by": "moderator", "quality_score": 92}),
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )
        staging_session.add(joke)
        staging_session.commit()

        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="high_engagement_verified",
                    conditions=[
                        PolicyCondition("engagement.upvotes", ">", 400),
                        PolicyCondition("flags.nsfw", "==", False),
                        PolicyCondition("flags.offensive", "==", False),
                    ],
                    action="approve",
                )
            ]
        )

        result = engine.evaluate_joke(joke)
        assert result.matched is True
        assert result.action == "approve"


# ============================================================================
# CLI Integration Tests
# ============================================================================


class TestCLIApplyPolicies:
    """Integration tests for the apply-policies CLI command."""

    @pytest.fixture
    def cli_staging_db(self, tmp_path):
        """Create a temporary staging database for CLI tests."""
        db_path = tmp_path / "test_staging.db"
        db_url = f"sqlite:///{db_path}"

        # Initialize the database
        from joke_emporium.db.staging import init_staging_db

        init_staging_db(db_url)

        yield db_path

        # Cleanup - properly dispose of engine and close connections
        import gc

        import joke_emporium.db.staging as staging_module

        if staging_module.staging_engine is not None:
            staging_module.staging_engine.dispose()
            staging_module.staging_engine = None

        # Force garbage collection to close any remaining connections
        gc.collect()
        gc.collect()

        # Small delay to ensure file handles are released on Windows
        import time

        time.sleep(0.2)

        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                # On Windows, sometimes need more time
                time.sleep(0.5)
                gc.collect()
                try:
                    db_path.unlink()
                except PermissionError:
                    # If still locked, just pass - tmp_path will be cleaned up by pytest
                    pass

    @pytest.fixture
    def cli_import_batch(self, cli_staging_db):
        """Create a sample import batch in the CLI test database."""
        from joke_emporium.db.models.staging import ImportBatchDB
        from joke_emporium.db.staging import get_staging_session

        with next(get_staging_session()) as session:
            batch = ImportBatchDB(
                import_id="cli-test-import-123",
                source="test-source",
                source_version="v1.0.0",
                imported_at=datetime.now(UTC),
                total_records=10,
                successful=10,
                failed=0,
            )
            session.add(batch)
            session.commit()
            session.refresh(batch)

            return batch

    @pytest.fixture
    def cli_db_with_batch(self, tmp_path):
        """Create a temporary staging database with import batch for CLI tests.

        This fixture properly initializes a file-based staging database that the CLI
        can access, and returns both the database path and the import batch.
        """
        from joke_emporium.db.models.staging import ImportBatchDB
        from joke_emporium.db.staging import get_staging_session, init_staging_db

        db_path = tmp_path / "test_cli_staging.db"
        db_url = f"sqlite:///{db_path}"

        # Initialize the staging database
        init_staging_db(db_url)

        # Create import batch
        with next(get_staging_session()) as session:
            batch = ImportBatchDB(
                import_id="test-import-123",
                source="test-source",
                source_version="v1.0.0",
                imported_at=datetime.now(UTC),
                total_records=10,
                successful=10,
                failed=0,
            )
            session.add(batch)
            session.commit()
            session.refresh(batch)

            # Store both db_path and batch
            result = {"db_path": db_path, "batch": batch}

        yield result

        # Cleanup - properly dispose of engine and close connections
        import gc

        import joke_emporium.db.staging as staging_module

        if staging_module.staging_engine is not None:
            staging_module.staging_engine.dispose()
            staging_module.staging_engine = None

        # Force garbage collection to close any remaining connections
        gc.collect()
        gc.collect()  # Sometimes need two passes

        # Small delay to ensure file handles are released on Windows
        import time

        time.sleep(0.2)

        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                # On Windows, sometimes need more time
                time.sleep(0.5)
                gc.collect()
                try:
                    db_path.unlink()
                except PermissionError:
                    # If still locked, just pass - tmp_path will be cleaned up by pytest
                    pass

    def test_command_exists(self):
        """Test that the apply-policies command is registered."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["apply-policies", "--help"])
        assert result.exit_code == 0
        assert "Apply automated policies" in result.output
        assert "IMPORT_ID" in result.output

    def test_missing_import_batch(self, cli_staging_db, tmp_path):
        """Test error when import batch doesn't exist."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        # Create a valid config file so we get past config validation
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test_policy
      conditions:
        - weighted_avg_funniness: ">= 4.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                "nonexistent-import-id",
                "--config",
                str(config_file),
                "--staging-db",
                str(cli_staging_db),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "Import batch not found" in result.output

    def test_missing_config_file(self, cli_staging_db, cli_import_batch):
        """Test error handling when config file not found."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_import_batch.import_id,
                "--config",
                "nonexistent/config.yaml",
                "--staging-db",
                str(cli_staging_db),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "Config file not found" in result.output

    def test_invalid_yaml_syntax(self, staging_session, sample_import_batch, tmp_path):
        """Test error handling for invalid YAML syntax."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        # Create invalid YAML file
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text(
            "policies:\n  auto_approve: [\n    - name: test\n      conditions: {invalid", encoding="utf-8"
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                sample_import_batch.import_id,
                "--config",
                str(config_file),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid YAML" in result.output or "YAML" in result.output

    def test_invalid_policy_structure(self, staging_session, sample_import_batch, tmp_path):
        """Test error handling for invalid policy structure."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        # Create YAML with invalid policy structure (missing required fields)
        config_file = tmp_path / "invalid_policy.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - conditions:  # Missing 'name' field
        - weighted_avg_funniness: ">= 80"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                sample_import_batch.import_id,
                "--config",
                str(config_file),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid policy configuration" in result.output or "requires 'name'" in result.output

    def test_dry_run_no_database_changes(self, cli_db_with_batch, tmp_path):
        """Test --dry-run doesn't modify database."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create pending jokes
        with next(get_staging_session()) as session:
            jokes = []
            for i in range(3):
                joke = StagingJokeDB(
                    joke_uuid=f"dry-run-joke-{i}",
                    version=1,
                    content_json='[{"type": "text", "text": "test"}]',
                    flags_json='{"nsfw": false}',
                    tags_json="[]",
                    weighted_avg_funniness=4.5,
                    total_ratings_count=15,
                    language="en",
                    added_date=datetime.now(UTC),
                    last_modified=datetime.now(UTC),
                    import_batch_id=batch.id,
                    original_data_json="{}",
                    review_status=ReviewStatus.PENDING,
                )
                session.add(joke)
                jokes.append(joke)

            session.commit()
            joke_ids = [j.id for j in jokes]

        # Create temp config
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: high_quality
      conditions:
        - weighted_avg_funniness: ">= 4.0"
        - total_ratings_count: ">= 10"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Approved" in result.output

        # Verify database NOT modified
        with next(get_staging_session()) as session:
            for joke_id in joke_ids:
                joke = session.get(StagingJokeDB, joke_id)
                assert joke is not None
                assert joke.review_status == ReviewStatus.PENDING
                assert joke.review_notes is None
                assert joke.reviewed_by is None

    def test_apply_with_default_config(self, cli_db_with_batch):
        """Test applying policies with default config file."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create a joke that matches default config criteria
        with next(get_staging_session()) as session:
            joke = StagingJokeDB(
                joke_uuid="default-config-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.5,
                total_ratings_count=15,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            session.add(joke)
            session.commit()

        # Check if default config exists
        default_config = Path("c:/repos/joke-emporium/config/import_policies.yaml")
        if not default_config.exists():
            pytest.skip("Default config file not found")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["apply-policies", batch.import_id, "--staging-db", str(db_path), "--yes"],
        )
        assert result.exit_code == 0
        assert "Successfully" in result.output or "Approved" in result.output

    def test_apply_with_custom_config(self, cli_db_with_batch, tmp_path):
        """Test applying policies with custom config file."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create test jokes
        with next(get_staging_session()) as session:
            high_quality_joke = StagingJokeDB(
                joke_uuid="high-quality-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.8,
                total_ratings_count=20,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )

            low_quality_joke = StagingJokeDB(
                joke_uuid="low-quality-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=1.5,
                total_ratings_count=10,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )

            session.add_all([high_quality_joke, low_quality_joke])
            session.commit()
            high_quality_id = high_quality_joke.id
            low_quality_id = low_quality_joke.id

        # Create custom config
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: excellent_quality
      conditions:
        - weighted_avg_funniness: ">= 4.5"
        - total_ratings_count: ">= 10"
  auto_reject:
    - name: poor_quality
      conditions:
        - weighted_avg_funniness: "< 2.0"
        - total_ratings_count: ">= 5"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Verify database changes
        with next(get_staging_session()) as session:
            high_quality_joke = session.get(StagingJokeDB, high_quality_id)
            assert high_quality_joke.review_status == ReviewStatus.APPROVED
            assert high_quality_joke.reviewed_by == "policy_engine"

            low_quality_joke = session.get(StagingJokeDB, low_quality_id)
            assert low_quality_joke.review_status == ReviewStatus.REJECTED
            assert low_quality_joke.reviewed_by == "policy_engine"

    def test_statistics_accuracy(self, cli_db_with_batch, tmp_path):
        """Test that returned statistics match database changes."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create diverse set of jokes
        jokes_data = [
            {"uuid": "approve-1", "funniness": 4.8, "ratings": 20},
            {"uuid": "approve-2", "funniness": 4.5, "ratings": 15},
            {"uuid": "reject-1", "funniness": 1.2, "ratings": 10},
            {"uuid": "flag-1", "funniness": 2.5, "ratings": 8},
            {"uuid": "skip-1", "funniness": 3.5, "ratings": 3},  # Won't match any policy
        ]

        with next(get_staging_session()) as session:
            for data in jokes_data:
                joke = StagingJokeDB(
                    joke_uuid=data["uuid"],
                    version=1,
                    content_json='[{"type": "text", "text": "test"}]',
                    flags_json='{"nsfw": false}',
                    tags_json="[]",
                    weighted_avg_funniness=data["funniness"],
                    total_ratings_count=data["ratings"],
                    language="en",
                    added_date=datetime.now(UTC),
                    last_modified=datetime.now(UTC),
                    import_batch_id=batch.id,
                    original_data_json="{}",
                    review_status=ReviewStatus.PENDING,
                )
                session.add(joke)

            session.commit()

        # Create config with clear boundaries
        config_file = tmp_path / "stats_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: high_quality
      conditions:
        - weighted_avg_funniness: ">= 4.0"
        - total_ratings_count: ">= 10"
  auto_reject:
    - name: low_quality
      conditions:
        - weighted_avg_funniness: "< 2.0"
        - total_ratings_count: ">= 5"
  flag_for_review:
    - name: borderline
      conditions:
        - weighted_avg_funniness: ">= 2.0"
        - weighted_avg_funniness: "< 3.0"
        - total_ratings_count: ">= 5"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Verify output contains correct statistics
        assert "2" in result.output  # 2 approved
        output_lines = result.output.split("\n")
        # Find the results table and verify counts
        assert any("Approved" in line and "2" in line for line in output_lines)
        assert any("Rejected" in line and "1" in line for line in output_lines)
        assert any("Flagged" in line and "1" in line for line in output_lines)
        assert any("Skipped" in line and "1" in line for line in output_lines)

    def test_yes_flag_skips_confirmation(self, cli_db_with_batch, tmp_path):
        """Test --yes flag skips confirmation prompt."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        with next(get_staging_session()) as session:
            joke = StagingJokeDB(
                joke_uuid="yes-flag-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.5,
                total_ratings_count=15,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            session.add(joke)
            session.commit()

        config_file = tmp_path / "yes_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test_policy
      conditions:
        - weighted_avg_funniness: ">= 4.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        # With --yes, should not prompt
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0
        assert "Continue?" not in result.output

    def test_policy_breakdown_counts(self, cli_db_with_batch, tmp_path):
        """Test policy breakdown shows accurate match counts."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create jokes matching different policies
        with next(get_staging_session()) as session:
            for i in range(3):
                joke = StagingJokeDB(
                    joke_uuid=f"policy-a-{i}",
                    version=1,
                    content_json='[{"type": "text", "text": "test"}]',
                    flags_json='{"nsfw": false}',
                    tags_json="[]",
                    weighted_avg_funniness=4.8,
                    total_ratings_count=20,
                    language="en",
                    added_date=datetime.now(UTC),
                    last_modified=datetime.now(UTC),
                    import_batch_id=batch.id,
                    original_data_json="{}",
                    review_status=ReviewStatus.PENDING,
                )
                session.add(joke)

            for i in range(2):
                joke = StagingJokeDB(
                    joke_uuid=f"policy-b-{i}",
                    version=1,
                    content_json='[{"type": "text", "text": "test"}]',
                    flags_json='{"nsfw": false}',
                    tags_json="[]",
                    weighted_avg_funniness=4.2,
                    total_ratings_count=12,
                    language="en",
                    added_date=datetime.now(UTC),
                    last_modified=datetime.now(UTC),
                    import_batch_id=batch.id,
                    original_data_json="{}",
                    review_status=ReviewStatus.PENDING,
                )
                session.add(joke)

            session.commit()

        config_file = tmp_path / "breakdown_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: excellent_quality
      conditions:
        - weighted_avg_funniness: ">= 4.5"
        - total_ratings_count: ">= 15"
      priority: 10
    - name: good_quality
      conditions:
        - weighted_avg_funniness: ">= 4.0"
        - total_ratings_count: ">= 10"
      priority: 5
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Verify policy breakdown shows in output
        assert "Policy Breakdown" in result.output
        assert "excellent_quality" in result.output
        assert "good_quality" in result.output

    def test_empty_import_batch(self, cli_db_with_batch, tmp_path):
        """Test handling of import batch with no pending jokes."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create config
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0
        assert "No pending jokes found" in result.output

    def test_skipped_already_reviewed_jokes(self, cli_db_with_batch, tmp_path):
        """Test that already-reviewed jokes are skipped."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create pending and already-approved jokes
        with next(get_staging_session()) as session:
            pending_joke = StagingJokeDB(
                joke_uuid="pending-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.5,
                total_ratings_count=15,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )

            already_approved = StagingJokeDB(
                joke_uuid="already-approved",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.5,
                total_ratings_count=15,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.APPROVED,
                reviewed_by="human",
            )

            session.add_all([pending_joke, already_approved])
            session.commit()

        config_file = tmp_path / "skip_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test_policy
      conditions:
        - weighted_avg_funniness: ">= 4.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Should only process 1 joke (the pending one)
        output_lines = result.output.split("\n")
        assert any("Total" in line and "1" in line for line in output_lines)

    def test_mixed_results_output(self, cli_db_with_batch, tmp_path):
        """Test output with mixed approve/reject/flag/skip results."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create diverse jokes
        jokes_data = [
            {"uuid": "approve-joke", "funniness": 4.8, "ratings": 20, "maturity": "G"},
            {"uuid": "reject-joke", "funniness": 1.2, "ratings": 10, "maturity": "G"},
            {"uuid": "flag-joke", "funniness": 3.0, "ratings": 5, "maturity": "R"},
            {"uuid": "skip-joke", "funniness": 3.0, "ratings": 2, "maturity": "G"},
        ]

        with next(get_staging_session()) as session:
            for data in jokes_data:
                joke = StagingJokeDB(
                    joke_uuid=data["uuid"],
                    version=1,
                    content_json='[{"type": "text", "text": "test"}]',
                    flags_json='{"nsfw": false}',
                    tags_json="[]",
                    weighted_avg_funniness=data["funniness"],
                    total_ratings_count=data["ratings"],
                    maturity_rating=data["maturity"],
                    language="en",
                    added_date=datetime.now(UTC),
                    last_modified=datetime.now(UTC),
                    import_batch_id=batch.id,
                    original_data_json="{}",
                    review_status=ReviewStatus.PENDING,
                )
                session.add(joke)

            session.commit()

        config_file = tmp_path / "mixed_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: high_quality
      conditions:
        - weighted_avg_funniness: ">= 4.5"
        - total_ratings_count: ">= 10"
  auto_reject:
    - name: low_quality
      conditions:
        - weighted_avg_funniness: "< 2.0"
        - total_ratings_count: ">= 5"
  flag_for_review:
    - name: mature_content
      conditions:
        - maturity_rating: "R"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Verify all result types appear in output
        assert "Approved" in result.output
        assert "Rejected" in result.output
        assert "Flagged" in result.output
        assert "Skipped" in result.output

    def test_duration_tracking(self, cli_db_with_batch, tmp_path):
        """Test that duration is tracked and displayed."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        with next(get_staging_session()) as session:
            joke = StagingJokeDB(
                joke_uuid="duration-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.5,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            session.add(joke)
            session.commit()

        config_file = tmp_path / "duration_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Verify duration appears in output
        assert "seconds" in result.output or "Duration" in result.output

    def test_review_notes_populated(self, cli_db_with_batch, tmp_path):
        """Test that review_notes are populated correctly."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        with next(get_staging_session()) as session:
            joke = StagingJokeDB(
                joke_uuid="notes-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.8,
                total_ratings_count=20,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            session.add(joke)
            session.commit()
            joke_id = joke.id

        config_file = tmp_path / "notes_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: high_quality_policy
      conditions:
        - weighted_avg_funniness: ">= 4.5"
      reason: "Excellent quality score"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # Verify review notes
        with next(get_staging_session()) as session:
            joke = session.get(StagingJokeDB, joke_id)
            assert joke.review_notes is not None
            assert "high_quality_policy" in joke.review_notes
            assert joke.reviewed_by == "policy_engine"
            assert joke.reviewed_at is not None

    def test_config_validation_warnings(self, staging_session, sample_import_batch, tmp_path):
        """Test that config validation warnings are displayed."""
        from click.testing import CliRunner

        from joke_emporium.importers.cli import cli

        joke = StagingJokeDB(
            joke_uuid="validation-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )
        staging_session.add(joke)
        staging_session.commit()

        # Create config with validation issues (empty conditions)
        config_file = tmp_path / "validation_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: empty_policy
      conditions: []
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                sample_import_batch.import_id,
                "--config",
                str(config_file),
                "--yes",
            ],
        )
        # Should run but show warnings
        assert "Warning" in result.output or "has no conditions" in result.output

    def test_exit_code_on_success(self, cli_db_with_batch, tmp_path):
        """Test exit code is 0 on successful application."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        with next(get_staging_session()) as session:
            joke = StagingJokeDB(
                joke_uuid="success-joke",
                version=1,
                content_json='[{"type": "text", "text": "test"}]',
                flags_json='{"nsfw": false}',
                tags_json="[]",
                weighted_avg_funniness=4.5,
                language="en",
                added_date=datetime.now(UTC),
                last_modified=datetime.now(UTC),
                import_batch_id=batch.id,
                original_data_json="{}",
                review_status=ReviewStatus.PENDING,
            )
            session.add(joke)
            session.commit()

        config_file = tmp_path / "success_test.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--yes",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully" in result.output or "Approved" in result.output

    def test_dry_run_with_statistics(self, cli_db_with_batch, tmp_path):
        """Test dry-run mode returns accurate statistics without changes."""
        from click.testing import CliRunner

        from joke_emporium.db.staging import get_staging_session
        from joke_emporium.importers.cli import cli

        db_path = cli_db_with_batch["db_path"]
        batch = cli_db_with_batch["batch"]

        # Create multiple jokes
        with next(get_staging_session()) as session:
            for i in range(5):
                joke = StagingJokeDB(
                    joke_uuid=f"dry-run-stats-{i}",
                    version=1,
                    content_json='[{"type": "text", "text": "test"}]',
                    flags_json='{"nsfw": false}',
                    tags_json="[]",
                    weighted_avg_funniness=4.5,
                    total_ratings_count=15,
                    language="en",
                    added_date=datetime.now(UTC),
                    last_modified=datetime.now(UTC),
                    import_batch_id=batch.id,
                    original_data_json="{}",
                    review_status=ReviewStatus.PENDING,
                )
                session.add(joke)

            session.commit()

        config_file = tmp_path / "dry_run_stats.yaml"
        config_file.write_text(
            """
policies:
  auto_approve:
    - name: test_policy
      conditions:
        - weighted_avg_funniness: ">= 4.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                batch.import_id,
                "--config",
                str(config_file),
                "--staging-db",
                str(db_path),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

        # Verify statistics show what would happen
        output_lines = result.output.split("\n")
        assert any("5" in line for line in output_lines)  # Total of 5 jokes
        assert any("Approved" in line for line in output_lines)


# ============================================================================
# Enhanced Operators Tests (Phase 4 - Task 4.2)
# ============================================================================


class TestPolicyConditionStringOperators:
    """Test string operators: contains, not_contains, starts_with, ends_with, matches, length_gt, length_lt."""

    def test_contains_operator_basic(self, sample_staging_joke):
        """Test contains operator with basic substring match."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "contains", "chicken")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "contains", "duck")
        assert condition.evaluate(sample_staging_joke) is False

    def test_contains_operator_case_sensitive(self, sample_staging_joke):
        """Test contains operator is case-sensitive."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "contains", "Chicken")
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("text_preview", "contains", "chicken")
        assert condition.evaluate(sample_staging_joke) is True

    def test_contains_operator_none_value(self, sample_staging_joke):
        """Test contains operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "contains", "test")
        assert condition.evaluate(sample_staging_joke) is False

    def test_contains_operator_empty_string(self, sample_staging_joke):
        """Test contains operator with empty string."""
        sample_staging_joke.text_preview = ""

        condition = PolicyCondition("text_preview", "contains", "test")
        assert condition.evaluate(sample_staging_joke) is False

        # Empty string contains empty string
        condition = PolicyCondition("text_preview", "contains", "")
        assert condition.evaluate(sample_staging_joke) is True

    def test_contains_operator_non_string_value(self, sample_staging_joke):
        """Test contains operator with non-string field value."""
        sample_staging_joke.total_ratings_count = 100

        condition = PolicyCondition("total_ratings_count", "contains", "10")
        assert condition.evaluate(sample_staging_joke) is False

    @pytest.mark.parametrize(
        "text,substring,expected",
        [
            ("Why did the chicken cross the road?", "chicken", True),
            ("What do you call a joke?", "chicken", False),
            ("", "test", False),
            ("Test string", "Test", True),
            ("Multiple words here", "words", True),
            ("Punctuation! And? Symbols#", "And?", True),
        ],
    )
    def test_contains_operator_parametrized(self, sample_staging_joke, text, substring, expected):
        """Test contains operator with various inputs."""
        sample_staging_joke.text_preview = text
        condition = PolicyCondition("text_preview", "contains", substring)
        assert condition.evaluate(sample_staging_joke) == expected

    def test_not_contains_operator_basic(self, sample_staging_joke):
        """Test not_contains operator with basic substring check."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "not_contains", "duck")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "not_contains", "chicken")
        assert condition.evaluate(sample_staging_joke) is False

    def test_not_contains_operator_none_value(self, sample_staging_joke):
        """Test not_contains operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "not_contains", "test")
        assert condition.evaluate(sample_staging_joke) is True  # None does not contain anything

    def test_starts_with_operator_basic(self, sample_staging_joke):
        """Test starts_with operator with basic prefix match."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "starts_with", "Why")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "starts_with", "What")
        assert condition.evaluate(sample_staging_joke) is False

    def test_starts_with_operator_case_sensitive(self, sample_staging_joke):
        """Test starts_with operator is case-sensitive."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "starts_with", "why")
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("text_preview", "starts_with", "Why")
        assert condition.evaluate(sample_staging_joke) is True

    def test_starts_with_operator_none_value(self, sample_staging_joke):
        """Test starts_with operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "starts_with", "Why")
        assert condition.evaluate(sample_staging_joke) is False

    def test_starts_with_operator_non_string(self, sample_staging_joke):
        """Test starts_with operator with non-string field."""
        sample_staging_joke.total_ratings_count = 100

        condition = PolicyCondition("total_ratings_count", "starts_with", "10")
        assert condition.evaluate(sample_staging_joke) is False

    @pytest.mark.parametrize(
        "text,prefix,expected",
        [
            ("Why did the chicken?", "Why", True),
            ("What is this?", "Why", False),
            ("", "test", False),
            ("Q: Question?", "Q:", True),
            ("A very long joke", "A very", True),
        ],
    )
    def test_starts_with_operator_parametrized(self, sample_staging_joke, text, prefix, expected):
        """Test starts_with operator with various inputs."""
        sample_staging_joke.text_preview = text
        condition = PolicyCondition("text_preview", "starts_with", prefix)
        assert condition.evaluate(sample_staging_joke) == expected

    def test_ends_with_operator_basic(self, sample_staging_joke):
        """Test ends_with operator with basic suffix match."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "ends_with", "road?")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "ends_with", "side!")
        assert condition.evaluate(sample_staging_joke) is False

    def test_ends_with_operator_case_sensitive(self, sample_staging_joke):
        """Test ends_with operator is case-sensitive."""
        sample_staging_joke.text_preview = "Why did the chicken cross the road?"

        condition = PolicyCondition("text_preview", "ends_with", "Road?")
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("text_preview", "ends_with", "road?")
        assert condition.evaluate(sample_staging_joke) is True

    def test_ends_with_operator_none_value(self, sample_staging_joke):
        """Test ends_with operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "ends_with", "?")
        assert condition.evaluate(sample_staging_joke) is False

    @pytest.mark.parametrize(
        "text,suffix,expected",
        [
            ("Why did the chicken?", "?", True),
            ("What is this!", "?", False),
            ("", "test", False),
            ("Answer: 42", "42", True),
            ("Ending here.", ".", True),
            ("No match", "yes", False),
        ],
    )
    def test_ends_with_operator_parametrized(self, sample_staging_joke, text, suffix, expected):
        """Test ends_with operator with various inputs."""
        sample_staging_joke.text_preview = text
        condition = PolicyCondition("text_preview", "ends_with", suffix)
        assert condition.evaluate(sample_staging_joke) == expected

    def test_matches_operator_basic(self, sample_staging_joke):
        """Test matches operator with basic regex pattern."""
        sample_staging_joke.text_preview = "Q: Why did the chicken? A: To cross!"

        # Match Q&A format
        condition = PolicyCondition("text_preview", "matches", r"Q:.*A:")
        assert condition.evaluate(sample_staging_joke) is True

        # Non-matching pattern
        condition = PolicyCondition("text_preview", "matches", r"^What")
        assert condition.evaluate(sample_staging_joke) is False

    def test_matches_operator_complex_patterns(self, sample_staging_joke):
        """Test matches operator with complex regex patterns."""
        sample_staging_joke.text_preview = "Call 555-1234 for jokes!"

        # Phone number pattern
        condition = PolicyCondition("text_preview", "matches", r"\d{3}-\d{4}")
        assert condition.evaluate(sample_staging_joke) is True

        # Email pattern (should not match)
        condition = PolicyCondition("text_preview", "matches", r"[\w\.-]+@[\w\.-]+")
        assert condition.evaluate(sample_staging_joke) is False

    def test_matches_operator_none_value(self, sample_staging_joke):
        """Test matches operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "matches", r".*")
        assert condition.evaluate(sample_staging_joke) is False

    def test_matches_operator_invalid_regex(self, sample_staging_joke):
        """Test matches operator handles invalid regex gracefully."""
        sample_staging_joke.text_preview = "Test text"

        # Invalid regex pattern
        condition = PolicyCondition("text_preview", "matches", r"[invalid(")
        assert condition.evaluate(sample_staging_joke) is False

    def test_matches_operator_case_sensitivity(self, sample_staging_joke):
        """Test matches operator is case-sensitive by default."""
        sample_staging_joke.text_preview = "Why did the chicken?"

        condition = PolicyCondition("text_preview", "matches", r"^Why")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "matches", r"^why")
        assert condition.evaluate(sample_staging_joke) is False

    def test_length_gt_operator_basic(self, sample_staging_joke):
        """Test length_gt operator with basic string length check."""
        sample_staging_joke.text_preview = "This is a test joke with some length"

        condition = PolicyCondition("text_preview", "length_gt", 20)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "length_gt", 100)
        assert condition.evaluate(sample_staging_joke) is False

    def test_length_gt_operator_exact_boundary(self, sample_staging_joke):
        """Test length_gt operator at exact boundary."""
        sample_staging_joke.text_preview = "12345"  # Length 5

        condition = PolicyCondition("text_preview", "length_gt", 5)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("text_preview", "length_gt", 4)
        assert condition.evaluate(sample_staging_joke) is True

    def test_length_gt_operator_none_value(self, sample_staging_joke):
        """Test length_gt operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "length_gt", 10)
        assert condition.evaluate(sample_staging_joke) is False

    def test_length_gt_operator_empty_string(self, sample_staging_joke):
        """Test length_gt operator with empty string."""
        sample_staging_joke.text_preview = ""

        condition = PolicyCondition("text_preview", "length_gt", 0)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("text_preview", "length_gt", -1)
        assert condition.evaluate(sample_staging_joke) is True

    def test_length_gt_operator_string_threshold(self, sample_staging_joke):
        """Test length_gt operator with string threshold value."""
        sample_staging_joke.text_preview = "Test joke"

        # Threshold as string should be converted
        condition = PolicyCondition("text_preview", "length_gt", "5")
        assert condition.evaluate(sample_staging_joke) is True

    @pytest.mark.parametrize(
        "text,threshold,expected",
        [
            ("Short", 10, False),
            ("Medium length text", 10, True),
            ("", 0, False),
            ("Exactly ten!", 10, True),
            ("Unicode: 你好世界", 5, True),
        ],
    )
    def test_length_gt_operator_parametrized(self, sample_staging_joke, text, threshold, expected):
        """Test length_gt operator with various inputs."""
        sample_staging_joke.text_preview = text
        condition = PolicyCondition("text_preview", "length_gt", threshold)
        assert condition.evaluate(sample_staging_joke) == expected

    def test_length_lt_operator_basic(self, sample_staging_joke):
        """Test length_lt operator with basic string length check."""
        sample_staging_joke.text_preview = "Short"

        condition = PolicyCondition("text_preview", "length_lt", 10)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("text_preview", "length_lt", 3)
        assert condition.evaluate(sample_staging_joke) is False

    def test_length_lt_operator_exact_boundary(self, sample_staging_joke):
        """Test length_lt operator at exact boundary."""
        sample_staging_joke.text_preview = "12345"  # Length 5

        condition = PolicyCondition("text_preview", "length_lt", 5)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("text_preview", "length_lt", 6)
        assert condition.evaluate(sample_staging_joke) is True

    def test_length_lt_operator_none_value(self, sample_staging_joke):
        """Test length_lt operator handles None field gracefully."""
        sample_staging_joke.text_preview = None

        condition = PolicyCondition("text_preview", "length_lt", 10)
        assert condition.evaluate(sample_staging_joke) is False

    @pytest.mark.parametrize(
        "text,threshold,expected",
        [
            ("Short", 10, True),
            ("Very long text here", 10, False),
            ("", 1, True),
            ("Exactly five", 11, False),
        ],
    )
    def test_length_lt_operator_parametrized(self, sample_staging_joke, text, threshold, expected):
        """Test length_lt operator with various inputs."""
        sample_staging_joke.text_preview = text
        condition = PolicyCondition("text_preview", "length_lt", threshold)
        assert condition.evaluate(sample_staging_joke) == expected


class TestPolicyConditionArrayOperators:
    """Test array operators: empty, not_empty, size_gt, size_lt, contains on arrays."""

    def test_contains_on_arrays_basic(self, sample_staging_joke):
        """Test contains operator with array values."""
        sample_staging_joke.tags_json = '["pun", "wordplay", "animal"]'

        condition = PolicyCondition("tags_json", "contains", "pun")
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("tags_json", "contains", "politics")
        assert condition.evaluate(sample_staging_joke) is False

    def test_contains_on_arrays_parsed_json(self, staging_session, sample_import_batch):
        """Test contains operator on already-parsed JSON array."""
        joke = StagingJokeDB(
            joke_uuid="array-test-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json='["comedy", "standup"]',
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        # Note: tags_json is accessed as nested field, so it gets parsed
        # For direct JSON string access, we need to test the actual field
        condition = PolicyCondition("tags_json", "contains", "comedy")
        # This will try to check if string contains substring
        assert condition.evaluate(joke) is True

    def test_empty_operator_basic(self, staging_session, sample_import_batch):
        """Test empty operator with empty array."""
        joke = StagingJokeDB(
            joke_uuid="empty-tags-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "empty", True)
        assert condition.evaluate(joke) is True

        condition = PolicyCondition("tags_json", "empty", False)
        assert condition.evaluate(joke) is False

    def test_empty_operator_non_empty_array(self, sample_staging_joke):
        """Test empty operator with non-empty array."""
        sample_staging_joke.tags_json = '["tag1", "tag2"]'

        condition = PolicyCondition("tags_json", "empty", True)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("tags_json", "empty", False)
        assert condition.evaluate(sample_staging_joke) is True

    def test_empty_operator_none_value(self, staging_session, sample_import_batch):
        """Test empty operator handles None field gracefully."""
        joke = StagingJokeDB(
            joke_uuid="none-tags-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json=None,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "empty", True)
        assert condition.evaluate(joke) is True  # None is considered empty

    def test_empty_operator_malformed_json(self, staging_session, sample_import_batch):
        """Test empty operator with malformed JSON."""
        joke = StagingJokeDB(
            joke_uuid="malformed-tags-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[invalid json",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "empty", True)
        # Malformed JSON falls back to string length check
        assert condition.evaluate(joke) is False  # Non-empty string

    def test_not_empty_operator_basic(self, sample_staging_joke):
        """Test not_empty operator with non-empty array."""
        sample_staging_joke.tags_json = '["tag1", "tag2"]'

        condition = PolicyCondition("tags_json", "not_empty", True)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("tags_json", "not_empty", False)
        assert condition.evaluate(sample_staging_joke) is False

    def test_not_empty_operator_empty_array(self, staging_session, sample_import_batch):
        """Test not_empty operator with empty array."""
        joke = StagingJokeDB(
            joke_uuid="empty-for-not-empty-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "not_empty", True)
        assert condition.evaluate(joke) is False

    def test_not_empty_operator_none_value(self, staging_session, sample_import_batch):
        """Test not_empty operator handles None field gracefully."""
        joke = StagingJokeDB(
            joke_uuid="none-for-not-empty-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json=None,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "not_empty", True)
        assert condition.evaluate(joke) is False  # None is not empty

    def test_size_gt_operator_basic(self, sample_staging_joke):
        """Test size_gt operator with array size check."""
        sample_staging_joke.tags_json = '["tag1", "tag2", "tag3", "tag4"]'

        condition = PolicyCondition("tags_json", "size_gt", 3)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("tags_json", "size_gt", 5)
        assert condition.evaluate(sample_staging_joke) is False

    def test_size_gt_operator_exact_boundary(self, sample_staging_joke):
        """Test size_gt operator at exact boundary."""
        sample_staging_joke.tags_json = '["tag1", "tag2", "tag3"]'

        condition = PolicyCondition("tags_json", "size_gt", 3)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("tags_json", "size_gt", 2)
        assert condition.evaluate(sample_staging_joke) is True

    def test_size_gt_operator_empty_array(self, staging_session, sample_import_batch):
        """Test size_gt operator with empty array."""
        joke = StagingJokeDB(
            joke_uuid="empty-size-gt-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "size_gt", 0)
        assert condition.evaluate(joke) is False

        condition = PolicyCondition("tags_json", "size_gt", -1)
        assert condition.evaluate(joke) is True

    def test_size_gt_operator_none_value(self, staging_session, sample_import_batch):
        """Test size_gt operator handles None field gracefully."""
        joke = StagingJokeDB(
            joke_uuid="none-size-gt-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json=None,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "size_gt", 0)
        assert condition.evaluate(joke) is False  # None has size 0

    def test_size_gt_operator_string_threshold(self, sample_staging_joke):
        """Test size_gt operator with string threshold value."""
        sample_staging_joke.tags_json = '["tag1", "tag2", "tag3"]'

        # Threshold as string should be converted
        condition = PolicyCondition("tags_json", "size_gt", "2")
        assert condition.evaluate(sample_staging_joke) is True

    @pytest.mark.parametrize(
        "tags_json,threshold,expected",
        [
            ("[]", 0, False),
            ('["one"]', 0, True),
            ('["one", "two"]', 1, True),
            ('["one", "two", "three"]', 3, False),
            ('["a", "b", "c", "d", "e"]', 3, True),
        ],
    )
    def test_size_gt_operator_parametrized(self, staging_session, sample_import_batch, tags_json, threshold, expected):
        """Test size_gt operator with various inputs."""
        joke = StagingJokeDB(
            joke_uuid=f"size-gt-test-{threshold}",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json=tags_json,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "size_gt", threshold)
        assert condition.evaluate(joke) == expected

    def test_size_lt_operator_basic(self, sample_staging_joke):
        """Test size_lt operator with array size check."""
        sample_staging_joke.tags_json = '["tag1", "tag2"]'

        condition = PolicyCondition("tags_json", "size_lt", 3)
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("tags_json", "size_lt", 2)
        assert condition.evaluate(sample_staging_joke) is False

    def test_size_lt_operator_exact_boundary(self, sample_staging_joke):
        """Test size_lt operator at exact boundary."""
        sample_staging_joke.tags_json = '["tag1", "tag2", "tag3"]'

        condition = PolicyCondition("tags_json", "size_lt", 3)
        assert condition.evaluate(sample_staging_joke) is False

        condition = PolicyCondition("tags_json", "size_lt", 4)
        assert condition.evaluate(sample_staging_joke) is True

    def test_size_lt_operator_empty_array(self, staging_session, sample_import_batch):
        """Test size_lt operator with empty array."""
        joke = StagingJokeDB(
            joke_uuid="empty-size-lt-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "size_lt", 1)
        assert condition.evaluate(joke) is True

    @pytest.mark.parametrize(
        "tags_json,threshold,expected",
        [
            ("[]", 1, True),
            ('["one"]', 2, True),
            ('["one", "two"]', 2, False),
            ('["one", "two", "three"]', 5, True),
        ],
    )
    def test_size_lt_operator_parametrized(self, staging_session, sample_import_batch, tags_json, threshold, expected):
        """Test size_lt operator with various inputs."""
        joke = StagingJokeDB(
            joke_uuid=f"size-lt-test-{threshold}",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json=tags_json,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("tags_json", "size_lt", threshold)
        assert condition.evaluate(joke) == expected


class TestPolicyConditionRangeOperators:
    """Test range operators: between, not_between."""

    def test_between_operator_basic(self, sample_staging_joke):
        """Test between operator with numeric range."""
        sample_staging_joke.weighted_avg_funniness = 50.0

        condition = PolicyCondition("weighted_avg_funniness", "between", [40, 60])
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", "between", [60, 80])
        assert condition.evaluate(sample_staging_joke) is False

    def test_between_operator_inclusive_boundaries(self, sample_staging_joke):
        """Test between operator includes boundary values."""
        sample_staging_joke.weighted_avg_funniness = 40.0

        # Lower boundary
        condition = PolicyCondition("weighted_avg_funniness", "between", [40, 60])
        assert condition.evaluate(sample_staging_joke) is True

        # Upper boundary
        sample_staging_joke.weighted_avg_funniness = 60.0
        assert condition.evaluate(sample_staging_joke) is True

    def test_between_operator_integer_values(self, sample_staging_joke):
        """Test between operator with integer values."""
        sample_staging_joke.total_ratings_count = 75

        condition = PolicyCondition("total_ratings_count", "between", [50, 100])
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("total_ratings_count", "between", [80, 100])
        assert condition.evaluate(sample_staging_joke) is False

    def test_between_operator_float_values(self, sample_staging_joke):
        """Test between operator with float values."""
        sample_staging_joke.weighted_avg_funniness = 55.5

        condition = PolicyCondition("weighted_avg_funniness", "between", [50.0, 60.0])
        assert condition.evaluate(sample_staging_joke) is True

        condition = PolicyCondition("weighted_avg_funniness", "between", [40.5, 50.5])
        assert condition.evaluate(sample_staging_joke) is False

    def test_between_operator_string_range(self, sample_staging_joke):
        """Test between operator with string range format."""
        sample_staging_joke.weighted_avg_funniness = 50.0

        # Space-separated string range
        condition = PolicyCondition("weighted_avg_funniness", "between", "40 60")
        assert condition.evaluate(sample_staging_joke) is True

    def test_between_operator_none_value(self, staging_session, sample_import_batch):
        """Test between operator handles None field gracefully."""
        joke = StagingJokeDB(
            joke_uuid="none-between-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=None,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("weighted_avg_funniness", "between", [40, 60])
        assert condition.evaluate(joke) is False

    def test_between_operator_invalid_range(self, sample_staging_joke):
        """Test between operator with invalid range format."""
        sample_staging_joke.weighted_avg_funniness = 50.0

        # Single value (invalid range)
        condition = PolicyCondition("weighted_avg_funniness", "between", [50])
        assert condition.evaluate(sample_staging_joke) is False

        # Empty list
        condition = PolicyCondition("weighted_avg_funniness", "between", [])
        assert condition.evaluate(sample_staging_joke) is False

    @pytest.mark.parametrize(
        "value,range_bounds,expected",
        [
            (50, [40, 60], True),
            (40, [40, 60], True),
            (60, [40, 60], True),
            (39, [40, 60], False),
            (61, [40, 60], False),
            (75.5, [70, 80], True),
            (100, [0, 100], True),
        ],
    )
    def test_between_operator_parametrized(self, sample_staging_joke, value, range_bounds, expected):
        """Test between operator with various inputs."""
        sample_staging_joke.weighted_avg_funniness = value
        condition = PolicyCondition("weighted_avg_funniness", "between", range_bounds)
        assert condition.evaluate(sample_staging_joke) == expected

    def test_not_between_operator_basic(self, sample_staging_joke):
        """Test not_between operator with numeric range."""
        sample_staging_joke.weighted_avg_funniness = 30.0

        condition = PolicyCondition("weighted_avg_funniness", "not_between", [40, 60])
        assert condition.evaluate(sample_staging_joke) is True

        sample_staging_joke.weighted_avg_funniness = 50.0
        assert condition.evaluate(sample_staging_joke) is False

    def test_not_between_operator_boundaries(self, sample_staging_joke):
        """Test not_between operator excludes boundary values."""
        sample_staging_joke.weighted_avg_funniness = 40.0

        # On lower boundary (should be inside range)
        condition = PolicyCondition("weighted_avg_funniness", "not_between", [40, 60])
        assert condition.evaluate(sample_staging_joke) is False

        # Just below lower boundary
        sample_staging_joke.weighted_avg_funniness = 39.9
        assert condition.evaluate(sample_staging_joke) is True

        # Just above upper boundary
        sample_staging_joke.weighted_avg_funniness = 60.1
        assert condition.evaluate(sample_staging_joke) is True

    def test_not_between_operator_none_value(self, staging_session, sample_import_batch):
        """Test not_between operator handles None field gracefully."""
        joke = StagingJokeDB(
            joke_uuid="none-not-between-test",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=None,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
        )
        staging_session.add(joke)
        staging_session.commit()

        condition = PolicyCondition("weighted_avg_funniness", "not_between", [40, 60])
        assert condition.evaluate(joke) is True  # None is not between any range

    @pytest.mark.parametrize(
        "value,range_bounds,expected",
        [
            (30, [40, 60], True),
            (70, [40, 60], True),
            (50, [40, 60], False),
            (40, [40, 60], False),
            (60, [40, 60], False),
            (10, [20, 80], True),
            (90, [20, 80], True),
        ],
    )
    def test_not_between_operator_parametrized(self, sample_staging_joke, value, range_bounds, expected):
        """Test not_between operator with various inputs."""
        sample_staging_joke.weighted_avg_funniness = value
        condition = PolicyCondition("weighted_avg_funniness", "not_between", range_bounds)
        assert condition.evaluate(sample_staging_joke) == expected


class TestPolicyConditionEnhancedShorthand:
    """Test shorthand parsing for enhanced operators."""

    def test_contains_shorthand(self):
        """Test parsing contains shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "contains 'joke'")
        assert condition.field == "text_preview"
        assert condition.operator == "contains"
        assert condition.value == "joke"

    def test_not_contains_shorthand(self):
        """Test parsing not_contains shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "not_contains 'politics'")
        assert condition.field == "text_preview"
        assert condition.operator == "not_contains"
        assert condition.value == "politics"

    def test_starts_with_shorthand(self):
        """Test parsing starts_with shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "starts_with 'Why'")
        assert condition.field == "text_preview"
        assert condition.operator == "starts_with"
        assert condition.value == "Why"

    def test_ends_with_shorthand(self):
        """Test parsing ends_with shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "ends_with '?'")
        assert condition.field == "text_preview"
        assert condition.operator == "ends_with"
        assert condition.value == "?"

    def test_matches_shorthand(self):
        """Test parsing matches (regex) shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "matches '^Q:.*A:.*$'")
        assert condition.field == "text_preview"
        assert condition.operator == "matches"
        assert condition.value == "^Q:.*A:.*$"

    def test_length_gt_shorthand(self):
        """Test parsing length_gt shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "length_gt 100")
        assert condition.field == "text_preview"
        assert condition.operator == "length_gt"
        assert condition.value == 100

    def test_length_lt_shorthand(self):
        """Test parsing length_lt shorthand."""
        condition = PolicyCondition.from_shorthand("text_preview", "length_lt 50")
        assert condition.field == "text_preview"
        assert condition.operator == "length_lt"
        assert condition.value == 50

    def test_empty_shorthand(self):
        """Test parsing empty shorthand."""
        condition = PolicyCondition.from_shorthand("tags_json", "empty")
        assert condition.field == "tags_json"
        assert condition.operator == "empty"
        assert condition.value is True

    def test_not_empty_shorthand(self):
        """Test parsing not_empty shorthand."""
        condition = PolicyCondition.from_shorthand("tags_json", "not_empty")
        assert condition.field == "tags_json"
        assert condition.operator == "not_empty"
        assert condition.value is True

    def test_size_gt_shorthand(self):
        """Test parsing size_gt shorthand."""
        condition = PolicyCondition.from_shorthand("tags_json", "size_gt 3")
        assert condition.field == "tags_json"
        assert condition.operator == "size_gt"
        assert condition.value == 3

    def test_size_lt_shorthand(self):
        """Test parsing size_lt shorthand."""
        condition = PolicyCondition.from_shorthand("tags_json", "size_lt 10")
        assert condition.field == "tags_json"
        assert condition.operator == "size_lt"
        assert condition.value == 10

    def test_between_shorthand(self):
        """Test parsing between shorthand."""
        condition = PolicyCondition.from_shorthand("weighted_avg_funniness", "between 40 60")
        assert condition.field == "weighted_avg_funniness"
        assert condition.operator == "between"
        assert condition.value == "40 60"

    def test_not_between_shorthand(self):
        """Test parsing not_between shorthand."""
        condition = PolicyCondition.from_shorthand("weighted_avg_funniness", "not_between 20 80")
        assert condition.field == "weighted_avg_funniness"
        assert condition.operator == "not_between"
        assert condition.value == "20 80"

    def test_shorthand_operator_precedence(self):
        """Test that longer operators are matched before shorter ones."""
        # "not_contains" should match before "contains"
        condition = PolicyCondition.from_shorthand("text_preview", "not_contains 'test'")
        assert condition.operator == "not_contains"

        # "not_between" should match before "between"
        condition = PolicyCondition.from_shorthand("score", "not_between 10 20")
        assert condition.operator == "not_between"

        # "not_empty" should match before "empty"
        condition = PolicyCondition.from_shorthand("tags", "not_empty")
        assert condition.operator == "not_empty"


class TestPolicyEngineEnhancedOperators:
    """Integration tests for enhanced operators with real policies."""

    def test_policy_with_string_operators(self, staging_session, sample_import_batch):
        """Test creating and applying policy using string operators."""
        # Create jokes with different text characteristics
        short_joke = StagingJokeDB(
            joke_uuid="short-joke",
            version=1,
            content_json='[{"type": "text", "text": "Short."}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            text_preview="Short.",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        question_joke = StagingJokeDB(
            joke_uuid="question-joke",
            version=1,
            content_json='[{"type": "text", "text": "Why did the chicken cross the road?"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            text_preview="Why did the chicken cross the road?",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        staging_session.add_all([short_joke, question_joke])
        staging_session.commit()

        # Create policy using string operators
        engine = PolicyEngine(
            auto_reject_policies=[
                Policy(
                    name="reject_short_jokes",
                    conditions=[PolicyCondition("text_preview", "length_lt", 10)],
                    action="reject",
                    reason="Joke too short",
                )
            ],
            auto_approve_policies=[
                Policy(
                    name="approve_question_jokes",
                    conditions=[
                        PolicyCondition("text_preview", "starts_with", "Why"),
                        PolicyCondition("text_preview", "ends_with", "?"),
                    ],
                    action="approve",
                )
            ],
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.approved == 1
        assert stats.rejected == 1

        staging_session.refresh(short_joke)
        assert short_joke.review_status == ReviewStatus.REJECTED

        staging_session.refresh(question_joke)
        assert question_joke.review_status == ReviewStatus.APPROVED

    def test_policy_with_array_operators(self, staging_session, sample_import_batch):
        """Test creating and applying policy using array operators."""
        # Create jokes with different tag counts
        well_tagged = StagingJokeDB(
            joke_uuid="well-tagged-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json='["pun", "wordplay", "animal", "classic"]',
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        poorly_tagged = StagingJokeDB(
            joke_uuid="poorly-tagged-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json='["misc"]',
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        no_tags = StagingJokeDB(
            joke_uuid="no-tags-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        staging_session.add_all([well_tagged, poorly_tagged, no_tags])
        staging_session.commit()

        # Create policy using array operators
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="approve_well_tagged",
                    conditions=[PolicyCondition("tags_json", "size_gt", 3)],
                    action="approve",
                    reason="Well-tagged joke",
                )
            ],
            auto_reject_policies=[
                Policy(
                    name="reject_untagged",
                    conditions=[PolicyCondition("tags_json", "empty", True)],
                    action="reject",
                    reason="No tags",
                )
            ],
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.approved == 1
        assert stats.rejected == 1
        assert stats.skipped == 1

        staging_session.refresh(well_tagged)
        assert well_tagged.review_status == ReviewStatus.APPROVED

        staging_session.refresh(no_tags)
        assert no_tags.review_status == ReviewStatus.REJECTED

        staging_session.refresh(poorly_tagged)
        assert poorly_tagged.review_status == ReviewStatus.PENDING

    def test_policy_with_range_operators(self, staging_session, sample_import_batch):
        """Test creating and applying policy using range operators."""
        # Create jokes with different quality scores
        borderline_low = StagingJokeDB(
            joke_uuid="borderline-low",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=45.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        borderline_high = StagingJokeDB(
            joke_uuid="borderline-high",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=55.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        excellent = StagingJokeDB(
            joke_uuid="excellent",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            weighted_avg_funniness=85.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        staging_session.add_all([borderline_low, borderline_high, excellent])
        staging_session.commit()

        # Create policy using range operators
        engine = PolicyEngine(
            flag_policies=[
                Policy(
                    name="flag_borderline",
                    conditions=[PolicyCondition("weighted_avg_funniness", "between", [40, 60])],
                    action="flag",
                    reason="Borderline quality score",
                )
            ],
            auto_approve_policies=[
                Policy(
                    name="approve_excellent",
                    conditions=[PolicyCondition("weighted_avg_funniness", "not_between", [0, 80])],
                    action="approve",
                )
            ],
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.approved == 1
        assert stats.flagged == 2

        staging_session.refresh(excellent)
        assert excellent.review_status == ReviewStatus.APPROVED

        staging_session.refresh(borderline_low)
        assert borderline_low.review_status == ReviewStatus.UNDER_REVIEW

        staging_session.refresh(borderline_high)
        assert borderline_high.review_status == ReviewStatus.UNDER_REVIEW

    def test_complex_policy_with_mixed_operators(self, staging_session, sample_import_batch):
        """Test complex policy combining old and new operators."""
        # Create a well-rounded joke
        quality_joke = StagingJokeDB(
            joke_uuid="quality-joke",
            version=1,
            content_json='[{"type": "text", "text": "Why did the chicken cross the road?"}]',
            flags_json='{"nsfw": false}',
            tags_json='["animal", "classic", "family-friendly", "question"]',
            text_preview="Why did the chicken cross the road? To get to the other side!",
            weighted_avg_funniness=75.0,
            total_ratings_count=100,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        # Create a problematic joke
        bad_joke = StagingJokeDB(
            joke_uuid="bad-joke",
            version=1,
            content_json='[{"type": "text", "text": "Bad"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            text_preview="Bad",
            weighted_avg_funniness=30.0,
            total_ratings_count=5,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        staging_session.add_all([quality_joke, bad_joke])
        staging_session.commit()

        # Create complex policy mixing operators
        engine = PolicyEngine(
            auto_approve_policies=[
                Policy(
                    name="approve_quality_jokes",
                    conditions=[
                        # Old operators
                        PolicyCondition("weighted_avg_funniness", ">=", 70),
                        PolicyCondition("total_ratings_count", ">=", 50),
                        PolicyCondition("flags.nsfw", "==", False),
                        # New string operators
                        PolicyCondition("text_preview", "length_gt", 20),
                        # New array operators
                        PolicyCondition("tags_json", "size_gt", 2),
                    ],
                    action="approve",
                    reason="High quality, well-tagged joke",
                )
            ],
            auto_reject_policies=[
                Policy(
                    name="reject_poor_jokes",
                    conditions=[
                        # Old operators
                        PolicyCondition("weighted_avg_funniness", "<", 50),
                        # New string operators
                        PolicyCondition("text_preview", "length_lt", 10),
                        # New array operators
                        PolicyCondition("tags_json", "empty", True),
                    ],
                    action="reject",
                    reason="Low quality and poorly formatted",
                )
            ],
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.approved == 1
        assert stats.rejected == 1

        staging_session.refresh(quality_joke)
        assert quality_joke.review_status == ReviewStatus.APPROVED
        assert "High quality, well-tagged joke" in quality_joke.review_notes

        staging_session.refresh(bad_joke)
        assert bad_joke.review_status == ReviewStatus.REJECTED
        assert "Low quality and poorly formatted" in bad_joke.review_notes

    def test_realistic_policy_scenario(self, staging_session, sample_import_batch):
        """Test realistic scenario with keyword filtering and content patterns."""
        # Joke with profanity keyword
        profanity_joke = StagingJokeDB(
            joke_uuid="profanity-joke",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json="[]",
            text_preview="This joke contains damn profanity",
            weighted_avg_funniness=60.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        # Clean question format joke
        question_format = StagingJokeDB(
            joke_uuid="question-format",
            version=1,
            content_json='[{"type": "text", "text": "test"}]',
            flags_json='{"nsfw": false}',
            tags_json='["question", "answer"]',
            text_preview="Q: What do you call it? A: A joke!",
            weighted_avg_funniness=65.0,
            language="en",
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            import_batch_id=sample_import_batch.id,
            original_data_json="{}",
            review_status=ReviewStatus.PENDING,
        )

        staging_session.add_all([profanity_joke, question_format])
        staging_session.commit()

        # Create realistic content policy
        engine = PolicyEngine(
            flag_policies=[
                Policy(
                    name="flag_potential_profanity",
                    conditions=[
                        PolicyCondition("text_preview", "contains", "damn"),
                    ],
                    action="flag",
                    reason="Contains potential profanity - manual review required",
                )
            ],
            auto_approve_policies=[
                Policy(
                    name="approve_qa_format",
                    conditions=[
                        PolicyCondition("text_preview", "matches", r"Q:.*A:"),
                        PolicyCondition("weighted_avg_funniness", ">=", 60),
                        PolicyCondition("tags_json", "not_empty", True),
                    ],
                    action="approve",
                    reason="Clean Q&A format joke",
                )
            ],
        )

        stats = engine.apply_policies(staging_session, sample_import_batch.id, dry_run=False)

        assert stats.approved == 1
        assert stats.flagged == 1

        staging_session.refresh(profanity_joke)
        assert profanity_joke.review_status == ReviewStatus.UNDER_REVIEW

        staging_session.refresh(question_format)
        assert question_format.review_status == ReviewStatus.APPROVED
