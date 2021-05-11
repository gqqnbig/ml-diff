import os
import sys
import tensorflow as tf
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization

import pytest

testFolder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testFolder + '/..')

import textVectorizationHelper


def test_Vectorization():
	input = tf.constant('\n+public')
	dataset = tf.data.Dataset.from_tensor_slices([input]).batch(20)

	t = TextVectorization(split=textVectorizationHelper.custom_split, max_tokens=20, output_mode='int')
	t.adapt(dataset)
	v = t.get_vocabulary()
	assert '\n' in v
	assert 'public' in v


def test_splitTensor():
	input = tf.constant('\n+public')

	res = textVectorizationHelper.custom_split(input)

	res = res.numpy().astype(str).tolist()
	assert len(res) == 3


def test_splitPunctuation():
	res = textVectorizationHelper.custom_split('\n+public')
	res = res.numpy().astype(str).tolist()
	assert len(res) == 3


def test_split():
	input = 'let us try fn(n)=1+2=3'

	input = '\nhello  world\n'
	res = textVectorizationHelper.custom_split(input)

	res = res.numpy().astype(str).tolist()
	res = list(filter(lambda s: len(s) > 0, res))
	assert len(res) == 4
	for item in res:
		assert item[0] == '\n' or (item[0] != '\n' and item[-1] != '\n')
