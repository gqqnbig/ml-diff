import os
import sys
import multiprocessing


from chardet.universaldetector import UniversalDetector

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
	return detector.result['encoding']


def _get_encoding_type(file):
	# with open(file, 'rb') as f:
	# 	rawdata = f.read()
	# return detect(rawdata)['encoding']

	# If file size is less than 1MB
	if os.path.getsize(file) / 1024.0 / 1024.0 <= 1:
		return _get_encoding_type_core(file)
	else:
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
