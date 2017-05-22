import random
import math

class Fire():

    def fire_front(patches_to_burn, model):
        model.fire_size[model.time] = 1
        model.fire_this_tick = True
        while len(patches_to_burn) != 0:
            patches_to_burn_new = []
            for this_patch in patches_to_burn:
                neighbours = this_patch.model.grid.get_neighbors(this_patch.pos, 1, False)
                # filter list of neighbours to only those that are landcape based and not burned
                land_scape_neighs = list(filter(lambda x: x.breed == 'Landscape' and x.is_patch_burned == False, neighbours))
                for neigh_patch in land_scape_neighs:
                    slope = math.atan(abs(neigh_patch.elevation - this_patch.elevation) / 1000)
                    if this_patch.elevation >= neigh_patch.elevation:
                        slope_burn_prob = (math.exp(3.533 * (math.tan(slope) ** 1.2)))
                    else:
                        slope_burn_prob = (1 - 0.033 * slope + 0.000749 * slope * 2) * math.cos(slope)
                    if random.random() <= 0.57 * slope_burn_prob and Fire.does_this_patch_burn(neigh_patch):
                        neigh_patch.is_patch_burned = True
                        patches_to_burn_new.append(neigh_patch)
                        model.fire_size[model.time] += 1
            patches_to_burn = patches_to_burn_new


    def does_this_patch_burn(patch_veg):
        if random.random() <= patch_veg.flamability * patch_veg.burn_s_m_p * patch_veg.burn_s_t_p \
                * patch_veg.model.rainfall_this_year * patch_veg.model.temp_this_year:
            return True
        else:
            return False