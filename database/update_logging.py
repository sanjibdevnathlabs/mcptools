#!/usr/bin/env python3
"""
Script to update all logging calls in database project files to use the new trace code system.
This updates old-style logging to the new structured JSON trace code format.
"""

import os
import re
import sys
from pathlib import Path

# Define the files to update (excluding already updated ones)
FILES_TO_UPDATE = [
    "server.py",
    "transport.py", 
    "monitoring.py",
    "security.py",
    "error_handling.py",
    "schema_manager.py"
]

# Common trace code mappings for different log patterns
TRACE_CODE_MAPPINGS = {
    # General patterns
    r'logger\.info\("([^"]+)"\)': r'self.logger.info("INFO_MESSAGE", {"message": "\1"})',
    r'logger\.info\(f"([^"]+)"\)': r'self.logger.info("INFO_MESSAGE", {"message": "\1"})',
    r'logger\.warning\("([^"]+)"\)': r'self.logger.warning("WARNING_MESSAGE", {"message": "\1"})',
    r'logger\.warning\(f"([^"]+)"\)': r'self.logger.warning("WARNING_MESSAGE", {"message": "\1"})',
    r'logger\.error\("([^"]+)"\)': r'self.logger.error("ERROR_MESSAGE", {"message": "\1"})',
    r'logger\.error\(f"([^"]+)"\)': r'self.logger.error("ERROR_MESSAGE", {"message": "\1"})',
    r'logger\.debug\("([^"]+)"\)': r'self.logger.debug("DEBUG_MESSAGE", {"message": "\1"})',
    r'logger\.debug\(f"([^"]+)"\)': r'self.logger.debug("DEBUG_MESSAGE", {"message": "\1"})',
}

# Import pattern to add
NEW_IMPORT = "from .logging_config import get_logger"
LOGGER_INIT = "        self.logger = get_logger('{module_name}')"

def update_imports(content: str, filename: str) -> str:
    """Update imports to include new logging system."""
    # Remove old logging import
    content = re.sub(r'^import logging\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^from typing import.*\n', 
                    lambda m: m.group(0) + NEW_IMPORT + '\n', content, flags=re.MULTILINE)
    
    # Remove old logger declaration
    content = re.sub(r'^logger = logging\.getLogger\(__name__\)\n', '', content, flags=re.MULTILINE)
    
    return content

def update_class_init(content: str, class_name: str, module_name: str) -> str:
    """Add logger initialization to class __init__ method."""
    # Find the __init__ method
    init_pattern = rf'(class {class_name}:.*?def __init__\(self.*?\):.*?""".*?""")(.*?)(^\s+\w+)'
    
    def add_logger_init(match):
        before = match.group(1)
        after = match.group(2)
        next_line = match.group(3)
        
        if 'self.logger' not in after:
            logger_line = LOGGER_INIT.format(module_name=module_name)
            return before + after + logger_line + '\n' + next_line
        return match.group(0)
    
    content = re.sub(init_pattern, add_logger_init, content, flags=re.MULTILINE | re.DOTALL)
    return content

def update_logging_calls(content: str) -> str:
    """Update logging calls to use trace codes."""
    # Update basic logging calls
    for pattern, replacement in TRACE_CODE_MAPPINGS.items():
        content = re.sub(pattern, replacement, content)
    
    # Handle more complex patterns manually
    # This is a simplified version - in practice you'd want more sophisticated parsing
    
    return content

def update_file(filepath: Path) -> bool:
    """Update a single file."""
    try:
        print(f"Updating {filepath.name}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Extract module name from filename
        module_name = filepath.stem
        
        # Update imports
        content = update_imports(content, filepath.name)
        
        # Update logging calls
        content = update_logging_calls(content)
        
        # Find main class and update it
        if module_name == "server":
            content = update_class_init(content, "DatabaseMCPServer", "server")
        elif module_name == "transport":
            content = update_class_init(content, "TransportManager", "transport")
        elif module_name == "monitoring":
            content = update_class_init(content, "ProductionMonitor", "monitoring")
        elif module_name == "security":
            content = update_class_init(content, "DatabaseSecurityManager", "security")
        elif module_name == "error_handling":
            content = update_class_init(content, "ErrorHandler", "error_handling")
        elif module_name == "schema_manager":
            content = update_class_init(content, "SchemaManager", "schema")
        
        # Only write if content changed
        if content != original_content:
            # Backup original file
            backup_path = filepath.with_suffix(filepath.suffix + '.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write updated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Updated {filepath.name} (backup: {backup_path.name})")
            return True
        else:
            print(f"  ➡️ No changes needed for {filepath.name}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error updating {filepath.name}: {e}")
        return False

def main():
    """Main function."""
    print("🔄 Updating Database MCP logging system...")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path(".")
    
    updated_files = 0
    total_files = 0
    
    for filename in FILES_TO_UPDATE:
        filepath = current_dir / filename
        if filepath.exists():
            total_files += 1
            if update_file(filepath):
                updated_files += 1
        else:
            print(f"⚠️ File not found: {filename}")
    
    print("\n" + "=" * 50)
    print(f"✅ Logging update complete!")
    print(f"   Files processed: {total_files}")
    print(f"   Files updated: {updated_files}")
    print(f"   Files unchanged: {total_files - updated_files}")
    
    if updated_files > 0:
        print("\n📋 Next steps:")
        print("1. Review the updated files for any manual adjustments needed")
        print("2. Test the logging system")
        print("3. Remove .backup files when satisfied")

if __name__ == "__main__":
    main()
