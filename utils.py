import os
import sys


def getParallelismHelp(short: bool):
	if short:
		return '--parallel num'
	else:
		return '--parallel\t\tSpecify the number of CPUs to use. By default the program will use all CPUs the main process can use.'


def getParallelism() -> int:
	"""
	get user specified parallelism or default value
	:return:
	"""

	try:
		p = sys.argv.index('--parallel')
		parallel = int(sys.argv[p + 1])
	except:
		if hasattr(os, 'sched_getaffinity'):
			parallel = len(os.sched_getaffinity(0))
		else:
			parallel = os.cpu_count()

	return parallel
