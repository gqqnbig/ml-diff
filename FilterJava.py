#!/usr/bin/env python3

import os
import sys

import multiprocessing
from typing import List

import FileEncodingConverter


def findLineStartsWith(lines, str, start):
	"""
	if str is not found, return len(lines).

	:param lines:
	:param str:
	:param start: inclusive
	:return:
	"""
	while start < len(lines) and lines[start].startswith(str) == False:
		start += 1
	return start


def removeNonJava(lines: List[str]):
	if len(lines) == 0:
		return lines

	if lines[0].startswith('diff --git ') == False:
		return lines

	javaLines = []
	i = 0
	while i < len(lines):
		nextPartIndex = findLineStartsWith(lines, 'diff --git ', i + 1)
		if lines[i].rstrip().endswith('.java'):
			j = findLineStartsWith(lines, '@@', i + 1)
			if j < findLineStartsWith(lines, 'diff --git ', i + 1):
				javaLines.extend(lines[j:nextPartIndex])

		i = nextPartIndex

	return javaLines


# def convertToUtf8(filePath:str):
# 	detector = UniversalDetector()
# 	for line in open(filePath,'rb'):
# 		detector.feed(line)
# 		if detector.done:
# 			break
# 	detector.close()
# 	print(detector.result)
# 	if detector.result is not None:
#
# 		with open(filePath, 'r', encoding=detector.result.encoding) as f:
# 			content= f.read()
#


def filterCombinedDiff(diffPath: str):
	ignoreEncodingError = False
	retried = False
	while True:
		try:
			with open(diffPath, 'r', encoding='utf-8', errors='ignore' if ignoreEncodingError else None) as f:
				lines = f.readlines()

			l = len(lines)
			lines = removeNonJava(lines)
			if len(lines) == 0:
				print(f'Delete {diffPath}.')
				os.remove(diffPath)
			elif l != len(lines):
				print(f'Remove {l - len(lines)} lines in {diffPath}.')
				with open(diffPath, 'w', encoding='utf-8') as f:
					f.writelines(lines)

			return
		except UnicodeDecodeError as e:
			if retried:
				print(f'{diffPath}: {str(e)}\n', file=sys.stderr)
				return
			retried = True
			ignoreEncodingError = FileEncodingConverter.convertToUtf8(diffPath) == False
		except Exception as e:
			print(diffPath + ': ' + str(e), file=sys.stderr)
			return


def scanRepo(repoPath):
	print(f'scan {repoPath}')
	for file in os.scandir(repoPath):
		if file.path.endswith('.diff'):
			filterCombinedDiff(file.path)


usage = f'{os.path.basename(sys.argv[0])} dataset'
usage += '''
--parallel\t\tSpecify the number of CPUs to use. By default the program will use all CPUs the main process can use.
--help\t\tPrint help
'''

if __name__ == '__main__':
	if '--help' in sys.argv:
		print(usage)
		exit()

	try:
		p = sys.argv.index('--parallel')
		parallel = int(sys.argv[p + 1])
	except:
		if hasattr(os, 'sched_getaffinity'):
			parallel = len(os.sched_getaffinity(0))
		else:
			parallel = os.cpu_count()

	if len(sys.argv) <= 1:
		print('dataset is not provided.\n\n' + usage, file=sys.stderr)
		exit(1)

	dataFolder = sys.argv[-1]
	dataFolder = os.path.expanduser(dataFolder)
	if os.path.isdir(dataFolder):
		with multiprocessing.Pool(parallel) as pool:
			multiple_results = [pool.apply_async(scanRepo, (path.path,)) for path in os.scandir(dataFolder) if path.is_dir() and path.name[0] != '.']
			[res.get() for res in multiple_results]
	else:
		print(f'dataset folder {dataFolder} does not exist.\n\n' + usage, file=sys.stderr)
		exit(1)
