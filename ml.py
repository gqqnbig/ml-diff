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
NUM_LABELS = 2
MAX_LINE_LENGTH = 200
MAX_LINES = 100


def getLabel(file):
	if 'add' in file.name:
		return [1, 0]
	# labels.append('add')
	elif 'delete' in file.name:
		return [0, 1]
	elif 'remove' in file.name:
		return [0, 1]
	elif 'both' in file.name:
		# continue
		return [1, 1]

	raise Exception('Label not found')


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


def loadData(folder):
	data = []
	labels = []
	vocaburary = set()
	vocaburary.add(0)

	max_line_length = 0
	for diff in os.scandir(folder):
		if diff.is_dir() or not diff.name.endswith('.diff'):
			continue

		with open(diff.path, 'r', encoding='utf-8') as f:
			# 抛弃开头5行
			# for i in range(5):
			# 	f.readline()

			# sample = f.read()
			lines = f.readlines()
			if len(lines) >= MAX_LINES:
				lines = lines[:MAX_LINES]

			if max_line_length < MAX_LINE_LENGTH:
				max_line_length = max(max_line_length, *[len(l) for l in lines])

		# sample = [ord(c) for c in sample]

		# lineCount = len(sample) // 22
		# assert len(sample) % 22 == 0, '输入必须是22的倍数，因为一行有22个字符。'
		#
		# for i in range(lineCount):
		# 	assert sample[i * 22 + 21] == ord('\n')

		# 只看第一个字符
		# firstColumn = [sample[i * 22] for i in list(range(lineCount))]
		# sample = firstColumn

		labels.append(getLabel(diff))

		# print([mapIndexToChar(c) for c in sample])
		data.append(lines)
	# vocaburary.update(set(sample))

	if max_line_length > MAX_LINE_LENGTH:
		max_line_length = MAX_LINE_LENGTH

	data = [''.join([cutAndPadLine(l, max_line_length) for l in lines]) for lines in data]
	print(f'{choppedLines} lines are longer than max lingth {MAX_LINE_LENGTH}, chopped.')

	# 确保data中每个sample长度相同
	featureSize = max([len(sample) for sample in data])
	for i in range(len(data)):
		if len(data[i]) < featureSize:
			data[i] += (' ' * (featureSize - len(data[i])))
	# for sample in data:
	# 	assert len(sample) == featureSize
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
	return tf.data.Dataset.from_tensor_slices((data, labels))


if __name__ == '__main__':
	dataset = loadData(r'D:\renaming\data\real\NewPipe')
	# Follow the glossary of Google https://developers.google.com/machine-learning/glossary#example
	print(f'Dataset loaded. Each example has {dataset.element_spec[0].shape[0]} features and a label vector of size {dataset.element_spec[1].shape[0]}. ' +
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
