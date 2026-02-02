#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IGNORE = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "target",
}
ENTRY_CANDIDATES = [
    "src/index.ts",
    "src/main.ts",
    "src/app.ts",
    "src/main.js",
    "src/main/java",
    "src/main/resources",
    "cmd",
    "internal",
    "crates",
    "src/main.rs",
    "src/lib.rs",
]
KEY_FILES = [
    "build.gradle",
    "settings.gradle",
    "gradle.properties",
    "pom.xml",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "README.md",
]
CONTRACT_DIRS = ["contracts", "openapi", "proto"]
DATA_DIRS = ["migrations", "schema", "db", "database", "data"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def list_dirs(root: Path, ignore: set[str]) -> list[Path]:
    dirs = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if child.name in ignore:
            continue
        dirs.append(child)
    return sorted(dirs, key=lambda p: p.name.lower())


def detect_tags(module: Path) -> list[str]:
    tags: list[str] = []
    name = module.name.lower()
    if (module / "package.json").exists() or name in {"ui", "frontend", "web"}:
        tags.append("Frontend UI")
    if (module / "build.gradle").exists() or (module / "pom.xml").exists():
        tags.append("Java module")
    if (module / "go.mod").exists():
        tags.append("Go service")
    if (module / "Cargo.toml").exists():
        tags.append("Rust crate")
    if name in {"docs", "doc"}:
        tags.append("Docs")
    if name in {"scripts", "tools"}:
        tags.append("Scripts/Automation")
    if name in {"contracts", "openapi", "proto"}:
        tags.append("Contracts")
    if not tags:
        tags.append("Module")
    return tags


def existing_paths(module: Path, candidates: list[str]) -> list[str]:
    results: list[str] = []
    for rel in candidates:
        path = module / rel
        if path.exists():
            results.append(rel)
    return results


def detect_contracts(module: Path) -> list[str]:
    found: list[str] = []
    for rel in CONTRACT_DIRS:
        path = module / rel
        if path.exists():
            found.append(rel)
    return found


def detect_data(module: Path) -> list[str]:
    found: list[str] = []
    for rel in DATA_DIRS:
        path = module / rel
        if path.exists():
            found.append(rel)
    return found


def render_module_en(module: Path) -> str:
    tags = ", ".join(detect_tags(module))
    entries = existing_paths(module, ENTRY_CANDIDATES)
    keys = existing_paths(module, KEY_FILES)
    contracts = detect_contracts(module)
    data = detect_data(module)
    return "\n".join(
        [
            f"### {module.name}",
            f"- Purpose: {tags}.",
            f"- Entrypoints: {', '.join(entries) if entries else 'N/A'}",
            f"- Key files: {', '.join(keys) if keys else 'N/A'}",
            f"- Dependencies: TBD",
            f"- Contracts: {', '.join(contracts) if contracts else 'N/A'}",
            f"- Data: {', '.join(data) if data else 'N/A'}",
            f"- Notes: Generated; refine as needed.",
            "",
        ]
    )


def render_module_zh(module: Path) -> str:
    tags = "、".join(detect_tags(module))
    entries = existing_paths(module, ENTRY_CANDIDATES)
    keys = existing_paths(module, KEY_FILES)
    contracts = detect_contracts(module)
    data = detect_data(module)
    return "\n".join(
        [
            f"### {module.name}",
            f"- 作用：{tags}。",
            f"- 入口：{('、'.join(entries)) if entries else '无'}",
            f"- 关键文件：{('、'.join(keys)) if keys else '无'}",
            f"- 依赖：待补充",
            f"- 契约：{('、'.join(contracts)) if contracts else '无'}",
            f"- 数据：{('、'.join(data)) if data else '无'}",
            f"- 备注：自动生成，需人工完善。",
            "",
        ]
    )


def render_header_en(project_root: Path) -> str:
    return "\n".join(
        [
            "# Module Map (Generated)",
            "",
            f"- GeneratedAt: {utc_now()}",
            f"- ProjectRoot: {project_root}",
            "",
            "## Module Index",
            "",
        ]
    )


def render_header_zh(project_root: Path) -> str:
    return "\n".join(
        [
            "# 模块地图（自动生成）",
            "",
            f"- 生成时间：{utc_now()}",
            f"- 项目根目录：{project_root}",
            "",
            "## 模块索引",
            "",
        ]
    )


def write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        default=str(ROOT),
        help="project root to scan (default: ai-context repo root)",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "module-map.md"),
        help="output markdown path",
    )
    parser.add_argument(
        "--output-zh",
        default=str(ROOT / "docs" / "module-map-zh.md"),
        help="output Chinese markdown path",
    )
    parser.add_argument(
        "--ignore",
        default="",
        help="comma-separated folder names to ignore",
    )
    parser.add_argument("--no-root", action="store_true", help="exclude root module entry")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    ignore = set(DEFAULT_IGNORE)
    if args.ignore:
        ignore.update({item.strip() for item in args.ignore.split(",") if item.strip()})

    modules = list_dirs(project_root, ignore)
    if not modules:
        modules = []

    content_en = [render_header_en(project_root)]
    content_zh = [render_header_zh(project_root)]

    if not args.no_root:
        content_en.append(render_module_en(project_root))
        content_zh.append(render_module_zh(project_root))

    for module in modules:
        content_en.append(render_module_en(module))
        content_zh.append(render_module_zh(module))

    write_output(Path(args.output), "\n".join(content_en))
    write_output(Path(args.output_zh), "\n".join(content_zh))
    print(f"Generated module maps: {args.output}, {args.output_zh}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
