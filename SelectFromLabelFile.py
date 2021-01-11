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
