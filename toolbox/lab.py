import math
import os
import re
import shutil
import sys
from datetime import datetime
from logging import Logger

import numpy as np
import pandas as pd
from progress.bar import Bar
from pytoolbox.bokeh_agent import BokehScatterAgent
from pytoolbox.config_agent import ConfigAgent

import toolbox.mappings as mappings
from toolbox import STASH_FOLDER
from toolbox.data_manager import DataManager


def init_log(logger: Logger, config: ConfigAgent, start: datetime.time):
    logger.info(f'Start at {start}')
    logger.info(f'* Run mode: {config.mode.mode.upper()}')
    logger.info(f'* Data range: {config.data.lower_bound} to {config.data.upper_bound}')


def get_data(logger: Logger, config: ConfigAgent, data_manager: DataManager) -> pd.DataFrame:
    logger.debug('Loading data from file')
    data_df = data_manager.load_data(config)
    # TBD
    # data_df = cnumber_list_to_df(data_list)
    if config.filters.filter_data:
         logger.info(f'Filtering data: {config.filters.filter_name}')
         data_df = filter_data(config, data_df)
         config.add_parameter('local', 'filter_name', config.filters.filter_name)

    return data_df


def set_clamp_filter(logger: Logger, config: ConfigAgent):
    '''Creates a filter for the sqlalchemy call to read only the specified data range'''
    logger.debug('Building clamp filter')
    config.local.clamp_filter = ('value', 'in', [value for value in range(config.local.lower_bound, config.local.upper_bound)])


def load_data_from_csv(logger: Logger, data_file_full_name: str) -> pd.DataFrame:
    '''Loads a csv file'''
    try:
        data_df = pd.read_csv(data_file_full_name, index_col='Unnamed: 0')
    except Exception as e:
        logger.error(f'Failed to read csv data file: {e}')
        logger.info('Exiting')
        sys.exit(1)

    return data_df


def prepare_data(config: ConfigAgent, data: pd.DataFrame, limit: int) -> pd.DataFrame:
    # enchancing data
    palette_range = config.plot.palette_range
    include_backbone = config.data.include_backbone
    colorization_field_config = config.plot.colorization_value
    colorization_field = mappings.colorization_field[colorization_field_config]    
    data_df = collection_to_df(data=data, palette_range=palette_range, include_backbone=include_backbone, colorization_field=colorization_field, limit=limit)

    return data_df


def collection_to_df(data: pd.DataFrame, palette_range: int, include_backbone: bool = False, colorization_field: str = 'dist', limit: int = 0) -> pd.DataFrame:
    '''
    Reads a csv file into a pandas DataFrame

    Params
    ------
    data: pd.DataFrame
        data as pandas DataFrame
    palette_range: int
        number of colors in the colorization palette
    include_backbone: bool = False, optional
        whether powers of 2 should be included in the dataframe (default is False)
    colorization_field: str = 'dist'
        name of the column to be used for detemining color buckets

    Returns
    ------
    pd.DataFrame
        dataframe
    '''
    if not include_backbone:
        data = data.drop(data[data['is_bb'] == True].index)
    # add coloration index column
    rawdict = data.to_dict(orient='records')
    data_dict = {}
    data_dict['value'] = []
    data_dict['is_bb'] = []
    data_dict['full_path'] = []
    data_dict['dist'] = []
    data_dict['dist_to_bb'] = []
    data_dict['closest_vert'] = []
    data_dict['closest_vert_value'] = []
    data_dict['peak'] = []
    data_dict['peak_slope'] = []
    data_dict['odd_parent'] = []
    data_dict['bounded'] = []
    data_dict['color_bucket'] = []

    max_value = (data[colorization_field].max())

    # check for values
    if max_value == 0:
        return None

    with Bar('Generating plot data', max=len(rawdict)) as bar:
        for item in rawdict:
            data_dict['value'].append(item['value'])
            data_dict['is_bb'].append('True' if item['is_bb'] else 'False')
            data_dict['full_path'].append(item['full_path'])
            data_dict['dist'].append(item['dist'])
            data_dict['dist_to_bb'].append(item['dist_to_bb'])
            data_dict['closest_vert'].append(item['closest_vert'])
            data_dict['closest_vert_value'].append(item['closest_vert_value'])
            data_dict['peak'].append(item['peak'])
            data_dict['peak_slope'].append(item['peak_slope'])
            data_dict['odd_parent'].append('True' if item['odd_parent'] else 'False')
            data_dict['bounded'].append('True' if item['peak'] <= limit else 'False')
            data_dict['color_bucket'].append(get_colour_bucket_index(
                item[colorization_field], max_value, palette_range))
            bar.next()

    data_df = pd.DataFrame(data_dict)

    return data_df


