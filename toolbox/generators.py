from multiprocessing import Process

import numpy as np


def is_even(value) -> bool:
    if value % 2 == 0:
        return True
    else:
        return False


class TailCalculator(Process):
    def __init__(self, queue, local_lower, local_upper, local_collection, limit):
        Process.__init__(self)
        self.queue = queue
        self.local_lower = local_lower
        self.local_upper = local_upper
        self.local_collection = local_collection
        self.limit = limit

    def get_target(self, value):
        if is_even(value):
            target = int(value/2)
        else:
            target = int(value * 3 + 1)
        return target

    def get_unbound_tail(self, value):
        out_path = []
        out_of_bounds = True
        target = value
        while out_of_bounds:
            target = self.get_target(target)
            out_path.append(target)
            if target < self.limit:
                out_of_bounds = False

        return out_path

    def run(self):
        updated_collection = []
        for record in self.local_collection:
            new_record = {}
            new_record['value'] = record['value']
            new_record['is_bb'] = record['is_bb']
            new_record['target'] = record['target']

            if record['is_bb']:
                new_record['tail'] = new_record['target']
                new_record['tail_path'] = [new_record['target']]
                updated_collection.append(new_record)
                continue

            immediate_target = self.get_target(record['value'])
            new_record['target'] = immediate_target
            if immediate_target >= self.limit:
                out_path = self.get_unbound_tail(record['value'])
                new_record['tail_path'] = out_path
                new_record['tail'] = out_path[-1]
            else:
                new_record['tail'] = immediate_target
                new_record['tail_path'] = [immediate_target]

            updated_collection.append(new_record)

        self.queue.put(updated_collection)


class BBPathCalculator(Process):
    def __init__(self, queue, local_collection):
        Process.__init__(self)
        self.queue = queue
        self.local_collection = local_collection

    def run(self):
        updated_collection = []
        for record in self.local_collection:
            new_record = {}
            new_record['value'] = record['value']
            new_record['is_bb'] = record['is_bb']
            new_record['target'] = record['target']
            new_record['tail'] = record['tail']
            new_record['tail_path'] = record['tail_path']

            if record['is_bb']:
                new_record['tail_path'] = self.get_full_bb_path(
                    new_record['value'])
                new_record['tail'] = new_record['tail_path'][-1]
                updated_collection.append(new_record)

            else:
                new_record['tail_path'] = record['tail_path']
                updated_collection.append(new_record)

        self.queue.put(updated_collection)

    def get_target(self, value):
        if is_even(value):
            target = int(value/2)
        else:
            target = int(value * 3 + 1)
        return target

    def get_full_bb_path(self, start_value):
        path = []
        target = start_value
        while target != 1:
            target = self.get_target(target)
            path.append(target)

        return path


class PathCalculator(Process):
    def __init__(self, queue, local_collection, full_collection):
        Process.__init__(self)
        self.queue = queue
        self.local_collection = local_collection
        self.full_collection = full_collection

    def run(self):
        updated_collection = []
        for record in self.local_collection:
            new_record = {}
            new_record['value'] = record['value']
            new_record['is_bb'] = record['is_bb']
            new_record['target'] = record['target']
            new_record['tail_path'] = record['tail_path']
            target_full_path = self.get_target_tail_path(record['tail'])
            new_record['tail_path'].extend(target_full_path)
            new_record['tail'] = new_record['tail_path'][-1]
            updated_collection.append(new_record)

        self.queue.put(updated_collection)

    def get_target_tail_path(self, value):
        for record in self.full_collection:
            if record['value'] == value:
                return record['tail_path']


class FullPropertiesCalculator(Process):
    def __init__(self, queue, local_collection):
        Process.__init__(self)
        self.queue = queue
        self.local_collection = local_collection

    def run(self):
        number_collection = []
        for number in self.local_collection:
            number['full_path'] = number['tail_path']
            number['dist'] = len(number['full_path'])
            dist_to_bb, closest_vert_value = self.get_bb_from_path(
                number['full_path'])
            number['dist_to_bb'] = 0 if number['is_bb'] else dist_to_bb
            number['closest_vert_value'] = number['value'] if number['is_bb'] else closest_vert_value
            number['closest_vert'] = int(np.log2(number['closest_vert_value']))
            number['peak'] = self.get_peak(
                number['value'], number['full_path'])
            number['peak_slope'] = self.get_peak_slope(
                number['value'], number['peak'])
            number['odd_parent'] = self.get_odd_parent(number['value'])

            number_collection.append(number)

        self.queue.put(number_collection)

    def is_bb(self, value) -> bool:
        log2 = np.log2(value)
        if log2 % 1 == 0:
            return True
        return False

    def get_bb_from_path(self, full_path):
        not_bb_nodes = []
        largest_vert = 0
        for node in full_path:
            if self.is_bb(node):
                largest_vert = max(largest_vert, node)
            else:
                not_bb_nodes.append(node)

        return (len(not_bb_nodes) + 1, largest_vert)

    def get_peak(self, value, full_path):
        peak = max(full_path)
        peak = max(value, peak)
        return peak

    def get_peak_slope(self, value, peak):
        peak_slope = peak / value
        return peak_slope

    def get_odd_parent(self, value):
        potential = (value - 1) / 3
        if potential < 0:
            return False
        if potential % 1 == 0:
            if int(potential) % 2 != 0:
                return True
        return False
