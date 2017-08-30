from itertools import cycle, islice
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
    throughputs = {}
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
                exec_cmd('./bin/mongod-{} --fork --syslog --storageEngine={}'.format(mongod, storage_engine))
            except CalledProcessError as err:
                print err
                print err.output
            # group_throughputs = []
            # initialize empty dictionaries
            for thread in dictionary['threads']:
                throughputs[mongod][storage_engine][thread] = {}

            for workload_file_group in range(len(dictionary['workload_files'])):
                threadgroup = dictionary['threads'][workload_file_group]
                throughputs[mongod][storage_engine][threadgroup] = []
                for workload_file in dictionary['workload_files'][workload_file_group]:
                    print 'loading {}...'.format(workload_file)
                    exec_cmd('./bin/ycsb load mongodb -s -P {}'.format(workload_file))
                    print 'running {}...'.format(workload_file)
                    exec_cmd('./bin/ycsb run mongodb -s -P {}'.format(workload_file))
                    result = parse_throughput(workload_file)
                    throughputs[mongod][storage_engine][threadgroup].append(result)

            # throughputs.append(group_throughputs)
            print 'done, going to kill this mongod'
            exec_cmd('pgrep mongod | xargs kill')

    dictionary['mongod_se'] = mongod_se
    dictionary['throughputs'] = throughputs
    print(dictionary)

def parse_throughput(workload_file):
    file = open(workload_file + '.out')
    line = file.readline()
    while 'Throughput' not in line:
        line = file.readline()
    line = line.split()
    # throughput_arr.append(float(line[-1]))
    return float(line[-1])

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

def ratios_to_label(dictionary, index, label):
    static_workloads = ['read', 'update', 'scan', 'insert']
    for rusi in static_workloads:
        if dictionary['workload_ratios'][index][rusi] > 0:
            # At this scale, concatenation in Python 2.4+ can be faster than append/join.
            label += '{}: {} '.format(rusi.title(), str(int(dictionary['workload_ratios'][index][rusi]*100)))
    return label

def choose_color(index):
    # colors = ['xkcd:sky blue', 'xkcd:purple', 'xkcd:green','xkcd:blue',
    #           'xkcd:teal', 'xkcd:maroon', 'xkcd:rose', 'xkcd:navy blue', 'xkcd:blue green'
    #           'xkcd:leaf green', 'xkcd:eggplant', 'xkcd:pinkish red', 'xkcd:cornflower blue',
    #           'xkcd:bright orange', 'xkcd:light mauve', 'xkcd:midnight purple'  ]
    colors = ['#7e1e9c', '#15b01a', '#0343df', '#e50000', '#029386', '#c20078', '#75bbfd']
    if index < len(colors):
        return colors[index]
    else:
        return colors[index / len(colors)]

