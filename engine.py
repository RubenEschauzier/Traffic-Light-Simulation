from queue import Queue

import pandas as pd
import numpy as np
from collections import deque


class SimulationStates:
    # No queue for right turning since this is always allowed
    # The queue is filled to the left and popped from the right to allow for FIFO
    def __init__(self):
        self.NS = deque()
        self.NL = deque()
        self.ES = deque()
        self.EL = deque()
        self.SS = deque()
        self.SL = deque()
        self.WS = deque()
        self.WL = deque()
        self.light_state = 0
        self.clock = 0.0
        self.time_last_orange = 0

    def departure(self, type_road):
        if type_road == 'NS':
            if self.NS:
                return self.NS.pop()[1]
        elif type_road == 'NL':
            if self.NL:
                return self.NL.pop()[1]
        elif type_road == 'ES':
            if self.ES:
                return self.ES.pop()[1]
        elif type_road == 'EL':
            if self.EL:
                return self.EL.pop()[1]
        elif type_road == 'SS':
            if self.SS:
                return self.SS.pop()[1]
        elif type_road == 'SL':
            if self.SL:
                return self.SL.pop()[1]
        elif type_road == 'WS':
            if self.WS:
                return self.WS.pop()[1]
        elif type_road == 'WL':
            if self.WL:
                return self.WL.pop()[1]
        else:
            raise ValueError('Not a valid type')

    def enqueue(self, type_road, time):
        if type_road == 'NS':
            self.NS.appendleft((1, time))
        if type_road == 'NL':
            self.NL.appendleft((1, time))
        if type_road == 'ES':
            self.ES.appendleft((1, time))
        if type_road == 'EL':
            self.EL.appendleft((1, time))
        if type_road == 'SS':
            self.SS.appendleft((1, time))
        if type_road == 'SL':
            self.SL.appendleft((1, time))
        if type_road == 'WS':
            self.WS.appendleft((1, time))
        if type_road == 'WL':
            self.WL.appendleft((1, time))

    def get_road_state(self, type_road):
        if type_road == 'NS':
            return self.NS
        elif type_road == 'NL':
            return self.NL
        elif type_road == 'ES':
            return self.ES
        elif type_road == 'EL':
            return self.EL
        elif type_road == 'SS':
            return self.SS
        elif type_road == 'SL':
            return self.SL
        elif type_road == 'WS':
            return self.WS
        elif type_road == 'WL':
            return self.WL
        else:
            raise ValueError('Not a valid type')

    def change_lights(self, new_value):
        self.light_state = new_value
        if new_value == 5:
            self.time_last_orange = self.clock

    def get_light_state(self):
        return self.light_state

    def advance_clock(self, time):
        self.clock = time

    def get_clock(self):
        return self.clock

    def get_time_last_orange(self):
        return self.time_last_orange

    def all_roads_empty(self):
        all_empty = True
        list_roads = [self.NS, self.NL, self.ES, self.EL, self.SS, self.SL, self.WS, self.WL]
        for road in list_roads:
            if road:
                all_empty = False
        return all_empty

    def get_total_cars(self):
        list_roads = [self.NS, self.NL, self.ES, self.EL, self.SS, self.SL, self.WS, self.WL]
        total_cars = 0

        for road in list_roads:
            total_cars += len(road)

        return total_cars

    def get_wait_time_per_road(self, dictionary_time, dictionary_cars):
        list_roads = ['NS', 'NL', 'ES', 'EL', 'SS', 'SL', 'WS', 'WL']
        total_time = 0
        num_cars = 0

        for road in list_roads:
            cont = True
            total_time_left = 0
            total_cars_left = 0
            while cont:
                try:
                    total_time_left += self.get_clock() - self.departure(road)
                    total_cars_left += 1
                except TypeError:
                    cont = False
            dictionary_time[road] += total_time_left
            dictionary_cars[road] += total_cars_left
            total_time += total_time_left
            num_cars += total_cars_left

        return dictionary_time, dictionary_cars, total_time, num_cars


class ScheduledEvents:
    # First letter stands for (D)eparture/(A)rrival, second for (N)orth / (E)est etc and the third for (S)traight or
    # (L)eft.
    def __init__(self):
        self.departures = deque()
        self.arrivals = deque()
        self.light_change = deque()
        self.list_queues = [self.departures, self.arrivals, self.light_change]

    def get_next_event(self):
        min_time = np.inf
        next_event = None
        type_event = None
        type_queue = None
        for queue in self.list_queues:
            if queue:
                if queue[0][0] < min_time:
                    type_queue = queue
                    next_event = queue[0]
                    min_time = queue[0][0]
                    if type_queue == self.arrivals:
                        type_event = 'arrival'
                    if type_queue == self.departures:
                        type_event = 'departure'
                    if type_queue == self.light_change:
                        type_event = 'light_change'

        type_queue.popleft()
        self.list_queues = [self.departures, self.arrivals, self.light_change]
        return next_event, type_event

    def schedule_arrival(self, time, type):
        self.arrivals.appendleft((time, type))
        self.sort_arrivals()
        self.list_queues = [self.departures, self.arrivals, self.light_change]

    def schedule_departure(self, time, type):
        self.departures.appendleft((time, type))
        self.sort_departures()
        self.list_queues = [self.departures, self.arrivals, self.light_change]

    def schedule_light_change(self, time, type):
        self.light_change.appendleft((time, type))
        self.list_queues = [self.departures, self.arrivals, self.light_change]

    def sort_arrivals(self):
        self.arrivals = deque(sorted(self.arrivals, key=lambda time: time[0]))
        self.list_queues = [self.departures, self.arrivals, self.light_change]

    def sort_departures(self):
        self.departures = deque(sorted(self.departures, key=lambda time: time[0]))
        self.list_queues = [self.departures, self.arrivals, self.light_change]

    def clear_light_change(self):
        self.light_change = deque()


def draw_exponential(rate):
    return np.random.exponential(rate)
