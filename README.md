# MongoDB YCSB Charts

## Introduction
This program creates a bubble chart. The y axis is the throughput as measured in ops / sec. The x axis shows number of threads the trials are run with. 
The size of the bubble is the absolute difference in proportions among read/update/scan/insert parameters (this is more of a visual aid to estimate the range of the proportions, by far not a scientific proxy). 
The color of the bubble denotes the combination of its storage engine, mongod version, and workload ratio.

## How to run
Make sure everything required of YCSB is installed (e.g. Maven and Java JDK). If running for the first time after cloning this repo, run ```mvn clean package```. Next, ensure that Python 2.7, pandas, appJar, matplotlib, and numpy are installed. Then run ```python create_chart.py``` to start.

## What works
Through a GUI, the script takes in several settings for running YCSB, how many trials you'd like to compare, and the settings for each trial. The script can also compare different mongod versions (binary files besides 3.4.7 and 3.5.10 need to be added in manually) and storage engines. Workload files are created and saved, then each workload file is loaded and executed by YCSB through the command line for all specified mongod / storage engine combinations. Each .out file resulting from these executions is parsed for the throughput metric, and the number is saved in an accumulating dictionary the program keeps for the duration of its lifetime. At the end, all throughput data points are fed into a bubble chart, and the resulting bubble chart appears.

This program has been tested on Mac OSX 10.12.

An example run is as follows:


## What needs work
The following known issues exist: 
First, the more trials, workload options, and mongod versions/storage engines you want to compare, the more patient you'd have to be - exponentially. While comparing 1-2 trials and 1-2 mongod versions may take a couple minutes to create the bubble chart, the entire operation could take upwards of 1 hour 20 minutes to eventually create the bubble chart if all the options are maxed out (e.g. 4 workload ratios, 8 thread groups, and 2 mongod versions each are compared). The slowdown occurs when MongoDB is writing to the log after executing each YCSB workload file.
Keep in mind YCSB has to load and run all the different workload ratios for all specified thread # groups for every unique mongod/storage engine combination. The solution to this could be to create mongod .conf files ahead of time and add them to the repo, allowing the Python script to run mongod based on these configuration files instead of just via the command line. In particular, the configuration files could have settings such as systemLog: quiet: true to limit the amount that MongoDB logs. These settings could add robustness from forking failure and potentially increase speed of the overall operation.  

Second, if the max execution time is too low or YCSB encounters a one-off problem with loading / running a workload file, this program isn't robust enough to handle such situations, resulting in a hang. Exiting the program after a set timeout limit is reached or restarting a failed command based on the error would help. 

Third, depending on how the bubbe chart comes out, the legend may need to be repositioned in order to see all the bubbles. If the entire program runs and the bubble chart comes out like this (even after enlarging the window), a workaround for the current version of the script is to take the final dictionary of data printed to stdout after all the executions and then feed it into the create_bubble_chart function, running only that function after tweaking the legend position parameters. Probably the best solution is to shrink the entire graph and move the legend outside the plot without having the window cut it off.

## Further information
This repo is based on the 10gen/MongoDB maintained partial YCSB repo with a few additional files, mainly create_chart.py and collect_settings.py. The files here should be mergable with the original project if necessary.  These files can be built and run standalone, but only MongoDB client and core YCSB libraries are provided.

For more details, see https://github.com/10gen-labs/YCSB/wiki and https://github.com/mongodb-labs/YCSB/blob/master/ycsb-mongodb/mongodb/README.md.
