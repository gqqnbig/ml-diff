import tensorflow as tf
import logging

logger = logging.getLogger('tfHelper')


def getColumn(ds: tf.data.Dataset, index):
	return ds.map(lambda *d: d[index])


def forceCache(dataset: tf.data.Dataset, filename=''):
	dataset = dataset.cache(filename)
	dataset.map(lambda *_: 1)
	return dataset


if hasattr(tf.data.Dataset, getColumn.__name__) == False:
	tf.data.Dataset.getColumn = getColumn
else:
	logger.warning(f'Extension method {getColumn.__name__} is not added.')

if hasattr(tf.data.Dataset, forceCache.__name__) == False:
	tf.data.Dataset.forceCache = forceCache
else:
	logger.warning(f'Extension method {forceCache.__name__} is not added.')
