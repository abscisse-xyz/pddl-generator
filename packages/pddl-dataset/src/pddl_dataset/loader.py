from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from pddl_dataset.schema import Generator


def load_registry(registry_dir: Path | None = None) -> dict[str, Generator]:
    if registry_dir is None:
        files = [r for r in resources.files("pddl_dataset.registry").iterdir() if r.name.endswith(".yaml")]
        sources = [(f.name, f.read_text()) for f in files]
    else:
        sources = [(p.name, p.read_text()) for p in sorted(registry_dir.glob("*.yaml"))]

    registry: dict[str, Generator] = {}
    for filename, text in sources:
        data = yaml.safe_load(text)
        if not isinstance(data, dict) or "name" not in data:
            raise ValueError(f"{filename}: must be a mapping with a top-level `name` key")
        gen = Generator.model_validate(data)
        if gen.name in registry:
            raise ValueError(f"duplicate generator name {gen.name!r} in {filename}")
        registry[gen.name] = gen
    return registry
