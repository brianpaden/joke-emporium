#!/usr/bin/env python3
"""Script to automatically fix CLI integration tests to use file-based database fixture."""

import re
from pathlib import Path

def fix_test_signatures(content):
    """Update test method signatures to use cli_db_with_batch instead of staging_session, sample_import_batch."""
    # Pattern 1: (self, staging_session, sample_import_batch, tmp_path)
    content = re.sub(
        r'def (test_\w+)\(self, staging_session, sample_import_batch, tmp_path\):',
        r'def \1(self, cli_db_with_batch, tmp_path):',
        content
    )

    # Pattern 2: (self, staging_session, sample_import_batch)
    content = re.sub(
        r'def (test_\w+)\(self, staging_session, sample_import_batch\):',
        r'def \1(self, cli_db_with_batch, tmp_path):',
        content
    )

    return content

def add_fixture_extraction(content):
    """Add db_path and batch extraction at start of test methods."""
    lines = content.split('\n')
    result = []
    in_cli_test_class = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Track if we're in TestCLIApplyPolicies class
        if 'class TestCLIApplyPolicies' in line:
            in_cli_test_class = True
        elif line.startswith('class ') and 'TestCLIApplyPolicies' not in line:
            in_cli_test_class = False

        result.append(line)

        # If this is a test method using cli_db_with_batch
        if in_cli_test_class and re.match(r'\s+def test_\w+\(self, cli_db_with_batch', line):
            # Look ahead for the docstring
            i += 1
            if i < len(lines) and '"""' in lines[i]:
                result.append(lines[i])  # Add docstring
                i += 1
                # Add import statements
                result.append('        from click.testing import CliRunner')
                result.append('')
                # Check if we need to add staging import
                has_staging_import = False
                j = i
                while j < min(i + 20, len(lines)) and not lines[j].strip().startswith('def '):
                    if 'from joke_emporium.db.staging import' in lines[j]:
                        has_staging_import = True
                        break
                    j += 1

                if not has_staging_import:
                    result.append('        from joke_emporium.db.staging import get_staging_session')
                result.append('        from joke_emporium.importers.cli import cli')
                result.append('')
                result.append('        db_path = cli_db_with_batch["db_path"]')
                result.append('        batch = cli_db_with_batch["batch"]')
                result.append('')
                continue

        i += 1

    return '\n'.join(result)

def main():
    test_file = Path('tests/test_importers/test_policies.py')

    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    content = test_file.read_text(encoding='utf-8')

    # Step 1: Fix test signatures
    content = fix_test_signatures(content)

    # Step 2: Add fixture extraction (this is complex, so we'll do it manually)
    # content = add_fixture_extraction(content)

    # Write back
    test_file.write_text(content, encoding='utf-8')
    print(f"Updated {test_file}")
    print("Test signatures have been updated.")
    print("You'll need to manually:")
    print("1. Add db_path and batch extraction in each test")
    print("2. Replace sample_import_batch.id with batch.id")
    print("3. Replace sample_import_batch.import_id with batch.import_id")
    print("4. Replace staging_session with get_staging_session() context managers")
    print("5. Add --staging-db parameter to CLI invocations")

if __name__ == '__main__':
    main()
