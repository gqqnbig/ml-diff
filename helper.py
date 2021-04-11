import os
import sys

import tensorflow as tf


def getLabel(file):
	file = os.path.normpath(file)
	components = file.split(os.sep)
	if components[-2] == 'yes':
		return 1
	elif components[-2] == 'no':
		return 0

	raise Exception(f'Label not found for file {file}')


def getDiffFiles(folder, maxFileSize: int):
	"""

	:param folder:
	:param maxFileSize: KB
	:return:
	"""
	for diff in os.scandir(folder):

		if diff.name.startswith('.'):
			continue

		# fullPath = os.path.join(folder, diff)
		if diff.is_dir():
			yield from getDiffFiles(diff.path, maxFileSize)
		if diff.name.endswith('.diff') and diff.stat().st_size <= maxFileSize * 1024:
			yield diff.path


def getColumn(ds: tf.data.Dataset, index):
	return ds.map(lambda *d: d[index])


def loadModelFromDisk(modelPath: str) -> bool:
	if os.path.exists(modelPath):
		if modelPath.endswith('-dirty'):
			print(f'Are you sure to read {modelPath}? [y]', flush=True)
			r = sys.stdin.read(1)
			if r.strip() == 'y':
				return True
		else:
			print(f'Load model from {modelPath}', flush=True)
			return True

	return False
