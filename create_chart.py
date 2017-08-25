from subprocess import check_output, CalledProcessError, STDOUT
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
    for mongod in dictionary['mongod_versions']:
        for storage_engine in dictionary['storage_engines']:
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
            for workload_file in dictionary['workload_files']:
                exec_cmd('./bin/ycsb load mongodb -s -P {}'.format(workload_file))
                print 'loaded {}'.format(workload_file)
                exec_cmd('./bin/ycsb run mongodb -s -P {}'.format(workload_file))
                print 'ran {}'.format(workload_file)

            print 'done, going to kill this mongod'
            exec_cmd('pgrep mongod | xargs kill')

        # Need to call parse_throughputs here actually...
    dictionary['mongod_se'] = mongod_se

def parse_throughputs(dictionary):
    '''Save throughput numbers from .out files and return modified dictionary'''
    group_results = []
    for group in dictionary['groups']:
        group_throughputs = []
        for workload_file in group:
            file = open(workload_file + '.out')
            line = file.readline()
            while 'Throughput' not in line:
                line = file.readline()
            line = line.split()
            group_throughputs.append(float(line[-1]))
        group_results.append(group_throughputs)
    dictionary['group_results'] = group_results
    print dictionary



    return dictionary

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
    dictionary = open_gui()
    print(dictionary)
    # print 'executing workload files...'
    # load_and_run(dictionary)
    # print 'finished loading / running workload files'
    # create_bar_chart(parse_throughputs(dictionary))
    # create_bubble_chart()
