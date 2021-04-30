#!/usr/bin/env python3

import multiprocessing
import os
import re
import sys

# from typing import List, Tuple, Optional
#
# from Antlr import *
#
#
# import JavaMiniParser
#
#
# def testRenaming(filePath):
# 	with open(filePath, 'r', encoding='utf-8') as f:
# 		lines = f.readlines()
#
# 	addedLines = [l for l in lines if l.startswith('+')]
# 	removedLines = [l for l in lines if l.startswith('-')]
#
# 	for key, pattern in JavaMiniParser.getDefinitionPatterns().items():
# 		matchAdd = False
# 		matchRemove = False
# 		for line in addedLines:
# 			m = re.match(pattern, line, re.IGNORECASE)
# 			if m:
# 				matchAdd = True
# 				break
# 		for line in removedLines:
# 			m = re.match(pattern, line, re.IGNORECASE)
# 			if m:
# 				matchRemove = True
# 				break


def findDifferenceStart(str1, str2, start):
	if str1 == str2:
		return -1

	shortestLength = min(len(str1), len(str2))

	for i in range(start, shortestLength):
		if str1[i] != str2[i]:
			return i
	return shortestLength


java_keywords = {"abstract",
				 "assert",
				 "boolean",
				 "break",
				 "byte",
				 "case",
				 "catch",
				 "char",
				 "class",
				 "const",
				 "continue",
				 "default",
				 "do",
				 "double",
				 "else",
				 "enum",
				 "extends",
				 "false",
				 "final",
				 "finally",
				 "float",
				 "for",
				 "goto",
				 "if",
				 "implements",
				 "import",
				 "instanceof",
				 "int",
				 "interface",
				 "long",
				 "native",
				 "new",
				 "null",
				 "package",
				 "private",
				 "protected",
				 "public",
				 "return",
				 "short",
				 "static",
				 "strictfp",
				 "super",
				 "switch",
				 "synchronized",
				 "this",
				 "throw",
				 "throws",
				 "transient",
				 "true",
				 "try",
				 "void",
				 "volatile",
				 "while",
				 }


def dos2unix(file_path):
	# replacement strings
	WINDOWS_LINE_ENDING = b'\r\n'
	UNIX_LINE_ENDING = b'\n'

	with open(file_path, 'rb') as open_file:
		content = open_file.read()

	content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

	with open(file_path, 'wb') as open_file:
		open_file.write(content)


def createLabels(file: str):
	with open(file, 'r', encoding='utf-8') as f:
		lines = f.readlines()
		if type(f.newlines) is tuple and len(f.newlines) > 1 or f.newlines != '\n':
			f.close()
			dos2unix(file)
			f = open(file, 'r', encoding='utf-8')
			lines = f.readlines()

	rearrangeBalancedAddRemove(lines, file)

	removedLines = len(list(filter(lambda l: l[0] == '-', lines)))
	addedLines = len(list(filter(lambda l: l[0] == '+', lines)))
	if removedLines != addedLines:
		return None

	labels = {}
	# currentOffset = 0
	removedLine = None
	for line in lines:
		if line[0] == ' ':
			pass
		elif line[0] == '-':
			removedLine = line
		elif line[0] == '+':
			if removedLine is not None:
				d = findDifferenceStart(line, removedLine, 1)

				oldWord = getWord(removedLine, d)
				newWord = getWord(line, d)

				if oldWord is None or newWord is None:
					return None
				if oldWord == newWord:
					return None
				if oldWord in java_keywords or newWord in java_keywords:
					return None

				if oldWord in labels:
					if labels[oldWord] != newWord:
						return None
				else:
					labels[oldWord] = newWord

				# labels.append(currentOffset - len(removedLine) + d)
				removedLine = None

	# currentOffset += len(line)

	return labels


def rearrangeBalancedAddRemove(lines: list, file):
	isRearranged = False
	removeCount = 0
	addCount = 0
	for i in range(len(lines)):
		if lines[i][0] == '-':
			removeCount += 1
			addCount = 0
		elif lines[i][0] == '+':
			addCount += 1
		else:
			if removeCount == addCount and removeCount > 1:
				# the change is balanced, rearrange the lines to interleave minus and plus.
				removeStart = i - addCount - removeCount
				for j in range(removeCount - 1):
					# find add for remove at line removeStart+j*2, ie. j-th remove
					# the add for j-th remove is at removeStart+j+removeCount

					lines.insert(removeStart + j * 2 + 1, lines[removeStart + j + removeCount])
					del lines[removeStart + j + removeCount + 1]

				isRearranged = True

			removeCount = 0
			addCount = 0

	if isRearranged:
		with open(file, 'w', encoding='utf-8', newline='\n') as f:
			f.writelines(lines)
	# print(f'rearrange diff {file}')


