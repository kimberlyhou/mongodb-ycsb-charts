from subprocess import check_output, CalledProcessError, STDOUT
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

from collect_settings import open_gui

# Future: Should x axis be something other than numThreads?
# Add other dimensions to be compared at the same time
# Save settings to a file and enable reloading of a setting from that file (last 20?)

def exec_cmd(cmd):
    '''Wrapper function'''
    check_output(cmd, stderr=STDOUT, shell=True)

def load_and_run(dictionary):
    '''Load and run workload files'''
    # Start mongod
    for mongod in dictionary['mongod_versions']:
        for storage_engine in dictionary['storage_engines']:
            exec_cmd('pgrep mongod | xargs kill')
            print 'just killed existing mongod processes'
            # 'killall -w mongod'
            try:
                # Suggestion: Have the user input a config file to setup mongod
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

    #example data frame
    x = [5, 10, 20, 30, 5, 10, 20, 30, 5, 10, 20, 30]
    y = [100, 100, 200, 200, 300, 300, 400, 400, 500, 500, 600, 600]
    s = [5, 10, 20, 30, 5, 10, 20, 30, 5, 10, 20, 30]
    users = ['mark', 'mark', 'mark', 'rachel', 'rachel', 'rachel', 'jeff',
             'jeff', 'jeff', 'lauren', 'lauren', 'lauren']

    # df = pd.DataFrame(dict(x=x, y=y, users=users)

    # # ax = df.plot.scatter(x='x', y='y', s=s, alpha=0.5)
    # # ax = df.plot.scatter(x='x', y='y', alpha=0.5)

    df = pd.DataFrame(dict(x=x, y=y, s=s, users=users))

    fig, ax = plt.subplots(facecolor='w')

    for key, row in df.iterrows():
        ax.scatter(row['x'], row['y'], s=row['s']*5, alpha=.5)
        ax.annotate(row['users'], xy=(row['x'], row['y']))

    # for i, txt in enumerate(df.users):
    #     ax.annotate(txt, (df.x.iat[i],df.y.iat[i]))
    plt.show()

if __name__ == "__main__":
    dictionary = open_gui()
    print 'executing workload files...'
    load_and_run(dictionary)
    print 'finished loading / running workload files'
    create_bar_chart(parse_throughputs(dictionary))
