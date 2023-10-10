import os
import sys
from datetime import datetime

from pytoolbox.config_agent import ConfigAgent

import toolbox.logger_agent as logger_agent
from agents.generator import run as run_generator
from agents.plotter import run as run_plotter
from toolbox import (
    get_config_filepath,
    get_data_folder,
    get_logger_filepath,
    get_output_folder,
    get_stash_folder,
)
from toolbox.data_manager import DataManager


project_title = 'CBD Exploration'

project_path = os.path.dirname(__file__)
HTML_FILENAME = 'main.html'
html_filepath = os.path.join(project_path, HTML_FILENAME)
config_filepath = get_config_filepath()
config = ConfigAgent(config_path=config_filepath)
logger_level = config.run.logger_level
logger_filepath = get_logger_filepath()
logger = logger_agent.get_logger(logger_filepath, logger_level)
data_folder = get_data_folder()
stash_folder = get_stash_folder()
output_folder = get_output_folder()
lower_bound = config.data.lower_bound
upper_bound = config.data.upper_bound
data_filepath = os.path.join(data_folder, config.files.data_file_name)
data_manager = DataManager(data_filepath)


def main():
    start = datetime.now()
    config.add_parameter('local', 'start', start)
    config.add_parameter('local', 'project_title', project_title)
    config.add_parameter('local', 'data_folder', data_folder)
    config.add_parameter('local', 'logger_filepath', logger_filepath)
    config.add_parameter('local', 'stash_folder', stash_folder)
    config.add_parameter('local', 'output_folder', output_folder)
    config.add_parameter('local', 'html_filepath', html_filepath)
    config.add_parameter('local', 'lower_bound', lower_bound)
    config.add_parameter('local', 'upper_bound', upper_bound)
    config.add_parameter('local', 'data_filepath', data_filepath)

    try:
        mode = config.mode.mode
        if mode == 'plot':
            run_plotter(logger, config, data_manager)
        elif mode == 'generate':
            run_generator(logger, config, data_manager)
        else:
            print(f'Run mode {mode} is not supported')
            sys.exit(1)
    except Exception as e:
        logger.exception(f'We ran into a problem: {e}')

if __name__ == "__main__":
    main()