def get_colour_bucket_index(value: int, max: int, palette_range: int) -> int:
    '''
    Get the index of the color bucket that a number with a given value should be assigned to

    Params
    ------
    value: int
        the value to be used for assignment
    max: int
        maximum for the value within the collection that the number is from
    palette_range: int
        maximum number of color buckets to be used

    Returns
    ------
    int:
        color index to bhe assigned to the value
    '''
    color_index = str(math.floor((palette_range * value) / max))

    return color_index


def generate_plot(logger: Logger, config: ConfigAgent, data: pd.DataFrame, project_title: str, html_filepath: str):
    plot = BokehScatterAgent()
    plot.set_data(data)
    logger.debug('Plot data set')

    palette_range = config.plot.palette_range
    config.add_parameter('local', 'plot_points', len(data))

    graph_params = get_graph_params(config, logger, project_title, html_filepath)
    plot.set_params(graph_params)
    logger.debug('Graph params collated')

    tooltips = [('number', '@value'), 
                ('is bb', '@is_bb'), 
                ('distance', '@dist'), 
                ('distance to bb', '@dist_to_bb'), 
                ('closest vert power', '@closest_vert'), 
                ('closest vert', '@closest_vert_value'), 
                ('peak', '@peak'), 
                ('peak slope', '@peak_slope'),
                ('odd parent', '@odd_parent'),
                ('bounded', '@bounded')]

    plot.set_tooltips(tooltips)
    logger.debug('Tooltips set')

    color_factors = get_color_factors(palette_range)
    plot.set_color_factors(color_factors)
    logger.debug('Color factors set')

    plot.generate()
    logger.info('Plot generated')

    return plot


def get_graph_params(config: ConfigAgent, logger: Logger, project_title: str, html_filepath: str) -> dict:
    '''
    Creates a dictionary with parameters for a bokeh plot

    Params
    ------
    config: ConfigAgent
        config agent instance
    project_title: str
        string to be used for the <title> of the generated html
    html_filepath: str
        full path of the html file to be generated

    Returns
    ------
    dict
        a dictionary with plot parameters

    '''
    plot_width = config.plot.width
    plot_height = config.plot.height
    palette = config.plot.palette
    point_size = config.plot.point_size
    include_backbone = config.data.include_backbone
    colorization_field_config = config.plot.colorization_value
    colorization_field = mappings.colorization_field[colorization_field_config]
    y_axis = config.plot.y_axis
    plot_points = config.local.plot_points

    graph_params = {}
    data_base_size = config.local.upper_bound - config.local.lower_bound
    data_ratio = plot_points / data_base_size
    data_ratio_string = "{:.4f}".format(data_ratio)
    logger.info(f'Data ratio: {data_ratio}')
    range_title_text = f'size {plot_points} / {str(data_base_size)} ({data_ratio_string})'
    parameters_title_text = range_title_text
    backbone_title_text = ' [ bb included ]' if include_backbone else ''
    filter_text = ""
    if config.filters.filter_data:
        filter_text = f" [ filter: {config.local.filter_name} ]"
    graph_params['title'] = f'Collatz: {mappings.y_axis_labels[y_axis]} [ Color: {mappings.colorization_title_suffix[colorization_field]} ] [{parameters_title_text}]{backbone_title_text}{filter_text}]'
    graph_params['y_axis_label'] = mappings.y_axis_labels[y_axis]
    graph_params['width'] = plot_width
    graph_params['height'] = plot_height
    graph_params['palette'] = palette
    graph_params['point_size'] = point_size
    graph_params['x_axis'] = 'value'
    graph_params['y_axis'] = mappings.y_axis_parameter[y_axis]
    graph_params['output_file_title'] = project_title
    graph_params['output_file_path'] = html_filepath

    return graph_params


def get_color_factors(palette_range: int) -> list[str]:
    '''
    Creates a list of consecutive integers

    Params
    ------
    palette_range: int
        total numbers in a palette, for which color factors are calculated

    Returns
    ------
    list[str]
        a list of int color factors, cast to str
    '''
    factors_list = []
    for index in range(palette_range):
        factors_list.append(str(index))

    return factors_list


