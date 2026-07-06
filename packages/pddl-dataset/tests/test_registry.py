from pddl_dataset.loader import load_registry


def test_load_registry_finds_starter_domains():
    registry = load_registry()
    assert {"gripper", "cavediving", "blocksworld"} <= registry.keys()


def test_gripper_shape():
    gen = load_registry()["gripper"]
    assert gen.binary == "./gripper"
    assert gen.domain_file.source == "static"
    assert gen.output.mode == "stdout"
    assert [p.name for p in gen.parameters] == ["balls"]


def test_blocksworld_outlier_shape():
    gen = load_registry()["blocksworld"]
    assert gen.domain_file.source == "copy"
    assert gen.domain_file.path == "3ops/domain.pddl"
    assert {p.positional for p in gen.parameters} == {0, 1, 2}


def test_cavediving_uses_file_arg_output():
    gen = load_registry()["cavediving"]
    assert gen.output.mode == "file_arg"
    assert gen.output.flag == "-problem_file"
    assert any(p.name == "cave_branches" and p.type == "int_seq" for p in gen.parameters)
