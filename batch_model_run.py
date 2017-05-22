from mesa.batchrunner import BatchRunner
from model import PaleoFire
import matplotlib.pyplot as plt

parameters = {"width": 800,
              "height": 800,
              "landscape_to_run": "GreatBarrier",
              "headless_mode": True}

batch_run = BatchRunner(PaleoFire,
                        parameters,
                        iterations=2,
                        max_steps=2,
                        model_reporters= {# "Burned": lambda m: self.count_burnt_trees(m),
                           0: lambda m: PaleoFire.count_agent_types(m, 0),
                           1: lambda m: PaleoFire.count_agent_types(m, 1),
                           2: lambda m: PaleoFire.count_agent_types(m, 2),
                           3: lambda m: PaleoFire.count_agent_types(m, 3),
                           4: lambda m: PaleoFire.count_agent_types(m, 4)})

batch_run.run_all()

run_data = batch_run.get_model_vars_dataframe()
print(run_data.head())
