#!/usr/bin/env python3
"""
Environment Detector - Comprehensive environment detection for AI Context Toolkit.

Detects:
- System environment (OS, Shell, Python, Node.js)
- Development environment (Git, virtual env, package managers)
- AI tools (CLI agents, API keys)
- Project type (frontend, backend, framework)
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class ProjectType(Enum):
    """Project type classification."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    LIBRARY = "library"
    CLI = "cli"
    UNKNOWN = "unknown"


class Framework(Enum):
    """Known frameworks."""
    # Frontend
    VUE = "vue"
    REACT = "react"
    ANGULAR = "angular"
    SVELTE = "svelte"
    NEXTJS = "nextjs"
    NUXT = "nuxt"
    
    # Backend
    SPRING_BOOT = "spring_boot"
    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    NESTJS = "nestjs"
    GIN = "gin"
    ACTIX = "actix"
    
    # Build tools
    VITE = "vite"
    RSBUILD = "rsbuild"
    WEBPACK = "webpack"
    
    UNKNOWN = "unknown"


@dataclass
class ToolInfo:
    """Information about a detected tool."""
    name: str
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AIAgentInfo:
    """Information about a detected AI agent."""
    name: str
    cli_command: str
    available: bool
    version: Optional[str] = None
    api_key_configured: bool = False
    api_key_env_var: Optional[str] = None
    config_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnvironmentInfo:
    """Complete environment information."""
    # System
    os_type: str
    os_version: str
    shell: str
    architecture: str
    
    # Languages
    python: Optional[ToolInfo] = None
    node: Optional[ToolInfo] = None
    java: Optional[ToolInfo] = None
    go: Optional[ToolInfo] = None
    rust: Optional[ToolInfo] = None
    
    # Development tools
    git: Optional[ToolInfo] = None
    docker: Optional[ToolInfo] = None
    
    # Package managers
    package_managers: List[ToolInfo] = field(default_factory=list)
    
    # Virtual environments
    virtual_env: Optional[str] = None
    conda_env: Optional[str] = None
    
    # AI Agents
    ai_agents: List[AIAgentInfo] = field(default_factory=list)
    
    # Project info
    project_type: str = ProjectType.UNKNOWN.value
    frameworks: List[str] = field(default_factory=list)
    project_root: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert ToolInfo and AIAgentInfo objects
        if self.python:
            data["python"] = self.python.to_dict()
        if self.node:
            data["node"] = self.node.to_dict()
        if self.java:
            data["java"] = self.java.to_dict()
        if self.go:
            data["go"] = self.go.to_dict()
        if self.rust:
            data["rust"] = self.rust.to_dict()
        if self.git:
            data["git"] = self.git.to_dict()
        if self.docker:
            data["docker"] = self.docker.to_dict()
        data["package_managers"] = [pm.to_dict() for pm in self.package_managers]
        data["ai_agents"] = [agent.to_dict() for agent in self.ai_agents]
        return data


