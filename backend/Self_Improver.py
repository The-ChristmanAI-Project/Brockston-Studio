
"""
╔══════════════════════════════════════════════════════════════╗
║                SELF IMPROVER - CODE ANALYZER                 ║
║           Luma Cognify AI - The Christman Project            ║
║                                                            ║
║  PURPOSE:                                                  ║
║    Scans Python code for common problems, explains         ║
║    how to fix them, and can automatically apply fixes.     ║
║                                                            ║
║  HOW TO USE:                                               ║
║    Single file:  python self_improver.py my_script.py      ║
║    Whole project: python self_improver.py ./my_project      ║
║    Demo mode:    python self_improver.py                   ║
║                                                            ║
║  AUTOCORRECT TOGGLE:                                       ║
║    True  = Diagnose AND fix problems automatically         ║
║    False = Only diagnose, show what would be fixed         ║
╚══════════════════════════════════════════════════════════════╝
"""

import ast
import re
import copy
import textwrap
import fnmatch
from pathlib import Path
from typing import List, Tuple, Optional


# ╔══════════════════════════════════════════════════════════╗
# ║                    MASTER TOGGLE                        ║
# ║  Change this to True or False to control auto-fixing    ║
# ╚══════════════════════════════════════════════════════════╝

AUTOCORRECT_ENABLED: bool = True


# ╔══════════════════════════════════════════════════════════╗
# ║                    ISSUE MODEL                          ║
# ║  Represents a single problem found in the code          ║
# ╚══════════════════════════════════════════════════════════╝

class CodeIssue:
    """Stores information about a problem found in the code."""
    
    def __init__(
        self,
        line: int,
        code: str,
        problem: str,
        suggestion: str,
        fixable: bool = False
    ):
        self.line       = line        # Line number (1-based), 0 means file-level issue
        self.code       = code        # Short code like "BARE_EXCEPT"
        self.problem    = problem     # Description of what's wrong
        self.suggestion = suggestion  # How to fix the problem
        self.fixable    = fixable     # Can the auto-fixer fix this?

    def __str__(self):
        loc   = f"Line {self.line}" if self.line else "File"
        auto  = " [CAN BE FIXED AUTOMATICALLY]" if self.fixable else ""
        
        return (
            f"\n  [{loc}] {self.code}{auto}\n"
            f"    Problem:    {self.problem}\n"
            f"    Suggestion: {self.suggestion}"
        )


# ╔══════════════════════════════════════════════════════════╗
# ║                  CODE ANALYZER                          ║
# ║  Reads Python code and finds common problems            ║
# ╚══════════════════════════════════════════════════════════╝

