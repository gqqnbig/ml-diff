import os
import re
import random
import io
import subprocess

import CreateLabel


def replaceWordAt(line, index, newWord):
	assert line[index].isalnum() or line[index] == '_'

	m = re.search(r'[\w_]+\b', line[index:])
	assert m is not None

	m.end()

	return line[:index] + newWord + line[index + m.end():]


def getPairs(list):
	l = len(list)
	while True:
		i = random.randint(0, l)
		j = random.randint(0, l)
		if i != j:
			yield list[i], list[j]


def getWordEnd(content: str, index):
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

	for i in range(index, len(content) + 1):
		if i == len(content):
			return i
		# doesn't consider unicode characters for now.
		elif content[i].isalnum() or content[i] == '_':
			continue
		else:
			return i

	raise Exception()


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

	matches = re.findall(r'\b[a-z_][\w_]*\b', content, re.IGNORECASE)
	return {m for m in matches if m not in CreateLabel.java_keywords}


def isLowerOrUnderscore(n: str):
	return n.islower() or n == '_'


def spawnFromTemplate(file: str, vocabulary: set, count):
	with open(file, 'r', encoding='utf-8') as f:
		lines = f.readlines()
		if len(lines) == 0:
			raise Exception(f'')
		if f.newlines != '\n':
			raise Exception(f'Currently, only Linux line ending (\\n) is supported. The line ending of {file} is {f.newlines}.')

		vocabulary = vocabulary.difference(getVocabulary(''.join(lines)))

	voc = list(vocabulary)
	# random.shuffle(voc)
	renamingPairs = getPairs(voc)

	CreateLabel.rearrangeBalancedAddRemove(lines, file)

	removedLines = len(list(filter(lambda l: l[0] == '-', lines)))
	addedLines = len(list(filter(lambda l: l[0] == '+', lines)))
	assert removedLines == addedLines

	for i in range(count):
		pair = next(renamingPairs)
		newLines = lines.copy()
		removedLine = False
		isPairVerified = False
		for j in range(len(newLines)):
			if newLines[j][0] == ' ':
				pass
			elif newLines[j][0] == '-':
				removedLine = True
			elif newLines[j][0] == '+':
				if removedLine:
					d = CreateLabel.findDifferenceStart(newLines[j], newLines[j - 1], 1)
					# go backwards to find the start of the word

					e1 = getWordEnd(newLines[j], d)
					e2 = getWordEnd(newLines[j - 1], d)
					if newLines[j][e1:] != newLines[j - 1][e2:]:
						raise NotImplementedError(f'Two changes in a single line is not supported!\n{newLines[j - 1]}{newLines[j]}')

					d = getWordStart(newLines[j], d)

					if d >= len(newLines[j]) or d >= len(newLines[j - 1]):
						continue

					while True:
						if pair is None:
							# vocabulary is exhausted.
							return
						if (newLines[j - 1][d].isupper() and pair[0][0].isupper() or isLowerOrUnderscore(newLines[j - 1][d]) and isLowerOrUnderscore(pair[0][0])) and \
								(newLines[j][d].isupper() and pair[1][0].isupper() or isLowerOrUnderscore(newLines[j][d]) and isLowerOrUnderscore(pair[1][0])):
							isPairVerified = True
							break
						else:
							assert isPairVerified == False
							pair = next(renamingPairs)

					newLines[j - 1] = replaceWordAt(newLines[j - 1], d, pair[0])
					newLines[j] = replaceWordAt(newLines[j], d, pair[1])

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
	vocabularyFile = r'vocabularyFile.txt'
	# collectVocabulary(vocabularyFile, [r'D:\renaming\data\real\AntennaPod', r'D:\renaming\data\real\baritone', r'D:\renaming\data\real\camel', r'D:\renaming\data\real\NewPipe'])
	# exit()

	with open(vocabularyFile, 'r', encoding='utf-8') as f:
		vocabulary = set(f.read().splitlines())

	rawChangeCount = 10
	# spawnFromTemplate(r'D:\renaming\data\generated\dd\LinkedList-1.diff', vocabulary, 10)

	# for file in os.scandir(r'D:\renaming\data\generated\dd'):
	# 	if file.name.count('-') == 1:
	# 		try:
	# 			spawnFromTemplate(file.path, vocabulary, 10)
	# 		except Exception as e:
	# 			print(f'File {file.name} has error:\n' + str(e))
	#
	# exit()

	outputDir = r'D:\renaming\data\generated\dd'

	for file in os.scandir(r'D:\renaming\data\generated\original'):
		if file.is_dir() or not file.name.endswith('.java'):
			continue

		previousDiffs = []
		print(f'\nOpen {file.name}.')
		pass_ = 0
		while pass_ < rawChangeCount:
			print(f'You will need to modify {rawChangeCount - pass_} more times.')

			try:
				diffFilePath = os.path.join(outputDir, os.path.splitext(file.name)[0] + '-' + str(pass_) + '.diff')
				userInput = input('When you are done with renaming, remember save the file. Press s to skip, n to stop, anything else to continue.')
				if userInput == 's':
					print(f'{diffFilePath} is untouched.')
					pass_ += 1
					continue
				elif userInput == 'n':
					break

				diff = subprocess.check_output('git diff --no-color ' + file.name, cwd=r'D:\renaming\data\generated\original').decode(errors='ignore')
				while diff in previousDiffs:
					input('This modification is the same as one of previous ones. Please try again. Press enter.')
					diff = subprocess.check_output('git diff --no-color ' + file.name, cwd=r'D:\renaming\data\generated\original').decode(errors='ignore')

				lines = diff.splitlines(True)

				with open(diffFilePath, 'w', encoding='utf-8', newline='\n') as f:
					f.writelines(lines[4:])

				spawnFromTemplate(diffFilePath, vocabulary, 10)
				subprocess.run(f'git checkout {file.name}', cwd=r'D:\renaming\data\generated\original', stderr=subprocess.DEVNULL)

				print(r'Good job. Diff registered. File is reverted.')
				pass_ += 1
			except NotImplementedError as e:
				print(e)

# spawnFromTemplate(r'D:\renaming\neural network\tests\Test Cases\catch exception rename-ex-e.diff', vocabulary, 10)

# spawnFromTemplate(r'D:\renaming\neural network\tests\Test Cases\catch exception rename-ex-e.diff')
