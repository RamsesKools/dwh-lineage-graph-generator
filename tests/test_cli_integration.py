"""Integration tests for CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from lineage.cli import cli


@pytest.fixture
def runner():
    """Provide a Click test runner."""
    return CliRunner()


@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"


class TestGenerateCommandIntegration:
    """Integration tests for generate command."""

    def test_generate_full_lineage(self, runner, test_data_dir, tmp_path):
        """Test generate command produces full lineage without filtering."""
        input_file = test_data_dir / "example_lineage.json"
        expected_output = test_data_dir / "example_full_lineage.mmd"
        actual_output = tmp_path / "actual_output.mmd"

        # Run the CLI command
        result = runner.invoke(
            cli, ["generate_mermaid", str(input_file), "-o", str(actual_output)]
        )

        # Check command succeeded
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify output file was created
        assert actual_output.exists(), "Output file was not created"

        # Compare actual output with expected output
        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        # Normalize line endings and trailing whitespace
        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [
            line.rstrip() for line in expected_content.strip().split("\n")
        ]

        assert actual_lines == expected_lines, "Generated output does not match expected output"

    def test_generate_with_different_directions(self, runner, test_data_dir, tmp_path):
        """Test generate command with different direction parameters."""
        input_file = test_data_dir / "example_lineage.json"

        for direction in ["LR", "RL", "TB", "BT"]:
            output_file = tmp_path / f"output_{direction}.mmd"

            result = runner.invoke(
                cli,
                ["generate_mermaid", str(input_file), "-o", str(output_file), "-d", direction],
            )

            assert result.exit_code == 0, f"CLI failed for direction {direction}"
            assert output_file.exists(), f"Output file not created for direction {direction}"

            # Verify the direction is in the output
            content = output_file.read_text()
            assert f"graph {direction}" in content, f"Graph direction {direction} not found in output"

    def test_generate_focus_both_directions(self, runner, test_data_dir, tmp_path):
        """Test generate with focus on node (both upstream and downstream)."""
        input_file = test_data_dir / "example_lineage.json"
        expected_output = test_data_dir / "example_focus_both.mmd"
        actual_output = tmp_path / "actual_focus_both.mmd"

        result = runner.invoke(
            cli,
            ["generate_mermaid", str(input_file), "--focus", "dim_customer", "-o", str(actual_output)],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert actual_output.exists(), "Output file was not created"

        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_content.strip().split("\n")]

        assert actual_lines == expected_lines, "Focus both directions output does not match"

    def test_generate_focus_upstream(self, runner, test_data_dir, tmp_path):
        """Test generate with focus on upstream only."""
        input_file = test_data_dir / "example_lineage.json"
        expected_output = test_data_dir / "example_focus_upstream.mmd"
        actual_output = tmp_path / "actual_focus_upstream.mmd"

        result = runner.invoke(
            cli,
            [
                "generate_mermaid",
                str(input_file),
                "--focus",
                "dim_customer",
                "--filter-direction",
                "upstream",
                "-o",
                str(actual_output),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert actual_output.exists(), "Output file was not created"

        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_content.strip().split("\n")]

        assert actual_lines == expected_lines, "Focus upstream output does not match"

    def test_generate_focus_downstream(self, runner, test_data_dir, tmp_path):
        """Test generate with focus on downstream only."""
        input_file = test_data_dir / "example_lineage.json"
        expected_output = test_data_dir / "example_focus_downstream.mmd"
        actual_output = tmp_path / "actual_focus_downstream.mmd"

        result = runner.invoke(
            cli,
            [
                "generate_mermaid",
                str(input_file),
                "--focus",
                "dim_customer",
                "--filter-direction",
                "downstream",
                "-o",
                str(actual_output),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert actual_output.exists(), "Output file was not created"

        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_content.strip().split("\n")]

        assert actual_lines == expected_lines, "Focus downstream output does not match"

    def test_generate_direct_only(self, runner, test_data_dir, tmp_path):
        """Test generate with direct connections only."""
        input_file = test_data_dir / "example_lineage.json"
        expected_output = test_data_dir / "example_direct_only.mmd"
        actual_output = tmp_path / "actual_direct_only.mmd"

        result = runner.invoke(
            cli,
            [
                "generate_mermaid",
                str(input_file),
                "--focus",
                "dim_customer",
                "--direct-only",
                "-o",
                str(actual_output),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert actual_output.exists(), "Output file was not created"

        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_content.strip().split("\n")]

        assert actual_lines == expected_lines, "Direct only output does not match"

    def test_generate_with_depth_limit(self, runner, test_data_dir, tmp_path):
        """Test generate with depth limit."""
        input_file = test_data_dir / "example_lineage.json"
        expected_output = test_data_dir / "example_depth_1.mmd"
        actual_output = tmp_path / "actual_depth_1.mmd"

        result = runner.invoke(
            cli,
            [
                "generate_mermaid",
                str(input_file),
                "--focus",
                "dim_customer",
                "--depth",
                "1",
                "-o",
                str(actual_output),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert actual_output.exists(), "Output file was not created"

        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_content.strip().split("\n")]

        assert actual_lines == expected_lines, "Depth limit output does not match"

    def test_generate_yaml_format(self, runner, test_data_dir, tmp_path):
        """Test generate command with YAML input format."""
        input_file = test_data_dir / "example_lineage.yaml"
        expected_output = test_data_dir / "example_full_lineage.mmd"
        actual_output = tmp_path / "actual_yaml_output.mmd"

        result = runner.invoke(
            cli, ["generate_mermaid", str(input_file), "-o", str(actual_output)]
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert actual_output.exists(), "Output file was not created"

        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_content.strip().split("\n")]

        assert actual_lines == expected_lines, "YAML format output does not match JSON output"


class TestLegendCommandIntegration:
    """Integration tests for legend command."""

    def test_legend_produces_expected_output(self, runner, test_data_dir, tmp_path):
        """Test legend command produces expected output."""
        expected_output = test_data_dir / "legend_output.mmd"
        actual_output = tmp_path / "actual_legend.mmd"

        # Run the CLI command
        result = runner.invoke(cli, ["generate_legend_mermaid", "-o", str(actual_output)])

        # Check command succeeded
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify output file was created
        assert actual_output.exists(), "Output file was not created"

        # Compare actual output with expected output
        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        # Normalize line endings and trailing whitespace
        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [
            line.rstrip() for line in expected_content.strip().split("\n")
        ]

        assert actual_lines == expected_lines, "Generated legend does not match expected output"


class TestExtractSqlCommandIntegration:
    """Integration tests for extract_from_sql command."""

    def test_extract_from_sql_basic(self, runner, test_data_dir, tmp_path):
        """Test extract_from_sql command extracts nodes from SQL file."""
        input_file = test_data_dir / "test_extract.sql"
        expected_output = test_data_dir / "test_extract_expected.yaml"
        actual_output = tmp_path / "actual_extract.yaml"

        # Run the CLI command
        result = runner.invoke(
            cli, ["extract_from_sql", str(input_file), "-o", str(actual_output)]
        )

        # Check command succeeded
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Extracted 3 nodes" in result.output

        # Verify output file was created
        assert actual_output.exists(), "Output file was not created"

        # Compare actual output with expected output
        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        # Normalize line endings and trailing whitespace
        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [
            line.rstrip() for line in expected_content.strip().split("\n")
        ]

        assert actual_lines == expected_lines, "Extracted nodes do not match expected output"

    def test_extract_from_sql_multiple_schemas(self, runner, test_data_dir, tmp_path):
        """Test extract_from_sql with complex lineage across multiple schemas."""
        input_file = test_data_dir / "test_extract2.sql"
        expected_output = test_data_dir / "test_extract2_expected.yaml"
        actual_output = tmp_path / "actual_extract2.yaml"

        # Run the CLI command
        result = runner.invoke(
            cli, ["extract_from_sql", str(input_file), "-o", str(actual_output)]
        )

        # Check command succeeded
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Extracted 10 nodes" in result.output

        # Verify output file was created
        assert actual_output.exists(), "Output file was not created"

        # Compare actual output with expected output
        actual_content = actual_output.read_text()
        expected_content = expected_output.read_text()

        # Normalize line endings and trailing whitespace
        actual_lines = [line.rstrip() for line in actual_content.strip().split("\n")]
        expected_lines = [
            line.rstrip() for line in expected_content.strip().split("\n")
        ]

        assert actual_lines == expected_lines, "Extracted nodes do not match expected output"

    def test_extract_from_sql_append_mode(self, runner, test_data_dir, tmp_path):
        """Test extract_from_sql with --append flag."""
        output_file = tmp_path / "combined.yaml"

        # First extraction
        result1 = runner.invoke(
            cli, ["extract_from_sql", str(test_data_dir / "test_extract.sql"), "-o", str(output_file)]
        )
        assert result1.exit_code == 0
        assert "Extracted 3 nodes" in result1.output

        # Second extraction with append (test_extract2 has 10 nodes, all new)
        result2 = runner.invoke(
            cli, ["extract_from_sql", str(test_data_dir / "test_extract2.sql"), "-o", str(output_file), "--append"]
        )
        assert result2.exit_code == 0
        assert "Appended 10 nodes" in result2.output

        # Verify combined output
        yaml = YAML()
        with output_file.open("r") as f:
            data = yaml.load(f)

        # Should have 3 (from test_extract) + 10 (from test_extract2) = 13 total
        assert len(data["nodes"]) == 13

        # Verify nodes from both files are present
        node_ids = [node["id"] for node in data["nodes"]]
        assert "datamart_schema.dim_customer" in node_ids  # from test_extract
        assert "source.raw_customers" in node_ids  # from test_extract2
        assert "staging.stg_customers" in node_ids  # from test_extract2

        # First 3 should be from test_extract (alphabetically sorted in first extraction)
        assert data["nodes"][0]["id"] == "analytics_schema.dim_customer"
        assert data["nodes"][1]["id"] == "analytics_schema.fact_orders"
        assert data["nodes"][2]["id"] == "datamart_schema.dim_customer"

        # Last 10 should be from test_extract2 (appended, also alphabetically sorted)
        appended_ids = node_ids[3:]
        assert appended_ids == sorted(appended_ids)

    def test_extract_from_sql_with_lineage(self, runner, test_data_dir, tmp_path):
        """Test that lineage is extracted from SQL files."""
        input_file = test_data_dir / "test_extract_demo.sql"
        output_file = tmp_path / "demo_output.yaml"

        result = runner.invoke(
            cli, ["extract_from_sql", str(input_file), "-o", str(output_file)]
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Extracted 2 nodes" in result.output

        # Parse the output YAML
        yaml = YAML()
        with output_file.open("r") as f:
            data = yaml.load(f)

        assert len(data["nodes"]) == 2

        # Check customer_summary view
        customer_summary = next(n for n in data["nodes"] if n["id"] == "analytics.customer_summary")
        assert customer_summary["data_type"] == "view"
        assert set(customer_summary["select_from"]) == {"raw.customers", "raw.orders"}

        # Check dim_customer table
        dim_customer = next(n for n in data["nodes"] if n["id"] == "warehouse.dim_customer")
        assert dim_customer["data_type"] == "table"
        assert set(dim_customer["select_from"]) == {"analytics.customer_summary", "raw.customer_addresses"}


class TestImputeMissingConnectingNodesCommandIntegration:
    """Integration tests for impute_missing_connecting_nodes command."""

    def test_no_missing_nodes(self, runner, tmp_path):
        """Test when no missing nodes exist."""
        yaml_content = """nodes:
  - id: node_a
    select_from:
      - node_b
  - id: node_b
    select_from:
"""
        input_file = tmp_path / "no_missing.yaml"
        input_file.write_text(yaml_content)
        output_file = tmp_path / "output.yaml"

        result = runner.invoke(
            cli, ["impute_missing_connecting_nodes", str(input_file), "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert "Missing nodes added: 0" in result.output
