import random
from mesa import Agent
from build_landscape import build_landscape
from fire import Fire
from copyit import Copyit as cp

class Landscape(Agent):

    def __init__(self, pos, model, elevation, burn_s_m_p, burn_s_t_p, vegetation_type, is_patch_burned,
                 time_colonised, is_patch_colonised, succ_s_m_p, succ_s_t_p, veg_this_patch):

        super().__init__(pos, model)
        self.elevation = elevation
        self.burn_s_m_p = burn_s_m_p
        self.burn_s_t_p = burn_s_t_p
        self.succ_s_m_p = succ_s_m_p
        self.succ_s_t_p = succ_s_t_p
        self.vegetation_type = vegetation_type
        self.is_patch_burned = is_patch_burned
        self.breed = "Landscape"
        self.time_since_last_burnt = 0
        self.time_colonised = time_colonised
        self.is_patch_colonised = is_patch_colonised
        self.dispersal_patches = []
        self.veg_this_patch = veg_this_patch
        # landscape agent could be close to several deposition sites - store distance to each
        self.distance_to_disperal = {}

    # automatically update the flamability value when vegetation type is changed
    @property
    def flamability(self):
        return max(k["flamability_probs"] for k in self.veg_this_patch.values())
        #return self.model.veg_data_dict[self.vegetation_type]["flamability_probs"][0]

    # automatically update succession times based on veg type
    @property
    def min_succession_time(self):
        return int(sum((k["succession_time_min"] for k in self.veg_this_patch.values())) / len(self.veg_this_patch))
        #return self.model.veg_data_dict[self.vegetation_type]["succession_time_min"][0]

    @property
    def max_succession_time(self):
        return int(sum((k["succession_time_max"] for k in self.veg_this_patch.values())) / len(self.veg_this_patch))

    @property
    def succession_probability(self):
        return succession_prob_calc(self.min_succession_time, self.max_succession_time)

    '''
    @property
    def functional_types(self):
        return self.model.veg_data_dict[self.vegetation_type]["functional_type"]

    @property
    def pollen_load(self):
        return self.model.veg_data_dict[self.vegetation_type]["pollen_loading"]
    '''

    def step(self):
        if self.is_patch_burned:
            # this will automatically update flammability
            self.vegetation_type = 0
            self.veg_this_patch = cp.deepish_copy(self.model.veg_data_dict[0])
            self.is_patch_burned = False
            self.is_patch_colonised = 0
            self.time_colonised = 0
        if self.is_patch_colonised == 1:
            self.succession()
        elif self.is_patch_colonised == 0:
            self.dispersal()

    def succession(self):
        self.time_colonised += 1
        # Should maybe include rule to succeed if max colonised time is reached?
        if self.vegetation_type <= 3 and self.time_colonised >= self.min_succession_time:
            if random.random() <= self.succession_probability * self.succ_s_m_p * self.succ_s_t_p * self.model.rainfall_this_year * self.model.temp_this_year:
                self.move_to_next_land_type(1)
                self.vegetation_type += 1

                #vegetation.set_veg_totals(self.model, self)
                # will further colonisation be required for succession?
                if self.vegetation_type == 1 or self.vegetation_type == 2:
                    self.is_patch_colonised = 0
                self.time_colonised = 0

    def dispersal(self):
        if self.vegetation_type == 0:
            self.is_patch_colonised = 1
        else:
            if not self.dispersal_patches:
                self.dispersal_patches, self.dispersal_radius = self.set_dispersal_patches()
            potential_dis_patches = list(
                filter(lambda x: x.vegetation_type > self.vegetation_type, self.dispersal_radius))

            try:
                if random.random() <= (len(potential_dis_patches) / self.dispersal_patch_count):
                    self.is_patch_colonised = 1
            except ZeroDivisionError:
                return
        return

    def set_dispersal_patches(self):
        # get all agents in dispersal range
        bird_dispersal_radius = int(self.model.model_params_dict["bird-dispersal-radius"])
        radius = self.model.grid.get_neighbors(self.pos, True, True, bird_dispersal_radius)
        # filter agent list so that only those in landscape are considered
        self.dispersal_radius = list(filter(lambda x: x.breed == "Landscape", radius))
        self.dispersal_patch_count = len(self.dispersal_radius)

        return self.dispersal_patch_count, self.dispersal_radius

    def move_to_next_land_type(self, distance):
        neighbours = self.model.grid.get_neighbors(self.pos, True, False, distance)
        potential_new_veg = filter(lambda x: x.breed == "Landscape", neighbours)
        potential_new_veg = list(filter(lambda x: x.vegetation_type > self.vegetation_type, potential_new_veg))
        if potential_new_veg:
            new_veg = random.choice(potential_new_veg)
            self.veg_this_patch = {}
            self.veg_this_patch = cp.deepish_copy(new_veg.veg_this_patch)
            return
        else:
            distance += 1
            self.move_to_next_land_type(distance)

class Lightning(Agent):

    def __init__(self, pos, model):
        super().__init__(pos, model)
        self.breed = "Lightning"

    def step(self):
        # Create lightning strikes
        x = random.randrange(self.model.width)
        y = random.randrange(self.model.height)
        strike = Lightning((x, y), self.model)
        self.model.grid.place_agent(strike, (x, y))
        self.model.schedule.add(strike)
        potential_to_burn = []
        struck_land = False

        this_cell = self.model.grid.get_cell_list_contents((x, y))

        # Check to see if lighting hits land
        for obj in this_cell:
            if obj.breed == "Landscape":
                patch_veg = obj
                struck_land = True

        if struck_land:
            if patch_veg.is_patch_burned == False:
                if Fire.does_this_patch_burn(patch_veg):
                    patch_veg.is_patch_burned = True
                    potential_to_burn.append(patch_veg)
                    Fire.fire_front(potential_to_burn, self.model)

        self.model.grid._remove_agent(self.pos, self)
        self.model.schedule.remove(self)

'''
Early ideas:
This agent should be created as a result of fire - several factors to consider:
1. Size of fire - Macroscopic/Microscopic - will determine how far it travels
2. Wind direction
3. Distance to deposition site - this will mean accurately identifying swamps/lakes on grid
4. Type of vegetation burning
'''
class charcoal(Agent):
    def __init__(self, pos, model, size_of_fire, vegetation_type_burning):
        print("charoal born!")

'''
Early ideas:
This agent should be created each tick??:
1. Amount of pollen produced - could be tricky to portray accurately as varied at species level
2. Age of species/functional type to be considered
2. Distance from deposition site - Can travel along way, maybe not so important
3. New class may not be needed and could just simply be a function of vegetation class?

First Steps!
1. Get center of deposition site...
'''
class pollen(Agent):
    def __init__(self, pos, model, pollen_type):
        print("pollen born!")

'''
Early ideas:
Should be born/die given set birth and death rates:
1. How many fires how often?
2. How many people of GBI before European arrival
3. Where did they go, why? Look at settlement records
'''
class tribe(Agent):
    def __init__(self, pos, model):
        print("Human born, we're all fucked!")


class Deposition_site(Agent):
    def __init__(self, pos, model, deposition_area):
        self.deposition_area = deposition_area
        self.breed = "deposition_site"

    @property
    def get_size_of_site(self):
        return build_landscape.depostion_sites[self.deposition_area]["size"]

    @property
    def get_center_of_site(self):
        return build_landscape.depostion_sites[self.deposition_area]["center"]

def succession_prob_calc(min, max):
    prob = 1 - (1 - 0.95) ** (1 / (min - max))
    return abs(prob)










