import zipfile
from pathlib import Path
from datetime import datetime

class BackupManager:
    def __init__(self, db_path, projects_dir=None):
        self.db_path = Path(db_path)
        self.projects_dir = Path(projects_dir) if projects_dir else None
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, include_projects=False) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if self.db_path.exists():
                zipf.write(self.db_path, arcname=self.db_path.name)

            thumb_dir = Path("thumbnails")
            if thumb_dir.exists():
                for file in thumb_dir.iterdir():
                    zipf.write(file, arcname=f"thumbnails/{file.name}")

            if include_projects and self.projects_dir and self.projects_dir.exists():
                for proj in self.projects_dir.iterdir():
                    if proj.is_dir():
                        for file in proj.rglob("*"):
                            zipf.write(file, arcname=f"projects/{proj.name}/{file.relative_to(proj)}")
        return str(backup_path)

    def restore_backup(self, zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(".")