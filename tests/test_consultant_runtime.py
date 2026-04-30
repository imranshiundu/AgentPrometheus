from pathlib import Path

from prometheus_consultant import RuntimeConfig, apply_patches, collect_evidence, compile_python, is_text_file
from prometheus_json import parse_consultant_json


def test_compile_python_does_not_write_pyc(tmp_path):
    source = tmp_path / "ok.py"
    source.write_text("x = 1\n", encoding="utf-8")
    errors = compile_python([source], tmp_path)
    assert errors == []
    assert not (tmp_path / "__pycache__").exists()


def test_dockerfile_variants_are_text():
    assert is_text_file(Path("docker/Manager.Dockerfile"))
    assert is_text_file(Path("Dockerfile"))


def test_hive_mind_db_is_ignored(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "hive_mind_db").mkdir(parents=True)
    (workspace / "hive_mind_db" / "logs.txt").write_text("secret logs", encoding="utf-8")
    (workspace / "app.py").write_text("print('ok')\n", encoding="utf-8")
    config = RuntimeConfig(workspace=workspace, max_files=20)
    evidence = collect_evidence("scan app", config)
    paths = {row["path"] for row in evidence["selected_files"]}
    assert "app.py" in paths
    assert "hive_mind_db/logs.txt" not in paths


def test_parse_consultant_json_repairs_basic_weak_model_output():
    parsed = parse_consultant_json("```json\n{summary: \"ok\", findings: [\"x\",], confidence: \"medium\",}\n```")
    assert parsed["summary"] == "ok"
    assert parsed["findings"] == ["x"]
    assert parsed["confidence"] == "medium"


def test_apply_patches_refuses_protected_paths(tmp_path):
    config = RuntimeConfig(workspace=tmp_path)
    results = apply_patches([{"op": "write_file", "path": "../escape.txt", "content": "bad"}], config)
    assert results[0]["applied"] is False
    assert "outside workspace" in results[0]["reason"]
