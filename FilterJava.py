#!/usr/bin/env python3

import os
import sys

import multiprocessing


def removeNonJava(lines):
	if len(lines) == 0:
		return lines

	if lines[0].startswith('diff --git '):
		nextPartIndex = 4
		while nextPartIndex < len(lines) and lines[nextPartIndex].startswith('diff --git ') == False:
			nextPartIndex += 1

		if lines[0].rstrip().endswith('.java'):
			return lines[4:nextPartIndex - 1] + removeNonJava(lines[nextPartIndex:-1])
		else:
			return removeNonJava(lines[nextPartIndex:-1])

	return lines


def filterCombinedDiff(diffPath: str):
	try:
		with open(diffPath, 'r', encoding='utf-8') as f:
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
	except Exception as e:
		print(diffPath + '\n' + str(e), file=sys.stderr)


def scanRepo(repoPath):
	print(f'scan {repoPath}')
	for file in os.scandir(repoPath):
		if file.path.endswith('.diff'):
			filterCombinedDiff(file.path)


if __name__ == '__main__':
	filterCombinedDiff(r'D:\renaming\diffs\repo1000\2125267.diff')
	exit()

	pool = multiprocessing.Pool(4)
	multiple_results = [pool.apply_async(scanRepo, (r'D:\renaming\diffs\\' + path,)) for path in os.listdir(r'D:\renaming\diffs')]
	print([res.get() for res in multiple_results])
