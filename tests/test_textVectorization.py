import os
import sys

import pytest

testFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testFolder + '/..')

import textVectorizationHelper


def test_splitPunctuation():
	res = textVectorizationHelper.custom_split('\n+public')
	res = res.numpy().astype(str).tolist()
	assert len(res) == 3


def test_split():
	input = 'let us try fn(n)=1+2=3'

	input = '\nhello  world\n'
	res = textVectorizationHelper.custom_split(input)

	res = res.numpy().astype(str).tolist()
	assert len(res) == 4
	for item in res:
		assert item[0] == '\n' or (item[0] != '\n' and item[-1] != '\n')
