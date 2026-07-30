"""Executive deployment identity reporting for Lyons Command Center.

This module provides enhanced version information for the /version command,
including repository identity, runtime environment, and system status.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_git_identity(repo_dir: Optional[Path] = None) -> dict:
    """Get Git repository identity information.
    
    Returns dict with: repo, branch, commit, short_commit
    """
    result = {
        "repo": "Unknown",
        "branch": "Unknown", 
        "commit": "Unknown",
        "short_commit": "Unknown"
    }
    
    if repo_dir is None:
        try:
            from hermes_cli.banner import _resolve_repo_dir
            repo_dir = _resolve_repo_dir()
        except Exception:
            return result
    
    if repo_dir is None:
        return result
    
    try:
        # Get remote URL
        url_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5, cwd=str(repo_dir)
        )
        if url_result.returncode == 0:
            url = (url_result.stdout or "").strip()
            # Parse repo from URL
            if url.startswith("git@"):
                # git@github.com:user/repo.git -> user/repo
                parts = url.split(":")[-1].split(".git")[0]
                result["repo"] = parts
            elif url.startswith("https://"):
                # https://github.com/user/repo -> user/repo
                parts = url.replace("https://", "").split("/", 1)
                result["repo"] = parts[-1] if len(parts) > 1 else "Unknown"
        
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(repo_dir)
        )
        if branch_result.returncode == 0:
            result["branch"] = (branch_result.stdout or "").strip()
        
        # Get full commit SHA
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(repo_dir)
        )
        if commit_result.returncode == 0:
            result["commit"] = (commit_result.stdout or "").strip()
            result["short_commit"] = result["commit"][:8] if len(result["commit"]) >= 8 else result["commit"]
    except Exception:
        pass
    
    return result


def get_runtime_environment() -> str:
    """Determine the runtime environment.
    
    Returns: 'Production', 'Development', or 'Unknown'
    """
    # Check for production indicators
    env_markers = [
        os.environ.get("HERMES_ENV", ""),
        os.environ.get("ENVIRONMENT", ""),
        os.environ.get("NODE_ENV", ""),
    ]
    
    for marker in env_markers:
        if marker.lower() == "production":
            return "Production"
    
    # Check for Railway or other deployment indicators
    if os.environ.get("RAILWAY_DEPLOYMENT_ID"):
        return "Production"
    
    if os.environ.get("PORT") and os.environ.get("RAILWAY_STATIC_URL"):
        return "Production"
    
    # Default to Development for local runs
    return "Development"


def get_database_status() -> dict:
    """Get database path and health status."""
    try:
        from hermes_constants import get_hermes_home
        hermes_home = get_hermes_home()
        db_path = hermes_home / "executions.db"
        
        exists = db_path.exists()
        size = db_path.stat().st_size if exists else 0
        
        return {
            "path": str(db_path),
            "exists": exists,
            "size_bytes": size if exists else 0,
            "health": "Healthy" if exists else "Not initialized"
        }
    except Exception:
        return {
            "path": "Unknown",
            "exists": False,
            "size_bytes": 0,
            "health": "Unavailable"
        }


def get_gateway_status() -> str:
    """Get gateway connection status."""
    try:
        # Check if gateway is running by looking for its process
        result = subprocess.run(
            ["pgrep", "-f", "hermes.*gateway|gateway.*hermes"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and (result.stdout or "").strip():
            return "Running"
        return "Stopped"
    except Exception:
        return "Unknown"


def get_telegram_status() -> str:
    """Get Telegram connection status."""
    try:
        from hermes_cli.config import load_config
        config = load_config()
        
        # Check if Telegram is configured
        gateway_config = config.get("gateway", {})
        telegram_config = gateway_config.get("telegram", {})
        
        if not telegram_config.get("enabled", False):
            return "Not configured"
        
        # Check for token
        if not telegram_config.get("bot_token"):
            return "Not configured"
        
        # Check if gateway is running
        status = get_gateway_status()
        return "Connected" if status == "Running" else "Disconnected"
    except Exception:
        return "Unknown"


def get_model_configuration() -> dict:
    """Get primary and fallback model configuration."""
    try:
        from hermes_cli.config import load_config
        config = load_config()
        
        model_config = config.get("model", {})
        primary_provider = model_config.get("provider", "Unknown")
        primary_model = model_config.get("model", "Unknown")
        
        # Get fallback model
        aux_config = config.get("auxiliary", {})
        fallback = aux_config.get("fallback_model", {})
        fallback_provider = fallback.get("provider", "None")
        fallback_model = fallback.get("model", "None")
        
        return {
            "primary": f"{primary_provider}/{primary_model}" if primary_model != "Unknown" else primary_provider,
            "fallback": f"{fallback_provider}/{fallback_model}" if fallback_model != "None" else "None"
        }
    except Exception:
        return {
            "primary": "Unknown",
            "fallback": "None"
        }


def get_active_session_count() -> int:
    """Get count of active sessions."""
    try:
        from hermes_state import SessionDB
        from hermes_constants import get_hermes_home
        
        hermes_home = get_hermes_home()
        db_path = hermes_home / "sessions.db"
        
        if not db_path.exists():
            return 0
        
        db = SessionDB(db_path)
        # Count sessions with active conversations
        count = db.count_active_sessions()
        db.close()
        return count
    except Exception:
        return 0


def get_memory_health() -> str:
    """Get memory provider health status."""
    try:
        from hermes_cli.config import load_config
        config = load_config()
        
        memory_config = config.get("memory", {})
        provider = memory_config.get("provider", "none")
        
        if provider == "none" or not provider:
            return "Not configured"
        
        # Check if provider is healthy
        if provider == "honcho":
            try:
                from agent.memory_providers.honcho import HonchoProvider
                p = HonchoProvider(memory_config)
                health = p.health_check()
                return "Healthy" if health else "Unhealthy"
            except Exception:
                return "Unavailable"
        
        return "Configured"
    except Exception:
        return "Unknown"


def format_executive_version_report() -> str:
    """Format the complete executive version report."""
    from hermes_cli.banner import format_banner_version_label
    from hermes_cli.config import detect_install_method
    from hermes_constants import PROJECT_ROOT
    
    lines = []
    
    # Version banner
    lines.append(format_banner_version_label())
    
    # Repository identity
    git_info = get_git_identity()
    lines.append(f"Repository: {git_info['repo']}")
    lines.append(f"Branch: {git_info['branch']}")
    lines.append(f"Commit: {git_info['commit']} ({git_info['short_commit']})")
    
    # Runtime environment
    env = get_runtime_environment()
    lines.append(f"Environment: {env}")
    
    # Database
    db_status = get_database_status()
    lines.append(f"Database: {db_status['path']}")
    lines.append(f"Memory Health: {db_status['health']}")
    
    # Gateway and Telegram
    lines.append(f"Gateway: {get_gateway_status()}")
    lines.append(f"Telegram: {get_telegram_status()}")
    
    # Models
    model_info = get_model_configuration()
    lines.append(f"Models: Primary ({model_info['primary']}), Fallback ({model_info['fallback']})")
    
    # Sessions
    session_count = get_active_session_count()
    lines.append(f"Active Sessions: {session_count}")
    
    # Python version
    lines.append(f"Python: {sys.version.split()[0]}")
    
    # OpenAI SDK
    try:
        from importlib.metadata import version as _pkg_version, PackageNotFoundError
        try:
            lines.append(f"OpenAI SDK: {_pkg_version('openai')}")
        except PackageNotFoundError:
            lines.append("OpenAI SDK: Not installed")
    except ImportError:
        lines.append("OpenAI SDK: Not installed")
    
    return "\n".join(lines)