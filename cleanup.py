#!/usr/bin/env python3
"""
cleanup.py - Remove old obsolete files from the refactored chatbot
This script safely deletes files from the old FAQ-based system
"""

import os
import shutil
from pathlib import Path

# Files that are safe to delete (old system)
OLD_FILES = [
    "logic_old.py",          # Backup of old logic
    "dl_engine.py",          # Sentence-Transformers (replaced by llm_engine)
    "ml_engine.py",          # Naive Bayes ML (no longer needed)
    "dl_trainer.py",         # Deep learning trainer (no longer needed)
    "trainer.py",            # ML trainer (no longer needed)
    "auto_train.py",         # Auto training (obsolete)
    "check_labels.py",       # Label checker (obsolete)
    "debug_faq.py",          # FAQ debugger (obsolete)
    "generator.py",          # Data generator (obsolete)
    "implementation_plan.md", # Old documentation
]

# Directories that can be cleaned (large model caches)
OLD_DIRS = [
    "model_cache/models--sentence-transformers*",  # Sentence transformers cache (3GB+)
    "__pycache__",                                   # Python cache
]

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def cleanup():
    """Remove old files"""
    print("\n" + "=" * 50)
    print("  Cleanup Old Chatbot Files")
    print("=" * 50 + "\n")
    
    total_freed = 0
    deleted_count = 0
    
    # Delete old Python files
    print("🗑️  Deleting old Python files...")
    for filename in OLD_FILES:
        filepath = Path(filename)
        if filepath.exists():
            try:
                size = filepath.stat().st_size
                filepath.unlink()
                total_freed += size
                deleted_count += 1
                print(f"   ✅ Deleted: {filename} ({format_size(size)})")
            except Exception as e:
                print(f"   ❌ Error deleting {filename}: {e}")
    
    # Delete old directories
    print("\n🗑️  Deleting old cache directories...")
    for dirname in OLD_DIRS:
        dirpath = Path(dirname)
        if "*" in dirname:
            # Handle wildcard
            base_path = dirname.split("*")[0]
            base_dir = Path(base_path)
            if base_dir.parent.exists():
                for item in base_dir.parent.glob(f"{base_dir.name}*"):
                    try:
                        if item.is_dir():
                            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item)
                            total_freed += size
                            deleted_count += 1
                            print(f"   ✅ Deleted: {item} ({format_size(size)})")
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
        else:
            dirpath = Path(dirname)
            if dirpath.exists():
                try:
                    size = sum(f.stat().st_size for f in dirpath.rglob('*') if f.is_file())
                    shutil.rmtree(dirpath)
                    total_freed += size
                    deleted_count += 1
                    print(f"   ✅ Deleted: {dirname} ({format_size(size)})")
                except Exception as e:
                    print(f"   ❌ Error deleting {dirname}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Cleanup Complete!")
    print(f"   Files deleted: {deleted_count}")
    print(f"   Space freed: {format_size(total_freed)}")
    print("=" * 50 + "\n")
    
    # Show remaining active files
    print("📁 Active files remaining:")
    active_files = [
        "llm_engine.py",
        "logic.py",
        "chatbot.py",
        "memory.py",
        "faqs.sql",
        "requirements.txt",
        ".env",
        "start.bat",
        "setup.py",
    ]
    
    for f in active_files:
        if Path(f).exists():
            size = Path(f).stat().st_size
            print(f"   ✅ {f} ({format_size(size)})")
    
    print("\n✨ You can now run: python chatbot.py\n")

if __name__ == "__main__":
    import sys
    
    print("\n⚠️  WARNING: This will delete old chatbot files!")
    print("    Make sure you have backups if needed.\n")
    
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm in ["yes", "y"]:
        cleanup()
    else:
        print("❌ Cleanup cancelled.")
        sys.exit(0)
