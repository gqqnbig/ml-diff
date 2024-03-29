import os
import sys

import pytest

testFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testFolder + '/..')

import textVectorizationHelper


def test_split():
	input = 'let us try fn(n)=1+2=3'

	input = '\nhello\nworld\n'
	res = textVectorizationHelper.split(input)
	assert len(res) == 5
	for item in res:
		assert item[0] == '\n' or (item[0] != '\n' and item[-1] != '\n')
