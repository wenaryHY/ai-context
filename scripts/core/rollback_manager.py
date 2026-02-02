#!/usr/bin/env python3
"""
Rollback Manager - Snapshot and rollback functionality for AI-assisted development.

Supports three modes:
1. Git mode (recommended): Uses git stash for efficient snapshots
2. File backup mode: Copies files for non-git projects
3. Hybrid mode: Git for tracked files, backup for untracked
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator
from enum import Enum


class SnapshotMode(Enum):
    """Snapshot storage mode."""
    GIT_STASH = "git_stash"
    FILE_BACKUP = "file_backup"
    HYBRID = "hybrid"


@dataclass
class Snapshot:
    """Represents a point-in-time snapshot of the project state."""
    id: str
    created_at: str
    task_id: str
    task_description: str
    agent: str
    mode: str
    files_modified: List[str] = field(default_factory=list)
    git_ref: Optional[str] = None
    backup_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        return cls(**data)


@dataclass
class DiffResult:
    """Result of comparing current state with a snapshot."""
    snapshot_id: str
    files_added: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    diff_content: str = ""


class RollbackManager:
    """
    Manages snapshots and rollbacks for AI-assisted development.
    
    Usage:
        manager = RollbackManager(project_root)
        
        # Create snapshot before AI task
        snapshot = manager.create_snapshot("task_123", "Implement login feature", "aider")
        
        # ... AI makes changes ...
        
        # View what changed
        diff = manager.diff(snapshot.id)
        
        # Rollback if needed
        manager.rollback(snapshot.id)
    """
    
    STORAGE_DIR = ".ai-context"
    SNAPSHOTS_DIR = "snapshots"
    LOGS_DIR = "logs"
    HISTORY_FILE = "rollback_history.json"
    METADATA_FILE = "metadata.json"
    BACKUP_FILE = "files.tar.gz"
    STASH_REF_FILE = "stash_ref.txt"
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize RollbackManager.
        
        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.storage_dir = self.project_root / self.STORAGE_DIR
        self.snapshots_dir = self.storage_dir / self.SNAPSHOTS_DIR
        self.logs_dir = self.storage_dir / self.LOGS_DIR
        self.history_file = self.logs_dir / self.HISTORY_FILE
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .gitignore for storage directory
        gitignore = self.storage_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("# AI Context storage\nsnapshots/\nlogs/\n", encoding="utf-8")
    
    def _is_git_repo(self) -> bool:
        """Check if project is a git repository."""
        return (self.project_root / ".git").exists()
    
    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        return subprocess.run(
            ["git", *args],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=check,
        )
    
    def _get_modified_files(self) -> List[str]:
        """Get list of modified files in the working directory."""
        if not self._is_git_repo():
            return []
        
        result = self._run_git(["status", "--porcelain"], check=False)
        if result.returncode != 0:
            return []
        
        files = []
        for line in result.stdout.splitlines():
            if line.strip():
                # Format: "XY filename" or "XY filename -> newname"
                status = line[:2]
                filename = line[3:].split(" -> ")[-1].strip()
                if status.strip():  # Has some status
                    files.append(filename)
        
        return files
    
    def _get_untracked_files(self) -> List[str]:
        """Get list of untracked files."""
        if not self._is_git_repo():
            return []
        
        result = self._run_git(["ls-files", "--others", "--exclude-standard"], check=False)
        if result.returncode != 0:
            return []
        
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    
    def _generate_snapshot_id(self) -> str:
        """Generate a unique snapshot ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"snap_{timestamp}"
    
    def _determine_mode(self) -> SnapshotMode:
        """Determine the best snapshot mode for this project."""
        if not self._is_git_repo():
            return SnapshotMode.FILE_BACKUP
        
        untracked = self._get_untracked_files()
        if untracked:
            return SnapshotMode.HYBRID
        
        return SnapshotMode.GIT_STASH
    
    def _create_git_stash(self, snapshot_dir: Path, message: str) -> Optional[str]:
        """Create a git stash and return the reference."""
        # Include untracked files in stash
        result = self._run_git(
            ["stash", "push", "-u", "-m", f"ai-context: {message}"],
            check=False
        )
        
        if result.returncode != 0:
            return None
        
        # Get the stash reference
        result = self._run_git(["stash", "list"], check=False)
        if result.returncode == 0 and result.stdout.strip():
            # First line should be our stash
            first_line = result.stdout.splitlines()[0]
            if "ai-context:" in first_line:
                stash_ref = first_line.split(":")[0]  # e.g., "stash@{0}"
                
                # Save reference to file
                ref_file = snapshot_dir / self.STASH_REF_FILE
                ref_file.write_text(stash_ref, encoding="utf-8")
                
                # Pop the stash to restore working state
                # (we saved the ref, so we can restore later)
                self._run_git(["stash", "pop"], check=False)
                
                return stash_ref
        
        return None
    
    def _create_file_backup(self, snapshot_dir: Path, files: List[str]) -> str:
        """Create a tar.gz backup of specified files."""
        backup_path = snapshot_dir / self.BACKUP_FILE
        
        with tarfile.open(backup_path, "w:gz") as tar:
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    tar.add(full_path, arcname=file_path)
        
        return str(backup_path)
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load rollback history."""
        if not self.history_file.exists():
            return []
        
        try:
            return json.loads(self.history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save rollback history."""
        self.history_file.write_text(
            json.dumps(history, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def _add_to_history(self, action: str, snapshot_id: str, details: Dict[str, Any] = None) -> None:
        """Add an entry to rollback history."""
        history = self._load_history()
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "snapshot_id": snapshot_id,
            "details": details or {},
        })
        self._save_history(history)
    
    def create_snapshot(
        self,
        task_id: str,
        task_description: str,
        agent: str,
        files: Optional[List[str]] = None
    ) -> Snapshot:
        """
        Create a snapshot of the current project state.
        
        Args:
            task_id: Unique identifier for the task
            task_description: Human-readable task description
            agent: Name of the AI agent being used
            files: Specific files to snapshot (None for all modified files)
        
        Returns:
            Snapshot object with metadata
        """
        snapshot_id = self._generate_snapshot_id()
        snapshot_dir = self.snapshots_dir / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        mode = self._determine_mode()
        modified_files = files or self._get_modified_files()
        
        git_ref = None
        backup_path = None
        
        if mode == SnapshotMode.GIT_STASH:
            git_ref = self._create_git_stash(snapshot_dir, f"{task_id}: {task_description}")
            if git_ref is None:
                # Fallback to file backup if stash fails
                mode = SnapshotMode.FILE_BACKUP
        
        if mode in (SnapshotMode.FILE_BACKUP, SnapshotMode.HYBRID):
            all_files = modified_files + self._get_untracked_files()
            if all_files:
                backup_path = self._create_file_backup(snapshot_dir, all_files)
        
        snapshot = Snapshot(
            id=snapshot_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            task_id=task_id,
            task_description=task_description,
            agent=agent,
            mode=mode.value,
            files_modified=modified_files,
            git_ref=git_ref,
            backup_path=backup_path,
        )
        
        # Save metadata
        metadata_file = snapshot_dir / self.METADATA_FILE
        metadata_file.write_text(
            json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        self._add_to_history("create", snapshot_id, {
            "task_id": task_id,
            "mode": mode.value,
            "files_count": len(modified_files),
        })
        
        return snapshot
    
    def list_snapshots(self) -> List[Snapshot]:
        """
        List all available snapshots.
        
        Returns:
            List of Snapshot objects, sorted by creation time (newest first)
        """
        snapshots = []
        
        if not self.snapshots_dir.exists():
            return snapshots
        
        for snapshot_dir in self.snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue
            
            metadata_file = snapshot_dir / self.METADATA_FILE
            if not metadata_file.exists():
                continue
            
            try:
                data = json.loads(metadata_file.read_text(encoding="utf-8"))
                snapshots.append(Snapshot.from_dict(data))
            except (json.JSONDecodeError, OSError, TypeError):
                continue
        
        # Sort by creation time, newest first
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        return snapshots
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get a specific snapshot by ID.
        
        Args:
            snapshot_id: The snapshot ID
        
        Returns:
            Snapshot object or None if not found
        """
        snapshot_dir = self.snapshots_dir / snapshot_id
        metadata_file = snapshot_dir / self.METADATA_FILE
        
        if not metadata_file.exists():
            return None
        
        try:
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            return Snapshot.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError):
            return None
    
    def diff(self, snapshot_id: str) -> Optional[DiffResult]:
        """
        Compare current state with a snapshot.
        
        Args:
            snapshot_id: The snapshot ID to compare against
        
        Returns:
            DiffResult object or None if snapshot not found
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return None
        
        result = DiffResult(snapshot_id=snapshot_id)
        
        if self._is_git_repo():
            # Use git diff for more accurate results
            diff_result = self._run_git(["diff", "--name-status"], check=False)
            if diff_result.returncode == 0:
                for line in diff_result.stdout.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        status, filename = parts[0], parts[-1]
                        if status.startswith("A"):
                            result.files_added.append(filename)
                        elif status.startswith("M"):
                            result.files_modified.append(filename)
                        elif status.startswith("D"):
                            result.files_deleted.append(filename)
            
            # Get full diff content
            full_diff = self._run_git(["diff"], check=False)
            if full_diff.returncode == 0:
                result.diff_content = full_diff.stdout
        else:
            # For non-git projects, compare with backup
            result.files_modified = snapshot.files_modified
        
        return result
    
    def rollback(
        self,
        snapshot_id: str,
        files: Optional[List[str]] = None
    ) -> bool:
        """
        Rollback to a snapshot state.
        
        Args:
            snapshot_id: The snapshot ID to rollback to
            files: Specific files to rollback (None for all files)
        
        Returns:
            True if rollback succeeded, False otherwise
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return False
        
        snapshot_dir = self.snapshots_dir / snapshot_id
        success = False
        
        if snapshot.mode == SnapshotMode.GIT_STASH.value and snapshot.git_ref:
            # Restore from git stash
            if files:
                # Selective rollback using git checkout
                for file in files:
                    self._run_git(["checkout", "HEAD", "--", file], check=False)
                success = True
            else:
                # Full rollback - reset to clean state
                self._run_git(["checkout", "--", "."], check=False)
                self._run_git(["clean", "-fd"], check=False)
                success = True
        
        elif snapshot.backup_path or (snapshot_dir / self.BACKUP_FILE).exists():
            # Restore from file backup
            backup_file = snapshot_dir / self.BACKUP_FILE
            if backup_file.exists():
                with tarfile.open(backup_file, "r:gz") as tar:
                    if files:
                        # Extract only specified files
                        for member in tar.getmembers():
                            if member.name in files:
                                tar.extract(member, self.project_root)
                    else:
                        # Extract all files
                        tar.extractall(self.project_root)
                success = True
        
        if success:
            self._add_to_history("rollback", snapshot_id, {
                "files": files,
                "full_rollback": files is None,
            })
        
        return success
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: The snapshot ID to delete
        
        Returns:
            True if deletion succeeded, False otherwise
        """
        snapshot_dir = self.snapshots_dir / snapshot_id
        
        if not snapshot_dir.exists():
            return False
        
        try:
            shutil.rmtree(snapshot_dir)
            self._add_to_history("delete", snapshot_id)
            return True
        except OSError:
            return False
    
    def cleanup_old_snapshots(self, keep_count: int = 10) -> int:
        """
        Remove old snapshots, keeping only the most recent ones.
        
        Args:
            keep_count: Number of snapshots to keep
        
        Returns:
            Number of snapshots deleted
        """
        snapshots = self.list_snapshots()
        
        if len(snapshots) <= keep_count:
            return 0
        
        deleted = 0
        for snapshot in snapshots[keep_count:]:
            if self.delete_snapshot(snapshot.id):
                deleted += 1
        
        return deleted
    
    def get_latest_snapshot(self) -> Optional[Snapshot]:
        """Get the most recent snapshot."""
        snapshots = self.list_snapshots()
        return snapshots[0] if snapshots else None


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rollback Manager")
    parser.add_argument("--list", action="store_true", help="List snapshots")
    parser.add_argument("--create", metavar="DESC", help="Create snapshot")
    parser.add_argument("--rollback", metavar="ID", help="Rollback to snapshot")
    parser.add_argument("--diff", metavar="ID", help="Show diff for snapshot")
    args = parser.parse_args()
    
    manager = RollbackManager()
    
    if args.list:
        snapshots = manager.list_snapshots()
        for s in snapshots:
            print(f"{s.id} | {s.created_at} | {s.task_description} | {len(s.files_modified)} files")
    
    elif args.create:
        snapshot = manager.create_snapshot("cli_test", args.create, "manual")
        print(f"Created snapshot: {snapshot.id}")
    
    elif args.rollback:
        if manager.rollback(args.rollback):
            print(f"Rolled back to: {args.rollback}")
        else:
            print(f"Failed to rollback to: {args.rollback}")
    
    elif args.diff:
        diff = manager.diff(args.diff)
        if diff:
            print(f"Added: {diff.files_added}")
            print(f"Modified: {diff.files_modified}")
            print(f"Deleted: {diff.files_deleted}")
        else:
            print(f"Snapshot not found: {args.diff}")


if __name__ == "__main__":
    main()
