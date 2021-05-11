import tensorflow as tf

import re
import string


def custom_standardization(input_data: tf.Tensor):
	assert input_data.dtype.name == 'string'
	# lowercase = tf.strings.lower(input_data)
	return tf.strings.regex_replace(input_data, r'\b\d+(\.\d*)?\b', '1')


# return tf.strings.regex_replace(stripped_html, '[%s]' % re.escape(string.punctuation), '')


wordSep = '\uE701'


@tf.keras.utils.register_keras_serializable()
def custom_split(input_data: tf.Tensor):
	# removed underscore (_) from string.punctuation
	punctuation = r'!"#$%&\'()*+,-./:;<=>?@[\\]^`{|}~'
	es = re.escape(punctuation)

	input_data = tf.strings.regex_replace(input_data, r'[ \t]+', wordSep)

	input_data = tf.strings.regex_replace(input_data, rf'(.?)([\n{es}])', rf'\1{wordSep}\2')
	input_data = tf.strings.regex_replace(input_data, rf'([\n{es}])(.?)', rf'\1{wordSep}\2')
	ragged_data = tf.strings.split(input_data, wordSep)

	result = tf.ragged.boolean_mask(ragged_data, tf.map_fn(lambda x: x != '', ragged_data, fn_output_signature=tf.bool))
	return result


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
