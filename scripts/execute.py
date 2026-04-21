#!/usr/bin/env python3
"""Phase executor for repository-local harness workflows."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import threading
import time
import types
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PHASES_DIRNAME = "phases"
DEFAULT_BRANCH_PREFIX = "codex/"
DEFAULT_AGENT_COMMAND = "claude"
CLAUDE_TIMEOUT_SECONDS = 1800
GUARDRAIL_FILES = (
    "AGENTS.md",
    "README.md",
    "SPEC.md",
    "references/local-adaptation.md",
)
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str] | Any]


@contextlib.contextmanager
def progress_indicator(label: str):
    """Show a spinner while a step is running."""
    frames = "◐◓◑◒"
    stop = threading.Event()
    t0 = time.monotonic()

    def _animate() -> None:
        idx = 0
        while not stop.wait(0.12):
            seconds = int(time.monotonic() - t0)
            sys.stderr.write(f"\r{frames[idx % len(frames)]} {label} [{seconds}s]")
            sys.stderr.flush()
            idx += 1
        sys.stderr.write("\r" + " " * (len(label) + 20) + "\r")
        sys.stderr.flush()

    thread = threading.Thread(target=_animate, daemon=True)
    thread.start()
    info = types.SimpleNamespace(elapsed=0.0)
    try:
        yield info
    finally:
        stop.set()
        thread.join()
        info.elapsed = time.monotonic() - t0


class StepExecutor:
    """Execute phase steps sequentially with retries and status updates."""

    MAX_RETRIES = 3
    FEAT_MSG = "feat({phase}): step {num} - {name}"
    CHORE_MSG = "chore({phase}): step {num} output"
    TZ = timezone(timedelta(hours=9))

    def __init__(
        self,
        phase_dir_name: str,
        *,
        root: Path | None = None,
        auto_push: bool = False,
        subprocess_run: SubprocessRunner = subprocess.run,
        branch_prefix: str | None = None,
        agent_command: str | None = None,
    ) -> None:
        self._root_path = (root or ROOT).resolve()
        self._root = str(self._root_path)
        self._phases_dir = self._root_path / PHASES_DIRNAME
        self._phase_dir = self._phases_dir / phase_dir_name
        self._phase_dir_name = phase_dir_name
        self._top_index_file = self._phases_dir / "index.json"
        self._auto_push = auto_push
        self._subprocess_run = subprocess_run
        self._branch_prefix = branch_prefix or os.getenv(
            "HARNESS_BRANCH_PREFIX",
            DEFAULT_BRANCH_PREFIX,
        )
        self._agent_command = agent_command or os.getenv(
            "HARNESS_AGENT_COMMAND",
            DEFAULT_AGENT_COMMAND,
        )

        if not self._phase_dir.is_dir():
            print(f"ERROR: {self._phase_dir} not found")
            raise SystemExit(1)

        self._index_file = self._phase_dir / "index.json"
        if not self._index_file.exists():
            print(f"ERROR: {self._index_file} not found")
            raise SystemExit(1)

        index = self._read_json(self._index_file)
        self._project = str(index.get("project", "project"))
        self._phase_name = str(index.get("phase", phase_dir_name))
        self._total = len(index["steps"])

    def run(self) -> None:
        self._print_header()
        self._check_blockers()
        self._ensure_clean_worktree()
        self._checkout_branch()
        guardrails = self._load_guardrails()
        self._ensure_created_at()
        self._execute_all_steps(guardrails)
        self._finalize()

    def _stamp(self) -> str:
        return datetime.now(self.TZ).strftime("%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _run_subprocess(self, cmd: list[str], **kwargs: Any) -> Any:
        return self._subprocess_run(cmd, **kwargs)

    def _run_git(self, *args: str) -> Any:
        return self._run_subprocess(
            ["git", *args],
            cwd=self._root,
            capture_output=True,
            text=True,
        )

    def _branch_name(self) -> str:
        return f"{self._branch_prefix}{self._phase_name}"

    def _checkout_branch(self) -> None:
        branch = self._branch_name()
        current = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if current.returncode != 0:
            print("  ERROR: git을 사용할 수 없거나 git repo가 아닙니다.")
            print(f"  {str(current.stderr).strip()}")
            raise SystemExit(1)

        if str(current.stdout).strip() == branch:
            return

        existing = self._run_git("rev-parse", "--verify", branch)
        if existing.returncode == 0:
            result = self._run_git("checkout", branch)
        else:
            result = self._run_git("checkout", "-b", branch)

        if result.returncode != 0:
            print(f"  ERROR: 브랜치 '{branch}' checkout 실패.")
            print(f"  {str(result.stderr).strip()}")
            print("  Hint: 변경사항을 stash하거나 commit한 후 다시 시도하세요.")
            raise SystemExit(1)

        print(f"  Branch: {branch}")

    def _ensure_clean_worktree(self) -> None:
        status = self._run_git("status", "--porcelain")
        if status.returncode != 0:
            print("  ERROR: git status 확인에 실패했습니다.")
            print(f"  {str(status.stderr).strip()}")
            raise SystemExit(1)

        dirty_lines = [line for line in str(status.stdout).splitlines() if line.strip()]
        if not dirty_lines:
            return

        print("  ERROR: 현재 executor는 clean worktree에서만 실행할 수 있습니다.")
        print("  Reason: unrelated local changes를 phase commit에 포함하지 않기 위해서입니다.")
        preview = "\n".join(f"  - {line}" for line in dirty_lines[:10])
        if preview:
            print("  Dirty entries:")
            print(preview)
        if len(dirty_lines) > 10:
            print(f"  ... and {len(dirty_lines) - 10} more")
        raise SystemExit(1)

    def _commit_step(self, step_num: int, step_name: str) -> None:
        output_rel = f"{PHASES_DIRNAME}/{self._phase_dir_name}/step{step_num}-output.json"
        index_rel = f"{PHASES_DIRNAME}/{self._phase_dir_name}/index.json"

        self._run_git("add", "-A")
        self._run_git("reset", "HEAD", "--", output_rel)
        self._run_git("reset", "HEAD", "--", index_rel)

        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            message = self.FEAT_MSG.format(phase=self._phase_name, num=step_num, name=step_name)
            result = self._run_git("commit", "-m", message)
            if result.returncode == 0:
                print(f"  Commit: {message}")
            else:
                print(f"  WARN: 코드 커밋 실패: {str(result.stderr).strip()}")

        self._run_git("add", "-A")
        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            message = self.CHORE_MSG.format(phase=self._phase_name, num=step_num)
            result = self._run_git("commit", "-m", message)
            if result.returncode != 0:
                print(f"  WARN: housekeeping 커밋 실패: {str(result.stderr).strip()}")

    def _update_top_index(self, status: str) -> None:
        if not self._top_index_file.exists():
            return

        top = self._read_json(self._top_index_file)
        timestamp = self._stamp()
        for phase in top.get("phases", []):
            if phase.get("dir") == self._phase_dir_name:
                phase["status"] = status
                stamp_key = {
                    "completed": "completed_at",
                    "error": "failed_at",
                    "blocked": "blocked_at",
                }.get(status)
                if stamp_key:
                    phase[stamp_key] = timestamp
                break
        self._write_json(self._top_index_file, top)

    def _load_guardrails(self) -> str:
        sections: list[str] = []
        for relative_path in GUARDRAIL_FILES:
            path = self._root_path / relative_path
            if not path.exists():
                continue
            sections.append(f"## {relative_path}\n\n{path.read_text(encoding='utf-8')}")
        return "\n\n---\n\n".join(sections)

    @staticmethod
    def _build_step_context(index: dict[str, Any]) -> str:
        lines = [
            f"- Step {step['step']} ({step['name']}): {step['summary']}"
            for step in index["steps"]
            if step["status"] == "completed" and step.get("summary")
        ]
        if not lines:
            return ""
        return "## 이전 Step 산출물\n\n" + "\n".join(lines) + "\n\n"

    def _build_preamble(
        self,
        guardrails: str,
        step_context: str,
        prev_error: str | None = None,
    ) -> str:
        retry_section = ""
        if prev_error:
            retry_section = f"\n## 이전 시도 실패\n\n{prev_error}\n\n---\n\n"
        commit_example = self.FEAT_MSG.format(
            phase=self._phase_name,
            num="N",
            name="<step-name>",
        )
        return (
            f"당신은 {self._project} 프로젝트의 개발자입니다. 아래 step을 수행하세요.\n\n"
            f"{guardrails}\n\n---\n\n"
            f"{step_context}{retry_section}"
            "## 작업 규칙\n\n"
            "1. 현재 저장소의 `AGENTS.md`와 repo-local skill 규칙을 우선한다.\n"
            "2. 이 step에 명시된 작업만 수행하고, 불필요한 추가 기능은 만들지 마라.\n"
            "3. `graphify-out/`는 generated output이므로 직접 수정하지 마라.\n"
            "4. Acceptance Criteria 검증을 직접 실행하라.\n"
            "5. "
            f"`/{PHASES_DIRNAME}/{self._phase_dir_name}/index.json`의 해당 step 상태를 "
            "업데이트하라.\n"
            '   - 성공: `"completed"` + `"summary"`\n'
            '   - 3회 시도 후 실패: `"error"` + `"error_message"`\n'
            '   - 사용자 개입 필요: `"blocked"` + `"blocked_reason"` 후 중단\n'
            "6. git add/commit/push/reset/checkout/clean 은 하지 마라. "
            "git 작업은 outer executor가 담당한다.\n"
            f"   executor commit format: {commit_example}\n\n---\n\n"
        )

    def _invoke_claude(self, step: dict[str, Any], preamble: str) -> dict[str, Any]:
        step_num = int(step["step"])
        step_name = str(step["name"])
        step_file = self._phase_dir / f"step{step_num}.md"
        if not step_file.exists():
            print(f"  ERROR: {step_file} not found")
            raise SystemExit(1)

        prompt = preamble + step_file.read_text(encoding="utf-8")
        result = self._run_subprocess(
            [
                self._agent_command,
                "-p",
                "--dangerously-skip-permissions",
                "--output-format",
                "json",
                prompt,
            ],
            cwd=self._root,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT_SECONDS,
        )

        if result.returncode != 0:
            print(f"\n  WARN: {self._agent_command}가 비정상 종료됨 (code {result.returncode})")
            if result.stderr:
                print(f"  stderr: {str(result.stderr)[:500]}")

        output = {
            "step": step_num,
            "name": step_name,
            "exitCode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        out_path = self._phase_dir / f"step{step_num}-output.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        return output

    def _print_header(self) -> None:
        print(f"\n{'=' * 60}")
        print("  Harness Step Executor")
        print(f"  Phase: {self._phase_name} | Steps: {self._total}")
        print(f"  Branch prefix: {self._branch_prefix}")
        if self._auto_push:
            print("  Auto-push: enabled")
        print(f"{'=' * 60}")

    def _check_blockers(self) -> None:
        index = self._read_json(self._index_file)
        for step in reversed(index["steps"]):
            if step["status"] == "error":
                print(f"\n  ✗ Step {step['step']} ({step['name']}) failed.")
                print(f"  Error: {step.get('error_message', 'unknown')}")
                print("  Fix and reset status to 'pending' to retry.")
                raise SystemExit(1)
            if step["status"] == "blocked":
                print(f"\n  ⏸ Step {step['step']} ({step['name']}) blocked.")
                print(f"  Reason: {step.get('blocked_reason', 'unknown')}")
                print("  Resolve and reset status to 'pending' to retry.")
                raise SystemExit(2)
            if step["status"] != "pending":
                break

    def _ensure_created_at(self) -> None:
        index = self._read_json(self._index_file)
        if "created_at" in index:
            return
        index["created_at"] = self._stamp()
        self._write_json(self._index_file, index)

    def _execute_single_step(self, step: dict[str, Any], guardrails: str) -> bool:
        step_num = int(step["step"])
        step_name = str(step["name"])
        completed_count = sum(
            1
            for item in self._read_json(self._index_file)["steps"]
            if item["status"] == "completed"
        )
        prev_error: str | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            index = self._read_json(self._index_file)
            step_context = self._build_step_context(index)
            preamble = self._build_preamble(guardrails, step_context, prev_error)

            label = f"Step {step_num}/{self._total - 1} ({completed_count} done): {step_name}"
            if attempt > 1:
                label += f" [retry {attempt}/{self.MAX_RETRIES}]"

            with progress_indicator(label) as info:
                self._invoke_claude(step, preamble)
                elapsed = int(info.elapsed)

            index = self._read_json(self._index_file)
            status = next(
                (
                    item.get("status", "pending")
                    for item in index["steps"]
                    if item["step"] == step_num
                ),
                "pending",
            )
            timestamp = self._stamp()

            if status == "completed":
                for item in index["steps"]:
                    if item["step"] == step_num:
                        item["completed_at"] = timestamp
                self._write_json(self._index_file, index)
                self._commit_step(step_num, step_name)
                print(f"  ✓ Step {step_num}: {step_name} [{elapsed}s]")
                return True

            if status == "blocked":
                for item in index["steps"]:
                    if item["step"] == step_num:
                        item["blocked_at"] = timestamp
                self._write_json(self._index_file, index)
                reason = next(
                    (
                        item.get("blocked_reason", "")
                        for item in index["steps"]
                        if item["step"] == step_num
                    ),
                    "",
                )
                print(f"  ⏸ Step {step_num}: {step_name} blocked [{elapsed}s]")
                print(f"    Reason: {reason}")
                self._update_top_index("blocked")
                raise SystemExit(2)

            error_message = next(
                (
                    item.get("error_message", "Step did not update status")
                    for item in index["steps"]
                    if item["step"] == step_num
                ),
                "Step did not update status",
            )

            if attempt < self.MAX_RETRIES:
                for item in index["steps"]:
                    if item["step"] == step_num:
                        item["status"] = "pending"
                        item.pop("error_message", None)
                self._write_json(self._index_file, index)
                prev_error = error_message
                print(f"  ↻ Step {step_num}: retry {attempt}/{self.MAX_RETRIES} - {error_message}")
                continue

            for item in index["steps"]:
                if item["step"] == step_num:
                    item["status"] = "error"
                    item["error_message"] = f"[{self.MAX_RETRIES}회 시도 후 실패] {error_message}"
                    item["failed_at"] = timestamp
            self._write_json(self._index_file, index)
            self._commit_step(step_num, step_name)
            print(
                "  ✗ Step "
                f"{step_num}: {step_name} failed after {self.MAX_RETRIES} attempts [{elapsed}s]"
            )
            print(f"    Error: {error_message}")
            self._update_top_index("error")
            raise SystemExit(1)

        return False

    def _execute_all_steps(self, guardrails: str) -> None:
        while True:
            index = self._read_json(self._index_file)
            pending = next((step for step in index["steps"] if step["status"] == "pending"), None)
            if pending is None:
                print("\n  All steps completed!")
                return

            step_num = int(pending["step"])
            for item in index["steps"]:
                if item["step"] == step_num and "started_at" not in item:
                    item["started_at"] = self._stamp()
                    self._write_json(self._index_file, index)
                    break

            self._execute_single_step(pending, guardrails)

    def _finalize(self) -> None:
        index = self._read_json(self._index_file)
        index["completed_at"] = self._stamp()
        self._write_json(self._index_file, index)
        self._update_top_index("completed")

        self._run_git("add", "-A")
        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            message = f"chore({self._phase_name}): mark phase completed"
            result = self._run_git("commit", "-m", message)
            if result.returncode == 0:
                print(f"  ✓ {message}")

        if self._auto_push:
            branch = self._branch_name()
            result = self._run_git("push", "-u", "origin", branch)
            if result.returncode != 0:
                print(f"\n  ERROR: git push 실패: {str(result.stderr).strip()}")
                raise SystemExit(1)
            print(f"  ✓ Pushed to origin/{branch}")

        print(f"\n{'=' * 60}")
        print(f"  Phase '{self._phase_name}' completed!")
        print(f"{'=' * 60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness Step Executor")
    parser.add_argument("phase_dir", help="Phase directory name (for example: 0-mvp)")
    parser.add_argument("--push", action="store_true", help="Push the branch after completion")
    args = parser.parse_args()

    StepExecutor(args.phase_dir, auto_push=args.push).run()


if __name__ == "__main__":
    main()
