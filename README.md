<p align="center">
  <img src="docs/assets/images/drivetraj-wordmark.svg" width="560" alt="DriveTraj">
</p>

<h1 align="center">Beyond a Single Human Demonstration:<br>Learning from Scored Trajectory Alternatives for End-to-End Driving</h1>

## Method

![DriveTraj method overview](docs/assets/images/overview.png)

DriveTraj constructs scored trajectory alternatives from driving logs and uses them to train generation, refinement, and selection.

- **Scored trajectory construction.** Smooth reference-path deformations are tracked and evaluated. Driving validity, trackability, and geometric separation produce **2.61M supervision targets from 103.3k real scenes**; unsuccessful paths remain in the scoring archive.
- **Stage 1: generation and scoring.** Dense one-to-one matching assigns screened targets to distinct autoregressive proposals alongside expert supervision. The scorer fits component labels and total scores on native candidates and stratified replay.
- **Stage 2: residual refinement.** A diffusion transformer learns corrections toward up to four compatible targets per parent. Denoising and trajectory losses share the same winner, while the scorer learns fresh labels on the refined candidate pool.
- **JEPA video adaptation.** A pretrained Joint-Embedding Predictive Architecture encoder learns from masked-video prediction. Separate adapters condition refinement and scoring on observed-frame features. Only the video objective updates the encoder; inference uses historical and current observations.
