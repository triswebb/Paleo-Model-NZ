import math
import matplotlib.pyplot as plt
from matplotlib.pyplot import *
from windrose import WindroseAxes
import pandas as pd

class pollen:

    def __init__(self):
        import seaborn as sns
        self.run_pollen()

    def set_style(self):
        plt.style.use(['seaborn-white', 'seaborn-paper'])
        matplotlib.rc("font", family="Arial")


    # Equation to calculate the total proportion of particles captured at a given distance from basin center
    # This equation estimates the source area
    test = 1-math.exp((4*1.5/0.25*0.03*math.sqrt((3.142)*0.21))*(math.pow(100,0.125) - (math.pow(200,0.125))))

    def pollen_distance (self, u, Vg, n=0.25, Cz=0.12, PI=3.14159,particles=1000):
        particles_left = particles * (math.exp((-4 * Vg * self.distance ** n / 2) / ((n * u) * math.sqrt(PI * Cz))))
        return particles_left

    def run_pollen (self):
        # Equation to estimate the number of pollen grains remaining in atmosphere at a given distance
        vx_param =[0.04, 0.06, 0.08]
        y=[]
        x=[]
        particles = 1000
        self.distance = 0
        self.set_style()
        f, axarr = plt.subplots(3, sharex=True)
        axarr[2].set_xlabel('Distance (m)')
        #f.tick_params(labelsize=10)

        for counter, v in enumerate(vx_param):
            for i in range(3, 10, 2):
                while (self.distance <= 5000):
                    particles_left = self.pollen_distance(i, v)
                    y.append((particles_left / particles) * 100)
                    x.append(self.distance)
                    self.distance += 100
                self.distance = 0
                axarr[counter].plot(x, y)
                axarr[counter].text(5050, min(y)-2, "{} m/s".format(i), size=6)
                axarr[counter].text(4600, max(y) - 10, "{} vg".format(v), size=6)
                axarr[counter].set_ylim(0, 100, 10)
                y, x = [], []
            if counter == 1:
                axarr[counter].set_ylabel('Percentage of pollen airborne', fontsize=10)

        plt.draw()
        plt.savefig('graphs/parameters/pollen/pollen_distance_004vg.png', dpi=600)
        plt.show()

class wind_rose():

    def __init__(self):
        self.build_wind_rose()

    def build_wind_rose(self):
        xls_file = pd.ExcelFile("input/GreatBarrier/weather_data/great_barrier.xlsx", dtype=int)
        wind_data = xls_file.parse('wind')
        wind_data = wind_data[wind_data.Direction <= 360]

        ax = WindroseAxes.from_ax()
        ax.bar(wind_data.Direction, wind_data.ms, bins=np.arange(0, 25, 5), normed=True)
        ax.set_legend()
        plt.draw()
        plt.savefig('graphs/parameters/wind/wind_rose.png', dpi=600)
        plt.show()



p = wind_rose()
p