def getWord(content: str, index):
	"""

	:param content:
	:param index:
	:return: return None if the given index is not a word. Otherwise return the word
	"""
	assert index >= 0

	if content[index].isalnum() == False and content[index] != '_':
		index -= 1
		if content[index].isalnum() == False and content[index] != '_':
			return None

	end = index + 1
	while end < len(content):
		# doesn't consider unicode characters for now.
		if content[end].isalnum() or content[end] == '_':
			end += 1
		else:
			break

	start = index
	while start >= 0:
		# doesn't consider unicode characters for now.
		if content[start].isalnum() or content[start] == '_':
			start -= 1
		else:
			break

	start += 1
	return content[start:end]


# def isIdentifierRenaming(diffFile: str) -> Optional[Tuple[List[int], List[str]]]:
# 	possibleLabels = createLabels(diffFile)
#
# 	with open(diffFile, 'r', encoding='utf-8') as f:
# 		content = f.read()
#
# 	changedWords = list(set([getWord(content, i) for i in possibleLabels]))
# 	if len(changedWords) == 1 and changedWords[0] is not None:
# 		print(changedWords)
# 		return possibleLabels, changedWords
# 	else:
# 		return None

def createLabelForRepo(repo, labelFile):
	with open(labelFile, 'w', encoding='utf-8') as labelFile:
		for diff in os.scandir(repo):
			if diff.is_dir() or not diff.name.endswith('.diff'):
				continue

			try:
				labels = createLabels(diff.path)
				if labels is not None:
					labelFile.write(diff.name[0:-len('.diff')])
					labelFile.write('|')
					# labelFile.write(str(labels)[1:-1])
					labelFile.write('|')

					s = ', '.join([k + "->" + v for k, v in labels.items()])
					if 0 < len(labels) <= 2:
						labelFile.write('y')

						# print(diff.name + ": " + s)
						labelFile.write('|' + s)
					elif len(labels) > 2:
						labelFile.write('skip')

						# print(diff.name + ": " + s)
						labelFile.write('|' + s)
					else:
						labelFile.write('n')

					labelFile.write('\n')
			except Exception as e:
				print(f'{diff.path} has error: {e}', file=sys.stderr)


def scanRepo(path):
	repo = os.path.basename(path)
	print(f'open {repo}')
	createLabelForRepo(path, os.path.join(path, '..', f'{repo}.txt'))
	print(f'{repo} done')


if __name__ == '__main__':
	if len(sys.argv) == 1 or '--help' in sys.argv:
		print(f'''
{sys.argv[0]} path
path could be a diff file or a folder. This form is usually for debugging.

{sys.argv[0]} [-c num] --dataset path
path is a folder of a dataset, which contains many sub-folders.
-c specifies the number of CPUs to use. If it's not set, environment variable SLURM_CPUS_PER_TASK will be read. Default value is 1.
''')
		exit()

	if '--dataset' in sys.argv:
		path = os.path.expanduser(sys.argv[-1])

		try:
			p = sys.argv.index('-c')
			parallelism = int(sys.argv[p + 1])
		except:
			parallelism = 1

		parallelism = int(os.getenv('SLURM_CPUS_PER_TASK', parallelism))

		print(f'Use {parallelism} cores.')
		if parallelism > 1:
			with multiprocessing.Pool(parallelism) as pool:
				multiple_results = [pool.apply_async(scanRepo, (path.path,)) for path in os.scandir(path) if path.is_dir() and path.name[0] != '.']
				[res.get() for res in multiple_results]
		else:
			for p in os.scandir(path):
				if p.name[0] != '.' and p.is_dir():
					scanRepo(p.path)
	else:
		path = os.path.expanduser(sys.argv[-1])
		if os.path.isfile(path):
			print(createLabels(path))
		elif os.path.isdir(path):
			scanRepo(path)
		else:
			print(f'{path} does not exist.', file=sys.stderr)

#
# repos = ["camel",
# 		 "camunda-bpm-platform",
# 		 "dbeaver",
# 		 "EhViewer",
# 		 "Geyser",
# 		 "iceberg",
# 		 "Java",
# 		 "java-design-patterns",
# 		 "jenkins",
# 		 "keycloak",
# 		 "libgdx",
# 		 "Mindustry",
# 		 # "NewPipe",
# 		 "openapi-generator",
# 		 "quarkus",
# 		 "Signal-Android",
# 		 "spring-petclinic",
# 		 "strimzi-kafka-operator",
# 		 "testcontainers-java",
# 		 "tutorials",
# 		 "wiremock",
# 		 ]

# for repo in repos:
# 	print('open ' + repo)
# 	createLabelForRepo(r'D:\renaming\diffs\\' + repo, rf'D:\renaming\diffs\{repo}.txt')
# createLabels(r'D:\renaming\data\real\AntennaPod\0499ef60ac7122dfad8c1579327c72eaca37cde9.diff')
#
# exit()

# try:
# 	result = isIdentifierRenaming(diff.path)
# 	if result is not None:
# 		labels = result[0]
# 		# if len(labels) > 1:
# 		# 1 place to change definition, other places to change references
# 		labelFile.write(diff.name[0:-len('.diff')])
# 		labelFile.write('|')
# 		labelFile.write(str(labels)[1:-1])
# 		labelFile.write('|')
# 		labelFile.write('\n')
# except Exception as e:
# 	print(diff.path + " has error:" + str(e))