def create_bubble_chart(dictionary):
    # input dictionary: 
    ''' 
    {'workload_files': [['fc20fl10rc20000-r95u5s0i0-t2', 'fc20fl10rc20000-r50u50s0i0-t2'], ['fc20fl10rc20000-r95u5s0i0-t4', 'fc20fl10rc20000-r50u50s0i0-t4']], 
    'throughputs': {'3.4.7': {'wiredTiger': {'2': [4161.464835622139, 3619.254433586681], '4': [5678.591709256105, 4640.371229698376]}}, 
    '3.5.10': {'wiredTiger': {'2': [4420.866489832007, 3463.8032559750604], '4': [5583.472920156337, 4593.477262287552]}}}, 
    'workload_ratios': [{'read': 0.95, 'insert': 0.0, 'update': 0.05, 'scan': 0.0}, {'read': 0.5, 'insert': 0.0, 'update': 0.5, 'scan': 0.0}], 
    'storage_engines': ['wiredTiger'], 
    'workload_ranges': [90, 0, 90, 0], 
    'mongod_se': ['3.4.7 wiredTiger', '3.5.10 wiredTiger'], 
    'threads': ['2', '4'], 
    'workload_labels': ['RUSI: 0.95-0.05-0.0-0.0', 'RUSI: 0.5-0.5-0.0-0.0', 'RUSI: 0.95-0.05-0.0-0.0', 'RUSI: 0.5-0.5-0.0-0.0'], 
    'mongod_versions': ['3.4.7', '3.5.10']}
    '''
    # for each group, y = [], s = []
    x_axis = []
    for t in dictionary['threads']:
        x_axis.append(int(t))
    df_data = {}
    df_columns = []
    labels = []
    y_s_axes = []
    for mongod in dictionary['mongod_versions']:
        for se in dictionary['storage_engines']:
            for w in range(len(dictionary['workload_ratios'])):
                throughputs = []
                label = ''
                label = ratios_to_label(dictionary, w, label)
                label += '- {} {}'.format(mongod, se)
                labels.append(label)
                for t in dictionary['threads']:
                    throughputs.append(int(dictionary['throughputs'][mongod][se][t][w]))
                bubble_size_arr = [dictionary['workload_ranges'][w]] * len(dictionary['threads'])
                y_s_axes.append((np.array(throughputs), np.array(bubble_size_arr)))

    # Collect all the y and s arrays into one dictionary for the dataframe
    for tuple_index in range(len(y_s_axes)):
        df_data['{}.y'.format(tuple_index)] = y_s_axes[tuple_index][0]
        df_data['{}.s'.format(tuple_index)] = y_s_axes[tuple_index][1]
    df_data['x'] = np.array(x_axis)
    df_columns = list(df_data.keys())
    df = pd.DataFrame(df_data, columns=df_columns)
    colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(df)))


    # Create the plot group by group
    for tuple_index in range(len(y_s_axes)):
        if tuple_index == 0:
            ax = df.plot(kind='scatter', x='x', y='{}.y'.format(tuple_index), \
                 s=(df['{}.s'.format(tuple_index)]+2)*15, color=choose_color(tuple_index), \
                 label=labels[tuple_index], alpha=0.5)
        else:
            df.plot(kind='scatter', x='x', y='{}.y'.format(tuple_index), \
                 s=(df['{}.s'.format(tuple_index)]+2)*15, color=choose_color(tuple_index), \
                 label=labels[tuple_index], ax=ax, alpha=0.5)

    # x = [2, 4, 6, 8, 10]
    # y = [2000, 2500, 3000, 3500, 3800]
    # s = [25, 1, 50, 25, 25]

    # b = [1000, 2300, 3200, 3600, 5000]
    # c = [30, 2, 93, 25, 25]

    # df = pd.DataFrame(dict(x=x, y=y, s=s, b=b, c=c), columns=['x', 'y', 's', 'b', 'c'])
    # ax = df.plot(kind='scatter', x='x', y='b', s=df['c']*20, color='DarkGreen', label='Group 1', alpha=0.5)
    # bx = df.plot(kind='scatter', x='x', y='b', s=df['c']*25, color='DarkOrange', label='Group 2', ax=ax, alpha=0.5)

    # df.plot(kind='scatter', x='x', y='y', s=df['s']*20, color='DarkBlue', label='Group 3', ax=ax, alpha=0.5)

    ax.set_xlabel("# threads")
    ax.set_ylabel("Throughput (ops / sec)")
    plt.legend(loc='center left', bbox_to_anchor=(0, 1))
    plt.show()

if __name__ == "__main__":
    #dictionary = open_gui()
    #print(dictionary)
    # print 'executing workload files...'
    #load_and_run(dictionary)
    # print 'finished loading / running workload files'
    # create_bar_chart(parse_throughputs(dictionary))
    dictionary = {'workload_files': [['fc20fl10rc20000-r95u5s0i0-t2', 'fc20fl10rc20000-r50u50s0i0-t2'], ['fc20fl10rc20000-r95u5s0i0-t4', 'fc20fl10rc20000-r50u50s0i0-t4']], 'throughputs': {'3.4.7': {'wiredTiger': {'2': [4161.464835622139, 3619.254433586681], '4': [5678.591709256105, 4640.371229698376]}}, '3.5.10': {'wiredTiger': {'2': [4420.866489832007, 3463.8032559750604], '4': [5583.472920156337, 4593.477262287552]}}}, 'workload_ratios': [{'read': 0.95, 'insert': 0.0, 'update': 0.05, 'scan': 0.0}, {'read': 0.5, 'insert': 0.0, 'update': 0.5, 'scan': 0.0}], 'storage_engines': ['wiredTiger'], 'workload_ranges': [90, 0, 90, 0], 'mongod_se': ['3.4.7 wiredTiger', '3.5.10 wiredTiger'], 'threads': ['2', '4'], 'workload_labels': ['RUSI: 0.95-0.05-0.0-0.0', 'RUSI: 0.5-0.5-0.0-0.0', 'RUSI: 0.95-0.05-0.0-0.0', 'RUSI: 0.5-0.5-0.0-0.0'], 'mongod_versions': ['3.4.7', '3.5.10']}
    create_bubble_chart(dictionary)
