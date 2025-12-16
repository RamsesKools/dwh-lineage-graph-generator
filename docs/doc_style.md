# Documentation Style Guide

This document defines our approach to writing and maintaining documentation.

## Core Principles

### Write Once

- Never duplicate information across README, docs, code, or comments
- If it's in a docstring, don't put it in documentation
- If it's in code, don't document it separately
- Single source of truth for every piece of information

### Be Concise

- Only document what adds new information
- Skip obvious details
- Avoid verbosity
- Get to the point quickly

### High-Level Focus

- Documentation is for concepts, conventions, and decisions
- Implementation details belong in docstrings
- Don't show full code examples when a description suffices
- Link to source code instead of duplicating it

### Maintainability First

- Don't document things that change frequently (file lists, exact syntax, colors)
- Point to commands or code that shows current state (`lineage generate_legend_mermaid`)
- Point to test fixtures instead of writing examples
- Avoid implementation details that will drift from actual code

## What to Document

- **Conventions**: Naming patterns, file organization, import styles
- **Design decisions**: Why we chose X over Y, architectural patterns
- **Non-obvious patterns**: Things that aren't clear from reading code
- **Workflows**: How to accomplish common tasks
- **Gotchas**: Common mistakes and how to avoid them
- **Philosophy**: "Write once" principle, documentation approach
- **Setup**: Prerequisites and initial configuration

## Documentation Structure

### `README.md`

- Project overview and purpose
- Quick start (minimal, just enough to run)
- Brief overview of main features
- Links to detailed documentation
- Keep under 200 lines

### `docs/`

Detailed documentation for specific topics:

### In-Code Documentation

- **Docstrings**: Function/class behavior, parameters, return values
- **Comments**: Why something is done, not what (code shows what)

## Writing Style

### Structure

- Use clear headings and hierarchy
- Keep sections focused on one topic
- Use bullet points for lists

### Code Examples

- Only include when necessary to explain a concept
- Keep examples minimal
- Point to actual test files for comprehensive examples
- Don't show full implementations - link to source instead

### References

- Link to source files: `[LineageGraph](../src/lineage/graph/lineage_graph.py)`
- Link to commands that show current state: "Run `lineage generate_legend_mermaid`"
- Link to test fixtures: "See `tests/data/` for examples"
- Link between docs: `[File Format](file_format.md)`
