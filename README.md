# MongoDB YCSB Charts

## Introduction
This program creates a bubble chart. The y axis is the throughput as measured in ops / sec. The x axis shows number of threads the trials are run with. 
The size of the bubble is the absolute difference in proportions among read/update/scan/insert parameters (this is more of a visual aid to estimate the range of the proportions, by far not a scientific proxy). 
The color of the bubble denotes the combination of its storage engine, mongod version, and workload ratio.

## How to run
To run, make sure everything required to run YCSB is installed (e.g. Maven and Java JDK). If running for the first time after cloning this repo, run ```mvn clean package```. Next, ensure that Python 2.7, pandas, appJar, matplotlib, and numpy are installed. Then run ```python create_chart.py``` to start.

## What works
This program has been tested on Mac OSX 10.12. 

## What needs work
Two primary issues exist:
First, only the system's default storage engine may currently be run. For instance, if 

Second, if all  


## Further information
This repo is based on the 10gen/MongoDB maintained partial YCSB repo with a few additional files, mainly create_chart.py and collect_settings.py. The files here should be mergable with the original project if necessary.  These files can be built and run standalone, but only MongoDB client and core YCSB libraries are provided.

For more details, see https://github.com/10gen-labs/YCSB/wiki and [ycsb-mongodb/mongodb/README.md](ycsb-mongodb/mongodb/README.md).
