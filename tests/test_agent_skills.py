import json
import os
import runpy
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fastapi_cabinet.agent_skills.cli import main
from fastapi_cabinet.agent_skills.fs_transaction import FSError, validate_no_symlinks
from fastapi_cabinet.agent_skills.manifest_rules import (
    ManifestError,
    build_manifest,
    parse_manifest,
    update_agents_md_bytes,
)
from fastapi_cabinet.agent_skills.orchestrator import (
    OrchestratorError,
    check_status,
    get_payload_files,
    perform_delete,
    perform_install,
)


def test_install_update_delete_preserve_unrelated_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = b"# Project rules\r\nKeep these rules.\r\n"
    (tmp_path / "AGENTS.md").write_bytes(original)
    payload = get_payload_files()
    assert {"SKILL.md", "references/composition.md", "references/integration.md"} <= payload.keys()

    perform_install(tmp_path)
    skill = tmp_path / ".agents/skills/codex-fastapi-cabinet"
    manifest = parse_manifest((skill / ".manifest.json").read_bytes())
    assert set(manifest["files"]) == set(payload)
    assert check_status(tmp_path)[0]
    (skill / "my-notes.md").write_text("owned by the project")

    upgraded = {"SKILL.md": b"---\nname: codex-fastapi-cabinet\ndescription: Updated\n---\n"}
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_payload_files", lambda: upgraded)
    perform_install(tmp_path, update=True)
    assert (skill / "SKILL.md").read_bytes() == upgraded["SKILL.md"]
    assert not (skill / "references/composition.md").exists()
    assert (skill / "my-notes.md").read_text() == "owned by the project"

    perform_delete(tmp_path)
    assert (tmp_path / "AGENTS.md").read_bytes() == original
    assert (skill / "my-notes.md").exists()
    assert not (skill / ".manifest.json").exists()


def test_install_and_delete_created_agents_file(tmp_path: Path) -> None:
    perform_install(tmp_path)
    assert check_status(tmp_path)[0]
    perform_delete(tmp_path)
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".agents/skills/codex-fastapi-cabinet").exists()


def test_modified_managed_file_blocks_update_and_delete(tmp_path: Path) -> None:
    perform_install(tmp_path)
    skill = tmp_path / ".agents/skills/codex-fastapi-cabinet"
    target = skill / "SKILL.md"
    target.write_bytes(target.read_bytes() + b"\nlocal edit\n")
    assert not check_status(tmp_path)[0]
    with pytest.raises(OrchestratorError, match="modified"):
        perform_install(tmp_path, update=True)
    with pytest.raises(OrchestratorError, match="modified"):
        perform_delete(tmp_path)
    assert target.read_bytes().endswith(b"local edit\n")


def test_orphan_block_and_unowned_directory_refused(tmp_path: Path) -> None:
    target = tmp_path / ".agents/skills/codex-fastapi-cabinet"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("user skill")
    with pytest.raises(OrchestratorError, match="without ownership manifest"):
        perform_install(tmp_path)
    assert (target / "SKILL.md").read_text() == "user skill"


def test_unowned_payload_collision_blocks_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    perform_install(tmp_path)
    target = tmp_path / ".agents/skills/codex-fastapi-cabinet" / "new.md"
    target.write_text("mine")
    payload = get_payload_files() | {"new.md": b"package"}
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_payload_files", lambda: payload)
    with pytest.raises(OrchestratorError, match="colliding"):
        perform_install(tmp_path, update=True)
    assert target.read_text() == "mine"


