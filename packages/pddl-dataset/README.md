# pddl-dataset

Library and registry for PDDL benchmark generation. Wraps the heterogeneous
generators in [AI-Planning/pddl-generators](https://github.com/AI-Planning/pddl-generators)
behind one uniform interface, each described by a YAML entry under
[src/pddl_dataset/registry/](src/pddl_dataset/registry/). The package ships
**60 generators**:

- **57 from upstream** (gripper, blocksworld, cavediving, logistics, rovers, …).
  Two are excluded — see [KNOWN-BROKEN.md](KNOWN-BROKEN.md).
- **3 first-party**: `citycar`, `travel`, and `logistic`, defined under
  [src/pddl_problem/](src/pddl_problem/). Their registry entries set
  `python_module:` instead of `binary:`.

## Where this fits

This package is **not the user-facing CLI**. End users go through
[`pddl-cli`](../../pddl-cli/) (the dispatcher at the repo root), which exposes
this generator as `pddl-cli dataset …`. Build and invoke the project from the
top-level [README](../../README.md).

The package also ships importable curated batch plans under
[`src/pddl_generator/batch/`](src/pddl_generator/batch/). The user-facing route
is `pddl-cli generate batch …`; it reuses the same registry and runner, but
derives per-instance parameters inside the app instead of shelling out to a
Docker command per problem.

This README focuses on the *library* concerns: how the registry works and how
to add a new generator.

## Registry schema

Each YAML entry in `src/pddl_dataset/registry/` validates against the Pydantic
[`Generator` model](src/pddl_dataset/schema.py). Three invocation styles are
supported, mutually exclusive:

| Field | When to use |
|---|---|
| `binary:` + `output:` | The common case — a compiled executable or a script in the cloned `pddl-generators` tree. |
| `python_module:` + `output:` | First-party generators that ship as importable Python modules in this package (`pddl_problem.<name>.generator_cmd_line`). |
| `custom_recipe:` | Escape hatch for generators with shell-only quirks (e.g. trailing positional output paths, multi-step wrappers). |

The schema also covers parameter declarations (`flag` xor `positional`,
`type`, defaults), domain-file resolution (`static`, `copy`, or
`emitted_by_generator` with optional flag), and output mode (`stdout`,
`file_arg`, `cwd_file`).

### Example entries

- Simple stdout + flag: [gripper.yaml](src/pddl_dataset/registry/gripper.yaml)
- Rich Python generator with file-arg output: [cavediving.yaml](src/pddl_dataset/registry/cavediving.yaml)
- First-party `python_module:` entry: [citycar.yaml](src/pddl_dataset/registry/citycar.yaml)
- Outlier with custom_recipe: [storage.yaml](src/pddl_dataset/registry/storage.yaml) (currently disabled — see KNOWN-BROKEN)

## CityCar modes

`citycar` is implemented as a first-party generator because the curated batch
needs more control than the upstream positional script exposes. It accepts a
`mode` parameter:

| Mode | Behavior |
|---|---|
| `current` | Density-style generation compatible with the old `rows`, `columns`, `cars`, `garages`, `density`, and `seed` workflow. |
| `topology-first` | Keeps grids small while varying topology families and mixed pressure profiles such as balanced, car-pressure, road-rich, garage-rich, junction-tight, and junction-open. |
| `solution-first` | Constructs a route skeleton before rendering the problem, then adds topology around that skeleton. |

The batch plan in [src/pddl_generator/batch/citycar.py](src/pddl_generator/batch/citycar.py)
uses `current` by default. Pass `-p mode=topology-first` or `-p mode=solution-first`
through `pddl-cli generate batch citycar` to select one of the small,
topology-controlled variants.

## Manifest output

Every generation run writes a structured `manifest.json` alongside the
`pNN.pddl` files, recording the command and resolved parameters per instance:

```json
{
  "domain": "gripper",
  "domain_file": "domain.pddl",
  "instances": [
    {
      "file": "p01.pddl",
      "seed": 42,
      "params": {"balls": 10},
      "command": ["./gripper", "-n", "10"]
    }
  ]
}
```

## Development

```sh
uv run pytest packages/pddl-dataset/tests
```

Tests run against fake-generator fixtures and never invoke the real upstream
binaries on the host. End-to-end verification with real generators happens in
the project-level Docker image (see the root README).
