"""Unit tests for the CLI argument parser."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path
from src.infrastructure.cli.argument_parser import parse_args


class TestArgumentParser:
    """Tests for the parse_args function."""

    def test_positional_args_parsed(self):
        result = parse_args(["coffee", "Penang"])
        assert result.keyword == "coffee"
        assert result.location == "Penang"

    def test_default_limit_is_200(self):
        result = parse_args(["coffee", "Penang"])
        assert result.limit == 200

    def test_default_output_is_results_json(self):
        result = parse_args(["coffee", "Penang"])
        assert result.output_path == Path("results.json")

    def test_headless_flag_false_by_default(self):
        result = parse_args(["coffee", "Penang"])
        assert result.headless is False

    def test_verbose_flag_false_by_default(self):
        result = parse_args(["coffee", "Penang"])
        assert result.verbose is False

    def test_custom_limit_parsed(self):
        result = parse_args(["coffee", "Penang", "--limit", "50"])
        assert result.limit == 50

    def test_custom_output_parsed_as_path(self):
        result = parse_args(["coffee", "Penang", "--output", "out/data.json"])
        assert result.output_path == Path("out/data.json")

    def test_headless_flag_set_when_passed(self):
        result = parse_args(["coffee", "Penang", "--headless"])
        assert result.headless is True

    def test_verbose_flag_set_when_passed(self):
        result = parse_args(["coffee", "Penang", "--verbose"])
        assert result.verbose is True

    def test_limit_over_1000_capped(self, capsys):
        result = parse_args(["coffee", "Penang", "--limit", "5000"])
        assert result.limit <= 1000

    def test_missing_keyword_exits(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_missing_location_exits(self):
        with pytest.raises(SystemExit):
            parse_args(["coffee"])
