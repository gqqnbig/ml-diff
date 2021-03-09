#!/usr/bin/env python3

import os

# disable tensorflow info log
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf

import sys
import numpy as np

try:
	tf.__version__
	# To fix progress bar, make each epoch update in-place.
	import ipykernel
except:
	pass

MAX_FILE_SIZE_IN_KB = 10
num_hiddens = 256
vocab_size = 126 - 32 + 1
lr = 1e2
clipping_theta = 1e-2
batch_size = 20
NUM_LABELS = 1
MAX_LINE_LENGTH = 200
MAX_LINES = 100


def getLabel(file):
	file = os.path.normpath(file)
	components = file.split(os.sep)
	if components[-2] == 'yes':
		return 1
	elif components[-2] == 'no':
		return 0

	raise Exception(f'Label not found for file {file}')


choppedLines = 0


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


def getDiffFiles(folder):
	for diff in os.scandir(folder):

		if diff.name.startswith('.'):
			continue

		# fullPath = os.path.join(folder, diff)
		if diff.is_dir():
			yield from getDiffFiles(diff.path)
		if diff.name.endswith('.diff') and diff.stat().st_size <= MAX_FILE_SIZE_IN_KB * 1024:
			yield diff.path


def loadDataset(folder):
	vocaburary = set()
	vocaburary.add(0)

	max_line_length = 0

	inputFiles = sorted(getDiffFiles(folder))
	data = []
	for file in inputFiles:
		with open(file, 'r', encoding='utf-8') as f:
			# 抛弃开头5行
			# for i in range(5):
			# 	f.readline()

			# sample = f.read()
			data.append(f.read())
		# if len(lines) >= MAX_LINES:
		# 	lines = lines[:MAX_LINES]

		# if max_line_length < MAX_LINE_LENGTH:
		# 	max_line_length = max(max_line_length, *[len(l) for l in lines])

	# 确保data中每个sample长度相同
	featureSize = max([len(sample) for sample in data])
	for i in range(len(data)):
		if len(data[i]) < featureSize:
			data[i] += (' ' * (featureSize - len(data[i])))
	for example in data:
		vocaburary.update(set(example))

	conversionDict = {v: i for i, v in enumerate(list(vocaburary))}
	assert conversionDict[0] == 0
	data = [[conversionDict[c] for c in example] for example in data]

	labels = [getLabel(f) for f in inputFiles]
	# import timeit
	# print(f"convert_as_int32 numpy_array: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data, dtype=np.int32), tf.int32)).timeit(1)} s")
	# print(f"convert_as_numpy_array (fastest!): {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data), tf.int32)).timeit(1)} s")
	# print(f"convert_as_numpy_array no hint: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data))).timeit(1)} s")
	# print(f"convert_as_list: {timeit.Timer(lambda: tf.convert_to_tensor(data, tf.int32)).timeit(1)} s")
	# exit()

	print('data loaded. Converting to tensor...', flush=True)
	data = np.asarray(data, np.int32)
	data = tf.convert_to_tensor(data, tf.int32)
	# assert data.shape[1] == featureSize
	# todo: 用 tf.RaggedTensor
	dataset = tf.data.Dataset.from_tensor_slices((data, labels, inputFiles))
	# dataset = dataset.map(lambda f: (tf.io.read_file(f), getLabel(f.numpy())))

	print(f'There are {len(list(filter(lambda d: d[1] == 1, dataset)))} yes examples, and {len(list(filter(lambda d: d[1] == 0, dataset)))} no examples.', flush=True)
	return dataset


def getColumn(ds: tf.data.Dataset, index):
	return ds.map(lambda *d: d[index])


