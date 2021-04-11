import tensorflow as tf

import re
import string


def custom_standardization(input_data: tf.Tensor):
	assert input_data.dtype.name == 'string'
	# lowercase = tf.strings.lower(input_data)
	return tf.strings.regex_replace(input_data, r'\b\d+(\.\d*)?\b', '1')


# return tf.strings.regex_replace(stripped_html, '[%s]' % re.escape(string.punctuation), '')


@tf.keras.utils.register_keras_serializable()
def custom_split(input_data: tf.Tensor):
	return tf.strings.split(input_data, ' ')


def standardize(input: str):
	return re.sub(r'\b\d+(\.\d*)?\b', '1', input)


# return tf.strings.regex_replace(input, , '1')


def split(input: str):
	"""
	split by space or punctuation

	:param input:
	:return:
	"""

	# removed underscore (_) from string.punctuation
	punctuation = r'!"#$%&\'()*+,-./:;<=>?@[\\]^`{|}~'
	es = re.escape(punctuation)

	result = re.split(r'(?:[ \t]+|(?=[\n' + es + '])|(?<=[\n' + es + ']))', input)
	return list(filter(lambda s: len(s) > 0, result))
