import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ProjectManager:
    def __init__(self, db_path="database/projects_db.json", thumbnails_dir="thumbnails"):
        self.db_path = Path(db_path)
        self.thumbnails_dir = Path(thumbnails_dir)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.projects = self.load_projects()

    def load_projects(self) -> List[Dict]:
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_projects(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.projects, f, ensure_ascii=False, indent=4)

    def add_project(self, name: str, path: str, description: str, category: str = "", tags: List[str] = None,
                    github_url: str = "", thumbnail_path: str = "", estimated_hours: int = 0) -> Dict:
        path = str(Path(path).resolve())
        project = {
            "id": len(self.projects) + 1,
            "name": name,
            "path": path,
            "description": description,
            "category": category,
            "tags": tags or [],
            "github_url": github_url,
            "thumbnail": thumbnail_path,
            "created": datetime.now().isoformat(),
            "last_run": None,
            "estimated_hours": estimated_hours
        }
        self.projects.append(project)
        self.save_projects()
        return project

    def update_project(self, project_id: int, **kwargs):
        for proj in self.projects:
            if proj["id"] == project_id:
                proj.update(kwargs)
                self.save_projects()
                return proj
        return None

    def get_project(self, project_id: int) -> Optional[Dict]:
        for proj in self.projects:
            if proj["id"] == project_id:
                return proj
        return None

    def delete_project(self, project_id: int):
        self.projects = [p for p in self.projects if p["id"] != project_id]
        self.save_projects()

    def run_project(self, project_id: int):
        project = self.get_project(project_id)
        if not project:
            return None
        self.update_project(project_id, last_run=datetime.now().isoformat())

        path = project["path"]
        if path.endswith('.py'):
            return subprocess.Popen([sys.executable, path])
        elif path.endswith('.exe'):
            return subprocess.Popen([path])
        else:
            main_file = Path(path) / "main.py"
            if main_file.exists():
                return subprocess.Popen([sys.executable, str(main_file)])
        return None

    def get_statistics(self) -> Dict:
        total = len(self.projects)
        categories = {}
        total_estimated = 0
        for p in self.projects:
            cat = p.get("category", "Uncategorized")
            categories[cat] = categories.get(cat, 0) + 1
            total_estimated += p.get("estimated_hours", 0)
        return {
            "total": total,
            "categories": categories,
            "total_estimated_hours": total_estimated,
            "last_updated": datetime.now().isoformat()
        }