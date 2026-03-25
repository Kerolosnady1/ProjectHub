import webbrowser
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

class GitHelper:
    @staticmethod
    def is_git_repo(path):
        if not GIT_AVAILABLE:
            return False
        try:
            repo = git.Repo(path)
            return True
        except:
            return False

    @staticmethod
    def get_repo_info(path):
        if not GIT_AVAILABLE:
            return {"error": "GitPython not installed"}
        try:
            repo = git.Repo(path)
            branch = repo.active_branch.name
            try:
                remote_url = repo.remotes.origin.url
            except:
                remote_url = None
            return {
                "branch": branch,
                "remote_url": remote_url,
                "has_uncommitted": repo.is_dirty(),
                "last_commit": str(repo.head.commit)[:7]
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def clone_repo(url, dest):
        if not GIT_AVAILABLE:
            return False, "GitPython not installed"
        try:
            git.Repo.clone_from(url, dest)
            return True, "Clone successful"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def open_github(project):
        if project.get("github_url"):
            webbrowser.open(project["github_url"])