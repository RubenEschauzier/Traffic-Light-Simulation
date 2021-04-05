from engine import SimulationStates, ScheduledEvents, draw_exponential
import time as t
import numpy as np


def init_simulation(policy, scheduled_events, roads, light_time, start_light, flow_first_car):
    # Schedule arrivals on each road
    for road, params in roads.items():
        time = -0.5 + params[0] * np.random.beta(params[1], params[2])
        scheduled_events.schedule_arrival(time, road)

    # Start departure of first car
    for road in policy[start_light]:
        time = draw_exponential(flow_first_car)
        scheduled_events.schedule_departure(time, road)

    # Schedule orange light
    scheduled_events.schedule_light_change(20, 5)

    # Sort arrivals and departures such that the earliest event is always taken first
    scheduled_events.sort_arrivals()
    scheduled_events.sort_departures()

    return scheduled_events


def main(light_policy, max_time, roads, rush_hour, flow_cars=2, flow_first_car=8,
         orange_time=1, starting_policy=1, light_times=[40, 30, 20, 60], verbose=1, smart=False):

    # Initialise metrics
    num_cars_in_system = []
    total_wait_time = 0
    total_cars = 0
    road_specific_wait = {'NL': 0, 'NS': 0, 'ES': 0, 'EL': 0, 'SS': 0, 'SL': 0, 'WS': 0, 'WL': 0}
    road_specific_cars = {'NL': 0, 'NS': 0, 'ES': 0, 'EL': 0, 'SS': 0, 'SL': 0, 'WS': 0, 'WL': 0}

    # Define the middle/peak of the rush hours
    mid_rush1 = rush_hour[0] + (rush_hour[1] - rush_hour[0]) / 2
    mid_rush2 = rush_hour[2] + (rush_hour[3] - rush_hour[2]) / 2

    # Calculate total seconds of light time
    total_seconds = sum(light_times)

    # Initialise the simulation engines
    states = SimulationStates()
    scheduled_events = ScheduledEvents()

    # Initialise the traffic lights to the starting lights
    states.change_lights(starting_policy)

    # Define a new time variable that will help us check if simulation runs properly by checking if time is running
    # smoothly (not going backwards)
    new_time = 0

    # Initialise the first arrivals, departures (at road that is open/green) and light change
    scheduled_events = init_simulation(light_policy, scheduled_events, roads, light_times[starting_policy - 1],
                                       start_light=starting_policy, flow_first_car=flow_first_car)

    while states.get_clock() < max_time:
        # Get event with lowest scheduled time from all events and process it
        event, type_event = scheduled_events.get_next_event()

        # Create list with roads where light is green
        open_roads = light_policy[states.get_light_state()]

        # Ensure that time is moving from low to high
        previous_time = states.get_clock()
        assert (previous_time <= new_time)

        # Process arrival events
        if type_event == 'arrival':
            # Advance the clock to the event time
            states.advance_clock(event[0])

            # Get current time to check for rush hour multiplier
            c_time = states.get_clock()

            # If the road is on green and the road is empty the car passes through and a new arrival is scheduled
            if event[1] in open_roads and not states.get_road_state(event[1]):

                if verbose == 1:
                    print('Type event: {} at road {} at time {}'.format(type_event, event[1], event[0]))
                    print('There is an open road and light is on green, the car just passes through.')

            # If not open and empty we enqueue a car at our road and note the current time
            else:
                if verbose == 1:
                    print('Type event: {} at road {} at time {}'.format(type_event, event[1], event[0]))

                states.enqueue(event[1], event[0])

            # Generate a new arrival with rate passed in simulation. It checks if it is rush hour and multiplies the
            # rate of arrival by 2 at peak rush hours, with the multiplier decreasing linearly as it is further from
            # peak rush hour

            gen_param = roads[event[1]]
            if rush_hour[0] < c_time < rush_hour[1]:
                multiplier = 2 - (abs(c_time - mid_rush1) / (2 * 60 * 60))
                time = min(-0.5 + gen_param[0] / multiplier * np.random.beta(gen_param[1],
                                                                         gen_param[2]), 1) + states.get_clock()
            elif rush_hour[2] < c_time < rush_hour[3]:
                multiplier = 2 - (abs(c_time - mid_rush2) / (2 * 60 * 60))
                time = min(-0.5 + gen_param[0] / multiplier * np.random.beta(gen_param[1],
                                                                         gen_param[2]), 1) + states.get_clock()
            else:
                time = min(-0.5 + gen_param[0] * np.random.beta(gen_param[1], gen_param[2]), 1) + states.get_clock()

            scheduled_events.schedule_arrival(time, event[1])

            # Sort arrivals to ensure newest arrival is first
            scheduled_events.sort_arrivals()

        # Process departures
        if type_event == 'departure':

            # Get event specifics
            road = event[1]
            time_departure = event[0]

            # Advance clock
            states.advance_clock(time_departure)

            # Checks if road has cars in it, if not new departure
            if states.get_road_state(road) and road in light_policy[states.get_light_state()]:
                if verbose == 1:
                    print('Type event: {} at road {} at time {}'.format(type_event, road, time_departure))

                # Do the departure
                time_departure = states.departure(road)

                # If we use smart lights we instantly switch to orange if both roads are empty
                if smart:
                    empty = False
                    for open_road in policies[states.get_light_state()]:
                        if not states.get_road_state(open_road):
                            empty = True
                    if empty:
                        scheduled_events.clear_light_change()
                        scheduled_events.schedule_light_change(states.get_clock(), 5)



                # Update metrics
                total_wait_time += states.get_clock() - time_departure
                total_cars += 1
                road_specific_wait[road] += states.get_clock() - time_departure
                road_specific_cars[road] += 1

                # Schedule new departure with lower flow rate than first departure, to simulate multiple cars following
                # closely together
                time = draw_exponential(flow_cars) + states.get_clock()
                scheduled_events.schedule_departure(time, road)

            # Check if light is orange and there are cars on the road
            elif states.get_road_state(road) and states.get_light_state() == 5:

                # Get time light has been on orange
                time_since_orange = states.get_clock() - states.get_time_last_orange()

                # Make car go through orange with probability based on the time the light has been on orange, low orange
                # time means high chance of passing through
                draw = np.random.uniform()
                if draw > (time_since_orange / orange_time):
                    if verbose == 1:
                        print('Passing through orange!')
                        print('Type event: {} at road {} at time {}'.format(type_event, road, time_departure))

                    # Do departure
                    time_departure = states.departure(road)

                    # Update metrics
                    total_wait_time += states.get_clock() - time_departure
                    total_cars += 1
                    road_specific_wait[road] += states.get_clock() - time_departure
                    road_specific_cars[road] += 1

                    # Schedule new departure
                    time = draw_exponential(flow_cars) + states.get_clock()
                    scheduled_events.schedule_departure(time, road)

                elif verbose == 1:
                    print('Stopped at orange!')
                    print('Type event: {} at road {} at time {}'.format(type_event, road, time_departure))

        # Handle lights change
        if type_event == 'light_change':
            # Advance the clock
            states.advance_clock(event[0])

            # Get new and old lights to determine what the new light change should be
            new_light = event[1]
            old_light = states.get_light_state()

            # If new light is orange, schedule the next non orange light quickly
            if new_light == 5:
                if verbose == 1:
                    print('Type event: {} to light state {} at time {}'.format(type_event, event[1], event[0]))

                if old_light // 4 == 1:
                    states.change_lights(new_light)
                    scheduled_events.schedule_light_change(orange_time + states.get_clock(), 1)
                else:
                    states.change_lights(new_light)
                    scheduled_events.schedule_light_change(orange_time + states.get_clock(), old_light + 1)

            # If the new light is not orange schedule the next orange light based on given light times
            else:
                if smart:
                    states.change_lights(new_light)
                    if verbose == 1:
                        print('Type event: {} to light state {} at time {}'.format(type_event,
                                                                                   states.get_light_state(),event[0]))
                    empty = True
                    total_cars_open = 0

                    # Check if the current open roads all are empty and schedule a new road light instantly
                    for open_road in policies[states.get_light_state()]:
                        total_cars_open += len(states.get_road_state(open_road))
                        if open_road:
                            empty = False

                    # Check if all roads are empty, if they are schedule new light 10 seconds from now to prevent rapid
                    # switching between lights.
                    all_empty = states.all_roads_empty()
                    if empty and not all_empty:
                        scheduled_events.schedule_light_change(states.get_clock(), 5)

                    elif empty and all_empty:
                        scheduled_events.schedule_light_change(states.get_clock()+10, 5)

                    else:
                        # Calculate the ratio of cars that are in this traffic light, if it is high increase time this
                        # Light stays open
                        total_cars_system = states.get_total_cars()
                        ratio = total_cars_open / total_cars_system

                        # Extra time is based on total amount of seconds lights stay open in 'dumb'
                        time = states.get_clock() + total_seconds * ratio
                        scheduled_events.schedule_light_change(time, 5)

                else:
                    states.change_lights(new_light)
                    if verbose == 1:
                        print('Type event: {} to light state {} at time {}'.format(type_event, event[1], event[0]))

                    scheduled_events.schedule_light_change(light_times[new_light - 1] + states.get_clock(), 5)

                for road in light_policy[new_light]:
                    time = draw_exponential(flow_first_car) + states.get_clock()
                    scheduled_events.schedule_departure(time, road)
                    scheduled_events.sort_departures()

        # Update new time after event
        new_time = states.get_clock()

        # Add an entry for the total number of cars in the system
        num_cars_in_system.append(states.get_total_cars())

    # Count the amount of time the cars that are still in the queue after the end of the simulation have waited
    road_specific_wait, road_specific_cars, left_wait_time, left_cars = \
        states.get_wait_time_per_road(road_specific_wait, road_specific_cars)

    # Update metrics
    total_wait_time += left_wait_time
    total_cars += left_cars

    # Create average waited time per road
    try:
        average_wait_per_road = {k: road_specific_wait[k] / road_specific_cars[k] for k in road_specific_wait}
    except ZeroDivisionError:
        average_wait_per_road = None

    return total_wait_time / total_cars, average_wait_per_road, num_cars_in_system


