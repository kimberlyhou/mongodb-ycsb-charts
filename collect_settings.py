'''This script contains the definitions for showing a GUI to the user
in order to collect options the user would like to select for a given
comparison'''

from appJar import gui

# Future: Save settings to a txt working_file and enable reloading of a setting from that working_file

def open_gui():
    '''Show GUI to user'''
    result_object = {}

    def start_gui():
        '''Entrypoint function'''
        app.addLabel('label_dimensions', \
                     'Welcome! How many workload ratios would you like to compare?')
        app.addOptionBox('dimension_comparisons', range(1, 5))
        app.addButton('Next', specify_dim_comparisons)
        app.go()

    def specify_dim_comparisons(btn):
        '''Second step'''
        app.removeButton('Next')
        app.disableOptionBox('dimension_comparisons')
        num_dimensions = int(app.getOptionBox('dimension_comparisons'))

        # Ensure the labeled mongod binary is in the bin/ directory of this repo.      
        for i in range(num_dimensions):
            app.addLabelNumericEntry('Read Proportion #{}'.format(i))
            app.addLabelNumericEntry('Update Proportion #{}'.format(i))
            app.addLabelNumericEntry('Scan Proportion #{}'.format(i))
            app.addLabelNumericEntry('Insert Proportion #{}'.format(i))
            app.setEntryDefault('Read Proportion #{}'.format(i), 0.25)
            app.setEntryDefault('Update Proportion #{}'.format(i), 0.25)
            app.setEntryDefault('Scan Proportion #{}'.format(i), 0.25)
            app.setEntryDefault('Insert Proportion #{}'.format(i), 0.25)

        app.addLabel('label_se',
                     'Choose at least one storage engine to compare:')
        storage_engines = {'wiredTiger' : False, 'mmapv1' : False}
        app.addProperties('Storage engines', storage_engines)
        app.addLabel('label_mongod',
                     'Choose at least one mongod version to compare:')
        mongod_versions = {'3.4.7' : False, '3.5.10' : False}
        app.addProperties('Mongod versions', mongod_versions)

        app.addButton('Next', choose_num_trials)

    def choose_num_trials(btn):
        '''Choose # groups and # threads per group'''
        app.removeButton('Next')
        app.addLabel('label_num_trials', \
             'How many trials would you like to compare? \
             Each trial has a different # of threads.')
        app.addOptionBox('num_trials', ['- # trials -', 1, 2, 3, 4, 5, 6, 7, 8])
        app.addButton('Next', specify_thread_comparisons)

    def specify_thread_comparisons(btn):
        '''Show x boxes to input threads per group'''
        app.removeButton('Next')
        app.disableOptionBox('num_trials')
        num_trials = int(app.getOptionBox('num_trials'))
        for i in range(num_trials):
            app.addLabel('label_num_threads_group' + str(i), '# threads for group ' + str(i))
            app.addOptionBox('num_threads_group' + str(i), range(1, 25))
        show_remaining_options()

    def show_remaining_options():
        '''Remaining options are fixed'''
        app.addLabelNumericEntry('Field Count')
        app.setEntryDefault('Field Count', 50)
        app.addLabelNumericEntry('Field Length')
        app.setEntryDefault('Field Length', 10)
        app.addLabelNumericEntry('Record Count')
        app.setEntryDefault('Record Count', 5000000)
        app.addLabelNumericEntry('Operation Count')
        app.setEntryDefault('Operation Count', 10000000)
        app.addLabelNumericEntry('Max Execution Time')
        app.setEntryDefault('Max Execution Time', 5000)
        app.addButton('Run', validate_before_write)

    def check_proportions(num_dimensions):
        '''Validate and add ratios to global variable result_object'''
        workload_ratios = []
        for i in range(num_dimensions):
            read = app.getEntry('Read Proportion #{}'.format(i))
            update = app.getEntry('Update Proportion #{}'.format(i))
            scan = app.getEntry('Scan Proportion #{}'.format(i))
            insert = app.getEntry('Insert Proportion #{}'.format(i))
            if read + update + scan + insert != 1:
                app.errorBox('errorWorkload', 'Error: Proportions have to add up to 1')
                return False
            workload_ratios.append(dict(read=read, update=update, scan=scan, insert=insert))
        result_object['workload_ratios'] = workload_ratios
        return True

    def validate_threads_input(num_trials):
        '''Validate before returning threads'''
        threads = []
        # Collect number of threads selected for each run with validation check
        for i in range(num_trials):
            threads.append(app.getOptionBox('num_threads_group' + str(i)))
        if len(threads) != len(set(threads)):
            revise = app.yesNoBox('warningDuplicateTrials',
                                  'Warning: At least one of your trials is a duplicate.'\
                                  'Would you like to revise?')
            if revise:
                return (False, [])
        return (True, threads)

    def check_properties(prop_name):
        '''Validate before returning properties'''
        dictionary = app.getProperties(prop_name)
        lst = []
        for key, value in dictionary.iteritems():
            if value:
                lst.append(key)
        if len(lst) == 0:
            app.errorBox('error_{}'.format(prop_name),\
                         'Error: Please select at least one property for {}.'.format(prop_name))
            return (False, [])
        return (True, lst)

    def validate_before_write(btn):
        '''When the run button is pressed, validate before writing'''
        app.disableButton('Run')
        num_trials = int(app.getOptionBox('num_trials')) 
        num_dimensions = int(app.getOptionBox('dimension_comparisons'))
        check_threads = validate_threads_input(num_trials)
        check_se = check_properties('Storage engines')
        check_mongod = check_properties('Mongod versions')
        valid = \
            check_threads[0] and \
            check_se[0] and \
            check_mongod[0] and \
            check_proportions(num_dimensions)
        if valid:
            write_workload_files(num_trials, num_dimensions, check_threads[1], \
                                 check_se[1], check_mongod[1])
        else:
            app.enableButton('Run')

    def write_workload_files(num_trials, num_dimensions, threads, storage_engines, mongods):
        '''Create workload files for all specified settings and set result_object'''
        field_count = int(app.getEntry('Field Count'))
        field_length = int(app.getEntry('Field Length'))
        record_count = int(app.getEntry('Record Count'))
        operation_count = int(app.getEntry('Operation Count'))
        max_exec_time = int(app.getEntry('Max Execution Time'))

        workload_files = []
        workload_labels = []
        workload_ranges = []

        for thread in range(num_trials):
            files_threadgroup = []
            for dim in range(num_dimensions):
                read = result_object['workload_ratios'][dim]['read']
                update = result_object['workload_ratios'][dim]['update']
                scan = result_object['workload_ratios'][dim]['scan']
                insert = result_object['workload_ratios'][dim]['insert']
                workload_labels.append('RUSI: {}-{}-{}-{}'.format(read, update, scan, insert))
                absolute_range = abs(abs(abs(int(read * 100) - int(update * 100)) - int(scan * 100)) - int(insert * 100))
                workload_ranges.append(absolute_range)

                filename = 'fc{}fl{}rc{}-r{}u{}s{}i{}-t{}'.format(field_count,
                    field_length, record_count, int(read * 100), int(update * 100),
                    int(scan * 100), int(insert * 100), threads[thread])

                working_file = open(filename, 'w')
                working_file.write('fieldcount={}\n'.format(field_count))
                working_file.write('fieldlength={}\n'.format(field_length))
                working_file.write('recordcount={}\n'.format(record_count))
                working_file.write('operationcount={}\n'.format(operation_count))
                working_file.write('maxexecutiontime={}\n'.format(max_exec_time))
                working_file.write('threadcount={}\n'.format(threads[thread]))
                working_file.write('workload=com.yahoo.ycsb.workloads.CoreWorkload\n')
                working_file.write('exportfile={}\n'.format(filename + '.out'))
                working_file.write('readallfields=true\n\n')
                working_file.write('readproportion={}\n'.format(read))
                working_file.write('updateproportion={}\n'.format(update))
                working_file.write('scanproportion={}\n'.format(scan))
                working_file.write('insertproportion={}\n\n'.format(insert))
                working_file.write('requestdistribution=zipfian\n')
                working_file.close()
                files_threadgroup.append(filename)
                print '{} has been saved.'.format(filename)
            workload_files.append(files_threadgroup)

        result_object['storage_engines'] = storage_engines
        result_object['mongod_versions'] = mongods
        result_object['workload_files'] = workload_files
        result_object['workload_labels'] = workload_labels
        result_object['workload_ranges'] = workload_ranges
        result_object['threads'] = threads
        app.stop()

    app = gui()
    start_gui()
    return result_object
