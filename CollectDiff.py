import io
import logging
import multiprocessing
import os
import subprocess
import sys

from git import Repo


def ignoreNoNewlineAtEnd(commit, file):
	with io.BytesIO(commit.parents[0].tree.join(file.a_path).data_stream.read()) as f:
		a = f.read().decode(errors='ignore')
	if len(a) > 0 and a[-1] != '\n':
		a += '\n'
	with io.BytesIO(commit.tree.join(file.b_path).data_stream.read()) as f:
		b = f.read().decode(errors='ignore')
	if len(b) > 0 and b[-1] != '\n':
		b += '\n'

	pid = os.getpid()
	with open(rf'B:\{pid}-a.txt', 'w', encoding='utf-8', newline='\n') as f:
		f.write(a)

	with open(rf'B:\{pid}-b.txt', 'w', encoding='utf-8', newline='\n') as f:
		f.write(b)

	output = subprocess.run([diffPath, '-u', rf'B:\{pid}-a.txt', rf'B:\{pid}-b.txt'], check=False, capture_output=True, text=True, encoding='utf-8').stdout
	if output == '':
		return ''

	lines2 = output.splitlines()

	assert lines2[0].startswith('---')
	assert lines2[1].startswith('+++')
	assert lines2[2].startswith('@@')

	lines = lines2[2:]
	return '\n'.join(lines)


def collectDiffFromRepo(repoPath, diffFolder, branch='master'):
	if not os.path.exists(diffFolder):
		os.makedirs(diffFolder)

	print(f'working on {os.path.basename(repoPath)}')
	repo = Repo(repoPath)

	max_count = None
	# first_parent=False because repositories often use pull-request pattern that the first parent often aggregates many changes.
	for commit in repo.iter_commits(branch, max_count=max_count, first_parent=False):
		if len(commit.parents) == 0:
			logging.info(f'reach root commit {commit.hexsha}')
			continue
		# first_parent=False makes sure all parents of a merge commit will be iterated.
		if len(commit.parents) == 2:
			logging.debug(f'Ignore merge commit {commit.hexsha}')
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

				c = diff.diff.decode(errors='ignore')

				if r"\ No newline at end of file" in c:
					c = ignoreNoNewlineAtEnd(commit, diff)
					assert r"\ No newline at end of file" not in c

				content += c

			content = content.replace('\r\n', '\n').replace('\r', '\n')

			diffFileName = f'{commit.hexsha}.diff'
			with open(os.path.join(diffFolder, diffFileName), 'w', encoding='utf-8', newline='\n') as f:
				f.write(content)

	print(f'finished {os.path.basename(repoPath)}')


diffPath = r'C:\Program Files\Git\usr\bin\diff.exe'

if __name__ == '__main__':

	repos = [
		"AntennaPod",
		"baritone",
		"camel",
		"camunda-bpm-platform",
		("dbeaver", 'devel'),
		"EhViewer",
		"Geyser",
		"iceberg",
		"Java",
		"java-design-patterns",
		"jenkins",
		"keycloak",
		"libgdx",
		"Mindustry",
		("NewPipe", 'dev'),
		"openapi-generator",
		"quarkus",
		"Signal-Android",
		("spring-petclinic", 'main'),
		"strimzi-kafka-operator",
		"testcontainers-java",
		"tutorials",
		"wiremock"
	]

	try:
		p = sys.argv.index('--log')
		logLevel = sys.argv[p + 1]
		numeric_level = getattr(logging, logLevel.upper(), None)
		logging.basicConfig(level=numeric_level)
	except:
		pass

	if hasattr(os, 'sched_getaffinity'):
		availableCpus = len(os.sched_getaffinity(0))
	else:
		availableCpus = os.cpu_count()
	logging.info(f'Use {availableCpus} CPUs.')
	res = []
	with multiprocessing.Pool(availableCpus - 1) as p:

		for repo in repos:
			if type(repo) is tuple:
				res.append(p.apply_async(collectDiffFromRepo, (r'D:\renaming\data\github\\' + repo[0], r'D:\renaming\data\real\\' + repo[0], repo[1])))
				# collectDiffFromRepo(r'D:\renaming\data\github\\' + repo[0], r'D:\renaming\data\real\\' + repo[0], repo[1])
			else:
				res.append(p.apply_async(collectDiffFromRepo, (r'D:\renaming\data\github\\' + repo, r'D:\renaming\data\real\\' + repo)))
				# collectDiffFromRepo(r'D:\renaming\data\github\\' + repo, r'D:\renaming\data\real\\' + repo)

		[r.get() for r in res]