def test_light_schedule(policy, schedules, n_simulations, time_horizon, road_list, rush_hours):
    results = []
    for schedule in schedules:
        print('Testing light times: {}'.format(schedule))
        total_sim_av_time = 0
        for i in range(n_simulations):
            print('Starting simulation {}/{}'.format(i+1, n_simulations))
            average_wait_time, _, _ = main(policy, time_horizon, road_list, rush_hours,
                                           orange_time=4, light_times=schedule, verbose=0, smart=schedule[-1])
            total_sim_av_time += average_wait_time

        results.append(total_sim_av_time / n_simulations)
    print(results)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # List of parameter [a, b, c] to form distribution -0.5 + a * Beta(b, c)
    roads_list = {'NS': [66, 0.971, 2.04], 'NL': [66, 0.971, 2.04], 'ES': [72, 0.963, 1.99], 'EL': [72, 0.963, 1.99],
                  'SS': [123, 0.968, 3.44], 'SL': [123, 0.968, 3.44], 'WS': [69, 0.634, 1.61], 'WL': [69, 0.634, 1.61]}
    policies = {1: ['SL', 'NL'], 2: ['NS', 'SS'], 3: ['ES', 'WS'], 4: ['WL', 'EL'], 5: ['']}
    rush_hour = [21600, 36000, 54000, 68400]
    horizon = 86400

    average_wait, _, _ = main(policies, horizon, roads_list, rush_hour, flow_cars=2, flow_first_car=8, orange_time=4,
                              starting_policy=1, light_times=[40, 40, 40, 40], verbose=0, smart=True)
    to_try = [[40, 40, 40, 60, False], [40, 40, 40, 60, True], [30, 40, 50, 60, False], [30, 40, 50, 60, True] ]

    test_light_schedule(policies, to_try, 20, horizon, roads_list, rush_hour)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
