"""Styling configuration for Mermaid diagram generation."""

from typing import Literal

DataType = Literal[
    "table",
    "view",
    "external-source",
    "external-resourcelink",
    "manual-source",
    "unknown",
]

DataLevel = Literal[
    "source",
    "staging",
    "base",
    "dimension",
    "fact",
    "export",
    "unknown",
]

ConnectionType = Literal[
    "select_from",
    "connected_to",
]


# Node shapes based on data_type
# Format: {data_type: (prefix, suffix)}
NODE_SHAPES: dict[str, tuple[str, str]] = {
    "table": ("[", "]"),  # Rectangle
    "view": ("([", "])"),  # Stadium
    "external-source": ("[(", ")]"),  # Cylinder
    "external-resourcelink": ("{{", "}}"),  # Hexagon
    "manual-source": ("[/", "\\]"),  # Trapezoid
    "unknown": ("[", "]"),  # Default to Rectangle
}

# CSS styles based on data_level
DATA_LEVEL_STYLES: dict[str, str] = {
    "source": "fill:#e1f5ff,stroke:#01579b,stroke-width:2px",
    "staging": "fill:#fff3e0,stroke:#e65100,stroke-width:2px",
    "base": "fill:#f3e5f5,stroke:#4a148c,stroke-width:2px",
    "dimension": "fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px",
    "fact": "fill:#fce4ec,stroke:#880e4f,stroke-width:3px",
    "export": "fill:#fff9c4,stroke:#f57f17,stroke-width:2px",
    "unknown": "fill:#ffffff,stroke:#000000,stroke-width:1px",
}

# Connection arrow styles
CONNECTION_STYLES: dict[str, str] = {
    "select_from": "-->",
    "connected_to": "---",
}

# Default connection type (first key from CONNECTION_STYLES)
DEFAULT_CONNECTION_TYPE = next(iter(CONNECTION_STYLES))