class CodeAnalyzer:
    """
    Checks Python source code for problems.
    Returns a list of CodeIssue objects describing each problem.
    """
    
    # ─────────────────────────────────────────────
    #  MAIN ANALYSIS METHOD
    # ─────────────────────────────────────────────
    
    def analyze(self, source: str) -> List[CodeIssue]:
        """Run all checks on the source code."""
        all_issues = []
        
        # Step 1: Check if the code is valid Python
        all_issues.extend( self._check_syntax(source) )
        
        # Step 2: Only continue if there are no syntax errors
        has_syntax_error = any(
            issue.code == "SYNTAX_ERROR" for issue in all_issues
        )
        
        if not has_syntax_error:
            tree = ast.parse(source)
            all_issues.extend( self._check_bare_except(tree) )
            all_issues.extend( self._check_mutable_defaults(tree) )
            all_issues.extend( self._check_unused_imports(tree, source) )
            all_issues.extend( self._check_print_statements(tree) )
        
        # Step 3: Check text-level issues (no parsing needed)
        all_issues.extend( self._check_trailing_whitespace(source) )
        all_issues.extend( self._check_long_lines(source) )
        
        # Sort by line number for easier reading
        return sorted(all_issues, key=lambda issue: issue.line)
    
    
    # ─────────────────────────────────────────────
    #  INDIVIDUAL CHECKS
    # ─────────────────────────────────────────────
    
    def _check_syntax(self, source: str) -> List[CodeIssue]:
        """
        CHECK #1: Syntax Errors
        Makes sure the code is valid Python before doing other checks.
        """
        try:
            ast.parse(source)
            return []
            
        except SyntaxError as error:
            return [
                CodeIssue(
                    line       = error.lineno or 0,
                    code       = "SYNTAX_ERROR",
                    problem    = f"Syntax error: {error.msg}",
                    suggestion = "Fix the syntax error before other checks can run.",
                    fixable    = False,
                )
            ]
    
    
    def _check_bare_except(self, tree: ast.AST) -> List[CodeIssue]:
        """
        CHECK #2: Bare Except Statements
        Finding 'except:' without specifying what exception to catch.
        """
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(
                    CodeIssue(
                        line       = node.lineno,
                        code       = "BARE_EXCEPT",
                        problem    = (
                            "Bare 'except:' catches EVERYTHING including "
                            "KeyboardInterrupt and SystemExit."
                        ),
                        suggestion = (
                            "Use 'except Exception as e:' "
                            "or catch a specific exception type."
                        ),
                        fixable    = True,
                    )
                )
        
        return issues
    
    
    def _check_mutable_defaults(self, tree: ast.AST) -> List[CodeIssue]:
        """
        CHECK #3: Mutable Default Arguments
        Finding functions that use [] or {} as default values.
        This is a common Python pitfall!
        """
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(
                            CodeIssue(
                                line       = node.lineno,
                                code       = "MUTABLE_DEFAULT",
                                problem    = (
                                    f"Function '{node.name}' uses a mutable "
                                    f"default argument like [] or {{}}."
                                ),
                                suggestion = (
                                    "Use None as the default instead, "
                                    "then initialize inside the function body."
                                ),
                                fixable    = False,
                            )
                        )
        
        return issues
    
    
    def _check_unused_imports(
        self, tree: ast.AST, source: str
    ) -> List[CodeIssue]:
        """
        CHECK #4: Unused Imports
        Finding imports that are never used in the code.
        """
        issues = []
        imported_names = {}
        
        # Find all imports and their line numbers
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names[name] = node.lineno
                    
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names[name] = node.lineno
        
        # Check if each imported name is actually used
        for name, lineno in imported_names.items():
            pattern = re.compile(rf'\b{re.escape(name)}\b')
            lines = source.splitlines()
            
            # Count uses outside the import line itself
            uses = sum(
                1 for i, line in enumerate(lines, 1)
                if i != lineno and pattern.search(line)
            )
            
            if uses == 0:
                issues.append(
                    CodeIssue(
                        line       = lineno,
                        code       = "UNUSED_IMPORT",
                        problem    = f"'{name}' is imported but never used.",
                        suggestion = f"Remove the unused import for '{name}'.",
                        fixable    = True,
                    )
                )
        
        return issues
    
    
    def _check_print_statements(self, tree: ast.AST) -> List[CodeIssue]:
        """
        CHECK #5: Print Statements
        Finding print() calls that might be leftover debug statements.
        """
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "print":
                    issues.append(
                        CodeIssue(
                            line       = node.lineno,
                            code       = "PRINT_STATEMENT",
                            problem    = (
                                "print() statement found - might be debug "
                                "output left in production code."
                            ),
                            suggestion = (
                                "Replace with logging.debug() or "
                                "remove if not needed."
                            ),
                            fixable    = False,
                        )
                    )
        
        return issues
    
    
    def _check_trailing_whitespace(self, source: str) -> List[CodeIssue]:
        """
        CHECK #6: Trailing Whitespace
        Finding lines with spaces or tabs at the end.
        """
        issues = []
        
        for line_number, line in enumerate(source.splitlines(), 1):
            if line != line.rstrip():
                issues.append(
                    CodeIssue(
                        line       = line_number,
                        code       = "TRAILING_WHITESPACE",
                        problem    = "This line has trailing whitespace.",
                        suggestion = "Remove the extra spaces or tabs at the end.",
                        fixable    = True,
                    )
                )
        
        return issues
    
    
    def _check_long_lines(
        self, source: str, max_length: int = 100
    ) -> List[CodeIssue]:
        """
        CHECK #7: Long Lines
        Finding lines that are too long and hard to read.
        """
        issues = []
        
        for line_number, line in enumerate(source.splitlines(), 1):
            if len(line) > max_length:
                issues.append(
                    CodeIssue(
                        line       = line_number,
                        code       = "LONG_LINE",
                        problem    = (
                            f"Line is {len(line)} characters long "
                            f"(limit is {max_length})."
                        ),
                        suggestion = (
                            "Break this line into multiple lines "
                            "or extract a variable."
                        ),
                        fixable    = False,
                    )
                )
        
        return issues


# ╔══════════════════════════════════════════════════════════╗
# ║                    AUTO FIXER                           ║
# ║  Applies fixes for problems that are safe to auto-fix   ║
# ║  Always works on a COPY - never changes the original    ║
# ╚══════════════════════════════════════════════════════════╝

