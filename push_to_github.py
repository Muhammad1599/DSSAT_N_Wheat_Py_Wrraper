import os
import sys
from pathlib import Path

# Add Git to PATH
git_path = r"C:\Program Files\Git\bin"
current_path = os.environ.get('PATH', '')
if git_path not in current_path:
    os.environ['PATH'] = f"{git_path};{current_path}"

# Now import git after PATH is updated
import git

def push_to_github():
    # Repository URL
    repo_url = "https://github.com/Muhammad1599/DSSAT_N_Wheat_Py_Wrraper.git"
    
    # Current directory
    repo_path = Path(".")
    
    try:
        # Check if already a git repository
        if not (repo_path / ".git").exists():
            print("Initializing git repository...")
            repo = git.Repo.init(repo_path)
        else:
            print("Opening existing git repository...")
            repo = git.Repo(repo_path)
        
        # Check if remote exists
        try:
            origin = repo.remote("origin")
            print(f"Remote 'origin' already exists: {origin.url}")
        except ValueError:
            print("Adding remote 'origin'...")
            repo.create_remote("origin", repo_url)
        
        # Add all files
        print("Adding all files...")
        repo.git.add(all=True)
        
        # Check if there are changes to commit
        if repo.is_dirty() or len(repo.untracked_files) > 0:
            print("Committing changes...")
            repo.git.commit(m="Initial commit: Add all project files")
        
        # Push to GitHub
        print("Pushing to GitHub...")
        repo.git.push("origin", "main", force=True)
        
        print("✓ Successfully pushed to GitHub!")
        
    except git.GitCommandError as e:
        print(f"Git error: {e}")
        print("\nTrying to push to master branch instead...")
        try:
            repo.git.push("origin", "master", force=True)
            print("✓ Successfully pushed to GitHub!")
        except Exception as e2:
            print(f"Error: {e2}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease make sure:")
        print("1. The repository exists on GitHub")
        print("2. You have push access to the repository")
        print("3. Your GitHub credentials are configured (git config --global user.name and user.email)")
        sys.exit(1)

if __name__ == "__main__":
    push_to_github()

