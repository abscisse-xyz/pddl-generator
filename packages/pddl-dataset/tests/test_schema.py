import pytest
from pydantic import ValidationError

from pddl_dataset.schema import Generator, Parameter


def test_parameter_requires_flag_xor_positional():
    with pytest.raises(ValidationError):
        Parameter(name="x", type="int")
    with pytest.raises(ValidationError):
        Parameter(name="x", type="int", flag="-x", positional=0)


def test_generator_rejects_sparse_positional_indices():
    with pytest.raises(ValidationError):
        Generator(
            name="g",
            binary="./g",
            domain_file={"source": "static"},
            output={"mode": "stdout"},
            parameters=[
                Parameter(name="a", type="int", positional=0),
                Parameter(name="b", type="int", positional=2),
            ],
        )


def test_generator_accepts_dense_positional_indices():
    Generator(
        name="g",
        binary="./g",
        domain_file={"source": "static"},
        output={"mode": "stdout"},
        parameters=[
            Parameter(name="a", type="int", positional=0),
            Parameter(name="b", type="int", positional=1),
        ],
    )


def test_generator_rejects_setting_both_binary_and_python_module():
    with pytest.raises(ValidationError, match="exactly one"):
        Generator(
            name="g",
            binary="./g",
            python_module="os.path",  # importable, but conflicts with binary
            domain_file={"source": "static"},
            output={"mode": "stdout"},
        )


def test_generator_rejects_neither_binary_nor_module_nor_recipe():
    with pytest.raises(ValidationError, match="exactly one"):
        Generator(
            name="g",
            domain_file={"source": "static"},
            output={"mode": "stdout"},
        )


def test_generator_rejects_unimportable_python_module():
    with pytest.raises(ValidationError, match="not importable"):
        Generator(
            name="g",
            python_module="this_module_does_not_exist_anywhere_xyz123",
            domain_file={"source": "static"},
            output={"mode": "stdout"},
        )


def test_generator_accepts_python_module_form():
    g = Generator(
        name="g",
        python_module="os.path",  # any importable stdlib module
        domain_file={"source": "emitted_by_generator", "flag": "-domain_file"},
        output={"mode": "file_arg", "flag": "-problem_file"},
    )
    assert g.python_module == "os.path"
    assert g.domain_file.flag == "-domain_file"
