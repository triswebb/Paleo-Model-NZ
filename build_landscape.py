import numpy as np
import os
import pandas as pd
from scipy import ndimage
import scipy
import xlrd

class build_landscape():

    height = 800
    width = 800

    def __init__(self, environment):

        self.import_geographyData(environment)

    @staticmethod
    def import_geoRasterArray(asciiRasterFile):
        # create a metadata dictionary
        metadata = {}
        # read in metadata
        inFile = open(asciiRasterFile, 'r')
        textLine = inFile.readline()
        metadata["NCOLS"] = int(textLine.split()[1])
        textLine = inFile.readline()
        metadata["NROWS"] = int(textLine.split()[1])
        textLine = inFile.readline()
        metadata["XLLCORNER"] = float(textLine.split()[1])
        textLine = inFile.readline()
        metadata["YLLCORNER"] = float(textLine.split()[1])
        textLine = inFile.readline()
        metadata["CELLSIZE"] = float(textLine.split()[1])
        textLine = inFile.readline()
        metadata["NODATA_VALUE"] = float(textLine.split()[1])
        inFile.close()

        # create a numpy array of the cost-surface data
        import numpy as np
        rasterArray = np.loadtxt(asciiRasterFile, skiprows=6)

        # package together metadata and rasterArray and return
        return (metadata, rasterArray)

    @classmethod
    def import_geographyData(self, environment):
        for filename in os.listdir("input/" + environment + "/Landscape_data/"):
            if filename.endswith(".asc"):
                env = os.path.join("input/" + environment + "/Landscape_data/", filename)
                dem = build_landscape.import_geoRasterArray(env)
                # get elevation data from .asc file (dem[0]) to get metdadata e.g. numrows etc
                geogData = dem[1]
                # get subset of geography data to fit grid
                subSetOfGeogDataImport = geogData[0:self.width, 0:self.height]
                # grid 0,0 starts from bottom left in grid class, so flip array 270 degrees so
                # imported array matches grid
                subSetOfGeogData = np.rot90(subSetOfGeogDataImport, 3)

                if 'Elev' in filename:
                    self.elevation = subSetOfGeogData
                elif 'Moist' in filename:
                    soil_moisture = subSetOfGeogData
                    # vectorise arrays with probabilities
                    self.burn_s_m_p_array = np.where(soil_moisture != -9999.0, np.round(2 - (1 / (1 + (np.exp(- (soil_moisture * 3)))) * 2), 4), -9999.0)
                    self.succ_s_m_p_array = np.where(soil_moisture != -9999.0, np.round(2 - (1 / (1 + (np.exp(- (soil_moisture * 0.5)))) * 2), 4), -9999.0)
                elif 'Temp' in filename:
                    soil_temp = subSetOfGeogData
                    self.burn_s_t_p_array = np.where(soil_temp != -9999.0, np.round(1/(1 + (np.exp(-(soil_temp * 1))) * 3), 4), -9999.0)
                    self.succ_s_t_p_array = np.where(soil_temp != -9999.0, np.round(1 / (1 + (np.exp(-(soil_temp * 1))) * 0.5), 4), -9999.0)
                elif 'time' in filename:
                    self.time_colonised = subSetOfGeogData
                elif 'colonised' in filename:
                    self.colonised = subSetOfGeogData
                elif 'nlm' in filename:
                    self.vegetation = subSetOfGeogData
                elif 'NonLand' in filename:
                    subSetOfGeogData[(subSetOfGeogData != 22) * (subSetOfGeogData != 70) * (subSetOfGeogData != 46)
                                     * (subSetOfGeogData != 20)] = -9999.0

                    # get non-land elements as 5
                    np.place(subSetOfGeogData, subSetOfGeogData > 0, 5)
                    depo_sites = subSetOfGeogData.astype(int)
                    depo_sites[depo_sites == -9999] = 0
                    # create pattern that identifies 'islands' (deposition sites)
                    s = np.tile(5, (3,3))
                    # get all identified 'islands' and the total number
                    label_m1, nb_labels1 = ndimage.label(depo_sites, structure=s)
                    self.deposition_area = label_m1
                    # get the size of each island
                    size = np.bincount(label_m1.ravel())
                    self.depostion_sites = {}

                    for i in range(nb_labels1):
                        # ignore the first site as this is everything but the deposition site
                        biggest_label = size[1:].argmax() + i
                        # get centre of the deposition sites
                        center = scipy.ndimage.center_of_mass(depo_sites, label_m1, biggest_label)
                        # convert center of depostion site to int
                        center = (int(center[0]), int(center[1]))
                        # create dictionary of dictionaries to store deposition sites details
                        self.depostion_sites[biggest_label] = {}
                        self.depostion_sites[biggest_label].update({"center": center, "size": size[i + 1]})

            else:
                continue
        # merge depoisiton sites and vegetation into the vegetation array so no duplicates
        np.place(self.vegetation, depo_sites == 5,  5)
        print("here")

    @classmethod
    def import_vegetation_data(self, environment):
        self.veg_data_dict = {}
        xls_file = pd.ExcelFile("input/" + environment + "/vegetation_data/vegetation_info_wth_param.xlsx")

        self.veg_data = xls_file.parse('vegetation_data')
        self.model_params = xls_file.parse('parameters')
        model_params_dict = self.model_params.set_index('Parameter')['Value'].to_dict()
        int(model_params_dict["bird-dispersal-radius"])
        #self.model_params = self.model_params.sheet_by_index(0)
        #key = self.model_params.col_values(0, 1)
        #value = self.model_params.col_values(1, 1)

        # identify unique values in veg data by landscape type
        for value in self.veg_data.landscape_type.unique():
            self.veg_data_dict[value] = {}
            # create dictionary of species types organised by landscape type
            for k in self.veg_data_dict:
                temp_veg_data = self.veg_data[self.veg_data['landscape_type'] == k].drop('landscape_type',
                                                                                  axis=1).copy()
                self.veg_data_dict[k] = temp_veg_data.set_index('functional_type').T.to_dict()

        return self.veg_data_dict, model_params_dict

    @classmethod
    def import_wind_data(self, environment):
        xls_file = pd.ExcelFile("input/" + environment + "/weather_data/great_barrier.xlsx", dtype=int)
        wind_data = xls_file.parse('wind')
        wind_data_dict = {}

        for column in wind_data:
            if column == "Direction" or column == "ms":
                wind_data_dict[column] = {}
                # create bins for speed and direction
                bin_num = int(max(wind_data[column]))
                # weight values to get relative frequency
                weights = np.ones_like(wind_data[column]) / len(wind_data[column])
                # create probability frequency for each direction and speed
                (prob, options) = np.histogram(wind_data[column], weights=weights, bins=bin_num)
                # store values probability arrays in dictionary
                wind_data_dict[column]["prob"] = prob
                wind_data_dict[column]["options"] = options
        return wind_data_dict














