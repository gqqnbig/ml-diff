import os

from git import Repo


# def getChangeType(diffContent: str):
# 	"""
# 	Find out if the diff content has added lines, removed lines, or both
#
# 	:param diffContent:
# 	:return: 'add', 'remove', 'both'
# 	"""
#
# 	lines = diffContent.splitlines()
# 	firsts = [line[0] for line in lines]
#
# 	hasAdd = '+' in firsts
# 	hasRemove = '-' in firsts
# 	if hasAdd and hasRemove:
# 		return 'both'
# 	if hasAdd:
# 		return 'add'
# 	if hasRemove:
# 		return 'delete'
#
# 	raise Exception('No change in diff.')

def collectDiffFromRepo(repoPath, diffFolder, branch='master'):
	if not os.path.exists(diffFolder):
		os.makedirs(diffFolder)

	# rorepo is a Repo instance pointing to the git-python repository.
	# For all you know, the first argument to Repo is a path to the repository
	# you want to work with
	repo = Repo(repoPath)

	max_count = None
	# first_parent=False because repositories often use pull-request pattern that the first parent often aggregates many changes.
	for commit in repo.iter_commits(branch, max_count=max_count, first_parent=False):
		if len(commit.parents) == 0:
			print(f'reach root commit {commit.hexsha}')
			break
		if len(commit.parents) == 2:
			print(f'Ignore merge commit {commit.hexsha}')
			continue
		# print(commit.hexsha)

		changedFiles = commit.parents[0].diff(commit, create_patch=True)
		# files = list(filter(lambda diff: diff.a_path and diff.b_path and diff.a_path.lower().endswith('.java') and len(diff.diff) > 0, changedFiles))
		# if len(files) == 1:
		# for simplicity, ignore commits that changes multiple files

		content = ''
		for i in range(len(changedFiles)):
			# try:
			diff = changedFiles[i]
			if diff.a_path and diff.b_path and diff.a_path.lower().endswith('.java'):
				# create_patch must be True to get diff.diff
				if len(diff.diff) == 0:
					continue

				# print(diff.a_path)

				content += diff.diff.decode(errors='ignore')
		# except UnicodeDecodeError as e:
		# 	print(e)

		if len(content) > 0:
			# if '\r\n' in content:
			content = content.replace('\r\n', '\n').replace('\r', '\n')
			# raise Exception('Currently, only Linux line ending (\\n) is supported.')

			# try:
			diffFileName = f'{commit.hexsha}.diff'
			with open(os.path.join(diffFolder, diffFileName), 'w', encoding='utf-8', newline='\n') as f:
				f.write(content)


# except Exception as e:
# 	print(str(e) + ' Possibly a file renaming.')


if __name__ == '__main__':
	repos = [
		# "AntennaPod",
		# "baritone",
		# "camel",
		# "camunda-bpm-platform",
		# ("dbeaver", 'devel'),
		# "EhViewer",
		# "Geyser",
		# "iceberg",
		# "Java",
		# "java-design-patterns",
		# "jenkins",
		# "keycloak",
		# "libgdx",
		# "Mindustry",
		# "NewPipe",
		# "openapi-generator",
		# "quarkus",
		# "Signal-Android",
		("spring-petclinic",'main'),
		"strimzi-kafka-operator",
		"testcontainers-java",
		"tutorials",
		"wiremock"]

	for repo in repos:
		print(f'Collecting {repo}')
		if type(repo) is tuple:
			collectDiffFromRepo(r'D:\renaming\data\github\\' + repo[0], r'D:\renaming\data\real\\' + repo[0], repo[1])
		else:
			collectDiffFromRepo(r'D:\renaming\data\github\\' + repo, r'D:\renaming\data\real\\' + repo)
