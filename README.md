<p align="center">
  <img src="docs/assets/images/drivetraj-wordmark.svg" width="560" alt="DriveTraj">
</p>

<h1 align="center">Beyond a Single Human Demonstration:<br>Learning from Scored Trajectory Alternatives for End-to-End Driving</h1>

Driving logs record one executed trajectory, while a planner must generate and compare many feasible alternatives. DriveTraj turns these records into scored trajectory supervision: constrained path construction and screening yield **2.61M high-quality targets** from 103.3k real scenes. Dense matching teaches distinct proposals, and replay of successful and failed paths trains their scores. A second stage learns local residual corrections, guided by a pretrained Joint-Embedding Predictive Architecture (JEPA) video encoder adapted to driving observations. DriveTraj-Scale reaches **95.55 NAVTEST PDMS**; its Stage 1 planner scores **91.32 NAVTEST EPDMS** and **56.13 NAVHARD EPDMS**. On 345 HUGSIM scenarios, Stage 2 achieves **56.09 route completion** and **46.69 HD-Score**.

## Method

![DriveTraj method overview](docs/assets/images/overview.png)
