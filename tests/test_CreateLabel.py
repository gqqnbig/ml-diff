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

		result = CreateLabel.createLabels(diff.path)
		parts = os.path.splitext(diff.name)[0].split('-')

		description = parts[0]
		if len(parts) > 1:
			oldName = parts[1]
			newName = parts[2]

			assert result != None and result[oldName] == newName, f'Case {description} failed.'
		else:
			if result is not None:
				pytest.fail(f'Fail to identify "{description}" as not renaming. Actual: {result}')


def testGetWord():
	assert 'a' == CreateLabel.getWord('a', 0)
	assert 'a' == CreateLabel.getWord('a', 1)
