"""Offline platform-profile acceptance; does not execute any product or install tooling."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "profiles/platforms/harness.json"
TASKS = ROOT / "profiles/platforms/tasks"
CHECKS: list[str] = []


def expect(condition: bool, description: str) -> None:
    if not condition:
        raise AssertionError(description)
    CHECKS.append(description)


def cli(operation: str, task: str | None = None, expected: int = 0):
    args = [sys.executable, str(ROOT / "tools/harness.py"), operation,
            "--root", str(ROOT), "--manifest", MANIFEST]
    if task is not None:
        args += ["--task", task]
    if operation == "evidence":
        args += ["--records", "profiles/platforms/evidence/records.json",
                 "--now", "2026-11-14T10:00:00Z"]
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise AssertionError(f"CLI returned non-JSON: {result.stdout} {result.stderr}") from exc
    if result.returncode != expected:
        raise AssertionError(f"{operation} {task}: expected exit {expected}, got {result.returncode}: {data}")
    return data


def markdown_links() -> int:
    checked = 0
    errors = []
    pages = sorted((ROOT / "docs/platforms").rglob("*.md")) + sorted((ROOT / "profiles").rglob("*.md"))
    for page in pages:
        text = page.read_text(encoding="utf-8-sig")
        # Our authored docs use inline links only; code fences are excluded.
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for match in re.finditer(r"!?\[[^]\n]*\]\(([^)\n]+)\)", text):
            target = match.group(1).strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("//"):
                continue
            resolved = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
            checked += 1
            if not resolved.is_file():
                errors.append(f"{page.relative_to(ROOT)} -> {target}: missing file")
            elif parsed.fragment:
                headings = []
                for line in resolved.read_text(encoding="utf-8-sig").splitlines():
                    if line.startswith("#"):
                        slug = re.sub(r"[^\w\- ]", "", line.lstrip("#").strip().lower()).replace(" ", "-")
                        headings.append(slug)
                if unquote(parsed.fragment) not in headings:
                    errors.append(f"{page.relative_to(ROOT)} -> {target}: missing heading")
    expect(not errors, "all internal Markdown links resolve" + (": " + "; ".join(errors) if errors else ""))
    return checked


def main() -> int:
    links = markdown_links()
    manifest = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))
    lint = cli("lint")
    expect(lint["status"] == "pass", "core CLI lint accepts profile")
    ids = {route["id"] for route in manifest["routes"]}
    expected_ids = {f"{prefix}{i}" for prefix, count in [("P", 10), ("W", 10), ("A", 11)] for i in range(1, count + 1)}
    expect(ids == expected_ids, "P10/W10/A11 route coverage exact")
    conditional_routes = 0
    with tempfile.TemporaryDirectory(prefix=".platform-check-", dir=ROOT / "profiles") as temporary:
        path = Path(temporary) / "task.json"
        relative = path.relative_to(ROOT).as_posix()
        def resolve_variant(task, expected=0):
            path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
            return cli("resolve", relative, expected)
        for route in manifest["routes"]:
            rid = route["id"]
            base = json.loads((TASKS / f"{rid}.json").read_text(encoding="utf-8"))
            resolved = cli("resolve", f"profiles/platforms/tasks/{rid}.json")
            expect(resolved["status"] == "pass" and resolved["matched_routes"] == [rid], f"{rid} resolves only its intended route")
            required = set(route["context_set"]["required"])
            expect(set(resolved["context_files"]) == required, f"{rid} false conditions omit optional context")
            conditions = route["context_set"]["conditional"]
            if conditions:
                conditional_routes += 1
                all_additions = set()
                for condition in conditions:
                    base["facts"][condition["when"]["fact"]] = True
                    all_additions.update(condition["add"])
                true_result = resolve_variant(base)
                expect(set(true_result["context_files"]) == required | all_additions, f"{rid} true conditions union context")
                fact = conditions[0]["when"]["fact"]
                base["facts"][fact] = None
                unknown = resolve_variant(base, 2)
                expect(unknown["status"] == "blocked", f"{rid} null condition blocks")
                del base["facts"][fact]
                missing = resolve_variant(base, 2)
                expect(missing["status"] == "blocked", f"{rid} missing condition blocks")
        static = cli("resolve", "profiles/platforms/tasks/static-web-release.json")
        expect("docs/platforms/web/data.md" not in static["context_files"], "static Web release does not load migration page")
        expect({"docs/platforms/web/operations.md", "docs/platforms/web/api-config.md", "docs/platforms/web/frontend.md"} <= set(static["context_files"]), "static Web retains deployment/config/frontend context")
        unknown = cli("resolve", "profiles/platforms/tasks/unknown-web-db.json", 2)
        expect(unknown["status"] == "blocked", "unknown DB cannot become N/A")
        hybrid = cli("resolve", "profiles/platforms/tasks/hybrid.json")
        expect(set(hybrid["matched_routes"]) == {"P5", "W8", "A4"}, "hybrid selects three platform routes")
        expect({"docs/platforms/plugin/ui-isolation.md", "docs/platforms/web/data.md", "docs/platforms/app/local-data.md"} <= set(hybrid["context_files"]), "hybrid preserves cross-platform context union")
        unauthorized = json.loads((TASKS / "P5.json").read_text(encoding="utf-8"))
        unauthorized["approved_paths"] = ["profiles/platforms/targets/web/**"]
        denied = resolve_variant(unauthorized, 2)
        expect(denied["status"] == "blocked", "unapproved actual paths block instead of granting permission")
        extra_platform = json.loads((TASKS / "P5.json").read_text(encoding="utf-8"))
        extra_platform["platforms"].append("cli")
        uncovered = resolve_variant(extra_platform, 2)
        expect(uncovered["status"] == "blocked" and any(error["code"] == "E_UNCOVERED_DIMENSION" for error in uncovered["errors"]),
               "new platform values are schema-valid but require explicit matched route coverage")
        evidence = cli("evidence", "profiles/platforms/tasks/hybrid.json", 2)
        expect(evidence["status"] == "not-run", "empty evidence cannot imply product pass")
    print(json.dumps({"status": "pass", "assertions": len(CHECKS), "routes": len(ids),
                      "conditional_routes": conditional_routes, "internal_links": links,
                      "hybrid_context_files": len(hybrid["context_files"]),
                      "limitations": ["offline document/routing validation only",
                                      "no real product, CI, host, device or production check executed"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
