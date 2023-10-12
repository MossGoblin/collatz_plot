import copy
import multiprocessing
import os
import sys
from datetime import datetime
from multiprocessing import Queue

import pandas as pd
from progress.bar import Bar

from toolbox.data_manager import DataManager
from toolbox.generators import (
    BBPathCalculator,
    FullPropertiesCalculator,
    TailCalculator,
)
from toolbox.lab import init_log, is_bb, stash_log_file


def run(logger, config, data_manager):
    start = config.local.start

    upper_bound = config.data.upper_bound
    cpu_count = multiprocessing.cpu_count()
    process_count = cpu_count
    pr_limit = int(upper_bound / (process_count - 1))
    # TEMP
    # process_count = 1
    # pr_limit = limit
    init_log(logger, config, start)
    logger.info(f'* Process count: {process_count}')

    if data_manager.data_already_exists(config):
        end = datetime.now()
        logger.info(f'The data range is already covered in the db. No new data will be generated')
        logger.info(f'End at {end}')
        logger.info(f'Total time: {end-start}')
        sys.exit(0)

    # create proto number collection
    logger.info('Creating proto collection...')
    step_start = datetime.now()
    proto_collection = []
    for value in range(2, upper_bound):
        proto_number = {}
        proto_number['value'] = value
        proto_number['is_bb'] = is_bb(value)
        proto_number['target'] = int(value / 2) if proto_number['is_bb'] else 0
        proto_collection.append(proto_number)
    step_end = datetime.now()
    logger.debug(f'...done in {step_end-step_start}')

    # calculate tails
    logger.info('Calculating first tails...')
    step_start = datetime.now()
    tail_calculators = []
    tail_queue = Queue()
    for counter in range(process_count):
        bound_lower = pr_limit * counter + 1 if counter > 0 else pr_limit * counter
        bound_upper = pr_limit * (counter + 1)
        local_collection = [record for record in proto_collection if record['value'] in range(bound_lower, bound_upper + 1)]
        tail_calculators.append(TailCalculator(queue=tail_queue, local_lower=bound_lower, local_upper=bound_upper, local_collection=local_collection, limit=upper_bound))

    for calculator in tail_calculators:
        calculator.start()
    
    tails_collection = []
    tail_process_count = process_count
    while tail_process_count > 0:
        result = tail_queue.get()
        tails_collection.extend(result)
        tail_process_count -= 1
    step_end = datetime.now()
    logger.debug(f'...done in {step_end-step_start}')

    # calculate bb paths
    logger.info('Creating backbone...')
    step_start = datetime.now()
    bb_path_calculators = []
    bb_path_queue = Queue()
    for counter in range(process_count):
        bound_lower = pr_limit * counter + 1 if counter > 0 else pr_limit * counter
        bound_upper = pr_limit * (counter + 1)
        local_collection = [record for record in tails_collection if record['value'] in range(bound_lower, bound_upper + 1)]
        bb_path_calculators.append(BBPathCalculator(queue=bb_path_queue, local_collection=local_collection))

    for calculator in bb_path_calculators:
        calculator.start()

    bb_path_collection = []
    bb_path_process_count = process_count
    while bb_path_process_count > 0:
        result = bb_path_queue.get()
        bb_path_collection.extend(result)
        bb_path_process_count -= 1
    step_end = datetime.now()
    logger.debug(f'...done in {step_end-step_start}')


    # split calculated by tail
    logger.info('Collating full paths...')
    step_start = datetime.now()
    all_paths_collection = copy.deepcopy(bb_path_collection)

    complete_tails_to_be_processed = []
    incomplete_tails = []
    for record in all_paths_collection:
        complete_tails_to_be_processed.append(record) if record['tail'] == 1 else incomplete_tails.append(record)
    complete_tails = copy.deepcopy(complete_tails_to_be_processed)
    
    # process unprocessed_queue
    with Bar('Collating tails', max = len(incomplete_tails)) as bar:
        while len(complete_tails_to_be_processed) > 0:
            record = complete_tails_to_be_processed.pop()
            # find parents
            parents_tail = record['value']
            parents = [record for record in incomplete_tails if record['tail'] == parents_tail]
            if len(parents) > 0:
                complete_tails_to_be_processed.extend(parents)
                for parent in parents:
                    parent['tail_path'].extend(record['tail_path'])
                    parent['tail'] = record['tail']
                    complete_tails.append(parents)
                    incomplete_tails.remove(parent)
            bar.next(n=len(parents))

    step_end = datetime.now()
    logger.debug(f'...done in {step_end-step_start}')

    # calculate additional parameters
    logger.info('Calculating parameters...')
    step_start = datetime.now()
    cnumber_calculators = []
    cnumber_queue = Queue()
    for counter in range(process_count):
        bound_lower = pr_limit * counter + 1 if counter > 0 else pr_limit * counter
        bound_upper = pr_limit * (counter + 1)
        local_collection = [record for record in all_paths_collection if record['value'] in range(bound_lower, bound_upper + 1)]
        cnumber_calculators.append(FullPropertiesCalculator(queue=cnumber_queue, local_collection=local_collection))

    for calculator in cnumber_calculators:
        calculator.start()

    cnumber_collection = []
    cnumber_process_count = process_count
    while cnumber_process_count > 0:
        result = cnumber_queue.get()
        cnumber_collection.extend(result)
        cnumber_process_count -= 1

    step_end = datetime.now()
    logger.debug(f'...done in {step_end-step_start}')

    logger.info('Saving dataframe to db')
    collection_df = pd.DataFrame.from_dict(cnumber_collection)
    collection_df.drop(columns=['target', 'tail', 'tail_path'], inplace=True)
    data_filename = config.files.data_file_name
    data_folder = config.local.data_folder
    data_filepath = os.path.join(data_folder, data_filename)
    data_manager = DataManager(data_filepath)
    data_manager.save_data(collection_df)

    end = datetime.now()
    logger.info(f'End at {end}')
    logger.info(f'Total time: {end-start}')

    # deal with the logger file
    logger_filename_prefix = 'GEN'
    stash_log_file(config, logger_filename_prefix)

if __name__ == "__main__":
    run()