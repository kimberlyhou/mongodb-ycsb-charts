import numpy as np
import matplotlib.pyplot as plot
from subprocess import check_output, CalledProcessError, STDOUT

# load and run the two files
# for each file, parse the output for [THROUGHPUT] metric
# save that number

def exec_cmd(cmd):
	check_output(cmd, stderr=STDOUT, shell=True)

def load_and_run():
	exec_cmd('pwd')
#	try:
	exec_cmd('./bin/ycsb load mongodb -s -P workloads/workloadb > outputLoadb.txt')
	exec_cmd('./bin/ycsb run mongodb -s -P workloads/workloadb > outputRunb.txt')
	exec_cmd('./bin/ycsb load mongodb -s -P workloads/workloadc > outputLoadc.txt')
	exec_cmd('./bin/ycsb run mongodb -s -P workloads/workloadc > outputRunc.txt')
#	except CalledProcessError as e:
#		print(e.output)

def parse_output_files():
	with open('outputRunb.txt') as b:
		lines = b.readlines()
		for line in lines:
			if 'RunTime' in line:
				line = line.split()
				v1_runtime = line[-1]
			if 'Throughput' in line:
				line = line.split()
				v1_throughput = line[-1]
	with open('outputRunc.txt') as b:
		lines = b.readlines()
		for line in lines:
			if 'RunTime' in line:
				line = line.split()
				v2_runtime = line[-1]
			if 'Throughput' in line:
				line = line.split()
				v2_throughput = line[-1]
	v1 = [float(v1_runtime), float(v1_throughput)]
	v2 = [float(v2_runtime), float(v2_throughput)]
	return [v1, v2]

def create_chart(results):
	n_groups = len(results)
	v1_data = (results[0][0], results[0][1])
	v2_data = (results[1][0], results[1][1])
	print(type(v1_data))

	fig, ax = plot.subplots()
	index = np.arange(n_groups)
	bar_width = 0.15
	opacity = 0.8

	rects1 = plot.bar(index, v1_data, bar_width,
                 alpha=opacity,
                 color='#d6b2ff',
                 label='Workload b',
                 align='edge',
                 linewidth=0.8)

	rects2 = plot.bar(index + bar_width, v2_data, bar_width,
                 alpha=opacity,
                 color='#a6ddff',
                 label='Workload c',
                 align='edge')

	plot.xlabel('Workload')
	plot.ylabel('Metrics')
	plot.title('Metrics by Workload')
	plot.xticks(index + bar_width, ('Runtime (m/s)', 'Throughput (ops/sec)'))
	plot.legend()
	plot.tight_layout()
	plot.show()

if __name__ == '__main__':
	load_and_run()
	create_chart(parse_output_files())
