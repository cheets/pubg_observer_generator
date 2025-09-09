"""
Test module for team short name generation logic.
"""

import pytest
from pubg_observer_generator.main import (
    create_team_short_name,
    resolve_short_name_conflicts,
)


class TestCreateTeamShortName:
    """Test cases for the create_team_short_name function."""

    def test_single_word_team(self):
        """Test teams with single words."""
        assert create_team_short_name("Eagles") == "EAGL"
        assert create_team_short_name("ABC") == "ABC"
        assert create_team_short_name("X") == "X"

    def test_team_with_number(self):
        """Test teams with numbers as the second word."""
        assert create_team_short_name("Team 1") == "TEAM"
        assert create_team_short_name("Team 2") == "TEAM"
        assert create_team_short_name("Squad 99") == "SQUAD"[:4]

    def test_team_with_multiple_words(self):
        """Test teams with multiple words."""
        assert create_team_short_name("Fancy Guys") == "FANC"
        assert create_team_short_name("Fancy Girls") == "FANC"
        assert create_team_short_name("Blue Dragons") == "BLUE"

    def test_empty_or_invalid_input(self):
        """Test edge cases with empty or invalid input."""
        assert create_team_short_name("") == "XXXX"
        assert create_team_short_name("   ") == "XXXX"
        assert create_team_short_name("!@#$") == "XXXX"

    def test_special_characters(self):
        """Test teams with special characters."""
        assert create_team_short_name("Team-Alpha") == "TEAM"
        assert create_team_short_name("Team_Beta") == "TEAM"
        assert create_team_short_name("Team & Co") == "TEAM"


class TestResolveShortNameConflicts:
    """Test cases for the resolve_short_name_conflicts function."""

    def test_no_conflicts(self):
        """Test when there are no conflicts."""
        team_names = ["Eagles", "Bears", "Lions"]
        result = resolve_short_name_conflicts(team_names)

        assert result["Eagles"] == "EAGL"
        assert result["Bears"] == "BEAR"
        assert result["Lions"] == "LION"

    def test_conflict_resolution(self):
        """Test conflict resolution between teams."""
        team_names = ["Fancy Guys", "Fancy Girls"]
        result = resolve_short_name_conflicts(team_names)

        # Both should get different short names
        assert result["Fancy Guys"] != result["Fancy Girls"]
        assert len(result["Fancy Guys"]) <= 4
        assert len(result["Fancy Girls"]) <= 4

    def test_team_with_numbers_conflict_resolution(self):
        """Test teams with numbers that conflict get resolved properly."""
        team_names = ["Team 1", "Team 2", "Team 3"]
        result = resolve_short_name_conflicts(team_names)

        # All should be different and use strategy 1 (3 chars + 1 from the second word)
        expected_values = {"TEA1", "TEA2", "TEA3"}
        actual_values = set(result.values())
        assert actual_values == expected_values

        # Verify specific mappings
        assert result["Team 1"] == "TEA1"
        assert result["Team 2"] == "TEA2"
        assert result["Team 3"] == "TEA3"

    def test_fancy_teams_specific_case(self):
        """Test the specific case of Fancy Guys vs. Fancy Girls."""
        team_names = ["Fancy Guys", "Fancy Girls"]
        result = resolve_short_name_conflicts(team_names)

        # Should resolve to FAGU and FAGI using strategy 2 (2+2 chars)
        expected_values = {"FAGU", "FAGI"}
        actual_values = set(result.values())
        assert actual_values == expected_values

        # Verify specific assignments
        assert result["Fancy Guys"] == "FAGU"
        assert result["Fancy Girls"] == "FAGI"

    def test_all_short_names_unique(self):
        """Test that all resolved short names are unique."""
        team_names = ["ABC Hitters", "Team 1", "Team 2", "Fancy Guys", "Fancy Girls"]
        result = resolve_short_name_conflicts(team_names)

        short_names = list(result.values())
        assert len(short_names) == len(
            set(short_names)
        ), "All short names should be unique"

    def test_mixed_team_types(self):
        """Test with a mix of different team name patterns."""
        team_names = ["Eagles", "Team 1", "Blue Dragons", "Fancy Guys", "Alpha Squad"]
        result = resolve_short_name_conflicts(team_names)

        # Verify all teams got short names
        assert len(result) == len(team_names)

        # Verify no duplicates
        short_names = list(result.values())
        assert len(short_names) == len(set(short_names))

        # Verify length constraints
        for short_name in short_names:
            assert len(short_name) <= 4
            assert len(short_name) > 0


if __name__ == "__main__":
    pytest.main([__file__])
