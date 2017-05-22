import numpy as np
from matplotlib import pyplot as plt
from collections import OrderedDict

veg_types = ["Bracken", "Scrub", "Shrub", "Young Forest", "Old Forest"]

class dynamic_plot(object):
    def __init__(self, number_of_elments_plt):
        #ND: These could be passed as part of the object instance
        self.colors_line_graph = [(249, 249, 18), (188, 152, 8), (170, 188, 8), (134, 188, 8), (98, 137, 8)]
        self.colors_line_graph = self.convert_colors(self.colors_line_graph)
        #create multiple multiple plots for each veg_type
        self.fig = plt.figure(figsize=(9, 9))
        self.fig2 = plt.figure(figsize=(9, 11))
        self.fig2.subplots_adjust(hspace=.6)
        self.fig.subplots_adjust(hspace=.8)
        self.ax3 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.h1 = [self.ax2.plot([], [], label=veg_types[i])[0] for i in range(number_of_elments_plt)]
        self.ax2.set_ylabel('% of vegetation type')
        self.ax3.set_ylabel('Pixels burned (log)')
        self.ax2.set_xlabel('Years')
        self.ax2.set_ylim([0, 100])
        plt.ion()

    def plot_tree(self, veg_count, time):
        self.ax2.set_xlim([0, 150])
        self.ax2.set_xticks(range(0, 150), 10)
        for i, h in zip(range(len(veg_count)), self.h1):
            h.set_xdata(np.append(h.get_xdata(), time))
            h.set_ydata(np.append(h.get_ydata(), veg_count.get(i)[time]))
            h._color = self.colors_line_graph[i]
        if time == 1:
            handles, labels = self.ax2.get_legend_handles_labels()
            by_label = OrderedDict(zip(labels, handles))
            self.ax2.legend(by_label.values(), by_label.keys(), fontsize=10, loc="upper right")
        plt.pause(0.001)

    def mk_groups(self, data, ax):
        try:
            newdata = data.items()
        except:
            return

        thisgroup = []
        groups = []
        for key, value in newdata:
            newgroups = self.mk_groups(value, ax)
            if newgroups is None:
                value = (value/self.total_pollen) * 100
                thisgroup.append((key, value))
            else:
                thisgroup.append((key, len(newgroups[-1])))
                if groups:
                    groups = [g + n for n, g in zip(newgroups, groups)]
                else:
                    groups = newgroups
        return [thisgroup] + groups

    def add_line(self, xpos, ypos, ax):
        line = plt.Line2D([xpos, xpos], [ypos + .1, ypos],
                          transform=ax.transAxes, color='black')
        line.set_clip_on(False)
        ax.add_line(line)

    def label_group_bar(self, data, ax, site_num, center):
        groups = self.mk_groups(data, ax)
        xy = groups.pop()
        x, y = zip(*xy)
        x = [elem[:3] for elem in x]
        ly = len(y)
        xticks = range(1, ly + 1)
        ax.set_xticks(xticks)
        self.ax1.set_title("Deposition site: {0} Center: {1}".format(site_num, center), fontsize=10)
        ax.set_xticklabels(x, rotation=90, size=10)
        ax.set_xlim(.5, ly + .5)
        ax.yaxis.grid(True)
        scale = 1. / ly
        for pos in range(ly + 1):
            self.add_line(pos * scale, -.1, ax)
        ypos = -.2
        while groups:
            group = groups.pop()
            pos = 0
            count = 0
            for label, rpos in group:
                lxpos = (pos + .5 * rpos) * scale
                ax.text(lxpos, ypos, label, ha='center', transform=ax.transAxes)
                self.add_line(pos * scale, ypos, ax)
                pos += rpos
                count += 1
            self.add_line(pos * scale, ypos)
            ypos -= .1
        ax.bar(xticks, y, align='center', color='#3CB371')

    def plot_pollen(self, pollen_count, time, total_pollen, dep_site):
        for k, pollen_to_plot in pollen_count[time].items():
            self.ax1 = self.fig2.add_subplot(len(pollen_count[time]), 1, k)
            self.ax1.clear()
            self.ax1.set_ylabel('Pollen sum %')
            self.total_pollen = total_pollen[time][k]
            self.label_group_bar(pollen_count[time][k], self.ax1, k, dep_site[k]["center"])

    def convert_colors(self, colors_line_graph):
        for i in range(len(colors_line_graph)):
            r, g, b = colors_line_graph[i]
            colors_line_graph[i] = (r / 255., g / 255., b / 255.)
        return colors_line_graph

    def plot_fire(self, fire_size):
        self.ax3.set_yscale('log')
        self.ax3.set_xticks(range(len(fire_size)))
        self.ax3.set_xticklabels(list(fire_size.keys()))
        self.ax3.bar(range(len(fire_size)), fire_size.values(), align='center', color='r')