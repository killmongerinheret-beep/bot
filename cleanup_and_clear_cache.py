"""
Clear all caches and move test files to archive
"""
import os
import sys
import django
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.cache import cache

print("=" * 80)
print("CLEANUP AND CACHE CLEAR")
print("=" * 80)

# 1. Clear Django cache
print("\n1. Clearing Django cache...")
cache.clear()
print("   ✅ Django cache cleared")

# 2. Clear Redis cache
print("\n2. Clearing Redis cache...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.flushdb()
    print("   ✅ Redis cache cleared")
except Exception as e:
    print(f"   ⚠️ Could not clear Redis: {e}")

# 3. Delete Python cache files
print("\n3. Deleting Python cache files...")
cache_count = 0
for root, dirs, files in os.walk('.'):
    # Skip node_modules and .git
    if 'node_modules' in root or '.git' in root:
        continue
    
    # Remove __pycache__ directories
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(pycache_path)
            cache_count += 1
        except:
            pass
    
    # Remove .pyc files
    for file in files:
        if file.endswith('.pyc'):
            try:
                os.remove(os.path.join(root, file))
                cache_count += 1
            except:
                pass

print(f"   ✅ Removed {cache_count} cache files/directories")

# 4. Create archive directory
print("\n4. Creating archive directory...")
archive_dir = Path('_archive')
archive_dir.mkdir(exist_ok=True)
print(f"   ✅ Archive directory: {archive_dir}")

# 5. Move test/debug files
print("\n5. Moving test and debug files to archive...")

# Patterns to move
patterns_to_move = [
    'test_*.py',
    'debug_*.py',
    'check_*.py',
    'verify_*.py',
    'analyze_*.py',
    'force_*.py',
    'compare_*.py',
    'benchmark_*.py',
    'send_*.py',
    '*_test.py',
    'quick_*.py',
    'deep_*.py',
    'comprehensive_*.py',
    'final_*.py',
    'live_*.py',
    'extract_*.py',
    'get_*.py',
    'make_*.py',
    'setup_*.py',
    'fix_*.py',
    'achieve_*.py',
    'add_*.py',
    'create_*.py',
    'set_*.py',
    'find_*.py',
    'update_*.py',
    'diagnose_*.py',
    'manual_*.py',
    'trigger_*.py',
]

moved_count = 0
for pattern in patterns_to_move:
    for file in Path('.').glob(pattern):
        if file.is_file() and not file.name.startswith('_'):
            try:
                shutil.move(str(file), str(archive_dir / file.name))
                moved_count += 1
                print(f"   Moved: {file.name}")
            except Exception as e:
                print(f"   ⚠️ Could not move {file.name}: {e}")

print(f"\n   ✅ Moved {moved_count} test/debug files")

# 6. Move markdown documentation files (keep important ones)
print("\n6. Moving old documentation files...")

# Keep these important files
keep_files = {
    'README.md',
    'START_HERE.md',
    '24_7_OPERATION_GUIDE.md',
    'SYSTEM_RESTORED_SUMMARY.md',
}

md_moved = 0
for md_file in Path('.').glob('*.md'):
    if md_file.name not in keep_files and md_file.is_file():
        try:
            shutil.move(str(md_file), str(archive_dir / md_file.name))
            md_moved += 1
            print(f"   Moved: {md_file.name}")
        except Exception as e:
            print(f"   ⚠️ Could not move {md_file.name}: {e}")

print(f"\n   ✅ Moved {md_moved} documentation files")

# 7. Move PowerShell scripts
print("\n7. Moving PowerShell scripts...")

ps_moved = 0
for ps_file in Path('.').glob('*.ps1'):
    if ps_file.is_file():
        try:
            shutil.move(str(ps_file), str(archive_dir / ps_file.name))
            ps_moved += 1
            print(f"   Moved: {ps_file.name}")
        except Exception as e:
            print(f"   ⚠️ Could not move {ps_file.name}: {e}")

print(f"\n   ✅ Moved {ps_moved} PowerShell scripts")

print("\n" + "="*80)
print("CLEANUP SUMMARY")
print("="*80)
print(f"\n✅ Django cache cleared")
print(f"✅ Redis cache cleared")
print(f"✅ {cache_count} Python cache files removed")
print(f"✅ {moved_count} test/debug Python files moved to _archive/")
print(f"✅ {md_moved} documentation files moved to _archive/")
print(f"✅ {ps_moved} PowerShell scripts moved to _archive/")
print(f"\nTotal files archived: {moved_count + md_moved + ps_moved}")
print(f"\nArchive location: {archive_dir.absolute()}")

print("\n" + "="*80)
