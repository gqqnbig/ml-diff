import mxnet as mx
import os
import os.path
import random
import subprocess


def indexToString(indexArray):
	str = []
	for line in indexArray:
		str.append(''.join([chr(i) for i in line]))
	return '\n'.join(str)


def makeText() -> mx.ndarray.NDArray:
	textArray = (mx.ndarray.random.uniform(shape=(10, 20)) * (126 - 32) + 32).round()
	textArray = mx.ndarray.cast(textArray, dtype='int32')
	return textArray


def generateFiles(baseFolder):
	originalFiles = 20
	modifyEachFile = 20
	for i in range(originalFiles):
		originalTextIndex = makeText()

		folder = baseFolder + str(i) + r'/'
		if not os.path.exists(folder):
			os.makedirs(folder)

		f = open(folder + 'original.txt', 'w')
		f.write(indexToString(originalTextIndex.asnumpy().tolist()))
		f.write('\n')
		f.close()

		for j in range(modifyEachFile):
			workingCopy = originalTextIndex.copy()
			workingCopy = workingCopy.asnumpy().tolist()

			choice = random.choice(['delete', 'add', 'both'])

			l = round(random.uniform(0, len(workingCopy) - 1))
			c = round(random.uniform(0, len(workingCopy[l]) - 1))
			if choice == 'delete':
				del workingCopy[l][c]
			elif choice == 'add':
				newChar = int(round(random.uniform(32, 126)))
				workingCopy[l].insert(c, newChar)
			else:
				newChar = int(round(random.uniform(32, 126)))
				workingCopy[l][c] = newChar

			f = open(folder + str(j) + '.txt', 'w')
			f.write(indexToString(workingCopy))
			f.write('\n')
			f.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
	asciiRange = (32, 126)

	# generateFiles(r'D:\renaming\data\generated' '\\')

	for dir in os.scandir(r'D:\renaming\data\generated'):
		if not dir.is_dir():
			continue

		originalFile = dir.path + r'\original.txt'
		if not os.path.isfile(originalFile):
			continue

		for file in os.scandir(dir.path):
			if file.path == originalFile:
				continue

			with open(os.path.join(r'D:\renaming\data\generated', dir.name + '-' + os.path.splitext(file.name)[0] + '.diff'), 'w') as f:
				p = subprocess.run(f'git diff --no-index "{originalFile}" "{file.path}', stdout=f)