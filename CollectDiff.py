import os

from git import Repo


def getChangeType(diffContent: str):
	"""
	Find out if the diff content has added lines, removed lines, or both

	:param diffContent:
	:return: 'add', 'remove', 'both'
	"""

	lines = diffContent.splitlines()
	firsts = [line[0] for line in lines]

	hasAdd = '+' in firsts
	hasRemove = '-' in firsts
	if hasAdd and hasRemove:
		return 'both'
	if hasAdd:
		return 'add'
	if hasRemove:
		return 'delete'

	raise Exception('No change in diff.')


if __name__ == '__main__':
	repoPath = r'D:\renaming\data\github\NewPipe'
	diffFolder = r'D:\renaming\data\real\NewPipe'
	if not os.path.exists(diffFolder):
		os.makedirs(diffFolder)

	# rorepo is a Repo instance pointing to the git-python repository.
	# For all you know, the first argument to Repo is a path to the repository
	# you want to work with
	repo = Repo(repoPath)

	max_count = None
	for commit in repo.iter_commits('dev', max_count=max_count, first_parent=True):
		print(commit.hexsha)
		if len(commit.parents) == 0:
			print('reach root commit')
			break

		changedFiles = commit.parents[0].diff(commit, create_patch=True)
		for i in range(len(changedFiles)):
			diff = changedFiles[i]
			if diff.a_path and diff.b_path and diff.a_path.lower().endswith('.java'):
				# create_patch must be True to get diff.diff
				if len(diff.diff) == 0:
					continue

				print(diff.a_path)

				content = diff.diff.decode()

				try:
					diffFileName = f'{commit.hexsha}-{i}-{getChangeType(content)}.diff'
					with open(os.path.join(diffFolder, diffFileName), 'w', encoding='utf-8') as f:
						f.write(content)
				except Exception as e:
					print(str(e) + ' Possibly a file renaming.')
