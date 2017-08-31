'''This script contains the definitions for executing workload files using ycsb
and then parsing the throughput datapoints to visualize on a bubble chart'''

from subprocess import check_output, CalledProcessError, STDOUT

import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import sys

from collect_settings import open_gui

def exec_cmd(cmd):
    '''Wrapper function'''
    check_output(cmd, stderr=STDOUT, shell=True)

def load_and_run(dictionary):
    '''Load and run workload files'''
    # Start mongod
    mongod_se = []
    throughputs = {}
    # To prevent starting a mongod on the same port before the previous mongod fully stopped,
    # a temporarily solution is to start each mongod on different ports to prevent an 
    # errno 48 upon failed --fork.
    port = 27018
    for mongod in dictionary['mongod_versions']:
        print 'mongod is {}'.format(mongod)
        throughputs[mongod] = {}
        for storage_engine in dictionary['storage_engines']:
            print 'storage_engine is {}'.format(storage_engine)
            mongod_se.append('{} {}'.format(mongod, storage_engine))
            throughputs[mongod][storage_engine] = {}
            exec_cmd('pgrep mongod | xargs kill')
            print 'just killed existing mongod processes'
            # 'killall -w mongod' on Linux
            try:
                # Future work: Have the user input a config file to setup mongod
                exec_cmd('./bin/mongod-{} --fork --logpath /dev/null --dbpath data/{} --port {} --storageEngine {}'.format(\
                         mongod, storage_engine, port, storage_engine))
            except CalledProcessError as err:
                print err
                print err.output
                sys.exit(1)

            # initialize empty dictionaries
            for thread in dictionary['threads']:
                throughputs[mongod][storage_engine][thread] = {}

            for workload_file_group in range(len(dictionary['workload_files'])):
                threadgroup = dictionary['threads'][workload_file_group]
                throughputs[mongod][storage_engine][threadgroup] = []
                for workload_file in dictionary['workload_files'][workload_file_group]:
                    print 'loading {}...'.format(workload_file)
                    exec_cmd('./bin/ycsb load mongodb -s -P {} -p mongodb.url=localhost:{}'.format(workload_file, port))
                    print 'running {}...'.format(workload_file)
                    exec_cmd('./bin/ycsb run mongodb -s -P {} -p mongodb.url=localhost:{}'.format(workload_file, port))
                    result = parse_throughput(workload_file)
                    throughputs[mongod][storage_engine][threadgroup].append(result)

            print 'done, going to kill this mongod'
            exec_cmd('pgrep mongod | xargs kill')
            port += 1

    dictionary['mongod_se'] = mongod_se
    dictionary['throughputs'] = throughputs

def parse_throughput(workload_file):
    '''Return the throughput number from an .out file'''
    working_file = open(workload_file + '.out')
    line = working_file.readline()
    while 'Throughput' not in line:
        line = working_file.readline()
    line = line.split()
    working_file.close()
    return float(line[-1])

def ratios_to_label(dictionary, index, label):
    '''Add and format the workload ratios to a given label'''
    static_workloads = ['read', 'update', 'scan', 'insert']
    for rusi in static_workloads:
        if dictionary['workload_ratios'][index][rusi] > 0:
            # At this scale, concatenation in Python 2.4+ can be faster than append/join.
            label += '{}: {} '.format(rusi.title(), \
                     str(int(dictionary['workload_ratios'][index][rusi]*100)))
    return label

def choose_color(index):
    '''Cycle through an array of colors'''
    colors = ['#7e1e9c', '#15b01a', '#0343df', '#e50000', '#029386', '#c20078', '#75bbfd',
              '#06470c', '#9a0eea', '#840000', '#b9a281', '#040273', '#fc5a50', '#5170d7',
              '#1fa774']
    if index < len(colors):
        return colors[index]
    else:
        return colors[index / len(colors)]

def create_bubble_chart(dictionary):
    '''Feed the data points into the bubble chart'''
    x_axis = []
    for thread in dictionary['threads']:
        x_axis.append(int(thread))
    dataframe_data = {}
    labels = []
    y_s_axes = []
    for mongod in dictionary['mongod_versions']:
        for storage_engine in dictionary['storage_engines']:
            for workload_index in range(len(dictionary['workload_ratios'])):
                throughputs = []
                label = ''
                label = ratios_to_label(dictionary, workload_index, label)
                label += '- {} {}'.format(mongod, storage_engine)
                labels.append(label)
                for thread in dictionary['threads']:
                    throughputs.append(int(dictionary['throughputs'][mongod][storage_engine]\
                                       [thread][workload_index]))
                bubble_size_arr = [dictionary['workload_ranges'][workload_index]] * \
                                  len(dictionary['threads'])
                y_s_axes.append((np.array(throughputs), np.array(bubble_size_arr)))

    # Collect all the y and s arrays into one dictionary for the dataframe
    for tuple_index in range(len(y_s_axes)):
        dataframe_data['{}.y'.format(tuple_index)] = y_s_axes[tuple_index][0]
        dataframe_data['{}.s'.format(tuple_index)] = y_s_axes[tuple_index][1]
    dataframe_data['x'] = np.array(x_axis)
    dataframe_columns = list(dataframe_data.keys())
    dataframe = pd.DataFrame(dataframe_data, columns=dataframe_columns)

    # Create the plot group by group
    for tuple_index in range(len(y_s_axes)):
        if tuple_index == 0:
            axes = dataframe.plot(kind='scatter', x='x', y='{}.y'.format(tuple_index), \
                 s=(dataframe['{}.s'.format(tuple_index)]+2)*15, color=choose_color(tuple_index), \
                 label=labels[tuple_index], alpha=0.5)
        else:
            dataframe.plot(kind='scatter', x='x', y='{}.y'.format(tuple_index), \
                 s=(dataframe['{}.s'.format(tuple_index)]+2)*15, color=choose_color(tuple_index), \
                 label=labels[tuple_index], ax=axes, alpha=0.5)

    axes.set_xlabel("# threads")
    axes.set_ylabel("Throughput (ops / sec)")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, shadow=True)
    plt.show()

if __name__ == "__main__":
    data = open_gui()
    print 'executing workload files...'
    load_and_run(data)
    print data
    print 'finished loading / running workload files'
    create_bubble_chart(data)