def stash_graph_html(hard_copy_filename: str):
    '''Copy the last html file into the output folder'''
    full_stashed_filename = hard_copy_filename + ".html"
    if os.path.isfile(full_stashed_filename):
        os.remove(full_stashed_filename)
    with open('main.html', 'r') as html_input_file:
        content = html_input_file.read()
        with open(full_stashed_filename, 'wt') as stashed_html_output_file:
            stashed_html_output_file.write(content)


def stash_log_file(config: ConfigAgent, log_filename_prefix: str):
    # ensure stash folder exists
    limit = f"{str(config.local.lower_bound)}_{str(config.local.upper_bound)}"
    start = config.local.start
    stash_folder = config.local.stash_folder
    logger_filepath = config.local.logger_filepath
    if not os.path.exists(STASH_FOLDER):
        os.makedirs(STASH_FOLDER)
    # copy the latest log file in the stash folder
    start_string = start.strftime("%d%m%Y_%H%M%S")
    stashed_log_filename = "_".join([log_filename_prefix, limit, start_string]) + ".log"
    stashed_log_filepath = os.path.join(stash_folder, stashed_log_filename)
    shutil.copy(logger_filepath, stashed_log_filepath)

    # reset main log file
    open(logger_filepath, 'w').close()


def is_bb(value) -> bool:
    log2 = np.log2(value)
    if log2 % 1 == 0:
        return True
    return False


def prep_output_folder(config: ConfigAgent):
    '''
    Prepare folder for output csv files
    '''
    folder_name = config.local.output_folder
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
        return
    else:
        if config.files.reset_output_data:
            for root, directories, files in os.walk(folder_name):
                for file in files:
                    file_path = root + '/' + file
                    os.remove(file_path)
        return


def generate_hard_copy_filename(config: ConfigAgent):
    '''Generate full path string for the csv and html files'''
    output_folder = config.local.output_folder
    timestamp_granularity = config.run.hard_copy_timestamp_granularity
    timestamp_format = generate_timestamp(timestamp_granularity)
    timestamp = datetime.utcnow().strftime(timestamp_format)
    limit_string = f"{str(config.local.lower_bound)}_{str(config.local.upper_bound)}"
    backbone_included_string = 'BB' if config.data.include_backbone else "NoBB"
    vert_filter = 'FLT_' + config.filters.filter_name if config.filters.filter_data else 'NoFLT'
    y_axis_mode = mappings.y_axis_filename_suffix[config.plot.y_axis]
    hard_copy_filename = "_".join(
        [limit_string, backbone_included_string, vert_filter, timestamp, y_axis_mode])

    hard_copy_filepath = os.path.join(output_folder, hard_copy_filename)

    return hard_copy_filepath


def generate_timestamp(granularity: int = 0):
    '''
    Generate timestamp string, depending on the desired granularity, set in config.toml
    '''

    timestamp_format = ''
    timestamp_granularity = granularity
    format_chunks = ['%d%m%Y', '_%H', '%M', '%S']
    for chunk_index in range(timestamp_granularity + 1):
        timestamp_format += format_chunks[chunk_index]
    return timestamp_format


def filter_data(config: ConfigAgent, data: pd.DataFrame, data_manager: DataManager):
    filter = {}
    filter['name'] = config.filters.filter_name
    filter['type'] = DataManager.FilterType(config.filters.filter_type)
    filter['polarity'] = config.filters.filter_polarity
    filter['column'] = config.filters.filter_column
    filter['parameters'] = config.filters.filter_parameters
    data_manager.set_data(data)
    data_manager.add_filter(filter)
    filtered_data = data_manager.apply_filter(filter['name'])
    return filtered_data


def cnumber_list_to_df(data_list: list) -> pd.DataFrame:

    data_dict = []
    for cnumber in data_list:
        record = {}
        record['value'] = cnumber.value
        record['is_bb'] = cnumber.is_bb
        record['full_path'] = cnumber.full_path
        record['dist'] = cnumber.dist
        record['dist_to_bb'] = cnumber.dist_to_bb
        record['closest_vert'] = cnumber.closest_vert
        record['closest_vert_value'] = cnumber.closest_vert_value
        record['peak'] = cnumber.peak
        record['peak_slope'] = cnumber.peak_slope
        record['odd_parent'] = cnumber.odd_parent
        data_dict.append(record)

    data_df = pd.DataFrame(data_dict)

    return data_df