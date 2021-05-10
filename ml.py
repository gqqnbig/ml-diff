#!/usr/bin/env python3

import logging
import os
import time

# disable tensorflow info log
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization

import sys
import subprocess

import helper
import textVectorizationHelper
import RepeatTimer

# vectorize_layer = TextVectorization(
# 	standardize=None,
# 	split=textVectorizationHelper.custom_split,
# 	# max_tokens=vocab_size,
# 	output_mode='int',
# 	output_sequence_length=100)
#
# vectorize_layer.adapt(['hello \n world'])
#
# print(vectorize_layer.get_vocabulary())
#
# exit()


try:
	tf.__version__
	# To fix progress bar, make each epoch update in-place.
	import ipykernel
except:
	pass


try:
	p = sys.argv.index('--log')
	logLevel = sys.argv[p + 1]
	numeric_level = getattr(logging, logLevel.upper(), None)
	logging.basicConfig(level=numeric_level)

	tf.get_logger().setLevel(logLevel)
except:
	pass


showProgress = '--no-progress' not in sys.argv

try:
	p = sys.argv.index('--size-limit-kb')
	MAX_FILE_SIZE_IN_KB = int(sys.argv[p + 1])
except:
	MAX_FILE_SIZE_IN_KB = 10

vocab_size = 20 * 1000
batch_size = 20
NUM_LABELS = 1

choppedLines = 0
maxSequenceLength = 0


def cutAndPadLine(line, length):
	global choppedLines
	l = len(line)
	if l < length:
		# assert line[-1] == '\n'
		# assert line[-2] != '\r'
		# line = line[:-1] + ' ' * (length - l) + line[-1]
		return line
	else:
		choppedLines += 1
		return line[:length]


def loadDataset(folder) -> tf.data.Dataset:
	"""

	:param folder:
	:return: shuffled dataset
	"""
	global maxSequenceLength

	inputFiles = sorted(helper.getDiffFiles(folder, MAX_FILE_SIZE_IN_KB))
	i = 0
	data = []
	maxSequenceLength = 0

	def reportProgress():
		print(f'Loading {i}/{len(inputFiles)}')

	timer = RepeatTimer.RepeatTimer(5, function=reportProgress)
	timer.start()
	while i < len(inputFiles):
		file = inputFiles[i]
		with open(file, 'r', encoding='utf-8') as f:
			content = f.read()
			assert content.startswith('@@'), f'diff, index, ---, +++ should be removed. File: {file}'
			split = textVectorizationHelper.split(textVectorizationHelper.standardize(content))
			maxSequenceLength = max(maxSequenceLength, len(split))
			data.append(' '.join(split))

		i += 1
	timer.cancel()

	# vectorize_layer = TextVectorization(
	# 	standardize=None,
	# 	split=textVectorizationHelper.custom_split,
	# 	# max_tokens=vocab_size,
	# 	output_mode='int',
	# 	output_sequence_length=100)
	#
	# vectorize_layer.adapt(['hello world'])
	#
	# print(vectorize_layer.get_vocabulary())
	#
	# exit()

	labels = [helper.getLabel(f) for f in inputFiles]
	# import timeit
	# print(f"convert_as_int32 numpy_array: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data, dtype=np.int32), tf.int32)).timeit(1)} s")
	# print(f"convert_as_numpy_array (fastest!): {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data), tf.int32)).timeit(1)} s")
	# print(f"convert_as_numpy_array no hint: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data))).timeit(1)} s")
	# print(f"convert_as_list: {timeit.Timer(lambda: tf.convert_to_tensor(data, tf.int32)).timeit(1)} s")
	# exit()

	print('data loaded. Converting to tensor...', flush=True)
	# data = np.asarray(data)
	data = tf.ragged.constant(data)
	# assert data.shape[1] == featureSize
	# todo: 用 tf.RaggedTensor
	dataset = tf.data.Dataset.from_tensor_slices((data, labels, inputFiles))

	if logging.root.level <= logging.DEBUG:
		timeStart = time.time()

	# We don't have to cache from_tensor_slices

	yesExamples = dataset.filter(lambda *d: d[1] == 1).cache()
	noExamples = dataset.filter(lambda *d: d[1] == 0).cache()


	yesLength = len(list(yesExamples))
	noLength = len(list(noExamples))
	assert yesLength > 0 and noLength > 0
	print(f'There are {yesLength} yes examples, and {noLength} no examples.', flush=True)

	if yesLength > noLength * 1.1 or noLength > yesLength * 1.1:
		count = min(yesLength, noLength)
		yesExamples = yesExamples.shuffle(yesLength).take(count)
		noExamples = noExamples.shuffle(noLength).take(count)
		print(f'Rebalance to {count} yes and {count} no examples.')

		dataset = yesExamples.concatenate(noExamples).shuffle(count * 2)
	else:
		dataset = dataset.shuffle(yesLength + noLength)

	if logging.root.level <= logging.DEBUG:
		l = len(list(dataset))
		timeEnd = time.time()
		logging.debug(f'Loading {l} data used {timeEnd - timeStart}s')
	return dataset


