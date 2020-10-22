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
num_epochs = 160


class RNNModel(mx.gluon.nn.Block):
	"""RNN model."""

	def __init__(self, rnn_layer, vocab_size, **kwargs):
		super(RNNModel, self).__init__(**kwargs)
		self.rnn = rnn_layer
		self.vocab_size = vocab_size
		self.dense = mx.gluon.nn.Dense(vocab_size)

	def forward(self, inputs, state):
		X = nd.one_hot(inputs.T, self.vocab_size)
		Y, state = self.rnn(X, state)
		output = self.dense(Y.reshape((-1, Y.shape[-1])))
		return output, state

	def begin_state(self, *args, **kwargs):
		return self.rnn.begin_state(*args, **kwargs)


def to_onehot(X, size):
	"""Represent inputs with one-hot encoding."""
	return [nd.one_hot(x, size) for x in X.T]


def grad_clipping(params, theta, ctx):
	"""Clip the gradient."""
	if theta is not None:
		norm = nd.array([0], ctx)
		for param in params:
			norm += (param.grad ** 2).sum()
		norm = norm.sqrt().asscalar()
		if norm > theta:
			for param in params:
				param.grad[:] *= theta / norm


def sgd(params, lr, batch_size):
	"""Mini-batch stochastic gradient descent."""
	for param in params:
		param[:] = param - lr * param.grad / batch_size


def lstm(inputs, state, params):
	[W_xi, W_hi, b_i, W_xf, W_hf, b_f, W_xo, W_ho, b_o, W_xc, W_hc, b_c, W_hq, b_q] = params
	(H, C) = state
	outputs = []
	for X in inputs:
		I = nd.sigmoid(nd.dot(X, W_xi) + nd.dot(H, W_hi) + b_i)
		F = nd.sigmoid(nd.dot(X, W_xf) + nd.dot(H, W_hf) + b_f)
		O = nd.sigmoid(nd.dot(X, W_xo) + nd.dot(H, W_ho) + b_o)
		C_tilda = nd.tanh(nd.dot(X, W_xc) + nd.dot(H, W_hc) + b_c)
		C = F * C + I * C_tilda
		H = O * C.tanh()
		Y = nd.dot(H, W_hq) + b_q
		outputs.append(Y)
	return outputs, (H, C)


def mapIndexToChar(index):
	if index <= 126:
		return chr(index)
	elif index == 127:
		return '\n-->Add'
	elif index == 128:
		return '\n-->Delete'
	elif index == 129:
		return '\n-->Both'


def init_lstm_state(batch_size, num_hiddens):
	"""
	返回隐藏状态和记忆细胞
	:param batch_size:
	:param num_hiddens:
	:param ctx:
	:return:
	"""

	return (nd.zeros(shape=(batch_size, num_hiddens)),
			nd.zeros(shape=(batch_size, num_hiddens)))


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

		sample = [ord(c) for c in sample]
		if 'add' in diff.name:
			labels.append(0)
		# labels.append('add')
		elif 'delete' in diff.name:
			labels.append(1)
		# labels.append('delete')
		elif 'both' in diff.name:
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
	data = mx.ndarray.array(data)
	assert data.shape[1] == num_steps
	return data, mx.ndarray.array(labels)


def predict_rnn(prefix, num_chars, rnn, params, init_rnn_state,
				num_hiddens, vocab_size, idx_to_char, char_to_idx):
	"""Predict next chars with a RNN model"""
	state = init_rnn_state(1, num_hiddens)
	output = [char_to_idx[prefix[0]]]
	for t in range(num_chars + len(prefix) - 1):
		X = to_onehot(nd.array([output[-1]]), vocab_size)
		(Y, state) = rnn(X, state, params)
		if t < len(prefix) - 1:
			output.append(char_to_idx[prefix[t + 1]])
		else:
			output.append(int(Y[0].argmax(axis=1).asscalar()))
	return ''.join([idx_to_char[i] for i in output])


def data_iter_random(data, batch_size):
	"""Sample mini-batches in a random order from sequential data."""

	sample_indices = list(range(len(data)))
	random.shuffle(sample_indices)

	maxIteration = len(data) // batch_size

	for i in range(maxIteration):
		batch_indices = sample_indices[i * batch_size: (i + 1) * batch_size]
		samples = data.take(mx.ndarray.array(batch_indices))
		X = samples[:, :-1]
		Y = samples[:, 1:]
		assert X.shape == Y.shape
		yield X, Y


# def data_iter_consecutive(corpus_indices, batch_size, num_steps):
# 	"""Sample mini-batches in a consecutive order from sequential data."""
# 	corpus_indices = nd.array(corpus_indices)
# 	data_len = len(corpus_indices)
# 	batch_len = data_len // batch_size
# 	indices = corpus_indices[0: batch_size * batch_len].reshape((
# 		batch_size, batch_len))
# 	epoch_size = (batch_len - 1) // num_steps
# 	for i in range(epoch_size):
# 		i = i * num_steps
# 		X = indices[:, i: i + num_steps]
# 		Y = indices[:, i + 1: i + num_steps + 1]
# 		yield X, Y


