import os
import re
import random
import io

import CreateLabel


def replaceWordAt(line, index, newWord):
	assert line[index].isalnum() or line[index] == '_'

	m = re.search(r'[\w_]+\b', line[index:])
	assert m is not None

	m.end()

	return line[:index] + newWord + line[index + m.end():]


def getPairs(list):
	for i in range(len(list)):
		for j in range(i, len(list)):
			if list[i] != list[j]:
				yield list[i], list[j]


def getWordStart(content: str, index):
	"""

	:param content:
	:param index:
	:return: return None if the given index is not a word. Otherwise return the word
	"""
	assert index >= 0

	# end = None
	# for i in range(index, len(content)):
	# 	# doesn't consider unicode characters for now.
	# 	if content[i].isalnum() or content[i] == '_':
	# 		continue
	# 	else:
	# 		end = i
	# 		break

	start = None
	for i in range(index - 1, 0, -1):
		# doesn't consider unicode characters for now.
		if content[i].isalnum() or content[i] == '_':
			continue
		else:
			start = i + 1
			break

	assert start is not None

	while start < len(content) and content[start].isnumeric():
		start += 1

	return start


def getVocabulary(content):
	"""
	Java keywords are not returned.

	:param content: TextIO or string. If content is TextIO, this method will not close it.
	:return:
	"""
	if isinstance(content, io.TextIOBase):
		content.seek(0)
		content = content.read()

	matches = re.findall(r'\b[a-z][\w_]*\b', content, re.IGNORECASE)
	return {m for m in matches if m not in CreateLabel.java_keywords}


def spawnFromTemplate(file: str, vocabulary: set, count):
	with open(file, 'r', encoding='utf-8') as f:
		lines = f.readlines()
		if type(f.newlines) is tuple and len(f.newlines) > 1:
			raise Exception(f'File {file} uses mixed line endings, which is not supported.')

		if f.newlines != '\n':
			raise Exception('Currently, only Linux line ending (\\n) is supported.')

		vocabulary = vocabulary.difference(getVocabulary(''.join(lines)))

	voc = list(vocabulary)
	random.shuffle(voc)
	renamingPairs = [x for _, x in zip(range(count), getPairs(voc))]

	CreateLabel.rearrangeBalancedAddRemove(lines, file)

	removedLines = len(list(filter(lambda l: l[0] == '-', lines)))
	addedLines = len(list(filter(lambda l: l[0] == '+', lines)))
	assert removedLines == addedLines

	for i in range(len(renamingPairs)):
		newLines = lines.copy()
		removedLine = False
		for j in range(len(newLines)):
			if newLines[j][0] == ' ':
				pass
			elif newLines[j][0] == '-':
				removedLine = True
			elif newLines[j][0] == '+':
				if removedLine:
					d = CreateLabel.findDifferenceStart(newLines[j], newLines[j - 1], 1)
					# go backwards to find the start of the word

					d = getWordStart(newLines[j], d)

					newLines[j - 1] = replaceWordAt(newLines[j - 1], d, renamingPairs[i][0])
					newLines[j] = replaceWordAt(newLines[j], d, renamingPairs[i][1])

					removedLine = False

		s = os.path.splitext(file)
		with open(s[0] + '-' + str(i) + s[1], 'w', encoding='utf-8', newline='\n') as f:
			f.writelines(newLines)


# def spawnFromTemplate(diffFile: str, vocaburary):
# 	renamingMappings = createLabels(diffFile)
# 	assert renamingMappings is not None


def findIdentifiers(file: str):
	with open(file, 'r', encoding='utf-8') as f:
		content = f.read()

	# for simplicity, limit word length to 10.
	matches = re.findall(r'\b[a-z][\w_]{,9}\b', content, re.IGNORECASE)

	words = {m for m in matches if m not in CreateLabel.java_keywords}
	return words


def collectVocabulary(vocabularyFile, dirs):
	vocabulary = {chr(c) for c in range(ord('a'), ord('z'))}
	for dir in dirs:
		print(f'Has {len(vocabulary)} vocabulary. Now reading {dir}.')
		for diff in os.scandir(dir):
			if diff.is_dir() or not diff.name.endswith('.diff'):
				continue

			with open(diff.path, 'r', encoding='utf-8') as f:
				vocabulary.update(getVocabulary(f))

	with open(vocabularyFile, 'w', encoding='utf-8') as f:
		f.write('\n'.join(sorted(list(vocabulary))))


if __name__ == '__main__':
	# collectVocabulary(r'vocabularyFile.txt', [r'D:\renaming\data\real\AntennaPod', r'D:\renaming\data\real\baritone', r'D:\renaming\data\real\camel', r'D:\renaming\data\real\NewPipe'])

# spawnFromTemplate(r'D:\renaming\neural network\tests\Test Cases\catch exception rename-ex-e.diff', vocabulary, 10)

# spawnFromTemplate(r'D:\renaming\neural network\tests\Test Cases\catch exception rename-ex-e.diff')
