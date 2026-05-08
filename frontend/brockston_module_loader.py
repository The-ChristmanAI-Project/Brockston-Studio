"""
BROCKSTON Module Loader - SOVEREIGN REWRITE
-------------------
Dynamically discovers and loads EVERY module in the directory.
No hardcoded lists. No lies. Absolute honesty.

"Every module makes BROCKSTON who he is"
"""

import sys
import os
import logging
import importlib
import traceback
from pathlib import Path

# Fix sys.path to ensure core and root are shoulder-to-shoulder
PROJECT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for _p in [str(PROJECT_ROOT), str(CORE_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ModuleLoader")

class BrockstonModuleLoader:
    """Loads and integrates ALL 365+ physical modules into the brain."""

    def __init__(self):
        self.loaded_modules = {}
        self.failed_modules = {}
        self.ignore_list = {'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}

    def discover_physical_modules(self):
        """Walks the directory and finds every single .py file Everett wrote."""
        discovered = {}
        for root, dirs, files in os.walk(os.getcwd()):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_list]
            for file in files:
                if file.endswith(".py") and file != "brockston_module_loader.py":
                    rel_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                    # Convert file path to python import notation
                    module_import_path = rel_path.replace(os.sep, ".").replace(".py", "")
                    # Use the filename as the key
                    module_name = Path(file).stem
                    discovered[module_name] = module_import_path
        return discovered

    def load_all_modules(self):
        """Force-loads every discovered module into BROCKSTON's consciousness."""
        # 1. Physical Inventory Check (Rule 13: Truth)
        physical_map = self.discover_physical_modules()
        total_physical = len(physical_map)
        
        logger.info(f"📦 PHYSICAL INVENTORY: {total_physical} modules found on disk.")
        logger.info("🧠 Initializing loading sequence...")
        logger.info("=" * 60)

        # 2. Sequential Loading
        for name, path in physical_map.items():
            try:
                # Reality over Theory: Actually try to load it
                module = importlib.import_module(path)
                self.loaded_modules[name] = module
                logger.info(f"  ✅ LOADED: {name} ({path})")
            except Exception as e:
                # Rule 6: Fail Loud
                error_detail = traceback.format_exc().splitlines()[-1]
                self.failed_modules[name] = error_detail
                logger.warning(f"  ❌ FAILED: {name} | Reason: {error_detail}")

        # 3. Truth Table Summary
        success_count = len(self.loaded_modules)
        failure_count = len(self.failed_modules)
        success_rate = (success_count / total_physical * 100) if total_physical > 0 else 0

        logger.info("\n" + "=" * 60)
        logger.info(f"📊 BROCKSTON REALITY REPORT")
        logger.info(f"   Total Physical Modules : {total_physical}")
        logger.info(f"   Successfully Integrated: {success_count}")
        logger.info(f"   Paralyzed/Failed       : {failure_count}")
        logger.info(f"   TRUE OPERATIONAL RATE  : {success_rate:.1f}%")
        logger.info("=" * 60)

        if failure_count > 0:
            logger.warning(f"⚠️  {failure_count} modules are sitting 'dark' due to errors.")
        
        return self.loaded_modules

# Global instance for the brain bridge
_brockston_loader = None

def load_brockston_consciousness():
    """Entry point for the brain bridge to wake up the system."""
    global _brockston_loader
    if _brockston_loader is None:
        _brockston_loader = BrockstonModuleLoader()
    
    _brockston_loader.load_all_modules()
    return _brockston_loader

if __name__ == "__main__":
    # Test the crawler directly
    load_brockston_consciousness()