def train_and_predict_rnn(rnn, get_params, init_rnn_state, num_hiddens, vocab_size, data, idx_to_char, char_to_idx, num_epochs, num_steps, lr, clipping_theta, batch_size, pred_period, pred_len, prefixes):
	"""Train an RNN model and predict the next item in the sequence."""
	# if is_random_iter:
	# else:
	# data_iter_fn = data_iter_consecutive
	params = get_params()
	loss = gloss.SoftmaxCrossEntropyLoss()

	for epoch in range(num_epochs):
		# if not is_random_iter:
		# 	state = init_rnn_state(batch_size, num_hiddens)
		l_sum, n, start = 0.0, 0, time.time()
		data_iter = data_iter_random(data, batch_size)
		for X, Y in data_iter:
			# if is_random_iter:
			state = init_rnn_state(batch_size, num_hiddens)
			# else:
			# 	for s in state:
			# 		s.detach()
			with autograd.record():
				inputs = to_onehot(X, vocab_size)
				(outputs, state) = rnn(inputs, state, params)
				outputs = nd.concat(*outputs, dim=0)
				y = Y.T.reshape((-1,))
				l = loss(outputs, y).mean()
			l.backward()
			grad_clipping(params, clipping_theta)
			sgd(params, lr, 1)
			l_sum += l.asscalar() * y.size
			n += y.size

		if (epoch + 1) % pred_period == 0:
			print('epoch %d, perplexity %f, time %.2f sec' % (
				epoch + 1, math.exp(l_sum / n), time.time() - start))
			for prefix in prefixes:
				print(' -', predict_rnn(
					prefix, pred_len, rnn, params, init_rnn_state,
					num_hiddens, vocab_size, idx_to_char, char_to_idx))


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
		print('epoch %d, loss %.4f, train acc %.3f, test acc %.3f'
			  % (epoch + 1, train_l_sum / n, train_acc_sum / n, test_acc))


if __name__ == '__main__':
	X, y = loadData()
	length = len(X)
	s = mx.ndarray.shuffle(mx.ndarray.array(list(range(length))))

	# num_steps = data.shape[1]

	trainX = mx.ndarray.take(X, mx.nd.crop(s, length // 10, (None,)))
	trainY = mx.ndarray.take(y, mx.nd.crop(s, length // 10, (None,)))
	testX = mx.ndarray.take(X, mx.nd.crop(s, 0, length // 10))
	testY = mx.ndarray.take(y, mx.nd.crop(s, 0, length // 10))
	assert trainX.shape[0] == trainY.shape[0], '输入与输出的长度必须相同'
	assert testX.shape[0] == testY.shape[0], '输入与输出的长度必须相同'
	assert trainX.shape[0] > testX.shape[0], '训练数据必须多于测试数据'

	trainIterator = mx.gluon.data.DataLoader(mx.gluon.data.ArrayDataset(trainX, trainY), batch_size=batch_size)
	testIterator = mx.gluon.data.DataLoader(mx.gluon.data.ArrayDataset(testX, testY), batch_size=batch_size)

	# +3是因为有三种操作类别
	vocab_size = 127 + 3
	net = nn.Sequential()
	net.add(nn.Dense(127, activation='relu'),
			nn.Dense(3))

	net.initialize(init.Normal(sigma=0.01))

	loss = gloss.SoftmaxCrossEntropyLoss()
	trainer = gluon.Trainer(net.collect_params(), 'sgd', {'learning_rate': 0.5})
	num_epochs = 5

	num_inputs = vocab_size
	num_outputs = vocab_size

	train_ch3(net, trainIterator, testIterator, loss, num_epochs, batch_size, None, None, trainer)

#
# def get_params():
# 	def _one(shape):
# 		return nd.random.normal(scale=0.01, shape=shape)
#
# 	def _three():
# 		return (_one((num_inputs, num_hiddens)),
# 				_one((num_hiddens, num_hiddens)),
# 				nd.zeros(num_hiddens))
#
# 	W_xi, W_hi, b_i = _three()  # 输入门参数
# 	W_xf, W_hf, b_f = _three()  # 遗忘门参数
# 	W_xo, W_ho, b_o = _three()  # 输出门参数
# 	W_xc, W_hc, b_c = _three()  # 候选记忆细胞参数
# 	# 输出层参数
# 	W_hq = _one((num_hiddens, num_outputs))
# 	b_q = nd.zeros(num_outputs)
# 	# 附上梯度
# 	params = [W_xi, W_hi, b_i, W_xf, W_hf, b_f, W_xo, W_ho, b_o, W_xc, W_hc, b_c, W_hq, b_q]
# 	for param in params:
# 		param.attach_grad()
# 	return params
#
#
# lstm_layer = rnn.LSTM(num_hiddens)
# model = RNNModel(lstm_layer, vocab_size)
#
# for X, Y in data_iter_random(trainData, batch_size):
# 	print(X)
# 	print(Y)
# 	print('----------------------')
#
# train_and_predict_rnn(lstm, get_params, init_lstm_state, num_hiddens, vocab_size, data, idx_to_char, False, num_epochs, num_steps, lr, clipping_theta, batch_size, pred_period, 1)