class AutoFixer:
    """
    Fixes problems that are marked as 'fixable'.
    Only makes safe, mechanical changes like removing whitespace.
    """
    
    def fix(
        self, source: str, issues: List[CodeIssue]
    ) -> Tuple[str, List[str]]:
        """
        Apply fixes to the source code.
        
        Returns:
            Tuple of (fixed_source_code, list_of_fixes_applied)
        """
        lines   = source.splitlines(keepends=True)
        applied = []
        fixable = [issue for issue in issues if issue.fixable]
        
        for issue in fixable:
            
            # ─── Fix Trailing Whitespace ─────────────
            if issue.code == "TRAILING_WHITESPACE":
                idx = issue.line - 1
                original   = lines[idx]
                lines[idx] = lines[idx].rstrip() + "\n"
                
                if lines[idx] != original:
                    applied.append(
                        f"Line {issue.line}: Removed trailing whitespace"
                    )
            
            # ─── Fix Bare Except ─────────────────────
            elif issue.code == "BARE_EXCEPT":
                idx = issue.line - 1
                
                if "except:" in lines[idx]:
                    lines[idx] = lines[idx].replace(
                        "except:", "except Exception as e:"
                    )
                    applied.append(
                        f"Line {issue.line}: "
                        f"Changed bare 'except:' to 'except Exception as e:'"
                    )
            
            # ─── Fix Unused Import ───────────────────
            elif issue.code == "UNUSED_IMPORT":
                idx = issue.line - 1
                lines[idx] = ""
                applied.append(
                    f"Line {issue.line}: Removed unused import"
                )
        
        return "".join(lines), applied


# ╔══════════════════════════════════════════════════════════╗
# ║                PROJECT ANALYZER                         ║
# ║  Scans entire directories of Python files               ║
# ╚══════════════════════════════════════════════════════════╝

class ProjectAnalyzer:
    """
    Analyzes all Python files in a directory.
    Can scan a whole project at once.
    """
    
    def __init__(self, analyzer: CodeAnalyzer, fixer: AutoFixer):
        self.analyzer     = analyzer
        self.fixer        = fixer
        self.total_files  = 0
        self.total_issues = 0
        self.total_fixes  = 0
    
    
    def scan_directory(
        self,
        directory: str,
        pattern: str = "*.py",
        exclude_patterns: Optional[List[str]] = None
    ) -> dict:
        """
        Scan all Python files in a directory.
        
        Args:
            directory: The folder to scan
            pattern: File pattern to look for (default: *.py)
            exclude_patterns: Files/folders to skip
        
        Returns:
            Dictionary with results for each file
        """
        
        # Default folders/files to skip
        if exclude_patterns is None:
            exclude_patterns = [
                '*_improved.py',
                '__pycache__/*',
                'venv/*',
                '.git/*',
                '.env/*',
                'build/*',
                'dist/*',
            ]
        
        results = {}
        root_path = Path(directory)
        
        # Find all matching files
        all_files = list(root_path.rglob(pattern))
        
        # Filter out files that should be skipped
        files_to_scan = []
        for file in all_files:
            should_skip = False
            for exclude in exclude_patterns:
                try:
                    rel_path = str(file.relative_to(root_path))
                    if fnmatch.fnmatch(rel_path, exclude):
                        should_skip = True
                        break
                except ValueError:
                    # File is not relative to root_path, skip it
                    should_skip = True
                    break
            
            if not should_skip:
                files_to_scan.append(file)
        
        
        # ─── Print Header ──────────────────────────
        
        print(f"\n{'='*60}")
        print(f"  SCANNING PROJECT: {directory}")
        print(f"  Found {len(files_to_scan)} Python files to check")
        print(f"  Autocorrect: {'ON' if AUTOCORRECT_ENABLED else 'OFF'}")
        print(f"{'='*60}")
        
        
        # ─── Scan Each File ────────────────────────
        
        for i, file_path in enumerate(files_to_scan, 1):
            rel_path = file_path.relative_to(root_path)
            
            print(f"\n[{i}/{len(files_to_scan)}] {rel_path}")
            print("-" * 40)
            
            try:
                # Read and analyze the file
                source = file_path.read_text(encoding="utf-8")
                issues = self.analyzer.analyze(source)
                
                self.total_files  += 1
                self.total_issues += len(issues)
                
                applied     = []
                fixed_source = None
                
                # Apply fixes if enabled
                if AUTOCORRECT_ENABLED and issues:
                    fixed_source, applied = self.fixer.fix(source, issues)
                    self.total_fixes += len(applied)
                    
                    # Save improved version if fixes were applied
                    if applied:
                        improved_path = (
                            file_path.parent / 
                            f"{file_path.stem}_improved{file_path.suffix}"
                        )
                        improved_path.write_text(fixed_source)
                
                # Store results
                results[str(rel_path)] = {
                    'issues': len(issues),
                    'fixes':  len(applied),
                    'details': issues
                }
                
                # Show summary for this file
                if issues:
                    print(f"  Found {len(issues)} issue(s)")
                    if applied:
                        print(f"  Fixed {len(applied)} issue(s) automatically")
                        print(f"  Saved improved version to: {improved_path}")
                    
                    # Show each issue
                    for issue in issues:
                        print(issue)
                else:
                    print(f"  No issues found - file looks clean")
                
            except Exception as error:
                print(f"  Error scanning file: {error}")
                results[str(rel_path)] = {
                    'issues': 0,
                    'fixes':  0,
                    'error':  str(error)
                }
        
        return results
    
    
    def print_summary(self):
        """Print a final summary of the entire project scan."""
        
        print(f"\n{'='*60}")
        print(f"  PROJECT SCAN COMPLETE")
        print(f"{'='*60}")
        print(f"  Files scanned:     {self.total_files}")
        print(f"  Issues found:      {self.total_issues}")
        print(f"  Auto-fixes applied: {self.total_fixes}")
        print(f"  Issues remaining:  {self.total_issues - self.total_fixes}")
        print(f"{'='*60}\n")


