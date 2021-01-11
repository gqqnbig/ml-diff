import timeit

import tensorflow as tf

import os
import sys
import numpy as np

try:
	tf.__version__
	# To fix progress bar, make each epoch update in-place.
	import ipykernel
except:
	pass

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
	for diff in os.listdir(folder):
		if diff.startswith('.'):
			continue
		fullPath = os.path.join(folder, diff)
		if os.path.isdir(fullPath):
			yield from getDiffFiles(fullPath)
		if diff.endswith('.diff'):
			yield fullPath


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

	# print(f"convert_as_int32 numpy_array: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data, dtype=np.int32), tf.int32)).timeit(1)} s")
	# print(f"convert_as_numpy_array: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data), tf.int32)).timeit(1)} s")
	# print(f"convert_as_numpy_array no hint: {timeit.Timer(lambda : tf.convert_to_tensor(np.asarray(data))).timeit(1)} s")
	# print(f"convert_as_list: {timeit.Timer(lambda: tf.convert_to_tensor(data, tf.int32)).timeit(1)} s")

	data = np.asarray(data, np.int32)
	data = tf.convert_to_tensor(data, tf.int32)
	# assert data.shape[1] == featureSize
	# todo: 用 tf.RaggedTensor
	labels = [getLabel(f) for f in inputFiles]
	dataset = tf.data.Dataset.from_tensor_slices((data, labels))
	# dataset = dataset.map(lambda f: (tf.io.read_file(f), getLabel(f.numpy())))

	print(f'There are {len(list(filter(lambda d: d[1] == 1, dataset)))} yes examples, and {len(list(filter(lambda d: d[1] == 0, dataset)))} no examples.')
	return dataset


if __name__ == '__main__':
	dataset = loadDataset(r'D:\renaming\data\generated\dataset')
	# Follow the glossary of Google https://developers.google.com/machine-learning/glossary#example
	print(f'Dataset loaded. Each example has {dataset.element_spec[0].shape[0]} features and a {dataset.element_spec[1].dtype.name} label. ' +
		  'However, without evaluating the dataset, it\'s unclear the total number of examples in this dataset.')

	length = tf.data.experimental.cardinality(dataset).numpy()
	print(f"Let's eagerly evaluate the dataset, we find out there are {length} examples.")

	maxEncoding = max([d[0].numpy().max() for d in dataset])
	print(f'Max encoding is {maxEncoding}.')

	print(f'The required memory to fit the dataset is about {length * dataset.element_spec[0].shape[0] * maxEncoding / 1024 / 1024 / 1024 * dataset.element_spec[0].dtype.size :.2f} GB.')

	dataset = dataset.map(lambda x, y: (tf.one_hot(x, maxEncoding), y))

	dataset = dataset.shuffle(length)
	train_length = int(length / 5 * 4)
	train_data = dataset.take(train_length)
	test_data = dataset.skip(train_length)
	print(f"After shuffling the examples, let's use {tf.data.experimental.cardinality(train_data).numpy()} examples for training, {tf.data.experimental.cardinality(test_data).numpy()} for testing.")

	train_data = train_data.batch(batch_size)
	test_data = test_data.batch(batch_size)

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

	test_example = list(dataset.skip(5).take(1))[0]
	# predict, as the same as fit, must take batches. Therefore, we must add a new dimension to the extracted features.
	prediction = model.predict(tf.expand_dims(test_example[0], 0))[0]
	prediction = tf.where(prediction > 0.5, tf.ones_like(prediction, tf.int32), tf.zeros_like(prediction, tf.int32)).numpy()
	print(f'prediction={prediction}, actual={test_example[1]}')
