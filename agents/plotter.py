import os
from datetime import datetime

from toolbox.lab import (
    generate_hard_copy_filename,
    generate_plot,
    get_data,
    init_log,
    prep_output_folder,
    prepare_data,
    stash_graph_html,
    stash_log_file,
)


def run(logger, config, data_manager):
    start = config.local.start

    init_log(logger, config, start)

    logger.info('Loading data')
    logger.debug('Getting data filename')
    upper_bound = config.data.upper_bound
    
    # set_clamp_filter(logger, config)

    data = get_data(logger, config, data_manager)

    # prepare data for plot
    logger.info('Preparing data')
    data = prepare_data(config, data, upper_bound)

    # plot data
    html_filepath = config.local.html_filepath
    project_title = config.local.project_title
    plot = generate_plot(logger, config, data, project_title, html_filepath)

    plot.display_plot()
    logger.info('Displaying plot')


    # Save output
    end = datetime.now()
    logger.info(f'End at {end}')
    logger.info(f'Total time: {end-start}')

    # Stash html and log files
    hard_copy_filename = generate_hard_copy_filename(config)
    prep_output_folder(config)
    stash_graph_html(hard_copy_filename)
    logger_filename_prefix = 'PLOT'
    stash_log_file(config, logger_filename_prefix)

if __name__ == "__main__":
    run()