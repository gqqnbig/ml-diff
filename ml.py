# import d2lzh as d2l
from mxnet import nd
from mxnet.gluon import rnn
from mxnet import autograd, gluon, image, init, nd
import mxnet as mx
import mxnet.gluon.loss as gloss
import math
import os
import random
import time

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


def loadData():
	folder = r'D:\renaming\data\generated'
	data = []
	# labels = []
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
			sample.append(128)
		# labels.append('add')
		elif 'delete' in diff.name:
			sample.append(129)
		# labels.append('delete')
		elif 'both' in diff.name:
			sample.append(130)
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
	return data


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


if __name__ == '__main__':
	data = loadData()
	num_steps = data.shape[1]

	data = mx.nd.shuffle(data)
	testData = mx.nd.crop(data, 0, len(data) // 10)
	trainData = mx.nd.crop(data, len(data) // 10, (None,))

	# +3是因为有三种操作类别
	vocab_size = 127 + 3

	num_inputs = vocab_size
	num_outputs = vocab_size


	def get_params():
		def _one(shape):
			return nd.random.normal(scale=0.01, shape=shape)

		def _three():
			return (_one((num_inputs, num_hiddens)),
					_one((num_hiddens, num_hiddens)),
					nd.zeros(num_hiddens))

		W_xi, W_hi, b_i = _three()  # 输入门参数
		W_xf, W_hf, b_f = _three()  # 遗忘门参数
		W_xo, W_ho, b_o = _three()  # 输出门参数
		W_xc, W_hc, b_c = _three()  # 候选记忆细胞参数
		# 输出层参数
		W_hq = _one((num_hiddens, num_outputs))
		b_q = nd.zeros(num_outputs)
		# 附上梯度
		params = [W_xi, W_hi, b_i, W_xf, W_hf, b_f, W_xo, W_ho, b_o, W_xc, W_hc, b_c, W_hq, b_q]
		for param in params:
			param.attach_grad()
		return params


	lstm_layer = rnn.LSTM(num_hiddens)
	model = RNNModel(lstm_layer, vocab_size)

	for X, Y in data_iter_random(trainData, batch_size):
		print(X)
		print(Y)
		print('----------------------')

	train_and_predict_rnn(lstm, get_params, init_lstm_state, num_hiddens, vocab_size, data, idx_to_char, False, num_epochs, num_steps, lr, clipping_theta, batch_size, pred_period, 1)
