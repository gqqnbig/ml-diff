import os
import sys

import pytest

testFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testFolder + '/..')

import CreateLabel


def testIsIdentifierRenaming():
	for diff in os.scandir(os.path.join(testFolder, 'Test Cases')):
		if diff.is_dir() or not diff.name.endswith('.diff'):
			continue

		result = CreateLabel.isIdentifierRenaming(diff.path)
		if result is None:
			pytest.fail(f'Fail to find renaming in {diff.name}')

		renamingMappings = result[1]
		parts = diff.name.split('-')

		description = parts[0]
		oldName = parts[1]
		newName = parts[2]

		assert oldName in renamingMappings, f'Case {description} failed.'
