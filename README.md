# MongoDB YCSB Charts

This is based on the 10gen/MongoDB maintained partial YCSB repo with two additional files - create_chart.py and collect_settings.py.

This program creates a bubble chart. The y axis is the throughput as measured in ops / sec. The x axis shows number of threads the trials are run with. 
The size of the bubble averages the proportions of read/update/scan/insert parameters that are bigger than 0 (this is more of a visual aid to estimate the differences between the proportions, by far not a scientific proxy). 
The color of the bubble denotes the combination of its storage engine and mongod version.

To run, make sure everything required to run YCSB is installed. Next, ensure that Python 2.7, pandas, appJar, matplotlib, and numpy are installed. Then run ```python create_chart.py``` to start. 

The files here should be mergable with the original project if necessary.  These files can be built and run standalone, but only MongoDB client and core YCSB libraries are provided.

For more details, see https://github.com/10gen-labs/YCSB/wiki and [ycsb-mongodb/mongodb/README.md](ycsb-mongodb/mongodb/README.md).
