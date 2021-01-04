import tensorflow as tf

import os
import sys

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


def getLabel(file):
	if 'add' in file.name:
		return [1, 0]
	# labels.append('add')
	elif 'delete' in file.name:
		return [0, 1]
	# labels.append('delete')
	elif 'both' in file.name:
		# continue
		return [1, 1]

	raise Exception('Label not found')



def loadData(folder):
	data = []
	labels = []
	for diff in os.scandir(folder):
		if diff.is_dir() or not diff.name.endswith('.diff'):
			continue

		with open(diff.path, 'r') as f:
			# 抛弃开头5行
			for i in range(5):
				f.readline()

			sample = f.read()
		# lines = f.readlines()

		sample = [ord(c) for c in sample]

		lineCount = len(sample) // 22
		assert len(sample) % 22 == 0, '输入必须是22的倍数，因为一行有22个字符。'

		for i in range(lineCount):
			assert sample[i * 22 + 21] == ord('\n')

		# 只看第一个字符
		# firstColumn = [sample[i * 22] for i in list(range(lineCount))]
		# sample = firstColumn

		labels.append(getLabel(diff))

		# print([mapIndexToChar(c) for c in sample])
		data.append(sample)
	# 确保data中每个sample长度相同
	num_steps = max([len(sample) for sample in data])
	for i in range(len(data)):
		if len(data[i]) < num_steps:
			data[i].extend([0] * (num_steps - len(data[i])))
	for sample in data:
		assert len(sample) == num_steps
	data = tf.convert_to_tensor(data)
	assert data.shape[1] == num_steps
	# todo: 用 tf.RaggedTensor
	return tf.data.Dataset.from_tensor_slices((data, labels))


if __name__ == '__main__':
	dataset = loadData(r'D:\renaming\data\generated')
	# Follow the glossary of Google https://developers.google.com/machine-learning/glossary#example
	print(f'Dataset loaded. Each example has {dataset.element_spec[0].shape[0]} features and a label vector of size {dataset.element_spec[1].shape[0]}. ' +
		  'However, without evaluating the dataset, it\'s unclear the total number of examples in this dataset.')

	length = tf.data.experimental.cardinality(dataset).numpy()
	print(f"Let's eagerly evaluate the dataset, we find out there are {length} examples.")

	maxEncoding = max([d[0].numpy().max() for d in dataset])

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

	num_epochs = 50
	model.fit(train_data, validation_data=test_data, epochs=num_epochs, callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=5)])

	test_example = list(dataset.skip(5).take(1))[0]
	# predict, as the same as fit, must take batches. Therefore, we must add a new dimension to the extracted features.
	prediction = model.predict(tf.expand_dims(test_example[0], 0))[0]
	prediction = tf.where(prediction > 0.5, tf.ones_like(prediction, tf.int32), tf.zeros_like(prediction, tf.int32)).numpy()
	print(f'prediction={prediction}, actual={test_example[1]}')
