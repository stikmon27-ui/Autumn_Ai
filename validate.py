#!/usr/bin/env python3
"""
Autumn AI - Pre-launch Validation Script
Checks that all critical components are properly configured before running.
"""

import sys
import os
from pathlib import Path

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_python_file_syntax(filepath: str) -> bool:
    """Check if a Python file compiles without syntax errors."""
    try:
        import py_compile
        py_compile.compile(filepath, doraise=True)
        print(f"✅ Syntax check: {filepath}")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return False

def check_variable_references():
    """Check for undefined variable references."""
    issues = []
    
    # Check brain.py
    brain_file = Path("ai-brain/brain.py")
    if brain_file.exists():
        content = brain_file.read_text()
        if "SYSTEM_PROMPT" in content and "ULTIMATE_HOMIE_PROMPT" not in content:
            issues.append("brain.py: SYSTEM_PROMPT referenced but ULTIMATE_HOMIE_PROMPT not defined")
        if "_llm.invoke" in content:
            issues.append("brain.py: _llm referenced instead of llm")
    
    # Check memory.py
    memory_file = Path("ai-brain/memory.py")
    if memory_file.exists():
        content = memory_file.read_text()
        if "_llm.invoke" in content:
            issues.append("memory.py: _llm referenced instead of llm")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return False
    else:
        print("✅ No undefined variable references found")
        return True

def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Autumn AI - Pre-launch Validation")
    print("=" * 60)
    print()
    
    os.chdir(Path(__file__).parent)
    
    checks = [
        # File existence checks
        lambda: check_file_exists("ai-brain/brain.py", "Brain module"),
        lambda: check_file_exists("ai-brain/memory.py", "Memory module"),
        lambda: check_file_exists("ai-brain/ui.py", "UI module"),
        lambda: check_file_exists("ai-brain/tools.py", "Tools module"),
        lambda: check_file_exists("ai-brain/skills.py", "Skills module"),
        lambda: check_file_exists("ai-brain/skill_ingestion.py", "Skill ingestion module"),
        lambda: check_file_exists("ai-brain/requirements.txt", "Requirements file"),
        
        # Syntax checks
        lambda: check_python_file_syntax("ai-brain/brain.py"),
        lambda: check_python_file_syntax("ai-brain/memory.py"),
        lambda: check_python_file_syntax("ai-brain/ui.py"),
        lambda: check_python_file_syntax("ai-brain/tools.py"),
        lambda: check_python_file_syntax("ai-brain/skills.py"),
        lambda: check_python_file_syntax("ai-brain/skill_ingestion.py"),
        
        # Variable reference checks
        check_variable_references,
    ]
    
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append(False)
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All validation checks PASSED!")
        print("Ready to run: python ai-brain/ui.py")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed} validation check(s) FAILED")
        print("Please fix the issues above before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
