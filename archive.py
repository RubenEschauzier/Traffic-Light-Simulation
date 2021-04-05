


def calculate_gradient(alpha, gamma, iteration, objective, policy,
                       time_horizon, road_list, rush_hours, orange_time,
                       theta):
    c_i = 1 / ((iteration + 1) ** gamma)
    delta = (2 * np.random.randint(0, 2, size=(len(theta))) - 1)

    theta_p = theta + c_i * delta
    theta_n = theta - c_i * delta

    objective_p = main(policy, time_horizon, road_list, rush_hours,
                       orange_time=orange_time, light_times=theta_p, verbose=0)
    objective_n = main(policy, time_horizon, road_list, rush_hours,
                       orange_time=orange_time, light_times=theta_n, verbose=0)

    gradient_est = (objective_p - objective_n) / 2 * c_i * delta

    return gradient_est


def gradient_decent(alpha, gamma, max_iter, initial_theta, policy, time_horizon, road_list, rush_hours, orange_time):
    theta = initial_theta
    current_obj = main(policy, time_horizon, road_list, rush_hours,
                       orange_time=orange_time, light_times=initial_theta, verbose=0)
    for i in range(max_iter):
        loop = True
        sigma = 100
        a_i = 1 / (i + 1) ** alpha

        gradient = calculate_gradient(alpha, gamma, i, current_obj, policy,
                                      time_horizon, road_list, rush_hours, orange_time, theta)
        print(gradient)

        obj = main(policy, time_horizon, road_list, rush_hours,
                   orange_time=orange_time, light_times=theta, verbose=0)

        print(obj)

        theta = theta + a_i * -gradient
        print(theta)

    pass