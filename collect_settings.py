from appJar import gui

'''Show GUI to user'''
def open_gui():
    result_object = {}

    '''Entrypoint function'''
    def start_gui():
        app.addLabel('label_dimensions', 'Welcome! Choose which dimension to compare:')
        app.addOptionBox('dimensions', ['Workload ratio', 'Storage engine', 'Mongod version'])
        app.addLabel('label_dimension_comparisons', 'How many comparisons along this dimension?')
        app.addOptionBox('dimension_comparisons', range(1, 5))
        app.addLabel('label_num_trials', \
                     'How many groups would you like to compare? \
                     Each trial has a different # of threads.')
        app.addOptionBox('num_trials', ['- # trials -', 1, 2, 3, 4, 5, 6, 7, 8])
        app.setOptionBoxChangeFunction('dimension_comparisons', dimensionSelected)
        app.setOptionBoxChangeFunction('num_trials', trials_selected)
        app.go()

    '''Show x boxes to input threads per group'''
    def trials_selected(optionBox):
        # print('trials_selected')
        num_trials = int(app.getOptionBox('num_trials'))
        for i in range(num_trials):
            app.addLabel('labelNumThreadsGroup' + str(i), '# threads for group ' + str(i))
            app.addOptionBox('numThreadsGroup' + str(i), range(1, 25))
        dimensionSelected(num_trials)

    def check_proportions(option):
        # print('check_proportions')
        read = app.getEntry('Read ' + option)
        update = app.getEntry('Update ' + option)
        scan = app.getEntry('Scan ' + option)
        insert = app.getEntry('Insert ' + option)
        if read + update + scan + insert != 1:
            app.errorBox('errorWorkload', 'Error: Proportions have to add up to 1')
            return False
        return True

    def validate_before_write(btn):
        num_trials = int(app.getOptionBox('num_trials')) 
        threads = validate_threads_input(num_trials)
        valid = False

        chosen_dimension = app.getOptionBox('dimensions')
        if chosen_dimension == 'Workload ratio':
            valid = check_proportions('Proportion Group 1') and check_proportions('Proportion Group 2')
        else:
            valid = check_proportions('Proportion')

        if valid:
            write_workload_files(num_trials, chosen_dimension, threads)

    def write_workload_files(num_trials, chosen_dimension, threads):
        field_count = int(app.getEntry('Field Count'))
        field_length = int(app.getEntry('Field Length'))
        record_count = int(app.getEntry('Record Count'))
        operation_count = int(app.getEntry('Operation Count'))
        max_exec_time = int(app.getEntry('Max Execution Time'))

        if chosen_dimension == 'Workload ratio':
            counter = 2
            readV1 = app.getEntry('Read Proportion Group 1')
            updateV1 = app.getEntry('Update Proportion Group 1')
            scanV1 = app.getEntry('Scan Proportion Group 1')
            insertV1 = app.getEntry('Insert Proportion Group 1')
            readV2 = app.getEntry('Read Proportion Group 2')
            updateV2 = app.getEntry('Update Proportion Group 2')
            scanV2 = app.getEntry('Scan Proportion Group 2')
            insertV2 = app.getEntry('Insert Proportion Group 2')
            result_object['group_labels'] = ['RUSI: {}-{}-{}-{}'.format(readV1, updateV1, scanV1, insertV1), \
                'RUSI: {}-{}-{}-{}'.format(readV2, updateV2, scanV2, insertV2)]
            #result_object['group_labels'] = ['r{}u{}s{}i{}'.format(int(readV1 * 100), int(updateV1 * 100), 
            #            int(scanV1 * 100), int(insertV1 * 100))]
        else:
            counter = 1
            read = app.getEntry('Read Proportion')
            update = app.getEntry('Update Proportion')
            scan = app.getEntry('Scan Proportion')
            insert = app.getEntry('Insert Proportion')
            result_object['workload'] = 'RUSI: {}-{}-{}-{}'.format(read, update, scan, insert)

        workload_files = []
        groupOne = []
        groupTwo = []
        c = 0
        while (c < counter):
            c += 1
            for i in range(num_trials):
                if (c == counter and counter == 1):
                    filename = 'fc{}fl{}rc{}-r{}u{}s{}i{}-t{}'.format(field_count, 
                        field_length, record_count, int(read * 100), int(update * 100), 
                        int(scan * 100), int(insert * 100), threads[i])
                elif (c < counter):
                    filename = 'fc{}fl{}rc{}-r{}u{}s{}i{}-t{}'.format(field_count, 
                        field_length, record_count, int(readV1 * 100), int(updateV1 * 100), 
                        int(scanV1 * 100), int(insertV1 * 100), threads[i])
                    groupOne.append(filename)
                else:
                    filename = 'fc{}fl{}rc{}-r{}u{}s{}i{}-t{}'.format(field_count, 
                        field_length, record_count, int(readV2 * 100), int(updateV2 * 100), 
                        int(scanV2 * 100), int(insertV2 * 100), threads[i])
                    groupTwo.append(filename)
                file = open(filename, 'w')
                file.write('fieldcount={}\n'.format(field_count))
                file.write('fieldlength={}\n'.format(field_length))
                file.write('recordcount={}\n'.format(record_count))
                file.write('operationcount={}\n'.format(operation_count))
                file.write('maxexecutiontime={}\n'.format(max_exec_time))
                file.write('threadcount={}\n'.format(threads[i]))
                file.write('workload=com.yahoo.ycsb.workloads.CoreWorkload\n')
                file.write('exportfile={}\n'.format(filename + '.out'))
                file.write('readallfields=true\n\n')
                if (c == counter and counter == 1):
                    file.write('readproportion={}\n'.format(read))
                    file.write('updateproportion={}\n'.format(update))
                    file.write('scanproportion={}\n'.format(scan))
                    file.write('insertproportion={}\n\n'.format(insert))
                elif (c < counter):
                    file.write('readproportion={}\n'.format(readV1))
                    file.write('updateproportion={}\n'.format(updateV1))
                    file.write('scanproportion={}\n'.format(scanV1))
                    file.write('insertproportion={}\n\n'.format(insertV1))
                else:
                    file.write('readproportion={}\n'.format(readV2))
                    file.write('updateproportion={}\n'.format(updateV2))
                    file.write('scanproportion={}\n'.format(scanV2))
                    file.write('insertproportion={}\n\n'.format(insertV2))
                file.write('requestdistribution=zipfian\n')
                file.close()
                workload_files.append(filename)
                print(filename + ' has been saved.')
        
        result_object['workload_files'] = workload_files
        result_object['threads'] = threads
        result_object['storage_engines'] = ['wiredTiger']
        result_object['mongod_versions'] = ['3.4.7']
        result_object['groups'] = [groupOne, groupTwo]
        app.stop()

    def validate_threads_input(num_trials):
        threads = []
        # Collect number of threads selected for each run with validation check
        for i in range(num_trials):
            threads.append(app.getOptionBox('numThreadsGroup' + str(i)))
        if len(threads) != len(set(threads)):
            # TODO
            app.yesNoBox('warningDuplicateTrials', 
                'Warning: At least one of your trials is a duplicate. Would you like to revise?')
        return threads

    def dimensionSelected(optionBox):
        chosen_dimension = app.getOptionBox('dimensions')
        dimension_comparisons = app.getOptionBox('dimension_comparisons')

        if chosen_dimension == 'Workload ratio':
            app.addLabelNumericEntry('Read Proportion Group 1')
            app.addLabelNumericEntry('Update Proportion Group 1')
            app.addLabelNumericEntry('Scan Proportion Group 1')
            app.addLabelNumericEntry('Insert Proportion Group 1')
            app.addLabelNumericEntry('Read Proportion Group 2')
            app.addLabelNumericEntry('Update Proportion Group 2')
            app.addLabelNumericEntry('Scan Proportion Group 2')
            app.addLabelNumericEntry('Insert Proportion Group 2')
        else:
            app.addLabelNumericEntry('Read Proportion')
            app.addLabelNumericEntry('Update Proportion')
            app.addLabelNumericEntry('Scan Proportion')
            app.addLabelNumericEntry('Insert Proportion')

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

    app = gui()
    start_gui()
    return result_object