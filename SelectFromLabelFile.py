import os
import shutil

if __name__ == '__main__':
	group = 'NewPipe'

	labelFile = rf"D:\renaming\data\real\{group}.txt"
	sourceFolder = rf'D:\renaming\data\real\{group}'
	yesFolder = rf'D:\renaming\data\samples\{group}\yes'
	noFolder = rf'D:\renaming\data\samples\{group}\no'

	os.makedirs(yesFolder, exist_ok=True)
	os.makedirs(noFolder, exist_ok=True)

	yesCases = []
	noCases = []

	with open(labelFile, 'r', encoding='utf-8') as fileName:
		for line in fileName:
			line = line.strip()
			parts = line.split('|')
			id = parts[0]
			differenceIndexes = parts[1]
			label = parts[2]
			if len(parts) > 3:
				message = parts[3]

			if label == 'y':
				yesCases.append(id)
			elif label == 'n':
				noCases.append(id)

	for fileName in yesCases:
		shutil.copy(os.path.join(sourceFolder, fileName + '.diff'), yesFolder)

	for fileName in noCases:
		shutil.copy(os.path.join(sourceFolder, fileName + '.diff'), noFolder)

	noFolder = r'D:\renaming\data\generated\dataset\presumable\no'
	numberOfFilesToCollect = 1000
	for file in os.scandir(sourceFolder):
		if numberOfFilesToCollect == 0:
			break
		if file.is_dir():
			continue

		if file.name not in yesCases and file.stat().st_size <= 5 * 1024:
			# assume the file is a no-renaming case
			shutil.copy(file.path, noFolder)
			numberOfFilesToCollect -= 1
