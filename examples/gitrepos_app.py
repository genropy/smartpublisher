#!/usr/bin/env python3
"""
Git Repository Manager - Organize your projects and repositories.

Manage git repositories organized by projects, with persistent JSON storage.

Usage:
    # Project management
    python gitrepos_app.py project add myproject "My awesome project"
    python gitrepos_app.py project list
    python gitrepos_app.py project remove myproject

    # Repository management
    python gitrepos_app.py repo add myproject frontend https://github.com/user/frontend.git
    python gitrepos_app.py repo add myproject backend https://github.com/user/backend.git --path /path/to/backend
    python gitrepos_app.py repo list
    python gitrepos_app.py repo list myproject
    python gitrepos_app.py repo info myproject frontend
    python gitrepos_app.py repo remove myproject frontend

    # HTTP mode
    python gitrepos_app.py
    # Then: curl http://localhost:8000/docs
"""

import json
from pathlib import Path
from typing import Optional
from smartswitch import Switcher
from smartpublisher import Publisher


class RepoManager:
    """Manage git repositories organized by projects."""

    api = Switcher(prefix="")

    def __init__(self, config_file: Optional[str] = None):
        """Initialize repository manager."""
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path.home() / ".gitrepos.json"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {"projects": {}}

    def _save_config(self):
        """Save configuration to JSON file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    # Project operations

    @api
    def project_add(self, name: str, description: str = "") -> dict:
        """
        Add a new project.

        Args:
            name: Project name
            description: Project description (optional)

        Returns:
            Success message with project details
        """
        if name in self.config["projects"]:
            return {"success": False, "error": f"Project '{name}' already exists"}

        self.config["projects"][name] = {"description": description, "repos": {}}
        self._save_config()

        return {
            "success": True,
            "message": f"Project '{name}' added",
            "project": self.config["projects"][name],
        }

    @api
    def project_list(self) -> dict:
        """
        List all projects.

        Returns:
            Dictionary with count and list of projects
        """
        projects = []
        for name, data in self.config["projects"].items():
            projects.append(
                {"name": name, "description": data["description"], "repo_count": len(data["repos"])}
            )

        return {"count": len(projects), "projects": projects}

    @api
    def project_info(self, name: str) -> dict:
        """
        Get project information.

        Args:
            name: Project name

        Returns:
            Project details with repositories
        """
        if name not in self.config["projects"]:
            return {"success": False, "error": f"Project '{name}' not found"}

        project = self.config["projects"][name]
        return {
            "success": True,
            "name": name,
            "description": project["description"],
            "repos": project["repos"],
        }

    @api
    def project_remove(self, name: str) -> dict:
        """
        Remove a project and all its repositories.

        Args:
            name: Project name

        Returns:
            Success message
        """
        if name not in self.config["projects"]:
            return {"success": False, "error": f"Project '{name}' not found"}

        del self.config["projects"][name]
        self._save_config()

        return {"success": True, "message": f"Project '{name}' removed"}

    # Repository operations

    @api
    def repo_add(
        self, project: str, name: str, url: str, path: str = "", branch: str = "main"
    ) -> dict:
        """
        Add repository to project.

        Args:
            project: Project name
            name: Repository name
            url: Git URL
            path: Local path (optional)
            branch: Default branch (default: main)

        Returns:
            Success message with repository details
        """
        if project not in self.config["projects"]:
            return {"success": False, "error": f"Project '{project}' not found"}

        if name in self.config["projects"][project]["repos"]:
            return {
                "success": False,
                "error": f"Repository '{name}' already exists in project '{project}'",
            }

        self.config["projects"][project]["repos"][name] = {
            "url": url,
            "path": path,
            "branch": branch,
        }
        self._save_config()

        return {
            "success": True,
            "message": f"Repository '{name}' added to project '{project}'",
            "repo": self.config["projects"][project]["repos"][name],
        }

    @api
    def repo_list(self, project: Optional[str] = None) -> dict:
        """
        List repositories (all or filtered by project).

        Args:
            project: Project name (optional, lists all if not specified)

        Returns:
            Dictionary with count and list of repositories
        """
        repos = []

        if project:
            # List repos for specific project
            if project not in self.config["projects"]:
                return {"success": False, "error": f"Project '{project}' not found"}

            for name, data in self.config["projects"][project]["repos"].items():
                repos.append({"project": project, "name": name, **data})
        else:
            # List all repos from all projects
            for proj_name, proj_data in self.config["projects"].items():
                for repo_name, repo_data in proj_data["repos"].items():
                    repos.append({"project": proj_name, "name": repo_name, **repo_data})

        return {"count": len(repos), "repos": repos}

    @api
    def repo_info(self, project: str, name: str) -> dict:
        """
        Get repository information.

        Args:
            project: Project name
            name: Repository name

        Returns:
            Repository details
        """
        if project not in self.config["projects"]:
            return {"success": False, "error": f"Project '{project}' not found"}

        if name not in self.config["projects"][project]["repos"]:
            return {
                "success": False,
                "error": f"Repository '{name}' not found in project '{project}'",
            }

        return {
            "success": True,
            "project": project,
            "name": name,
            **self.config["projects"][project]["repos"][name],
        }

    @api
    def repo_remove(self, project: str, name: str) -> dict:
        """
        Remove repository from project.

        Args:
            project: Project name
            name: Repository name

        Returns:
            Success message
        """
        if project not in self.config["projects"]:
            return {"success": False, "error": f"Project '{project}' not found"}

        if name not in self.config["projects"][project]["repos"]:
            return {
                "success": False,
                "error": f"Repository '{name}' not found in project '{project}'",
            }

        del self.config["projects"][project]["repos"][name]
        self._save_config()

        return {"success": True, "message": f"Repository '{name}' removed from project '{project}'"}

    @api
    def repo_update(
        self,
        project: str,
        name: str,
        url: Optional[str] = None,
        path: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> dict:
        """
        Update repository information.

        Args:
            project: Project name
            name: Repository name
            url: New Git URL (optional)
            path: New local path (optional)
            branch: New default branch (optional)

        Returns:
            Success message with updated repository details
        """
        if project not in self.config["projects"]:
            return {"success": False, "error": f"Project '{project}' not found"}

        if name not in self.config["projects"][project]["repos"]:
            return {
                "success": False,
                "error": f"Repository '{name}' not found in project '{project}'",
            }

        repo = self.config["projects"][project]["repos"][name]

        if url is not None:
            repo["url"] = url
        if path is not None:
            repo["path"] = path
        if branch is not None:
            repo["branch"] = branch

        self._save_config()

        return {"success": True, "message": f"Repository '{name}' updated", "repo": repo}


class GitReposApp(Publisher):
    """Git Repository Manager application."""

    def on_init(self):
        """Initialize and publish repository manager."""
        manager = RepoManager()
        self.publish("project", manager)
        self.publish("repo", manager)


if __name__ == "__main__":
    app = GitReposApp()
    app.run()