def trainModel(sequence_length, train_data, test_data):
	"""

	:param train_data: must be batched
	:param test_data: must be batched
	:return:
	"""

	assert len(train_data.element_spec) == len(test_data.element_spec), 'train_data and test_data must have the same components.'
	for i in range(len(train_data.element_spec)):
		# ragged tensor may not have shape.
		if isinstance(train_data.element_spec[0], tf.RaggedTensorSpec) == False:
			assert train_data.element_spec[i].shape.ndims == test_data.element_spec[i].shape.ndims, \
				f'The shape of component {i} does not match.\ntrain_data.element_spec[{i}].shape={train_data.element_spec[i].shape}\ntest_data.element_spec[{i}].shape={test_data.element_spec[i].shape}'
	if len(train_data.element_spec) == 3:
		assert train_data.element_spec[2].dtype != tf.string, 'If dataset has 3 components, the last one must be sample weights of type int32.'

	try:
		version = subprocess.check_output(['git', 'describe', '--always', '--dirty'], cwd=os.path.dirname(os.path.abspath(__file__)))
		version = version.decode("utf-8").strip()
	except Exception as e:
		logging.error('Unable to determine code version from git. ' + str(e))
		version = "unknown"
	modelPath = os.path.join('SavedModels', version)

	if helper.loadModelFromDisk(modelPath):
		model = tf.keras.models.load_model(modelPath)
	else:
		if __debug__:
			str_data = helper.getColumn(train_data, 0).concatenate(helper.getColumn(test_data, 0))
			testTextVectorization(str_data, standardize=None,
								  split=textVectorizationHelper.custom_split,
								  output_mode='int',
								  output_sequence_length=sequence_length)

		vectorize_layer = TextVectorization(
			standardize=None,
			split=textVectorizationHelper.custom_split,
			ngrams=2,
			max_tokens=vocab_size,
			output_mode='int',
			# I use train_data plus test_data to adapt the vectorization layer.
			# If I don't set output_sequence_length, the layer will infer from train_data plus test_data.
			# However when training, the layer will infer output_sequence_length again, which may cause
			# mismatch.
			output_sequence_length=sequence_length)

		vectorize_layer.adapt(helper.getColumn(train_data, 0))
		# vocabulary = vectorize_layer.get_vocabulary()

		# a=vectorize_layer.__call__(train_data)
		# a=tf.keras.layers.Embedding(vocab_size, embedding_dim).__call__(a)

		embedding_dim = 16

		model = tf.keras.Sequential()
		model.add(vectorize_layer)
		model.add(tf.keras.layers.Embedding(vocab_size, embedding_dim))
		model.add(tf.keras.layers.Flatten())
		model.add(tf.keras.layers.Dense(100, activation='relu'))
		model.add(tf.keras.layers.Dense(10, activation='relu'))
		model.add(tf.keras.layers.Dense(2, activation='softmax'))

		if __debug__:
			y_pred = model.predict(helper.getColumn(train_data, 0))
			assert len(y_pred.shape) == 2, \
				'The prediction should have 2 dimensions. The first dimension is the number of examples; the second one is 2, indicating a probability distribution.'

		model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['sparse_categorical_accuracy'], run_eagerly=sys.flags.optimize > 0)

		num_epochs = 20
		model.fit(train_data, validation_data=test_data, epochs=num_epochs, verbose=1 if showProgress else 2,
				  callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_sparse_categorical_accuracy', patience=5, restore_best_weights=True)])

		model.summary()
		model.save(modelPath)

	return model


def testTextVectorization(str_data, **kwargs):
	# looks like kwargs is pass by value
	if 'ngrams' in kwargs:
		del kwargs['ngrams']

	vectorize_layer = TextVectorization(**kwargs, ngrams=1)
	vectorize_layer.adapt(str_data)
	vocabulary = vectorize_layer.get_vocabulary()

	# if tf.__version__.startswith('2.1'):
	#   assert isinstance(vocabulary[0], bytes), 'The type of elements in vocabulary is bytes.'
	# if tf.__version__.startswith('2.3'):
	#   assert isinstance(vocabulary[0], str), 'The type of elements in vocabulary is string.'

	assert '\n' in vocabulary, f'vocabulary={vocabulary[:100]}'
	assert textVectorizationHelper.wordContinuation in vocabulary
	assert len(list(filter(lambda s: len(s) > 1 and (s[0] == '\n' or s[-1] == '\n'), vocabulary))) == 0, \
		r'No token should start with or end with \n.'
	print(f'Without capping, the 1-gram vocabulary size is {len(vocabulary)}.')
	vectorize_layer = TextVectorization(**kwargs, ngrams=2)
	vectorize_layer.adapt(str_data)
	print(f'Without capping, the 2-gram vocabulary size is {len(vectorize_layer.get_vocabulary())}.')


usage = f'{os.path.basename(sys.argv[0])} dataset-folder'

if __name__ == '__main__':
	if len(sys.argv) <= 1:
		print('You have to specify dataset folder.\n\n' + usage, file=sys.stderr)
		exit(1)

	print(f'tensorflow version is {tf.__version__}.')
	if tf.__version__.startswith('2.3') == False:
		logging.warning(f'This program is expected to run on Tensorflow 2.3. It may not work on {tf.__version__}.')

	if len(tf.config.list_physical_devices('GPU')) == 0:
		logging.warning('GPU not available!')

	tf.random.set_seed(977)

	dataset = loadDataset(sys.argv[-1])
	# Follow the glossary of Google https://developers.google.com/machine-learning/glossary#example
	print('Dataset loaded.')
	if isinstance(dataset.element_spec[0], tf.RaggedTensorSpec):
		print(f'Each example has feature of variable length and a label of {dataset.element_spec[1].dtype.name}.', flush=True)
		print('Model will further process the features.')
	elif len(dataset.element_spec[0].shape) == 0:
		print(f'Each example has feature of {dataset.element_spec[0].dtype.name} and a label of {dataset.element_spec[1].dtype.name}.', flush=True)
	else:
		print(f'Each example has {dataset.element_spec[0].shape[0]} features and a label of {dataset.element_spec[1].dtype.name}.', flush=True)

	length = len(list(dataset))
	assert length > 0, 'Dataset length is incorrect.'

	print(f'Max sequence length is {maxSequenceLength}.')

	# featureSize = len(list(dataset.take(1))[0][0])
	# maxEncoding = max([d[0].numpy().max().item() for d in dataset])
	# print(f'Max encoding is {maxEncoding}.', flush=True)
	#
	# print(f'The required memory to fit the dataset is about {length * dataset.element_spec[0].shape[0] * maxEncoding / 1024 / 1024 / 1024 * dataset.element_spec[0].dtype.size :.2f} GB.', flush=True)
	#
	# dataset = dataset.map(lambda x, y, filePath: (tf.one_hot(x, maxEncoding), y, filePath)).cache()
	dataset = dataset.cache()

	if __debug__:
		a = list(dataset)[0]
		b = list(dataset)[0]
		assert len(a) == len(b)
		assert all((a[i] == b[i]).numpy().all() for i in range(len(a))), 'dataset is not stable. It should return deterministic elements. You need to call cache after shuffle.'

	train_length = int(length / 5 * 4)

	# train data don't need file path
	train_data = dataset.take(train_length)
	test_data = dataset.skip(train_length)
	test_length = len(list(test_data))
	print(f"After shuffling the examples, let's use {len(list(train_data))} examples for training, {test_length} for testing.", flush=True)

	logging.info(f'test_data[0]: {list(test_data)[0]}')

	a = train_data.shuffle(train_length, reshuffle_each_iteration=True).batch(batch_size).map(lambda x, y, filePath: (x, y))
	b = test_data.shuffle(test_length, reshuffle_each_iteration=True).batch(batch_size).map(lambda x, y, filePath: (x, y))
	model = trainModel(maxSequenceLength, a, b)

	# batch size in predict/evaluate is irrelevant to the one in fit.
	predictions = model.predict_classes(helper.getColumn(test_data, 0).batch(batch_size))
	actuals = helper.getColumn(test_data, 1)
	incorrectPredictions = zip(predictions, actuals, helper.getColumn(test_data, 2))
	incorrectPredictions = map(lambda x: (int(x[0]), x[1].numpy(), x[2].numpy().decode()), incorrectPredictions)
	incorrectPredictions = filter(lambda x: x[0] != x[1], incorrectPredictions)
	incorrectPredictions = sorted(incorrectPredictions, key=lambda x: x[2])

	cm = tf.math.confusion_matrix(tf.convert_to_tensor(list(actuals)), predictions)
	print(f'Confusion matrix:\n{cm}\nFalse Positive={cm[1][0]}/{test_length}={cm[1][0] / test_length :.2f} (Actual is no, prediction is yes)')

	if logging.root.level <= logging.INFO:
		for prediction, actual, path in incorrectPredictions:
			logging.info(f'{path}: actual={actual}, prediction={prediction}')
	print(f'Total incorrect prediction is {len(incorrectPredictions)}. predict_classes accuracy is {1 - len(incorrectPredictions) / test_length :.4f}.')
