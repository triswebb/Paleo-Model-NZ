'''
PaleoFire Mode
================================
Add description here
'''

import random
import numpy as np
import os
import math
import collections
from copyit import Copyit as cp
from build_landscape import build_landscape
from dynamic_plot import dynamic_plot

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agents import Landscape, Lightning, Deposition_site
from schedule import RandomActivationByBreed

class PaleoFire(Model):
    '''
    PaleoFire Model
    '''

    height = 800
    width = 800

    verbose = False  # Print-monitoring

    def __init__(self, height=800, width=800, landscape_to_run="", headless_mode=False):
        """
        Create a new PaleoFire model with the given parameters.
        """

        # Set parameters
        self.headless_mode = headless_mode
        self.height = height
        self.width = width
        self.landscape_to_run = landscape_to_run
        # activate each agent at random - similar to NetLogo behaviours
        self.schedule = RandomActivationByBreed(self)
        self.grid = MultiGrid(self.height, self.width, torus=True)
        # get landscape data
        self.landscape = build_landscape(self.landscape_to_run)
        # get vegetation data dictionary
        self.veg_data_dict, self.model_params_dict = build_landscape.import_vegetation_data(self.landscape_to_run)
        # populate graph at each step
        self.model_reporters = {# "Burned": lambda m: self.count_burnt_trees(m),
                           0: lambda m: self.count_agent_types(m, 0),
                           1: lambda m: self.count_agent_types(m, 1),
                           2: lambda m: self.count_agent_types(m, 2),
                           3: lambda m: self.count_agent_types(m, 3),
                           4: lambda m: self.count_agent_types(m, 4)}
        self.datacollector = DataCollector(model_reporters=self.model_reporters)
        # import weather data
        self.import_weather_data(self.landscape_to_run)
        # set weather for this year
        self.temp_this_year = self.weather_this_year[random.randrange(100), :][0]
        self.rainfall_this_year = self.weather_this_year[random.randrange(100), :][1]
        self.running = True
        self.deposition_xy_list = []
        self.pollen_count = []
        self.fire_size = collections.OrderedDict()
        self.fire_this_tick = False
        self.time = 0
        self.total_pollen_per_dep = {}
        self.pollen_count_this_tick = {}
        self.source_sites = {}
        self.pollen_count_this_tick[self.time] = {}
        self.total_pollen_per_dep[self.time] = {}
        self.wind_data_dict = build_landscape.import_wind_data(self.landscape_to_run)

        # Create landscape and deposition site patches on grid
        for agent, x, y in self.grid.coord_iter():
            # check that patch is land
            if self.landscape.elevation[x, y] != -9999.0:
                elevation_xy = int(self.landscape.elevation[x, y])

                # calculate burn probabilities based on soil and temp
                burn_s_m_p = self.landscape.burn_s_m_p_array[x, y]
                burn_s_t_p = self.landscape.burn_s_t_p_array[x, y]

                # calculate succession probabilities based on soil and temp
                succ_s_m_p = self.landscape.succ_s_m_p_array[x, y]
                succ_s_t_p = self.landscape.succ_s_t_p_array[x, y]

                if self.landscape.vegetation[x, y] != 5:
                    vegetation_typ_xy = self.landscape.vegetation[x, y]

                    # make sure any changes done to base dictionary are reset
                    self.reset_dictionary(self.veg_data_dict)
                    self.land_list = [1, 2, 3, 4]
                    self.temp_dict = {}
                    self.create_vegetation(vegetation_typ_xy, 0)
                    veg_this_patch = cp.deepish_copy(self.temp_dict)

                time_colonised_xy = self.landscape.time_colonised[x, y]
                is_patch_colonised_xy = self.landscape.colonised[x, y]

                # populate landscape patch with values
                patch = Landscape((x, y), self, elevation_xy, burn_s_m_p, burn_s_t_p, vegetation_typ_xy,
                                  False, time_colonised_xy, is_patch_colonised_xy, succ_s_m_p, succ_s_t_p, veg_this_patch)
                self.grid.place_agent(patch, (x, y))
                self.schedule.add(patch)

            if self.landscape.vegetation[x, y] == 5:
                deposition_area_xy = self.landscape.vegetation[x, y]

                # populate landscape patch with values
                patch = Deposition_site((x, y), self, deposition_area_xy)
                self.grid.place_agent(patch, (x, y))
                self.deposition_xy_list.append([x, y])
                self.schedule.add(patch)

        # Create lightning strikes
        for i in range(1):
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            strike = Lightning((x, y), self)
            self.grid.place_agent(strike, (x, y))
            self.schedule.add(strike)

    def create_vegetation(self, land_type, total):
        if land_type == 0:
            # for now assume that all burned patches are 100% bracken
            self.temp_dict = self.veg_data_dict[land_type]
            self.temp_dict["Dennstaedtiaceae"]["total_species_of_type"] = 100
            return
        else:
            for i in self.veg_data_dict[land_type]:
                num_this_type = np.random.randint(self.veg_data_dict[land_type][i]["min_species_percent"], self.veg_data_dict[land_type][i]["max_species_percent"])
                total += num_this_type
                # if patch has not reached 100% occupation
                if total < 100:
                    self.veg_data_dict[land_type][i]["total_species_of_type"] = num_this_type
                elif total >= 100:
                    diff = total - 100
                    num_this_type = num_this_type - diff
                    self.veg_data_dict[land_type][i]["total_species_of_type"] = num_this_type
                    self.temp_dict.update(self.veg_data_dict[land_type])
                    # remove any vegetation that is 0
                    keys_to_remove = [k for k in self.temp_dict if self.temp_dict[k]["total_species_of_type"] == 0]
                    for k in keys_to_remove:
                        del self.temp_dict[k]
                    return
            self.land_list.remove(land_type)

            # if loop reaches the end and there is still vegetation to add get next landscape type
            # if landscape type 4 then move to 3, 2 and 1
            # if 3 then 4, 2, 1
            # if 2 then 3, 4, 1
            # if 1 then 2, 3, 4
            if self.land_list:
                try:
                    new_land_type = min(filter(lambda x: x > land_type, self.land_list))
                except (ValueError, TypeError):
                    new_land_type = max(filter(lambda x: x < land_type, self.land_list))
            else:
                self.temp_dict.update((self.veg_data_dict[land_type]))
                self.temp_dict[i]["total_species_of_type"] = self.temp_dict[i]["total_species_of_type"] + (100-total)
                return

            if total < 100:
                self.temp_dict.update(self.veg_data_dict[land_type])
                self.create_vegetation(new_land_type, total)

    # reset any changes made to base veg_dict
    def reset_dictionary(self, dict_reset):
        for key, value in dict_reset.items():
            for v in dict_reset[key]:
                dict_reset[key][v]["total_species_of_type"] = 0
        return dict_reset

    def step(self):
        if not self.headless_mode:
            if self.time == 0:
                self.dynam_plot = dynamic_plot(len(self.model_reporters))
        self.wind_speed = [np.random.choice((self.wind_data_dict['ms']['options'])[:-1], size=1, replace=False,
                                           p=self.wind_data_dict['ms']['prob'])]
        self.wind_direction = [np.random.choice((self.wind_data_dict['Direction']['options'])[:-1], size=1, replace=False,
                                           p=self.wind_data_dict['Direction']['prob'])]

        self.schedule.step()
        self.datacollector.collect(self)
        self.temp_this_year = self.weather_this_year[random.randrange(100), :][0]
        self.rainfall_this_year = self.weather_this_year[random.randrange(100), :][1]
        self.produce_pollen()
        if not self.headless_mode:
            self.dynam_plot.plot_tree(self.datacollector.model_vars, self.time)
            self.dynam_plot.plot_pollen(self.pollen_count_this_tick, self.time, self.total_pollen_per_dep, build_landscape.depostion_sites)
        if self.fire_this_tick:
            self.fire_this_tick = False
            if not self.headless_mode:
                self.dynam_plot.plot_fire(self.fire_size)

        if self.verbose:
            print([self.schedule.time,
                   Landscape.get_burned_trees(self)])
        self.time += 1
        self.pollen_count_this_tick[self.time] = {}
        self.total_pollen_per_dep[self.time] = {}

    def run_model(self, step_count):
        if self.verbose:
            print('number of trees: ',
                  self.schedule.get_breed_count(Landscape))

        for i in range(step_count):
            self.step()

    def import_weather_data(self, environment=""):
        for filename in os.listdir("input/"+environment+"/weather_data/"):
            if filename.endswith(".txt"):
                file = os.path.join("input/"+environment+"/weather_data/", filename)
                self.weather_this_year = np.loadtxt(file)

    @staticmethod
    def count_agent_types(model, veg_type):
        """
        Helper method to count landscape agents that have burned.
        """
        # Filter agents on agent type and vegetation type
        total_veg_type = list(filter(lambda x: x.breed == 'Landscape' and x.vegetation_type == veg_type, model.schedule.agents))
        # calculate percentage of vegetation type
        count = int(len(total_veg_type)/model.schedule.get_breed_count(Landscape)*100)
        return count

    @staticmethod
    def count_burnt_trees(model):
        """
        Helper method to count landscape agents that have burned.
        """
        count = 0
        for agent in model.schedule.agents:
            if agent.breed == 'Lightning':
                continue
            if agent.is_patch_burned:
                count += 1
        return count

    def produce_pollen(self):
        """
         Get all locations from the center of a deposition site (50 indicates the radius, i.e. 50 cells). Currently
         this code only includes one deposition site - need to implement all sites. Store in Potential Source Sites
         (p_s_sites)
        """
        for key in build_landscape.depostion_sites:
            # for first iteration capture all potential source sites for every deposition site
            if self.time == 0:
                p_s_sites = self.grid.get_neighbors(build_landscape.depostion_sites[key]["center"], True, False, 10)
                # Some p_s_sites will include water, so filter those sites returned to only include 'Landscape'
                self.source_sites[key] = list(filter(lambda x: x.breed == 'Landscape', p_s_sites))
                self.set_distance_from_depo_site(self.source_sites, key)

            self.pollen_count_this_tick[self.time][key] = {}
            # for each source patch calculate how much pollen from each spices gets to each deposistion site
            for source in self.source_sites[key]:
                #for source in sites:
                for k in source.veg_this_patch:
                    # Calculate how much pollen reaches the center of the depostion site. Equation based on Sutton (1953)
                    pollen_remaining = source.veg_this_patch[k]["pollen_loading"] * (math.exp((-4 * source.veg_this_patch[k]["vel_pollen_deposistion"]
                                                                                               * source.distance_to_disperal[key]
                                                                                               ** self.model_params_dict["turbulence_parameter"] / 2)
                                                                                              / ((self.model_params_dict["turbulence_parameter"] *
                                                                                                  self.wind_speed[0]) *
                                                                                                 math.sqrt(math.pi * self.model_params_dict["vertical_diffucsion_coefficent"]))))
                    if k in self.pollen_count_this_tick[self.time][key]:
                        self.pollen_count_this_tick[self.time][key][k] += pollen_remaining
                    else:
                        self.pollen_count_this_tick[self.time][key][k] = pollen_remaining
            # need to create new dict here
            self.total_pollen_per_dep[self.time][key] = {}
            self.total_pollen_per_dep[self.time][key] = sum(x for x in self.pollen_count_this_tick[self.time][key].values())


    def set_distance_from_depo_site(self, source, key):
        for k, v in source.items():
            for site in v: site.distance_to_disperal[key] = get_distance(site.pos, build_landscape.depostion_sites[key]["center"], self.width,
                                             self.height)


def get_distance(pos_1, pos_2, width, height):
    """ Get the distance between two point, accounting for toroidal space.
    Args:
        pos_1, pos_2: Coordinate tuples for both points.
    """
    x1, y1 = pos_1
    x2, y2 = pos_2
    d_x = abs(x1 - x2)
    d_y = abs(y1 - y2)
    dx = min(d_x, width - d_x)
    dy = min(d_y, height - d_y)
    return math.sqrt(dx ** 2 + dy ** 2)













