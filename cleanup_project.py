#!/usr/bin/env python3
"""
Project Cleanup Script
Removes unnecessary files and clears caches
"""

import os
import shutil
import glob

def cleanup_project():
    """Clean up unnecessary files and caches"""
    
    print("🧹 Starting project cleanup...")
    
    # Files to delete (keep essential ones)
    files_to_delete = [
        # Debug files
        "debug_monday_*.py",
        "debug_*.html",
        "debug_*.png",
        "*debug*.html",
        "*debug*.png",
        "monday_debug_*.html",
        "monday_debug_*.png",
        "monday_page_*.png",
        "vatican_debug*",
        "search_api_*.png",
        "march16_*.html",
        "march16_*.png",
        
        # Test files (keep test_telegram_groups.py)
        "test_complete_flow.py",
        "test_enhanced_notification.py",
        "test_march23_flow.py",
        "test_monday_api_slots.py",
        "test_search_api*.py",
        "test_telegram_all_tasks.py",
        "test_timeavail_with_search_id.py",
        
        # Temporary files
        "temp_key.pub",
        "tunnel_*.log",
        "*.tar.gz",
        "*.json" if "Proxy lists.json" not in glob.glob("*.json") else "",
        
        # Old documentation (keep current ones)
        "COLOSSEUM_REMOVAL_SUMMARY.md",
        "CURRENT_SITUATION.md",
        "CURRENT_STATUS_MARCH7_2PM.md",
        "DATE_FORMAT_FIX.md",
        "MONDAY_DEBUG_INSTRUCTIONS.md",
        "MONDAY_ISSUE_RESOLVED.md",
        "MONDAY_SOLUTION_COMPLETE.md",
        "SEARCH_API_FINDINGS.md",
        "SEARCH_API_MIGRATION_COMPLETE.md",
        "SEARCH_API_UNIVERSAL_SOLUTION.md",
        "USE_SEARCH_API_FOR_MONDAYS.md",
        "SYSTEM_STATUS_MARCH7.md",
        
        # Old scripts
        "probe_*.py",
        "patch_*.py",
        "dump_*.py",
        "save_*.py",
        "update_to_search_api.py",
        "sync_vatican_to_dashboard.py",
        "run_vatican_bot.py",
        "sniffer.py",
        "direct_api_test_march16.py",
        "diagnostic_avail.py",
        "vatican_bot_security_audit.py",
        "telegram_bot_calendar.py",
        "telegram_bot.py",
        "send_test_notification.py",
        
        # Old batch files
        "*.bat",
        "fix_*.sh",
        "run_*.bat",
        "start_*.bat",
        "start_*.sh",
        
        # Old docker files
        "docker-compose-local.yml",
        "docker-compose-optimized.yml",
        "compact_docker*",
        "docker_reset_solution.md",
        
        # Backup files
        "backup_before_reset.sql",
        
        # PDF files
        "*.pdf",
    ]
    
    deleted_count = 0
    
    for pattern in files_to_delete:
        if not pattern:  # Skip empty patterns
            continue
            
        matches = glob.glob(pattern)
        for file_path in matches:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"  ✅ Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to delete {file_path}: {e}")
    
    # Clean up Python cache files
    print("\n🐍 Cleaning Python cache files...")
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        ".pytest_cache",
    ]
    
    for pattern in cache_patterns:
        matches = glob.glob(pattern, recursive=True)
        for cache_path in matches:
            try:
                if os.path.isdir(cache_path):
                    shutil.rmtree(cache_path)
                    print(f"  ✅ Removed cache dir: {cache_path}")
                else:
                    os.remove(cache_path)
                    print(f"  ✅ Removed cache file: {cache_path}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to remove {cache_path}: {e}")
    
    # Clean up node_modules cache (if exists)
    if os.path.exists("frontend/node_modules/.cache"):
        try:
            shutil.rmtree("frontend/node_modules/.cache")
            print("  ✅ Removed frontend cache")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Failed to remove frontend cache: {e}")
    
    # Clean up Docker build cache (show command)
    print("\n🐳 Docker cleanup commands:")
    print("  Run these manually to clean Docker cache:")
    print("  docker system prune -f")
    print("  docker builder prune -f")
    print("  docker image prune -f")
    
    print(f"\n✅ Cleanup complete! Removed {deleted_count} files/directories.")
    
    # Show remaining important files
    print("\n📋 Keeping essential files:")
    essential_files = [
        "docker-compose.yml",
        "README.md",
        "requirements.txt",
        ".env",
        ".env.local",
        "manage_telegram_groups.py",
        "test_telegram_groups.py",
        "cleanup_project.py",
        "CURRENT_STATUS_SUMMARY.md",
        "FINAL_STATUS_UPDATE.md",
        "SAAS_TRANSFORMATION_PLAN.md",
        "30_DAY_LAUNCH_PLAN.md",
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (missing)")

if __name__ == "__main__":
    cleanup_project()