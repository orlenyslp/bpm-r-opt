import sys
import copy

import autograd.numpy as anp
from pymoo.model.problem import Problem

from data_structures.pools_info import PoolInfo
from support_modules.bpmn_parser import update_resource_pools
from support_modules.simulation_runner import perform_simulation
from support_modules.file_manager import update_genetic_stats_file


class NSGA2Problem(Problem):
    def __init__(self, log_name, pools_info, simulation_count):
        self.log_name = log_name
        self.it_number = 0
        self.initial_pools_info = pools_info

        self.simulation_count = simulation_count

        xl = [1] * len(pools_info.pools)
        xu = [pools_info.total_resoures] * len(pools_info.pools)
        super().__init__(n_var=len(pools_info.pools),
                         n_obj=2,
                         n_constr=0,
                         xl=anp.array(xl),
                         xu=anp.array(xu))

    def _evaluate(self, x, out, *args, **kwargs):
        population_times = []
        population_costs = []
        for resorces_count in x:
            [cost, cycle_time] = self._generate_solution(resorces_count)
            population_costs.append(cost)
            population_times.append(cycle_time)

        out["F"] = anp.column_stack([population_costs, population_times])

    def _generate_solution(self, total_resources):
        pools = self.initial_pools_info.pools
        new_pools = copy.deepcopy(pools)
        index = 0
        for pool_name in new_pools:
            new_pools[pool_name].total_amount = total_resources[index]
            index += 1
        new_pools_info = PoolInfo(new_pools, self.initial_pools_info.task_pools)

        update_resource_pools(new_pools_info.pools)
        simulation_info = perform_simulation(new_pools_info, self.log_name, self.simulation_count, self.it_number)
        self.it_number += 1
        print_iteration_info(new_pools_info, self.it_number)

        if simulation_info is None:
            return [sys.float_info.max, sys.float_info.max]

        update_genetic_stats_file(self.log_name, self.it_number, simulation_info, new_pools_info)

        return [simulation_info.execution_cost(), simulation_info.cycle_time()]


def print_iteration_info(pools_info, sol_number):
    print("SOLUTION-EVAL # %d" % sol_number)
    print("SOLUTION-ID: " + pools_info.id)
    print("------------------------------------------------------------------------------------")