def test_corrupt_agents_block_blocks_mutation(tmp_path: Path) -> None:
    perform_install(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_bytes(agents.read_bytes().replace(b"Use [codex-fastapi-cabinet]", b"Changed [codex-fastapi-cabinet]"))
    with pytest.raises(OrchestratorError, match="Corrupt AGENTS.md block"):
        perform_delete(tmp_path)
    assert (tmp_path / ".agents/skills/codex-fastapi-cabinet/.manifest.json").exists()


def test_cli_reports_os_error_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr("fastapi_cabinet.agent_skills.cli.perform_install", fail)
    with pytest.raises(SystemExit) as result:
        main(["install", "--project", str(tmp_path)])
    assert result.value.code == 1
    assert "disk unavailable" in capsys.readouterr().err


def test_install_rolls_back_after_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_bytes(b"# Existing rules\n")
    real_replace = os.replace
    calls = 0

    def fail_second_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        real_replace(source, target)

    monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.os.replace", fail_second_replace)
    with pytest.raises(FSError, match="rolled back"):
        perform_install(tmp_path)
    assert agents.read_bytes() == b"# Existing rules\n"
    assert not (tmp_path / ".agents/skills/codex-fastapi-cabinet/.manifest.json").exists()
    assert not list(tmp_path.glob(".codex-fastapi-cabinet-tx-*"))


def _installation_bytes(project: Path) -> dict[str, bytes]:
    return {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and ".codex-fastapi-cabinet-tx-" not in path.as_posix()
    }


def test_update_failure_restores_entire_installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_bytes(b"# Existing rules\r\nKeep these rules.\r\n")
    perform_install(tmp_path)
    skill = tmp_path / ".agents/skills/codex-fastapi-cabinet"
    (skill / "project-notes.md").write_bytes(b"unowned\r\n")
    before = _installation_bytes(tmp_path)

    upgraded = {"SKILL.md": b"updated skill", "references/new.md": b"new reference"}
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_payload_files", lambda: upgraded)
    real_replace = os.replace
    calls = 0

    def fail_after_first_write(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("update interrupted")
        real_replace(source, target)

    monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.os.replace", fail_after_first_write)
    with pytest.raises(FSError, match="rolled back"):
        perform_install(tmp_path, update=True)
    assert _installation_bytes(tmp_path) == before
    assert not (skill / "references/new.md").exists()
    assert not list(tmp_path.glob(".codex-fastapi-cabinet-tx-*"))
    monkeypatch.undo()
    assert check_status(tmp_path)[0]


def test_delete_failure_restores_entire_installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_bytes(b"# Existing rules\n")
    perform_install(tmp_path)
    before = _installation_bytes(tmp_path)
    real_unlink = Path.unlink
    calls = 0

    def fail_after_first_delete(path: Path, missing_ok: bool = False) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("delete interrupted")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.Path.unlink", fail_after_first_delete)
    with pytest.raises(FSError, match="rolled back"):
        perform_delete(tmp_path)
    assert _installation_bytes(tmp_path) == before
    assert not list(tmp_path.glob(".codex-fastapi-cabinet-tx-*"))
    monkeypatch.undo()
    assert check_status(tmp_path)[0]


def test_failed_recovery_retains_intact_backups(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "AGENTS.md").write_bytes(b"# Existing rules\n")
    perform_install(tmp_path)
    before = _installation_bytes(tmp_path)
    upgraded = {"SKILL.md": b"updated skill"}
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_payload_files", lambda: upgraded)
    real_replace = os.replace
    real_copy2 = shutil.copy2
    replace_calls = 0

    def fail_second_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("write interrupted")
        real_replace(source, target)

    def fail_one_restore(
        source: str | os.PathLike[str], target: str | os.PathLike[str], *, follow_symlinks: bool = True
    ) -> str:
        source_path = Path(source)
        target_path = Path(target)
        if source_path.parent.name == "backup" and target_path.name == "SKILL.md":
            raise OSError("restore interrupted")
        return str(real_copy2(source, target, follow_symlinks=follow_symlinks))

    monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.os.replace", fail_second_replace)
    monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.shutil.copy2", fail_one_restore)
    with pytest.raises(FSError, match="Backups retained at") as result:
        perform_install(tmp_path, update=True)
    assert "restore interrupted" in str(result.value)
    recovery_dir = Path(str(result.value).split("Backups retained at ", 1)[1])
    assert recovery_dir.parent == tmp_path
    backups = list((recovery_dir / "backup").iterdir())
    assert backups
    assert before[".agents/skills/codex-fastapi-cabinet/SKILL.md"] in [file.read_bytes() for file in backups]
    assert (recovery_dir / "backup").is_dir()


def test_symlink_destination_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "AGENTS.md"
    linked = tmp_path / "elsewhere.md"
    linked.write_text("keep")
    try:
        target.symlink_to(linked)
    except (OSError, NotImplementedError):
        # Exercise the same lstat branch when Windows denies symlink creation.
        original_lstat = Path.lstat

        def reparse_lstat(path: Path, *args: object, **kwargs: object) -> os.stat_result | SimpleNamespace:
            if path == target:
                return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
            return original_lstat(path, *args, **kwargs)

        monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.Path.lstat", reparse_lstat)
    with pytest.raises(FSError, match="Symlink"):
        perform_install(tmp_path)
    assert linked.read_text() == "keep"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction test")
def test_windows_junction_ancestor_is_refused(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    junction = tmp_path / ".agents"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(external)], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"Windows junction unavailable: {result.stderr.strip()}")
    with pytest.raises(FSError, match="Symlink or reparse point"):
        perform_install(tmp_path)
    assert list(external.iterdir()) == []


def test_dangling_link_is_refused_before_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "AGENTS.md"
    try:
        target.symlink_to(tmp_path / "missing.md")
    except (OSError, NotImplementedError):
        original_lstat = Path.lstat

        def dangling_lstat(path: Path, *args: object, **kwargs: object) -> os.stat_result | SimpleNamespace:
            if path == target:
                return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
            return original_lstat(path, *args, **kwargs)

        monkeypatch.setattr("fastapi_cabinet.agent_skills.fs_transaction.Path.lstat", dangling_lstat)
    with pytest.raises(FSError, match="Symlink"):
        validate_no_symlinks(target)
    assert not (tmp_path / ".agents").exists()


@pytest.mark.parametrize("bad_path", ["../escape", "/absolute", "a/../b", "a\\b", "CON.md", "x//y"])
def test_manifest_rejects_unsafe_paths(bad_path: str) -> None:
    manifest = {
        "version": "1.0",
        "skill": "codex-fastapi-cabinet",
        "package_version": "1",
        "files": {"SKILL.md": "a" * 64, bad_path: "a" * 64},
        "agents_created": False,
    }
    with pytest.raises(ManifestError):
        parse_manifest(json.dumps(manifest).encode())


def test_cli_lifecycle_and_absent_status(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for action, code in [("status", 1), ("install", 0), ("status", 0), ("update", 0), ("delete", 0)]:
        if code:
            with pytest.raises(SystemExit) as result:
                main([action, "--project", str(tmp_path)])
            assert result.value.code == code
        else:
            main([action, "--project", str(tmp_path)])
    assert "Not installed." in capsys.readouterr().out


def test_cli_invalid_project_and_module_entry(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as result:
        main(["install", "--project", str(tmp_path / "absent")])
    assert result.value.code == 1
    assert "does not exist" in capsys.readouterr().err
    with pytest.raises(SystemExit) as result:
        runpy.run_module("fastapi_cabinet.agent_skills", run_name="__main__")
    assert result.value.code == 2


def test_status_detects_version_payload_and_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    perform_install(tmp_path)
    assert check_status(tmp_path)[0]
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_package_version", lambda: "future")
    assert "version differs" in check_status(tmp_path)[1]
    monkeypatch.undo()
    payload = get_payload_files() | {"new.md": b"new"}
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_payload_files", lambda: payload)
    assert "file list differs" in check_status(tmp_path)[1]
    monkeypatch.undo()
    payload = get_payload_files()
    payload["SKILL.md"] += b"\n"
    monkeypatch.setattr("fastapi_cabinet.agent_skills.orchestrator.get_payload_files", lambda: payload)
    assert "payload differs" in check_status(tmp_path)[1]
    monkeypatch.undo()
    (tmp_path / ".agents/skills/codex-fastapi-cabinet/SKILL.md").unlink()
    assert "Missing file" in check_status(tmp_path)[1]
    with pytest.raises(OrchestratorError, match="modified or are missing"):
        perform_delete(tmp_path)


def test_corrupt_manifest_and_missing_agents_block(tmp_path: Path) -> None:
    perform_install(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.unlink()
    assert "instruction missing" in check_status(tmp_path)[1]
    with pytest.raises(OrchestratorError, match="instruction missing"):
        perform_install(tmp_path, update=True)
    manifest = tmp_path / ".agents/skills/codex-fastapi-cabinet/.manifest.json"
    manifest.write_text("not json")
    assert "Corrupt ownership manifest" in check_status(tmp_path)[1]
    with pytest.raises(OrchestratorError, match="Corrupt ownership manifest"):
        perform_delete(tmp_path)


def test_unmanaged_states(tmp_path: Path) -> None:
    with pytest.raises(OrchestratorError, match="Not installed"):
        perform_install(tmp_path, update=True)
    perform_delete(tmp_path)
    perform_install(tmp_path)
    perform_install(tmp_path)
    skill = tmp_path / ".agents/skills/codex-fastapi-cabinet"
    (skill / ".manifest.json").unlink()
    assert "Orphan" in check_status(tmp_path)[1]
    with pytest.raises(OrchestratorError, match="Orphan"):
        perform_install(tmp_path)
    with pytest.raises(OrchestratorError, match="No ownership manifest"):
        perform_delete(tmp_path)


@pytest.mark.parametrize(
    "content",
    [
        b"not json",
        b'{"version": "1.0"}',
        b'{"version": "1.0", "version": "1.0"}',
        b'{"version": "1.0", "skill": "wrong", "package_version": "1", "files": {}, "agents_created": false}',
    ],
)
def test_manifest_rejects_corruption(content: bytes) -> None:
    with pytest.raises(ManifestError):
        parse_manifest(content)


def test_manifest_rejects_alias_parent_conflict_and_bad_hash() -> None:
    with pytest.raises(ManifestError, match="Case alias"):
        build_manifest("1", {"SKILL.md": b"x", "skill.md": b"y"})
    with pytest.raises(ManifestError, match="parent conflict"):
        build_manifest("1", {"SKILL.md": b"x", "a": b"x", "a/b": b"y"})
    with pytest.raises(ManifestError, match="Reserved"):
        build_manifest("1", {"SKILL.md": b"x", ".manifest.json": b"y"})
    manifest = json.loads(build_manifest("1", {"SKILL.md": b"x"}))
    manifest["files"]["SKILL.md"] = "wrong"
    with pytest.raises(ManifestError, match="SHA256"):
        parse_manifest(json.dumps(manifest).encode())


def test_agents_block_round_trip_and_tampering() -> None:
    original = b"\xef\xbb\xbf# Rules\r\nKeep."
    installed = update_agents_md_bytes(original)
    assert update_agents_md_bytes(installed) == installed
    assert update_agents_md_bytes(installed, remove=True) == original
    assert update_agents_md_bytes(original, remove=True) == original
    with pytest.raises(ManifestError):
        update_agents_md_bytes(installed.replace(b":skill:end", b":skill:bad"))
    with pytest.raises(ManifestError):
        update_agents_md_bytes(installed + installed)