def trainModel(train_data, test_data):
	"""

	:param train_data: must be batched
	:param test_data: must be batched
	:return:
	"""

	assert len(train_data.element_spec) == len(test_data.element_spec), 'train_data and test_data must have the same components.'
	for i in range(len(train_data.element_spec)):
		assert train_data.element_spec[i].shape.ndims == test_data.element_spec[i].shape.ndims, \
			f'The shape of component {i} does not match.\ntrain_data.element_spec[{i}].shape={train_data.element_spec[i].shape}\ntest_data.element_spec[{i}].shape={test_data.element_spec[i].shape}'
	if len(train_data.element_spec) == 3:
		assert train_data.element_spec[2].dtype != tf.string, 'If dataset has 3 components, the last one must be sample weights of type int32.'

	savedModel = 'model.save'
	if os.path.exists(savedModel):
		print('Model loaded', flush=True)
		model = tf.keras.models.load_model(savedModel)
	else:
		model = tf.keras.Sequential()
		model.add(tf.keras.layers.Flatten())
		model.add(tf.keras.layers.Dense(maxEncoding, activation='relu'))
		model.add(tf.keras.layers.Dense(100, activation='relu'))
		model.add(tf.keras.layers.Dense(10, activation='relu'))
		model.add(tf.keras.layers.Dense(NUM_LABELS, activation='sigmoid'))

		model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'], run_eagerly=sys.flags.optimize > 0)
		# model.summary()

		num_epochs = 50
		model.fit(train_data, validation_data=test_data, epochs=num_epochs, callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=5)])
		model.save('model.save')

	return model


usage = f'{os.path.basename(sys.argv[0])} dataset-folder'

if __name__ == '__main__':
	if len(sys.argv) <= 1:
		print('You have to specify dataset folder.\n\n' + usage, file=sys.stderr)
		exit(1)

	dataset = loadDataset(sys.argv[1])
	# Follow the glossary of Google https://developers.google.com/machine-learning/glossary#example
	print(f'Dataset loaded. Each example has {dataset.element_spec[0].shape[0]} features and a {dataset.element_spec[1].dtype.name} label. ' +
		  'However, without evaluating the dataset, it\'s unclear the total number of examples in this dataset.', flush=True)

	length = tf.data.experimental.cardinality(dataset).numpy()
	print(f"Let's eagerly evaluate the dataset, we find out there are {length} examples.", flush=True)

	maxEncoding = max([d[0].numpy().max() for d in dataset])
	print(f'Max encoding is {maxEncoding}.', flush=True)

	print(f'The required memory to fit the dataset is about {length * dataset.element_spec[0].shape[0] * maxEncoding / 1024 / 1024 / 1024 * dataset.element_spec[0].dtype.size :.2f} GB.', flush=True)

	dataset = dataset.shuffle(length).map(lambda x, y, filePath: (tf.one_hot(x, maxEncoding), y, filePath)).cache()

	if __debug__:
		a = list(dataset)[0]
		b = list(dataset)[0]
		assert len(a) == len(b)
		assert all((a[i] == b[i]).numpy().all() for i in range(len(a))), 'dataset is not stable. It should return deterministic elements.'

	train_length = int(length / 5 * 4)

	# train data don't need file path
	train_data = dataset.take(train_length)
	test_data = dataset.skip(train_length)
	print(f"After shuffling the examples, let's use {tf.data.experimental.cardinality(train_data).numpy()} examples for training, {tf.data.experimental.cardinality(test_data).numpy()} for testing.", flush=True)

	a = train_data.batch(batch_size).map(lambda x, y, filePath: (x, y))
	b = test_data.batch(batch_size).map(lambda x, y, filePath: (x, y))
	model = trainModel(a, b)

	predictions = model.predict_classes(getColumn(test_data, 0).batch(batch_size))
	incorrectPredictions = zip(predictions, getColumn(test_data, 1), getColumn(test_data, 2))
	incorrectPredictions = map(lambda x: (int(x[0]), x[1].numpy(), x[2].numpy().decode()), incorrectPredictions)
	incorrectPredictions = filter(lambda x: x[0] != x[1], incorrectPredictions)
	incorrectPredictions = sorted(incorrectPredictions, key=lambda x: x[2])

	for prediction, actual, path in incorrectPredictions:
		print(f'{path}: actual={actual}, prediction={prediction}')
	print(f'Total incorrect prediction is {len(incorrectPredictions)}. predict_classes accuracy is {1 - len(incorrectPredictions) / tf.data.experimental.cardinality(test_data).numpy() :.4f}.')
