from mxnet.gluon import rnn
from mxnet import autograd, gluon, image, init, nd
from mxnet.gluon import data as gdata, loss as gloss, nn, utils as gutils
import mxnet as mx
import math
import os
import random
import time

import typing

num_hiddens = 256
vocab_size = 126 - 32 + 1
lr = 1e2
clipping_theta = 1e-2
batch_size = 20


def sgd(params, lr, batch_size):
	"""Mini-batch stochastic gradient descent."""
	for param in params:
		param[:] = param - lr * param.grad / batch_size


def loadData() -> typing.Tuple[mx.ndarray.NDArray, mx.ndarray.NDArray]:
	folder = r'D:\renaming\data\generated'
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

		if 'add' in diff.name:
			labels.append(0)
		# labels.append('add')
		elif 'delete' in diff.name:
			labels.append(1)
		# labels.append('delete')
		elif 'both' in diff.name:
			# continue
			labels.append(2)
		# labels.append('both')
		else:
			print(f'Unknown file: {diff.path}')

		# print([mapIndexToChar(c) for c in sample])
		data.append(sample)
	# 确保data中每个sample长度相同
	num_steps = max([len(sample) for sample in data])
	for i in range(len(data)):
		if len(data[i]) < num_steps:
			data[i].extend([0] * (num_steps - len(data[i])))
	for sample in data:
		assert len(sample) == num_steps
	data = mx.ndarray.array(data, dtype='int8')
	assert data.shape[1] == num_steps
	return data, mx.ndarray.array(labels, dtype='int8')


def evaluate_accuracy(data_iter, net):
	"""Evaluate accuracy of a model on the given data set."""

	acc_sum, n = nd.array([0]), 0
	for batch in data_iter:
		features, labels, _ = _get_batch(batch, [mx.cpu()])
		for X, y in zip(features, labels):
			y = y.astype('float32')
			acc_sum += (net(X).argmax(axis=1) == y).sum().copyto(mx.cpu())
			n += y.size
		acc_sum.wait_to_read()
	return acc_sum.asscalar() / n


def _get_batch(batch, ctx):
	"""Return features and labels on ctx."""
	features, labels = batch
	if labels.dtype != features.dtype:
		labels = labels.astype(features.dtype)
	return (gutils.split_and_load(features, ctx),
			gutils.split_and_load(labels, ctx), features.shape[0])


def train_ch3(net, trainIterator, testIterator, loss, num_epochs, batch_size,
			  params=None, lr=None, trainer=None):
	"""Train and evaluate a model with CPU."""
	for epoch in range(num_epochs):
		train_l_sum, train_acc_sum, n = 0.0, 0.0, 0
		for X, y in trainIterator:
			assert y.ndim == 1, "Y is 1-d array whose values are categories."
			with autograd.record():
				y_hat = net(X)

				categoryCount = y_hat.shape[1]
				for item in y:
					assert 0 <= item < categoryCount, 'y_hat和y不匹配。y是类别编号的数组，从0起。对于第i个样本，y_hat[i]是一个数组，记录每个类别的概率。\n' \
													  f'目前，y_hat的形状为{y_hat.shape}，说明应有{categoryCount}种类别；但是y中有数值{item.asscalar()}，不对应任何类别。'

				l = loss(y_hat, y).sum()
			l.backward()
			if trainer is None:
				sgd(params, lr, batch_size)
			else:
				trainer.step(batch_size)
			y = y.astype('float32')
			train_l_sum += l.asscalar()
			train_acc_sum += (y_hat.argmax(axis=1) == y).sum().asscalar()
			n += y.size
		test_acc = evaluate_accuracy(testIterator, net)
		print('epoch %d, loss %.4f, train acc %.3f, test acc %.3f' % (epoch + 1, train_l_sum / n, train_acc_sum / n, test_acc))


if __name__ == '__main__':
	X, y = loadData()

	X = nd.one_hot(X, X.max().asscalar())
	length = len(X)
	s = mx.ndarray.shuffle(mx.ndarray.array(list(range(length))))

	trainX = mx.ndarray.take(X, mx.nd.crop(s, length // 10, (None,)))
	trainY = mx.ndarray.take(y, mx.nd.crop(s, length // 10, (None,)))
	testX = mx.ndarray.take(X, mx.nd.crop(s, 0, length // 10))
	testY = mx.ndarray.take(y, mx.nd.crop(s, 0, length // 10))
	assert trainX.shape[0] == trainY.shape[0], '输入与输出的长度必须相同'
	assert testX.shape[0] == testY.shape[0], '输入与输出的长度必须相同'
	assert trainX.shape[0] > testX.shape[0], '训练数据必须多于测试数据'

	trainIterator = mx.gluon.data.DataLoader(mx.gluon.data.ArrayDataset(trainX, trainY), batch_size=batch_size)
	testIterator = mx.gluon.data.DataLoader(mx.gluon.data.ArrayDataset(testX, testY), batch_size=batch_size)

	net = nn.Sequential()
	net.add(nn.Dense(127, activation='relu'),
			nn.Dense(3))

	net.initialize(init.Normal(sigma=0.01))

	loss = gloss.SoftmaxCrossEntropyLoss()
	trainer = gluon.Trainer(net.collect_params(), 'sgd', {'learning_rate': 0.5})
	num_epochs = 50

	train_ch3(net, trainIterator, testIterator, loss, num_epochs, batch_size, None, None, trainer)
