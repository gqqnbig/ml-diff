import os
import sys
import multiprocessing
import psutil

import tensorflow as tf
from chardet.universaldetector import UniversalDetector


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


def _get_encoding_type_core(file):
	# with open(file, 'rb') as f:
	# 	rawdata = f.read()
	# return detect(rawdata)['encoding']

	# If file size is less than 1MB
	detector = UniversalDetector()
	for line in open(file, 'rb'):
		detector.feed(line)
		if detector.done:
			break
	detector.close()
	print(detector.result.encoding)
	return detector.result.encoding


def _get_encoding_type(file):
	# with open(file, 'rb') as f:
	# 	rawdata = f.read()
	# return detect(rawdata)['encoding']

	# If file size is less than 1MB
	if os.path.getsize(file) / 1024.0 / 1024.0 <= 1:
		return _get_encoding_type_core(file)
	else:
		# def increasePriority(process):
		# 	p = psutil.Process(os.getpid())
		# 	p.nice(psutil.HIGH_PRIORITY_CLASS)

		# When the pool process is running, this process is idle. Hence there is no over-parallelism.
		pool = multiprocessing.Pool(1)
		return pool.apply_async(_get_encoding_type_core, (file,)).get(5)


def convertToUtf8(filePath: str):
	"""
	Convert a file to utf8 encoding.
	If the conversion is successful, return true, otherwise return false.

	:param filePath:
	:return:
	"""

	try:
		from_codec = _get_encoding_type(filePath)
		with open(filePath, 'r', encoding=from_codec) as f:
			text = f.read()  # for small files, for big use chunks
		with open(filePath, 'w', encoding='utf-8') as e:
			e.write(text)
		print(f'Converted {filePath} from {from_codec} to UTF-8.')
		return True
	except TimeoutError:
		print(f'Unable to determine encoding of {filePath} within time limit.', file=sys.stderr)
		return False
	except Exception as e:
		print(f'convertToUtf8: {filePath}: {e}', file=sys.stderr)
		return False
