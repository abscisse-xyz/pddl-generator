from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

ParamType = Literal["int", "float", "str", "bool", "int_seq", "float_seq"]


class Parameter(BaseModel):
    name: str
    type: ParamType
    flag: str | None = None
    positional: int | None = None
    required: bool = False
    default: object | None = None
    default_test: object | None = None
    range: tuple[float | None, float | None] | None = None
    description: str = ""

    @model_validator(mode="after")
    def _flag_xor_positional(self) -> Parameter:
        if (self.flag is None) == (self.positional is None):
            raise ValueError(f"parameter {self.name!r}: exactly one of `flag` or `positional` must be set")
        return self


class StaticDomain(BaseModel):
    source: Literal["static"] = "static"
    path: str = "domain.pddl"


class CopyDomain(BaseModel):
    source: Literal["copy"] = "copy"
    path: str


class EmittedDomain(BaseModel):
    source: Literal["emitted_by_generator"] = "emitted_by_generator"
    filename: str = "domain.pddl"
    # When set, the runner appends `<flag> <absolute_domain_path>` to argv and skips
    # the post-run move (the generator wrote directly where we asked).
    flag: str | None = None


DomainSource = Annotated[Union[StaticDomain, CopyDomain, EmittedDomain], Field(discriminator="source")]


class StdoutOutput(BaseModel):
    mode: Literal["stdout"] = "stdout"


class FileArgOutput(BaseModel):
    mode: Literal["file_arg"] = "file_arg"
    flag: str


class CwdFileOutput(BaseModel):
    mode: Literal["cwd_file"] = "cwd_file"
    filename: str


Output = Annotated[Union[StdoutOutput, FileArgOutput, CwdFileOutput], Field(discriminator="mode")]


class CustomRecipe(BaseModel):
    """Escape hatch for ad-hoc generators (multi-step shell scripts, wrappers).
    Each command is rendered with placeholders: {gen_dir}, {out_dir}, {domain_path},
    {problem_path}, {seed}, {instance_name}, and {param_<name>} for each parameter.
    """

    commands: list[str]


class Generator(BaseModel):
    name: str
    binary: str = ""
    python_module: str | None = None  # invoked as `python -m <module>` for in-package generators
    cwd: str = "."
    domain_file: DomainSource
    output: Output | None = None
    parameters: list[Parameter] = Field(default_factory=list)
    fixed_args: list[str] = Field(default_factory=list)
    custom_recipe: CustomRecipe | None = None

    @model_validator(mode="after")
    def _positional_indices_unique_and_dense(self) -> Generator:
        positions = sorted(p.positional for p in self.parameters if p.positional is not None)
        if positions != list(range(len(positions))):
            raise ValueError(f"{self.name}: positional indices must be 0..N-1 with no gaps, got {positions}")
        return self

    @model_validator(mode="after")
    def _invocation_consistency(self) -> Generator:
        paths = sum([bool(self.binary), self.python_module is not None, self.custom_recipe is not None])
        if paths != 1:
            raise ValueError(
                f"{self.name}: must set exactly one of `binary`, `python_module`, or `custom_recipe`; got {paths}"
            )
        if (self.binary or self.python_module is not None) and self.output is None:
            raise ValueError(f"{self.name}: must set `output` when using `binary` or `python_module`")
        return self

    @model_validator(mode="after")
    def _python_module_importable(self) -> Generator:
        if self.python_module is None:
            return self
        import importlib.util

        if importlib.util.find_spec(self.python_module) is None:
            raise ValueError(f"{self.name}: python_module {self.python_module!r} is not importable")
        return self
