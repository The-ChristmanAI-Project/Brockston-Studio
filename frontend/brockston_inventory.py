"""
BROCKSTON HARD INVENTORY
------------------------
Cardinal Rule 13: Absolute honesty.
No stories. No percentages. Just a raw count of the physical files.
"""

import os

def get_inventory():
    root_dir = os.getcwd()
    inventory = []
    
    # Folders we don't count as BROCKSTON modules
    ignore_list = {
        'venv', '.git', '__pycache__', '.pytest_cache', 
        '.idea', '.vscode', 'node_modules'
    }

    print("\n" + "="*60)
    print(f"📦 INVENTORYING: {root_dir}")
    print("="*60 + "\n")

    for root, dirs, files in os.walk(root_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_list]
        
        for file in files:
            if file.endswith(".py"):
                # Calculate relative path to see the "City Layout"
                rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                inventory.append(rel_path)

    # Sort so neighbors stay together
    inventory.sort()

    for i, module in enumerate(inventory, 1):
        print(f"{i:03} | {module}")

    print("\n" + "="*60)
    print(f"📊 TOTAL PHYSICAL MODULES: {len(inventory)}")
    print("="*60)

    # Reality Check on the Loader's 137 claim
    if len(inventory) != 137:
        print(f"⚠️  DISCREPANCY: Loader claims 137, but I found {len(inventory)}.")
        print("This usually means the loader is counting non-existent paths or ghost files.")
    else:
        print("✅ PHYSICAL COUNT MATCHES LOADER EXPECTATION.")

if __name__ == "__main__":
    get_inventory()
