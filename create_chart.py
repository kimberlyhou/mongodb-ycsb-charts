from subprocess import check_output, CalledProcessError, STDOUT
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

from collect_settings import open_gui

# Save settings to a file and enable reloading of a setting from that file (last 20?)

def exec_cmd(cmd):
    '''Wrapper function'''
    check_output(cmd, stderr=STDOUT, shell=True)

def load_and_run(dictionary):
    '''Load and run workload files'''
    # Start mongod
    mongod_se = []
    # For every element in mongod_se, there is a list element in throughputs.
    throughputs = []
    for mongod in dictionary['mongod_versions']:
        print 'mongod is {}'.format(mongod)
        for storage_engine in dictionary['storage_engines']:
            print 'storage_engine is {}'.format(storage_engine)
            mongod_se.append('{} {}'.format(mongod, storage_engine))
            exec_cmd('pgrep mongod | xargs kill')
            print 'just killed existing mongod processes'
            # 'killall -w mongod' on Linux
            try:
                # Future work: Have the user input a config file to setup mongod
                exec_cmd('./bin/mongod-{} --fork --syslog --storageEngine={}'.format(mongod, storage_engine))
            except CalledProcessError as err:
                print err
                print err.output
            group_throughputs = []
            for workload_file in dictionary['workload_files']:
                exec_cmd('./bin/ycsb load mongodb -s -P {}'.format(workload_file))
                print 'loaded {}'.format(workload_file)
                exec_cmd('./bin/ycsb run mongodb -s -P {}'.format(workload_file))
                print 'ran {}'.format(workload_file)
                parse_throughput(workload_file, group_throughputs)
            print group_throughputs
            throughputs.append(group_throughputs)
            print 'done, going to kill this mongod'
            exec_cmd('pgrep mongod | xargs kill')

    dictionary['mongod_se'] = mongod_se
    dictionary['throughputs'] = throughputs
    print(dictionary)

def parse_throughput(workload_file, throughput_arr):
    file = open(workload_file + '.out')
    line = file.readline()
    while 'Throughput' not in line:
        line = file.readline()
    line = line.split()
    throughput_arr.append(float(line[-1]))

def create_bar_chart(dictionary):
    '''Defunct function that had worked for POC'''
    groups = len(dictionary['groups'])
    v1_data = dictionary['group_results'][0]
    v2_data = dictionary['group_results'][1]

    fig, ax = plt.subplots()
    index = np.arange(groups)
    bar_width = 0.15
    opacity = 0.8

    plt.bar(index, v1_data, bar_width, alpha=opacity, \
        color='#d6b2ff', label=dictionary['group_labels'][0], align='center', linewidth=0.8)

    plt.bar(index + bar_width, v2_data, bar_width, alpha=opacity, \
        color='#a6ddff', label=dictionary['group_labels'][1], align='center')

    plt.xlabel('# threads')
    plt.ylabel('Throughput (ops / sec)')
    plt.title('Throughput Comparison')
    plt.xticks(index + bar_width, (dictionary['threads'][0], dictionary['threads'][1]))
    plt.legend()
    # plt.tight_layout()
    plt.show()

def create_bubble_chart():
    # for each group, y = [], s = []
    x_axis = result_object['threads']


    x = [2, 4, 6, 8, 10]
    y = [2000, 2500, 3000, 3500, 3800]
    s = [25, 1, 50, 25, 25]

    b = [1000, 2300, 3200, 3600, 5000]
    c = [30, 2, 93, 25, 25]

    df = pd.DataFrame(dict(x=x_axis, y=y, s=s, b=b, c=c), columns=['# threads', 'y', 's', 'b', 'c'])
    ax = df.plot(kind='scatter', x='x', y='b', s=df['c']*20, color='DarkGreen', label='Group 1', alpha=0.5)
    # print(dict(x=x, y=y, s=s))
    df.plot(kind='scatter', x='x', y='y', s=df['s']*20, color='DarkBlue', label='Group 2', ax=ax, alpha=0.5)

    plt.show()

if __name__ == "__main__":
    # dictionary = open_gui()
    dictionary = {'workload_files': ['fc50fl10rc200000-r95u5s0i0-t1', 'fc50fl10rc200000-r50u50s0i0-t1', 'fc50fl10rc200000-r95u5s0i0-t3', 'fc50fl10rc200000-r50u50s0i0-t3'], 'workload_ratios': [{'read': 0.95, 'insert': 0.0, 'update': 0.05, 'scan': 0.0}, {'read': 0.5, 'insert': 0.0, 'update': 0.5, 'scan': 0.0}], 'storage_engines': ['wiredTiger'], 'threads': ['1', '3'], 'workload_labels': ['RUSI: 0.95-0.05-0.0-0.0', 'RUSI: 0.5-0.5-0.0-0.0', 'RUSI: 0.95-0.05-0.0-0.0', 'RUSI: 0.5-0.5-0.0-0.0'], 'mongod_versions': ['3.4.7', '3.5.10']}
    print(dictionary)
    # print 'executing workload files...'
    load_and_run(dictionary)
    # print 'finished loading / running workload files'
    # create_bar_chart(parse_throughputs(dictionary))
    #create_bubble_chart()
