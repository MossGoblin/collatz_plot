from enum import Enum, auto
from sqlalchemy import create_engine, Column, Integer, Boolean, Float, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from progress.bar import Bar

import pandas as pd

Base = declarative_base()


'''
filter = {
            'name': name of filter,
            'type': FilterType
            'polarity': bool
            'column': name of column to be filtered
            'parameters':
                [p1, p2]
}

LTE = auto() lower than or equal; polarity changes to GT
GTE = auto() greater than or equal; polarity changes to LT
RNG = auto() within range (inclusive); polarity changes to outside of range (exclusive)
LST = auto() in a list; polarity changes to not in a list
EQL = auto() equals; polarity changes to not equals

alternative filtering at 
# LINK https://www.peterspython.com/en/blog/slqalchemy-dynamic-query-building-and-filtering-including-soft-deletes
'''


class CNumber(Base):
    __tablename__ = "cnumbers"
    # uid = Column("uid", Integer, primary_key=True, autoincrement=True)
    value = Column("value", Integer, primary_key=True)
    is_bb = Column("is_bb", Boolean)
    full_path = Column("full_path", String)
    dist = Column("dist", Integer)
    dist_to_bb = Column("dist_to_bb", Integer)
    closest_vert_value = Column("closest_vert_value", Integer)
    closest_vert = Column("closest_vert", Integer)
    peak = Column("peak", Integer)
    peak_slope = Column("peak_slope", Float)
    odd_parent = Column("odd_parent", Boolean)

# ,value,is_bb,full_path,dist,dist_to_bb,closest_vert_value,closest_vert,peak,peak_slope,odd_parent

    def __init__(self, number_dict):
        self.value = number_dict['value']
        self.is_bb = number_dict['is_bb']
        self.full_path = self.compile_path_string(number_dict['full_path'])
        self.dist = number_dict['dist']
        self.dist_to_bb = number_dict['dist_to_bb']
        self.closest_vert_value = number_dict['closest_vert_value']
        self.closest_vert = number_dict['closest_vert']
        self.peak = number_dict['peak']
        self.peak_slope = number_dict['peak_slope']
        self.odd_parent = number_dict['odd_parent']

    def compile_path_string(self, path_list: list) -> str:
        path_string = ",".join([str(value) for value in path_list])
        return path_string


class DataManager():
    '''Governs the persistence and filtering of data'''
    class FilterType(Enum):
        LTE = auto()
        GTE = auto()
        RNG = auto()
        LST = auto()
        EQL = auto()


    def __init__(self, db_filepath):
        self.engine = create_engine(f"sqlite:///{db_filepath}")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.filters = []


    def data_already_exists(self, config):
        lower_bound = config.local.lower_bound
        upper_bound = config.local.upper_bound - 1
        if len(self.load_data(config)) < upper_bound - lower_bound:
            return False
        return True


    def save_data(self, data: pd.DataFrame):
        '''Saves the data via sqlalchemy'''
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        data_list = data.to_dict(orient="records")
        with Bar('Adding records to db', max=len(data_list)) as bar:
            for record in data_list:
                test_cnumber = CNumber(record)
                session.merge(test_cnumber)
                bar.next()        
        session.commit()
        

    def load_data(self, config):
        '''Loads data, clamped with lowerbound and upperbound'''
        lowerbound = config.local.lower_bound
        upperbound = config.local.upper_bound
        raw_df = pd.read_sql(self.session.query(CNumber).filter(CNumber.value > lowerbound, CNumber.value <= upperbound).statement, self.session.bind)
        return raw_df


    def set_data(self, data: pd.DataFrame):
        self.data = data


    def add_filter(self, filter: dict):
        '''Add filter to the filter list for later application'''
        try:
            self._validate_filter(filter)
        except Exception as e:
            raise e
        self.filters.append(filter)


    def list_filters(self):
        '''Get list of all filters'''
        filter_names = []
        for filter in self.filters:
            filter_names.append(filter['name'])
        return filter_names


    def apply_filter(self, filter_name: str):
        '''Apply previously added filter, specified by name'''
        active_filter = [filter for filter in self.filters if filter["name"] == filter_name][0]
        # check for column name
        column_name = active_filter['column']
        if not column_name in self.data:
            raise ValueError(f'The data does not contain a column named "{column_name}"')
        elif active_filter['type'] == self.FilterType.LTE:
            if active_filter['polarity']:
                filtered_data = self.data[self.data[column_name] <= active_filter['parameters'][0]]
            else:
                filtered_data = self.data[self.data[column_name] > active_filter['parameters'][0]]
        elif active_filter['type'] == self.FilterType.GTE:
            if active_filter['polarity']:
                filtered_data = self.data[self.data[column_name] >= active_filter['parameters'][0]]
            else:
                filtered_data = self.data[self.data[column_name] < active_filter['parameters'][0]]
        elif active_filter['type'] == self.FilterType.RNG:
            if active_filter['polarity']:
                filtered_data = self.data[self.data[column_name] >= active_filter['parameters'] and self.data[column_name] <= active_filter['parameters'][0]]
            else:
                filtered_data = self.data[self.data[column_name] < active_filter['parameters'] or self.data[column_name] > active_filter['parameters'][0]]
        elif active_filter['type'] == self.FilterType.LST:
            if active_filter['polarity']:
                filtered_data = self.data.loc[self.data[column_name].isin(active_filter['parameters'])]
            else:
                filtered_data = self.data.loc[~self.data[column_name].isin(active_filter['parameters'])]
        elif active_filter['type'] == self.FilterType.EQL:
            if active_filter['polarity']:
                filtered_data = self.data[self.data[column_name] == active_filter['parameters'][0]]
            else:
                filtered_data = self.data[self.data[column_name] != active_filter['parameters'][0]]
    
        return filtered_data


    def _validate_filter(self, filter: dict):
        for key_name in ['name', 'type', 'polarity', 'column', 'parameters']:
            if filter.get(key_name) is None:
                raise ValueError(f'Filter "{key_name}" is missing')
        if not isinstance(filter['name'], str):
            raise ValueError('Filter parameter "name" should be string')
        if not isinstance(filter['type'], self.FilterType):
            raise ValueError('Filter parameter "type" should be of FilterType enum members')
        if not isinstance(filter['polarity'], bool):
            raise ValueError('Filter parameter "positive" should be boolean')
        if not isinstance(filter['column'], str):
            raise ValueError('Filter parameter "column" should be boolean')
        if not isinstance(filter['parameters'], list):
            raise ValueError('Filter parameter "parameters" should be a list')
        # single parameter
        if filter['type'] in [self.FilterType.GTE, self.FilterType.LTE, self.FilterType.EQL]:
            if len(filter['parameters']) != 1:
                raise ValueError('Filter parameters should be exactly one')
        # single numeric
        if filter['type'] in [self.FilterType.GTE, self.FilterType.LTE]:
            if not isinstance(filter['parameters'][0], int) and not isinstance(filter['parameters'][0], float):
                raise ValueError('Filter parameters should numeric')
        # range
        if filter['type'] in [self.FilterType.RNG]:
            if len(filter['parameters']) != 2:
                raise ValueError('Filter should have at least two parameters')
            if not isinstance(filter['parameters'][0], int) and not isinstance(filter['parameters'][1], int):
                raise ValueError('Filter parameters should be both int or float')
            if not isinstance(filter['parameters'][0], float) and not isinstance(filter['parameters'][1], float):
                raise ValueError('Filter parameters should be both int or float')

        return True

