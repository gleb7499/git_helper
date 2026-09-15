"""
Git Docker Utilities Module

Module for working with Docker and Git repositories.
Supports repository root discovery, super-linter runs, and result processing.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List


class GitDockerUtils:
    """Utilities for working with Git and Docker."""
    
    def __init__(self):
        """Initialize the utilities."""
        self.super_linter_image = "ghcr.io/super-linter/super-linter:v6"
    
    def find_git_root(self, start_path: str) -> Optional[Path]:
        """
        Find the Git repository root by walking up the directory tree.
        
        Args:
            start_path: Path to start the search from
            
        Returns:
            Path to the repository root or None if not found
        """
        current = Path(start_path).resolve()
        
        # Go up until .git is found
        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                return current
            current = current.parent
        
        return None
    
    def get_relative_path(self, full_path: str, repo_root: Path) -> str:
        """
        Compute the path relative to the repository root.
        
        Args:
            full_path: Full path to the folder
            repo_root: Repository root
            
        Returns:
            Relative path in Unix format
        """
        full = Path(full_path).resolve()
        relative = full.relative_to(repo_root)
        # Convert to Unix format (for Docker)
        return str(relative).replace("\\", "/")
    
    def check_docker_running(self) -> Tuple[bool, str]:
        """
        Check whether Docker is running.
        
        Returns:
            Tuple (success, message)
        """
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "✅ Docker запущен и доступен"
            else:
                return False, "❌ Docker не отвечает. Убедитесь, что Docker Desktop запущен."
        except subprocess.TimeoutExpired:
            return False, "❌ Docker не отвечает (timeout). Запустите Docker Desktop."
        except FileNotFoundError:
            return False, "❌ Docker не установлен. Установите Docker Desktop."
        except Exception as e:
            return False, f"❌ Ошибка проверки Docker: {str(e)}"
    
    def check_config_exists(self, repo_root: Path, config_name: str = ".markdownlint.yaml") -> bool:
        """
        Check for a configuration file in the repository root.
        
        Args:
            repo_root: Repository root
            config_name: Config file name
            
        Returns:
            True if the file exists
        """
        config_path = repo_root / config_name
        return config_path.exists()
    
    def run_super_linter(
        self,
        repo_root: Path,
        relative_path: str,
        linters: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Run the super-linter via Docker.
        
        Args:
            repo_root: Git repository root
            relative_path: Relative path to the folder to check
            linters: List of linters to activate (MARKDOWN only by default)
            
        Returns:
            Tuple (success, command output)
        """
        try:
            # Build the Docker command
            if linters is None:
                linters = ["MARKDOWN"]
            
            # Base parameters
            docker_cmd = [
                "docker", "run", "--rm",
                "-e", "RUN_LOCAL=true",
                "-e", "DEFAULT_BRANCH=main",
                "-e", "VALIDATE_ALL_CODEBASE=true",
                # Use find instead of git to search for files
                # (solves the Cyrillic file names problem)
                "-e", "USE_FIND_ALGORITHM=true",
                # Linter configuration (as in GitHub Actions)
                "-e", "LINTER_RULES_PATH=.",
                "-e", "MARKDOWN_CONFIG_FILE=.markdownlint.yaml",
            ]
            
            # Add linter activation
            for linter in linters:
                docker_cmd.extend(["-e", f"VALIDATE_{linter}=true"])
            
            # Add a filter for the specific folder
            # Regex matches files in the folder and all subfolders
            filter_regex = f".*{relative_path}.*"
            docker_cmd.extend(["-e", f"FILTER_REGEX_INCLUDE={filter_regex}"])
            
            # Exclude folders (as in GitHub Actions)
            docker_cmd.extend(["-e", "FILTER_REGEX_EXCLUDE=(node_modules/|tools/ci/out/)"])
            
            # Mount the repository root
            # Use an absolute path for Windows
            mount_path = str(repo_root).replace("\\", "/")
            docker_cmd.extend(["-v", f"{mount_path}:/tmp/lint"])
            
            # Add the image
            docker_cmd.append(self.super_linter_image)
            
            # Run Docker
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False,
                cwd=str(repo_root),
                shell=False
            )
            
            # Collect the output
            output = result.stdout + result.stderr
            
            return True, output
            
        except Exception as e:
            return False, f"❌ Ошибка запуска Docker: {str(e)}"
    
    def has_linter_errors(self, output: str) -> bool:
        """
        Check whether the super-linter output contains linting errors.
        
        Args:
            output: Super-linter output
            
        Returns:
            True if linting errors are found
        """
        # Look for super-linter error markers
        error_markers = [
            "[ERROR]   Found errors when linting",
            "[ERROR]   Super-linter detected linting errors",
            "Errors found in"
        ]
        return any(marker in output for marker in error_markers)
    
    def get_extension_to_linter_mapping(self) -> dict:
        """
        Return the mapping of file extensions to super-linter linters.
        
        Returns:
            Dictionary {extension: list_of_linters}
        """
        return {
            ".md": ["MARKDOWN"],
            ".markdown": ["MARKDOWN"],
            ".js": ["JAVASCRIPT_ES"],
            ".jsx": ["JAVASCRIPT_ES"],
            ".py": ["PYTHON_PYLINT", "PYTHON_FLAKE8"],
            ".html": ["HTML"],
            ".htm": ["HTML"],
            ".css": ["CSS"],
            ".scss": ["CSS"],
            ".json": ["JSON"],
            ".yml": ["YAML"],
            ".yaml": ["YAML"],
            ".sh": ["BASH"],
            ".bash": ["BASH"],
            ".ts": ["TYPESCRIPT_ES"],
            ".tsx": ["TYPESCRIPT_ES"],
            ".xml": ["XML"],
            ".sql": ["SQL"],
            ".dockerfile": ["DOCKERFILE_HADOLINT"],
        }
    
    def scan_directory_for_file_types(self, directory: Path) -> dict:
        """
        Scan a directory and determine all file types.
        Excludes node_modules and tools/ci/out.
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            Dictionary {extension: file_count}
        """
        file_types = {}
        
        # Folders to exclude (as in GitHub Actions)
        excluded_dirs = {'node_modules', 'tools'}
        
        try:
            # Recursively walk all files
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Check if the file is in excluded directories
                    parts = file_path.relative_to(directory).parts
                    if any(excluded_dir in parts for excluded_dir in excluded_dirs):
                        continue
                    
                    # Get the extension (lowercased)
                    ext = file_path.suffix.lower()
                    
                    # Skip files without an extension and hidden files
                    if not ext or file_path.name.startswith("."):
                        continue
                    
                    # Count files by extension
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return file_types
            
        except Exception as e:
            print(f"⚠️  Ошибка сканирования директории: {str(e)}")
            return {}
    
    def detect_linters_from_files(self, directory: Path) -> Tuple[List[str], dict]:
        """
        Automatically determine the required linters based on found files.
        
        Args:
            directory: Path to the directory to analyze
            
        Returns:
            Tuple (list_of_linters, file_statistics)
        """
        # Scan the directory
        file_types = self.scan_directory_for_file_types(directory)
        
        if not file_types:
            return [], {}
        
        # Get the extension-to-linter mapping
        ext_to_linters = self.get_extension_to_linter_mapping()
        
        # Collect unique linters
        detected_linters = set()
        for ext, count in file_types.items():
            if ext in ext_to_linters:
                detected_linters.update(ext_to_linters[ext])
        
        return sorted(list(detected_linters)), file_types
    
    def get_linter_description(self, linter_code: str) -> str:
        """
        Return the linter description.
        
        Args:
            linter_code: Linter code
            
        Returns:
            Linter description
        """
        descriptions = {
            "MARKDOWN": "Markdown",
            "JAVASCRIPT_ES": "JavaScript/ES",
            "TYPESCRIPT_ES": "TypeScript",
            "PYTHON_PYLINT": "Python (Pylint)",
            "PYTHON_BLACK": "Python (Black)",
            "PYTHON_FLAKE8": "Python (Flake8)",
            "HTML": "HTML",
            "CSS": "CSS/SCSS",
            "JSON": "JSON",
            "YAML": "YAML",
            "BASH": "Bash",
            "XML": "XML",
            "SQL": "SQL",
            "DOCKERFILE_HADOLINT": "Dockerfile",
        }
        return descriptions.get(linter_code, linter_code)
