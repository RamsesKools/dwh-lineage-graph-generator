"""CLI tool for generating Mermaid diagrams from data warehouse lineage."""

import sys
from pathlib import Path
from typing import Optional

import click

from __init__ import __version__
from extractor.sql_parser import extract_nodes_from_sql_files
from extractor.yaml_writer import write_nodes_to_yaml
from lineage_graph import LineageGraph
from lineage_parser import load_lineage_file
from mmd_generator import MermaidGenerator, generate_legend
from missing_nodes_imputer import impute_missing_connecting_nodes


@click.command(
    name="generate_mermaid",
    help="Generate Mermaid diagram from JSON or YAML lineage data",
)
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "-d",
    "--direction",
    type=click.Choice(["LR", "RL", "TB", "BT"], case_sensitive=False),
    default="LR",
    help="Diagram flow direction (default: LR)",
)
@click.option(
    "--focus",
    type=str,
    help="Focus on specific node(s), comma-separated (e.g., 'dim_customer' or 'dim_customer,fact_orders')",
)
@click.option(
    "--filter-direction",
    type=click.Choice(["upstream", "downstream", "both"], case_sensitive=False),
    default="both",
    help="Filter direction when using --focus (default: both)",
)
@click.option(
    "--depth",
    type=int,
    help="Maximum depth for graph traversal when using --focus (default: unlimited)",
)
@click.option(
    "--direct-only",
    is_flag=True,
    help="Show only direct connections when using --focus",
)
def mmd_generate_command(
    input_file: Path,
    output: Optional[Path],
    direction: str,
    focus: Optional[str],
    filter_direction: str,
    depth: Optional[int],
    direct_only: bool,
) -> None:
    """Generate Mermaid diagram from lineage data.

    Supports JSON and YAML input formats.

    \b
    Options:
    -o, --output: Output file path
    -d, --direction: Diagram direction (LR/RL/TB/BT)
    --focus: Focus on specific nodes (comma-separated)
    --filter-direction: Filter direction (upstream/downstream/both)
    --depth: Maximum traversal depth
    --direct-only: Show only direct connections
    """
    try:
        # Load and parse lineage data (supports JSON and YAML)
        nodes, connections = load_lineage_file(input_file)

        # Get node IDs for validation
        node_ids = {node.id for node in nodes}

        # Apply focus filtering if requested
        if focus:
            focus_node_ids = [node_id.strip() for node_id in focus.split(",")]

            # Validate focus nodes exist
            for focus_node_id in focus_node_ids:
                if focus_node_id not in node_ids:
                    click.echo(
                        f"Error: Focus node '{focus_node_id}' not found in data",
                        err=True,
                    )
                    sys.exit(1)

            # Create graph and filter
            graph = LineageGraph(nodes, connections)

            if direct_only:
                nodes, connections = graph.get_direct_subgraph(focus_node_ids)
            else:
                nodes, connections = graph.get_subgraph(
                    focus_node_ids,
                    direction=filter_direction,  # type: ignore
                    max_depth=depth,
                )

        # Generate Mermaid diagram
        click.echo("Generating Mermaid diagram...")
        mmd_generator = MermaidGenerator(
            nodes=nodes,
            connections=connections,
            direction=direction.upper(),  # type: ignore
        )
        mermaid_output = mmd_generator.generate()

        # Output result
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(mermaid_output)
            click.echo(f"Mermaid diagram written to {output}")
        else:
            click.echo(mermaid_output)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command(
    name="generate_legend_mermaid",
    help="Generate a legend showing all available node types, data levels, and connection styles",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path (default: stdout)",
)
def mmd_legend_command(
    output: Optional[Path],
) -> None:
    """Generate a legend diagram showing all available styles.

    \b
    The legend includes:
    - All node shapes (data types)
    - All data levels with colors
    - All connection types

    \b
    The legend is displayed with subgraphs stacked vertically,
    while content within each subgraph flows left to right.

    \b
    Examples:
        python cli.py legend
        python cli.py legend -o legend.mmd
    """
    try:
        # Generate legend
        mermaid_output = generate_legend()

        # Output result
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(mermaid_output)
            click.echo(f"Legend diagram written to {output}")
        else:
            click.echo(mermaid_output)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command(
    name="extract_from_sql",
    help="Extract lineage nodes from SQL files",
)
@click.argument(
    "pattern",
    type=str,
)
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output YAML file path",
)
@click.option(
    "--append",
    is_flag=True,
    help="Append to existing YAML file instead of overwriting",
)
def extract_from_sql_command(
    pattern: str,
    output: Path,
    append: bool,
) -> None:
    """Extract nodes from SQL files using glob patterns.

    PATTERN: Glob pattern to match SQL files. Supports:
    - Single file: "path/to/file.sql"
    - Directory: "sql/*.sql"
    - Recursive: "sql/**/*.sql" (all subdirectories)

    Only schema-qualified objects (schema.table) are extracted.
    Extracts CREATE TABLE and CREATE VIEW statements as nodes.
    Connections (select_from) and data_level are set as placeholders for manual completion.

    \b
    Options:
    -o, --output: Output YAML file path (required)
    --append: Append to existing file (only adds new nodes, preserves existing)

    \b
    Examples:
    # Extract from all SQL files recursively
    poetry run python cli.py extract_from_sql "sql/**/*.sql" -o lineage.yaml

    # Extract from specific directory
    poetry run python cli.py extract_from_sql "sql/staging/*.sql" -o staging.yaml

    # Append to existing file
    poetry run python cli.py extract_from_sql "sql/base/*.sql" -o lineage.yaml --append

    # Single file
    poetry run python cli.py extract_from_sql "create_tables.sql" -o output.yaml
    """
    try:
        # Extract nodes from SQL files
        nodes = extract_nodes_from_sql_files(pattern)

        if not nodes:
            click.echo(f"Warning: No nodes found matching pattern: {pattern}", err=True)
            return

        # Write YAML output (append or overwrite)
        stats = write_nodes_to_yaml(
            nodes, output, update_nodes=False, prevent_file_overwrite=not append
        )

        if append:
            click.echo(f"Appended {stats['nodes_added']} nodes to {output}")
        else:
            click.echo(f"Extracted {stats['nodes_added']} nodes to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group(
    name="lineage",
    help="Data Lineage related commands",
)
@click.version_option(version=__version__, prog_name="lineage")
def cli() -> None:
    """Data Lineage CLI tool."""
    pass


