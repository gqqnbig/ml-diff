import tensorflow as tf
import logging

logger = logging.getLogger('tfHelper')


def getColumn(ds: tf.data.Dataset, index):
	return ds.map(lambda *d: d[index])


if hasattr(tf.data.Dataset, getColumn.__name__) == False:
	tf.data.Dataset.getColumn = getColumn
else:
	logger.warning(f'Extension method {getColumn.__name__} is not added.')


def forceCache(dataset: tf.data.Dataset, filename=''):
	dataset = dataset.cache(filename)
	dataset.map(lambda *_: 1)
	return dataset


if hasattr(tf.data.Dataset, forceCache.__name__) == False:
	tf.data.Dataset.forceCache = forceCache
else:
	logger.warning(f'Extension method {forceCache.__name__} is not added.')


def count(dataset: tf.data.Dataset):
	# __len__() throws exception if the length is unknown.
	c = dataset.cardinality()
	if c != tf.data.UNKNOWN_CARDINALITY:
		return c
	else:
		c = dataset.reduce(0, lambda x, _: x + 1).numpy()
		return c


if hasattr(tf.data.Dataset, count.__name__) == False:
	tf.data.Dataset.count = count
else:
	logger.warning(f'Extension method {count.__name__} is not added.')
