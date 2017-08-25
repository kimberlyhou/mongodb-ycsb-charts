from appJar import gui

def open_gui():
    '''Show GUI to user'''
    result_object = {}
  
    def start_gui():
        '''Entrypoint function'''
        app.addLabel('label_dimensions', 'Welcome! Choose which dimension to compare:')
        app.addOptionBox('dimensions', ['Workload ratio', 'Storage engine', 'Mongod version'])
        app.addLabel('label_dimension_comparisons', 'How many comparisons along this dimension?')
        app.addOptionBox('dimension_comparisons', range(1, 5))
        app.addButton('Next', specify_dim_comparisons)
        app.go()

    def specify_dim_comparisons(btn):
        '''Second step'''
        app.removeButton('Next')
        app.disableOptionBox('dimensions')
        app.disableOptionBox('dimension_comparisons')
        chosen_dimension = app.getOptionBox('dimensions')
        num_dimensions = int(app.getOptionBox('dimension_comparisons'))

        # Ensure the labeled mongod binary is in the bin/ directory of this repo.        
        if chosen_dimension == 'Workload ratio':
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
                         'Choose a storage engine:')
            app.addOptionBox('storage_engines', ['wiredTiger', 'mmapv1'])
            app.addLabel('label_mongod', 
                         'Choose a mongod version:')
            app.addOptionBox('mongod_versions', ['3.4.7', '3.5.10'])
        else:
            if chosen_dimension == 'Storage engine':
                app.addLabel('label_se_note', 
                             'Note: only WT and MMAPv1 currently supported, so both will be automatically compared.')
                # app.addOptionBox('storage_engines', ['WiredTiger', 'MMAPv1'])
                app.addLabel('label_mongod', 
                             'Choose a mongod version:')
                app.addOptionBox('mongod_versions', ['3.4.7', '3.5.10'])
            elif chosen_dimension == 'Mongod version':
                #TODO: update the mongod binary to 3.5.12
                app.addLabel('label_mongod_note', 
                             'Note: only 3.4.7 and 3.5.10 currently supported, so both will be automatically compared.')
                # app.addOptionBox('mongod_versions', ['3.4.7', '3.5.10'])
                app.addLabel('label_se', 
                             'Choose a storage engine:')
                app.addOptionBox('storage_engines', ['wiredTiger', 'mmapv1'])
                app.addLabelNumericEntry('Read Proportion #0')
                app.addLabelNumericEntry('Update Proportion #0')
                app.addLabelNumericEntry('Scan Proportion #0')
                app.addLabelNumericEntry('Insert Proportion #0')
                app.setEntryDefault('Read Proportion #0', 0.25)
                app.setEntryDefault('Update Proportion #0', 0.25)
                app.setEntryDefault('Scan Proportion #0', 0.25)
                app.setEntryDefault('Insert Proportion #0', 0.25)

        app.addButton('Next', choose_num_trials)

    def choose_num_trials(btn):
        '''Choose # groups and # threads per group'''
        app.removeButton('Next')
        app.addLabel('label_num_trials', \
             'How many groups would you like to compare? \
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
        showRemainingOptions()

    def showRemainingOptions():
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
        '''Validate and add ratios to global var result_object'''
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
        threads = []
        # Collect number of threads selected for each run with validation check
        for i in range(num_trials):
            threads.append(app.getOptionBox('num_threads_group' + str(i)))
        if len(threads) != len(set(threads)):
            # TODO: Restructure to take action based on the yes / no input
            app.yesNoBox('warningDuplicateTrials', 
                'Warning: At least one of your trials is a duplicate. Would you like to revise?')
        return threads

    def validate_before_write(btn):
        app.disableButton('Run')
        num_trials = int(app.getOptionBox('num_trials')) 
        threads = validate_threads_input(num_trials)
        valid = False

        chosen_dimension = app.getOptionBox('dimensions')
        num_dimensions = int(app.getOptionBox('dimension_comparisons'))
        if chosen_dimension == 'Workload ratio':
            valid = check_proportions(num_dimensions)
        else:
            valid = check_proportions(1)

        if valid:
            write_workload_files(num_trials, num_dimensions, chosen_dimension, threads)

    def write_workload_files(num_trials, num_dimensions, chosen_dimension, threads):
        field_count = int(app.getEntry('Field Count'))
        field_length = int(app.getEntry('Field Length'))
        record_count = int(app.getEntry('Record Count'))
        operation_count = int(app.getEntry('Operation Count'))
        max_exec_time = int(app.getEntry('Max Execution Time'))

        result_object['chosen_dimension'] = chosen_dimension
        workload_files = []
        workload_labels = []
        workload_ranges = []
        if chosen_dimension == 'Workload ratio':
            for t in range(num_trials):
                for d in range(num_dimensions):
                    read = result_object['workload_ratios'][d]['read']
                    update = result_object['workload_ratios'][d]['update']
                    scan = result_object['workload_ratios'][d]['scan']
                    insert = result_object['workload_ratios'][d]['insert']
                    workload_labels.append('RUSI: {}-{}-{}-{}'.format(read, update, scan, insert))
                    absolute_range = abs(abs(abs(int(read * 100) - int(update * 100)) - int(scan * 100)) - int(insert * 100))
                    workload_ranges.append(absolute_range)

                    filename = 'fc{}fl{}rc{}-r{}u{}s{}i{}-t{}'.format(field_count, 
                        field_length, record_count, int(read * 100), int(update * 100), 
                        int(scan * 100), int(insert * 100), threads[t])

                    file = open(filename, 'w')
                    file.write('fieldcount={}\n'.format(field_count))
                    file.write('fieldlength={}\n'.format(field_length))
                    file.write('recordcount={}\n'.format(record_count))
                    file.write('operationcount={}\n'.format(operation_count))
                    file.write('maxexecutiontime={}\n'.format(max_exec_time))
                    file.write('threadcount={}\n'.format(threads[t]))
                    file.write('workload=com.yahoo.ycsb.workloads.CoreWorkload\n')
                    file.write('exportfile={}\n'.format(filename + '.out'))
                    file.write('readallfields=true\n\n')
                    file.write('readproportion={}\n'.format(read))
                    file.write('updateproportion={}\n'.format(update))
                    file.write('scanproportion={}\n'.format(scan))
                    file.write('insertproportion={}\n\n'.format(insert))
                    file.write('requestdistribution=zipfian\n')
                    file.close()
                    workload_files.append(filename)
                    print(filename + ' has been saved.')
                    result_object['storage_engines'] = [app.getOptionBox('storage_engines')]
                    result_object['mongod_versions'] = [app.getOptionBox('mongod_versions')]
        else:
            if chosen_dimension == 'Storage engine':
                result_object['storage_engines'] = ['wiredTiger', 'mmapv1']
                result_object['mongod_versions'] = [app.getOptionBox('mongod_versions')]
            elif chosen_dimension == 'Mongod version':
                result_object['storage_engines'] = [app.getOptionBox('storage_engines')]
                result_object['mongod_versions'] = ['3.4.7', '3.5.10']

            read = result_object['workload_ratios'][0]['read']
            update = result_object['workload_ratios'][0]['update']
            scan = result_object['workload_ratios'][0]['scan']
            insert = result_object['workload_ratios'][0]['insert']
            workload_labels.append('RUSI: {}-{}-{}-{}'.format(read, update, scan, insert))

            for t in range(num_trials):
                filename = 'fc{}fl{}rc{}-r{}u{}s{}i{}-t{}'.format(field_count, 
                        field_length, record_count, int(read * 100), int(update * 100), 
                        int(scan * 100), int(insert * 100), threads[t])

                # To refactor
                file = open(filename, 'w')
                file.write('fieldcount={}\n'.format(field_count))
                file.write('fieldlength={}\n'.format(field_length))
                file.write('recordcount={}\n'.format(record_count))
                file.write('operationcount={}\n'.format(operation_count))
                file.write('maxexecutiontime={}\n'.format(max_exec_time))
                file.write('threadcount={}\n'.format(threads[t]))
                file.write('workload=com.yahoo.ycsb.workloads.CoreWorkload\n')
                file.write('exportfile={}\n'.format(filename + '.out'))
                file.write('readallfields=true\n\n')
                file.write('readproportion={}\n'.format(read))
                file.write('updateproportion={}\n'.format(update))
                file.write('scanproportion={}\n'.format(scan))
                file.write('insertproportion={}\n\n'.format(insert))
                file.write('requestdistribution=zipfian\n')
                file.close()
                workload_files.append(filename)
                print(filename + ' has been saved.')

        result_object['workload_labels'] = workload_labels
        result_object['workload_files'] = workload_files
        result_object['threads'] = threads
    
        # result_object['groups'] = [groupOne, groupTwo]
        app.stop()


    app = gui()
    start_gui()
    return result_object