@click.command(
    name="impute_missing_connecting_nodes",
    help="Add missing nodes that are referenced in select_from fields",
)
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path (default: modify input file in-place)",
)
def impute_missing_connecting_nodes_command(
    input_file: Path,
    output: Optional[Path],
) -> None:
    """Impute missing connecting nodes in a lineage YAML file.

    Identifies nodes that are referenced in select_from fields but do not
    exist in the nodes list, and appends them to the end with null values
    for data_level and data_type. Preserves comments, formatting, and node order.

    INPUT_FILE: Path to the YAML lineage file

    \b
    Behavior:
    - Scans all select_from fields to find referenced node IDs
    - Identifies which referenced nodes are missing from the nodes list
    - Appends missing nodes to the end of the nodes list
    - New nodes have null data_level and data_type
    - New nodes have empty select_from lists
    - Self-references are excluded (node referencing itself)

    \b
    Options:
    -o, --output: Output file path (if not specified, modifies input file in-place)

    \b
    Examples:
    # Modify file in-place
    poetry run python cli.py impute_missing_connecting_nodes lineage.yaml

    # Create new file with imputed nodes
    poetry run python cli.py impute_missing_connecting_nodes input.yaml -o output.yaml
    """
    try:
        # Determine output path (default to input for in-place modification)
        output_path = output if output else input_file

        # Perform imputation
        stats = impute_missing_connecting_nodes(input_file, output_path)

        # Output results
        if output:
            click.echo(f"Imputed lineage written to {output}")
        else:
            click.echo(f"Modified {input_file} in-place")

        click.echo(str(stats))

    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)



# Add commands to the group
cli.add_command(extract_from_sql_command)
cli.add_command(mmd_generate_command)
cli.add_command(mmd_legend_command)
cli.add_command(impute_missing_connecting_nodes_command)


if __name__ == "__main__":
    cli()