# ╔══════════════════════════════════════════════════════════╗
# ║                    REPORTER                             ║
# ║  Formats and displays results to the console            ║
# ╚══════════════════════════════════════════════════════════╝

def report(
    source_path: str,
    issues: List[CodeIssue],
    fixed_source: Optional[str],
    applied: List[str]
):
    """Print results of a single file scan."""
    
    print(f"\n{'='*60}")
    print(f"  FILE ANALYSIS: {source_path}")
    print(f"  Autocorrect: {'ON' if AUTOCORRECT_ENABLED else 'OFF'}")
    print(f"{'='*60}")

    if not issues:
        print("\n  No issues found. Code looks clean.")
    else:
        print(f"\n  Found {len(issues)} issue(s):")
        for issue in issues:
            print(issue)
            print()

    if AUTOCORRECT_ENABLED:
        if applied:
            print(f"\n{'-'*40}")
            print("  FIXES APPLIED:")
            for fix in applied:
                print(f"    {fix}")
            
            # Save the improved file
            out_path = source_path.replace(".py", "_improved.py")
            Path(out_path).write_text(fixed_source)
            print(f"\n  Improved file saved to: {out_path}")
        else:
            print("\n  No auto-fixable issues found - nothing changed.")
    else:
        fixable_count = sum(1 for issue in issues if issue.fixable)
        if fixable_count:
            print(f"\n{'-'*40}")
            print(f"  {fixable_count} issue(s) could be fixed automatically.")
            print("  Set AUTOCORRECT_ENABLED = True to apply them.")

    print(f"\n{'='*60}\n")


# ╔══════════════════════════════════════════════════════════╗
# ║              SINGLE FILE PROCESSING                     ║
# ║  Runs the analyzer on a single Python file              ║
# ╚══════════════════════════════════════════════════════════╝

def run(file_path: str):
    """Analyze and optionally fix a single Python file."""
    
    source = Path(file_path).read_text(encoding="utf-8")

    analyzer = CodeAnalyzer()
    issues   = analyzer.analyze(source)

    fixed_source = None
    applied      = []

    if AUTOCORRECT_ENABLED:
        fixer        = AutoFixer()
        fixed_source, applied = fixer.fix(source, issues)

    report(file_path, issues, fixed_source, applied)


# ╔══════════════════════════════════════════════════════════╗
# ║                    MAIN PROGRAM                         ║
# ║  Entry point - decides what mode to run in              ║
# ╚══════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    import sys
    
    
    # ─────────────────────────────────────────────
    #  MODE 1: No arguments - run built-in demo
    # ─────────────────────────────────────────────
    
    if len(sys.argv) < 2:
        
        # Demo code with intentional problems
        demo_code = textwrap.dedent("""\
            import os
            import json

            def greet(name, tags=[]):
                try:
                    print("Hello " + name)
                except:
                    pass
            
            greet("Everett")   
        """)

        demo_path = "/tmp/demo_target.py"
        Path(demo_path).write_text(demo_code)
        
        print("\n" + "="*60)
        print("  DEMO MODE - Analyzing built-in sample code")
        print("  To scan your own code:")
        print("    python self_improver.py my_script.py")
        print("    python self_improver.py ./my_project")
        print("="*60 + "\n")
        
        run(demo_path)
    
    
    # ─────────────────────────────────────────────
    #  MODE 2: File or directory argument
    # ─────────────────────────────────────────────
    
    else:
        target = sys.argv[1]
        target_path = Path(target)
        
        # Check if target is a directory
        if target_path.is_dir():
            
            print(f"\n  Scanning project directory: {target_path}\n")
            
            analyzer = CodeAnalyzer()
            fixer    = AutoFixer()
            project  = ProjectAnalyzer(analyzer, fixer)
            
            results = project.scan_directory(target)
            project.print_summary()
        
        
        # Check if target is a file
        elif target_path.is_file():
            run(target)
        
        
        # Target doesn't exist
        else:
            print(f"\n  ERROR: '{target}' is not a valid file or directory.\n")