class EnvDetector:
    """
    Comprehensive environment detector for AI-assisted development.
    
    Usage:
        detector = EnvDetector(project_root="/path/to/project")
        info = detector.detect_all()
        print(info.to_dict())
    """
    
    # AI Agent definitions
    AI_AGENTS = [
        {
            "name": "Aider",
            "cli_command": "aider",
            "api_key_env_var": "OPENAI_API_KEY",
            "version_flag": "--version",
        },
        {
            "name": "Claude CLI",
            "cli_command": "claude",
            "api_key_env_var": "ANTHROPIC_API_KEY",
            "version_flag": "--version",
        },
        {
            "name": "GitHub Copilot CLI",
            "cli_command": "gh",
            "subcommand": "copilot",
            "api_key_env_var": "GITHUB_TOKEN",
            "version_flag": "--version",
        },
        {
            "name": "OpenAI CLI",
            "cli_command": "openai",
            "api_key_env_var": "OPENAI_API_KEY",
            "version_flag": "--version",
        },
        {
            "name": "Google Cloud CLI",
            "cli_command": "gcloud",
            "api_key_env_var": "GOOGLE_APPLICATION_CREDENTIALS",
            "version_flag": "--version",
        },
        {
            "name": "Ollama",
            "cli_command": "ollama",
            "api_key_env_var": None,  # Local model, no API key
            "version_flag": "--version",
        },
        {
            "name": "Continue.dev",
            "cli_command": "continue",
            "api_key_env_var": None,
            "version_flag": "--version",
            "config_path": "~/.continue/config.json",
        },
        {
            "name": "Cursor",
            "cli_command": "cursor",
            "api_key_env_var": None,
            "version_flag": "--version",
        },
    ]
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize environment detector.
        
        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()
    
    def _run_command(
        self,
        command: List[str],
        timeout: int = 5
    ) -> Tuple[bool, str, str]:
        """
        Run a command and return success status, stdout, stderr.
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root,
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False, "", ""
    
    def _extract_version(self, output: str) -> Optional[str]:
        """Extract version number from command output."""
        # Common version patterns
        patterns = [
            r"(\d+\.\d+\.\d+)",  # Semantic version
            r"(\d+\.\d+)",       # Major.minor
            r"v(\d+\.\d+\.\d+)", # v prefix
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return None
    
    def detect_system(self) -> Dict[str, str]:
        """Detect system information."""
        return {
            "os_type": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "shell": os.environ.get("SHELL", os.environ.get("COMSPEC", "unknown")),
        }
    
    def detect_python(self) -> Optional[ToolInfo]:
        """Detect Python installation."""
        python_cmd = shutil.which("python3") or shutil.which("python")
        
        if not python_cmd:
            return ToolInfo(name="Python", available=False)
        
        success, stdout, _ = self._run_command([python_cmd, "--version"])
        version = self._extract_version(stdout) if success else None
        
        return ToolInfo(
            name="Python",
            available=True,
            version=version,
            path=python_cmd,
            details={
                "pip": shutil.which("pip3") or shutil.which("pip"),
                "venv": self._detect_virtual_env(),
            }
        )
    
    def detect_node(self) -> Optional[ToolInfo]:
        """Detect Node.js installation."""
        node_cmd = shutil.which("node")
        
        if not node_cmd:
            return ToolInfo(name="Node.js", available=False)
        
        success, stdout, _ = self._run_command([node_cmd, "--version"])
        version = self._extract_version(stdout) if success else None
        
        # Detect npm/yarn/pnpm
        npm = shutil.which("npm")
        yarn = shutil.which("yarn")
        pnpm = shutil.which("pnpm")
        bun = shutil.which("bun")
        
        return ToolInfo(
            name="Node.js",
            available=True,
            version=version,
            path=node_cmd,
            details={
                "npm": npm,
                "yarn": yarn,
                "pnpm": pnpm,
                "bun": bun,
            }
        )
    
    def detect_java(self) -> Optional[ToolInfo]:
        """Detect Java installation."""
        java_cmd = shutil.which("java")
        
        if not java_cmd:
            return ToolInfo(name="Java", available=False)
        
        success, stdout, stderr = self._run_command([java_cmd, "-version"])
        # Java outputs version to stderr
        version = self._extract_version(stderr or stdout) if success else None
        
        return ToolInfo(
            name="Java",
            available=True,
            version=version,
            path=java_cmd,
            details={
                "maven": shutil.which("mvn"),
                "gradle": shutil.which("gradle"),
                "java_home": os.environ.get("JAVA_HOME"),
            }
        )
    
    def detect_go(self) -> Optional[ToolInfo]:
        """Detect Go installation."""
        go_cmd = shutil.which("go")
        
        if not go_cmd:
            return ToolInfo(name="Go", available=False)
        
        success, stdout, _ = self._run_command([go_cmd, "version"])
        version = self._extract_version(stdout) if success else None
        
        return ToolInfo(
            name="Go",
            available=True,
            version=version,
            path=go_cmd,
            details={
                "gopath": os.environ.get("GOPATH"),
                "goroot": os.environ.get("GOROOT"),
            }
        )
    
    def detect_rust(self) -> Optional[ToolInfo]:
        """Detect Rust installation."""
        rustc_cmd = shutil.which("rustc")
        
        if not rustc_cmd:
            return ToolInfo(name="Rust", available=False)
        
        success, stdout, _ = self._run_command([rustc_cmd, "--version"])
        version = self._extract_version(stdout) if success else None
        
        return ToolInfo(
            name="Rust",
            available=True,
            version=version,
            path=rustc_cmd,
            details={
                "cargo": shutil.which("cargo"),
            }
        )
    
    def detect_git(self) -> Optional[ToolInfo]:
        """Detect Git installation and repository status."""
        git_cmd = shutil.which("git")
        
        if not git_cmd:
            return ToolInfo(name="Git", available=False)
        
        success, stdout, _ = self._run_command([git_cmd, "--version"])
        version = self._extract_version(stdout) if success else None
        
        # Check if in a git repo
        is_repo, _, _ = self._run_command([git_cmd, "rev-parse", "--is-inside-work-tree"])
        
        # Get current branch
        branch = None
        if is_repo:
            success, branch_out, _ = self._run_command([git_cmd, "branch", "--show-current"])
            branch = branch_out if success else None
        
        # Check for uncommitted changes
        has_changes = False
        if is_repo:
            success, status, _ = self._run_command([git_cmd, "status", "--porcelain"])
            has_changes = bool(status)
        
        return ToolInfo(
            name="Git",
            available=True,
            version=version,
            path=git_cmd,
            details={
                "is_repo": is_repo,
                "branch": branch,
                "has_uncommitted_changes": has_changes,
            }
        )
    
    def detect_docker(self) -> Optional[ToolInfo]:
        """Detect Docker installation."""
        docker_cmd = shutil.which("docker")
        
        if not docker_cmd:
            return ToolInfo(name="Docker", available=False)
        
        success, stdout, _ = self._run_command([docker_cmd, "--version"])
        version = self._extract_version(stdout) if success else None
        
        # Check if Docker daemon is running
        daemon_running, _, _ = self._run_command([docker_cmd, "info"])
        
        return ToolInfo(
            name="Docker",
            available=True,
            version=version,
            path=docker_cmd,
            details={
                "daemon_running": daemon_running,
                "compose": shutil.which("docker-compose") or shutil.which("docker compose"),
            }
        )
    
    def _detect_virtual_env(self) -> Optional[str]:
        """Detect active virtual environment."""
        # Check VIRTUAL_ENV (standard venv/virtualenv)
        venv = os.environ.get("VIRTUAL_ENV")
        if venv:
            return venv
        
        # Check CONDA_DEFAULT_ENV
        conda = os.environ.get("CONDA_DEFAULT_ENV")
        if conda:
            return f"conda:{conda}"
        
        # Check for local .venv or venv directory
        for venv_dir in [".venv", "venv", "env"]:
            venv_path = self.project_root / venv_dir
            if venv_path.exists() and (venv_path / "bin" / "python").exists():
                return str(venv_path)
        
        return None
    
    def detect_package_managers(self) -> List[ToolInfo]:
        """Detect available package managers."""
        managers = []
        
        # Python
        for pm in ["pip", "pip3", "poetry", "uv", "pipenv", "conda"]:
            cmd = shutil.which(pm)
            if cmd:
                managers.append(ToolInfo(name=pm, available=True, path=cmd))
        
        # Node.js
        for pm in ["npm", "yarn", "pnpm", "bun"]:
            cmd = shutil.which(pm)
            if cmd:
                managers.append(ToolInfo(name=pm, available=True, path=cmd))
        
        # Java
        for pm in ["mvn", "gradle"]:
            cmd = shutil.which(pm)
            if cmd:
                managers.append(ToolInfo(name=pm, available=True, path=cmd))
        
        # Rust
        cargo = shutil.which("cargo")
        if cargo:
            managers.append(ToolInfo(name="cargo", available=True, path=cargo))
        
        # Go
        go = shutil.which("go")
        if go:
            managers.append(ToolInfo(name="go mod", available=True, path=go))
        
        return managers
    
    def detect_ai_agents(self) -> List[AIAgentInfo]:
        """Detect available AI agents."""
        agents = []
        
        for agent_def in self.AI_AGENTS:
            cli_cmd = shutil.which(agent_def["cli_command"])
            
            agent = AIAgentInfo(
                name=agent_def["name"],
                cli_command=agent_def["cli_command"],
                available=cli_cmd is not None,
            )
            
            if cli_cmd:
                # Get version
                version_flag = agent_def.get("version_flag", "--version")
                cmd = [cli_cmd, version_flag]
                
                # Handle subcommands (e.g., gh copilot)
                if "subcommand" in agent_def:
                    cmd = [cli_cmd, agent_def["subcommand"], version_flag]
                
                success, stdout, stderr = self._run_command(cmd)
                if success:
                    agent.version = self._extract_version(stdout or stderr)
            
            # Check API key
            if agent_def.get("api_key_env_var"):
                agent.api_key_env_var = agent_def["api_key_env_var"]
                agent.api_key_configured = bool(os.environ.get(agent_def["api_key_env_var"]))
            
            # Check config file
            if agent_def.get("config_path"):
                config_path = Path(agent_def["config_path"]).expanduser()
                if config_path.exists():
                    agent.config_path = str(config_path)
            
            agents.append(agent)
        
        return agents
    
    def detect_project_type(self) -> Tuple[ProjectType, List[Framework]]:
        """Detect project type and frameworks."""
        frameworks = []
        has_frontend = False
        has_backend = False
        
        # Check for frontend indicators
        if (self.project_root / "package.json").exists():
            try:
                pkg = json.loads((self.project_root / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                if "vue" in deps:
                    frameworks.append(Framework.VUE)
                    has_frontend = True
                if "react" in deps:
                    frameworks.append(Framework.REACT)
                    has_frontend = True
                if "angular" in deps or "@angular/core" in deps:
                    frameworks.append(Framework.ANGULAR)
                    has_frontend = True
                if "svelte" in deps:
                    frameworks.append(Framework.SVELTE)
                    has_frontend = True
                if "next" in deps:
                    frameworks.append(Framework.NEXTJS)
                    has_frontend = True
                if "nuxt" in deps:
                    frameworks.append(Framework.NUXT)
                    has_frontend = True
                if "vite" in deps:
                    frameworks.append(Framework.VITE)
                if "@rsbuild/core" in deps:
                    frameworks.append(Framework.RSBUILD)
                if "express" in deps:
                    frameworks.append(Framework.EXPRESS)
                    has_backend = True
                if "@nestjs/core" in deps:
                    frameworks.append(Framework.NESTJS)
                    has_backend = True
            except (json.JSONDecodeError, OSError):
                pass
        
        # Check for Java/Spring Boot
        if (self.project_root / "build.gradle").exists() or (self.project_root / "pom.xml").exists():
            has_backend = True
            # Check for Spring Boot
            for gradle_file in ["build.gradle", "build.gradle.kts"]:
                gradle_path = self.project_root / gradle_file
                if gradle_path.exists():
                    content = gradle_path.read_text()
                    if "spring-boot" in content.lower():
                        frameworks.append(Framework.SPRING_BOOT)
        
        # Check for Python backends
        if (self.project_root / "requirements.txt").exists() or (self.project_root / "pyproject.toml").exists():
            for req_file in ["requirements.txt", "pyproject.toml"]:
                req_path = self.project_root / req_file
                if req_path.exists():
                    content = req_path.read_text().lower()
                    if "django" in content:
                        frameworks.append(Framework.DJANGO)
                        has_backend = True
                    if "flask" in content:
                        frameworks.append(Framework.FLASK)
                        has_backend = True
                    if "fastapi" in content:
                        frameworks.append(Framework.FASTAPI)
                        has_backend = True
        
        # Check for Go
        if (self.project_root / "go.mod").exists():
            has_backend = True
            content = (self.project_root / "go.mod").read_text().lower()
            if "gin" in content:
                frameworks.append(Framework.GIN)
        
        # Check for Rust
        if (self.project_root / "Cargo.toml").exists():
            has_backend = True
            content = (self.project_root / "Cargo.toml").read_text().lower()
            if "actix" in content:
                frameworks.append(Framework.ACTIX)
        
        # Determine project type
        if has_frontend and has_backend:
            project_type = ProjectType.FULLSTACK
        elif has_frontend:
            project_type = ProjectType.FRONTEND
        elif has_backend:
            project_type = ProjectType.BACKEND
        else:
            project_type = ProjectType.UNKNOWN
        
        return project_type, frameworks
    
    def detect_all(self) -> EnvironmentInfo:
        """
        Detect all environment information.
        
        Returns:
            EnvironmentInfo object with complete detection results.
        """
        system = self.detect_system()
        project_type, frameworks = self.detect_project_type()
        
        return EnvironmentInfo(
            os_type=system["os_type"],
            os_version=system["os_version"],
            shell=system["shell"],
            architecture=system["architecture"],
            python=self.detect_python(),
            node=self.detect_node(),
            java=self.detect_java(),
            go=self.detect_go(),
            rust=self.detect_rust(),
            git=self.detect_git(),
            docker=self.detect_docker(),
            package_managers=self.detect_package_managers(),
            virtual_env=self._detect_virtual_env(),
            conda_env=os.environ.get("CONDA_DEFAULT_ENV"),
            ai_agents=self.detect_ai_agents(),
            project_type=project_type.value,
            frameworks=[f.value for f in frameworks],
            project_root=str(self.project_root),
        )
    
    def get_available_ai_agents(self) -> List[AIAgentInfo]:
        """Get list of AI agents that are both installed and configured."""
        agents = self.detect_ai_agents()
        return [
            agent for agent in agents
            if agent.available and (
                agent.api_key_configured or
                agent.api_key_env_var is None  # Local models like Ollama
            )
        ]
    
    def get_recommended_agent(self) -> Optional[AIAgentInfo]:
        """Get the recommended AI agent based on availability and capability."""
        available = self.get_available_ai_agents()
        
        if not available:
            return None
        
        # Priority order
        priority = ["Aider", "Claude CLI", "GitHub Copilot CLI", "Cursor", "OpenAI CLI", "Ollama"]
        
        for name in priority:
            for agent in available:
                if agent.name == name:
                    return agent
        
        return available[0]


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Detector")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--project-root", "-p", help="Project root directory")
    parser.add_argument("--agents-only", action="store_true", help="Only show AI agents")
    args = parser.parse_args()
    
    detector = EnvDetector(args.project_root)
    
    if args.agents_only:
        agents = detector.detect_ai_agents()
        if args.json:
            print(json.dumps([a.to_dict() for a in agents], indent=2))
        else:
            print("Available AI Agents:")
            print("-" * 40)
            for agent in agents:
                status = "✅" if agent.available else "❌"
                key_status = ""
                if agent.api_key_env_var:
                    key_status = " 🔑" if agent.api_key_configured else " ⚠️ (no API key)"
                print(f"{status} {agent.name} ({agent.cli_command}){key_status}")
                if agent.version:
                    print(f"   Version: {agent.version}")
    else:
        info = detector.detect_all()
        if args.json:
            print(json.dumps(info.to_dict(), indent=2))
        else:
            print(f"Environment Detection Results")
            print("=" * 50)
            print(f"OS: {info.os_type} {info.os_version}")
            print(f"Architecture: {info.architecture}")
            print(f"Shell: {info.shell}")
            print(f"Project Root: {info.project_root}")
            print(f"Project Type: {info.project_type}")
            print(f"Frameworks: {', '.join(info.frameworks) or 'None detected'}")
            print()
            print("Languages:")
            for lang in [info.python, info.node, info.java, info.go, info.rust]:
                if lang and lang.available:
                    print(f"  ✅ {lang.name}: {lang.version or 'unknown version'}")
            print()
            print("AI Agents:")
            for agent in info.ai_agents:
                if agent.available:
                    print(f"  ✅ {agent.name}")


if __name__ == "__main__":
    main()
