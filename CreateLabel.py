import os
import re


def findDifferenceStart(str1, str2, start):
	if str1 == str2:
		return -1

	shortestLength = min(len(str1), len(str2))

	for i in range(start, shortestLength):
		if str1[i] != str2[i]:
			return i
	return shortestLength


def createLabels(file: str):
	with open(file, 'r', encoding='utf-8') as f:
		lines = f.readlines()
		if type(f.newlines) is tuple and len(f.newlines) > 1:
			raise Exception(f'File {file} uses mixed line endings, which is not supported.')

		if f.newlines != '\n':
			raise Exception('Currently, only Linux line ending (\\n) is supported.')

	rearrangeBalancedAddRemove(lines, file)

	removedLines = len(list(filter(lambda l: l[0] == '-', lines)))
	addedLines = len(list(filter(lambda l: l[0] == '+', lines)))
	if removedLines != addedLines:
		return []

	labels = []
	currentOffset = 0
	removedLine = None
	for line in lines:
		if line[0] == ' ':
			pass
		elif line[0] == '-':
			removedLine = line
		elif line[0] == '+':
			if removedLine is not None:
				d = findDifferenceStart(line, removedLine, 1)
				labels.append(currentOffset - len(removedLine) + d)
				removedLine = None

		currentOffset += len(line)

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
		print(f'rearrange diff {file}')


def getWord(content: str, index):
	m = re.search(r'\w\b', content[index:])
	if m is None:
		return None
	else:
		return content[index:index + m.end()]


def isIdentifierRenaming(diffFile):
	possibleLabels = createLabels(diffFile)

	with open(diffFile, 'r', encoding='utf-8') as f:
		content = f.read()

	changedWords = [getWord(content, i) for i in possibleLabels]
	print(changedWords)
	if len(set(changedWords)) == 1:
		return possibleLabels
	else:
		return []


if __name__ == '__main__':
	folder = r'D:\renaming\data\real\baritone'
	labelFile = r'D:\renaming\data\real\baritone.txt'

	with open(labelFile, 'w', encoding='utf-8') as labelFile:
		for diff in os.scandir(folder):
			if diff.is_dir() or not diff.name.endswith('.diff'):
				continue

			labels = isIdentifierRenaming(diff.path)
			if len(labels) > 1:
				# 1 place to change definition, other places to change references
				labelFile.write(diff.name[0:-len('.diff')])
				labelFile.write('|')
				labelFile.write(str(labels)[1:-1])
				labelFile.write('|')
				labelFile.write('\n')
