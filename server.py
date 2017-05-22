from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule

from agents import Landscape, Lightning, Deposition_site
from model import PaleoFire

def paleo_fire_portrayal(agent):
    if agent is None:
        return

    portrayal = {"Shape": "circle",
                 "Filled": "true"}

    if type(agent) is Lightning:
        portrayal["Color"] = "#666666"
        portrayal["r"] = 0.8
        portrayal["Layer"] = 3

    elif type(agent) is Landscape:
        if agent.elevation != 9999:
            if agent.vegetation_type == 0:
                portrayal["Color"] = "#F8F520"
            if agent.vegetation_type == 1:
                portrayal["Color"] = "#AF9B3D"
            if agent.vegetation_type == 2:
                portrayal["Color"] = "#9AAF3D"
            if agent.vegetation_type == 3:
                portrayal["Color"] = "#86CB14"
            if agent.vegetation_type == 4:
                portrayal["Color"] = "#5B8A0D"
            if agent.is_patch_burned == True:
                portrayal["Color"] = "Red"
            portrayal["Shape"] = "rect"
            portrayal["Layer"] = 2
            portrayal["w"] = 1
            portrayal["h"] = 1

    elif type(agent) is Deposition_site:
            portrayal["Color"] = "blue"
            portrayal["Shape"] = "rect"
            portrayal["Layer"] = 2
            portrayal["w"] = 1
            portrayal["h"] = 1

    return portrayal

canvas_element = CanvasGrid(paleo_fire_portrayal, 800, 800, 800, 800)
chart_element = ChartModule([{"Label": "Burned", "Color": "#AA0000"},
                             {"Label": 0, "Color": "#FFD700"},
                             {"Label": 1, "Color": "#DEB887"},
                             {"Label": 2, "Color": "#DAA520"},
                             {"Label": 3, "Color": "#8FBC8F"},
                             {"Label": 4, "Color": "#006400"}])

server = ModularServer(PaleoFire, [canvas_element, chart_element],
                       "PaleoFire", landscape_to_run = "GreatBarrier")


server.launch()
