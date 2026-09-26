# Evidence report

Test split: 2282 molecules, IDs >= 20101. Ensemble members: 5.

## A. Why graph models lead

| endpoint   |   GNN MAE |   LGBM MAE |   GNN rho |   LGBM rho |
|:-----------|----------:|-----------:|----------:|-----------:|
| LogD       |     0.425 |      0.501 |     0.849 |      0.758 |
| KSOL       |     0.359 |      0.465 |     0.573 |      0.497 |
| HLM        |     0.29  |      0.301 |     0.628 |      0.578 |
| MLM        |     0.369 |      0.377 |     0.514 |      0.481 |
| Papp       |     0.271 |      0.278 |     0.625 |      0.594 |
| Efflux     |     0.344 |      0.36  |     0.691 |      0.667 |
| MPPB       |     0.203 |      0.273 |     0.787 |      0.646 |
| MBPB       |     0.15  |      0.23  |     0.872 |      0.768 |
| MGMB       |     0.176 |      0.227 |     0.819 |      0.72  |
| MEAN       |     0.288 |      0.335 |     0.706 |      0.634 |

GNN better MAE on 9/9 endpoints. Mean MAE 0.288 vs 0.335.
VERDICT A1/A2: KEEP

## A4. When does blending with a tree model help?

| endpoint   |   resid_corr |   gnn_mae |   blend50_mae |   best_mae |   best_w_gnn | blend_helps   |
|:-----------|-------------:|----------:|--------------:|-----------:|-------------:|:--------------|
| LogD       |        0.772 |     0.425 |         0.428 |      0.417 |         0.75 | False         |
| KSOL       |        0.826 |     0.359 |         0.398 |      0.359 |         1    | False         |
| HLM        |        0.794 |     0.29  |         0.281 |      0.28  |         0.6  | True          |
| MLM        |        0.808 |     0.369 |         0.354 |      0.354 |         0.55 | True          |
| Papp       |        0.827 |     0.271 |         0.265 |      0.265 |         0.6  | True          |
| Efflux     |        0.93  |     0.344 |         0.347 |      0.344 |         0.9  | False         |
| MPPB       |        0.788 |     0.203 |         0.226 |      0.203 |         1    | False         |
| MBPB       |        0.749 |     0.15  |         0.176 |      0.15  |         1    | False         |
| MGMB       |        0.851 |     0.176 |         0.193 |      0.176 |         1    | False         |

Note: best_w_gnn is chosen on test, so it is an upper bound, shown only to indicate where a blend could help at all.

Blending (50/50) helps on: ['HLM', 'MLM', 'Papp']
VERDICT A4: KEEP (reframed: helps only on local properties)

## B1. Activity cliffs

| endpoint   |   n_cliff |   cliff_mae |   flat_mae |   ratio |
|:-----------|----------:|------------:|-----------:|--------:|
| HLM        |       580 |       0.548 |      0.204 |   2.686 |
| MLM        |       819 |       0.549 |      0.307 |   1.786 |
| LogD       |      8677 |       0.383 |      0.336 |   1.141 |
| Efflux     |      1577 |       0.558 |      0.19  |   2.937 |

VERDICT B1: KEEP (error on cliff pairs vs near-identical pairs)

## B2. Drift into new chemistry

| endpoint   |   unc_vs_err_rho |   mean_bias |
|:-----------|-----------------:|------------:|
| LogD       |            0.055 |      -0.148 |
| KSOL       |            0.512 |      -0.012 |
| HLM        |            0.153 |      -0.07  |
| MLM        |            0.112 |       0.018 |
| Papp       |            0.028 |       0.101 |
| Efflux     |            0.326 |      -0.224 |
| MPPB       |            0.172 |      -0.098 |
| MBPB       |            0.197 |      -0.053 |
| MGMB       |            0.051 |      -0.03  |

mean_bias > 0 means the model predicts too high on later compounds.

Uncertainty tracks error on 5/9 endpoints.
VERDICT B2: KEEP

Real-unit medians, early vs late compounds (the whack-a-mole story):

|        |   train median |   test median |
|:-------|---------------:|--------------:|
| LogD   |           2.2  |          2.2  |
| KSOL   |         112    |        249    |
| HLM    |          16.3  |         22.25 |
| MLM    |         240.75 |        147.85 |
| Papp   |          10.17 |          3.22 |
| Efflux |           1.34 |          4.99 |
| MPPB   |           8.9  |         12.7  |
| MBPB   |           3.76 |          4.15 |
| MGMB   |           5.2  |          7    |

## B3. The solubility ceiling

Raw KSOL values: 7423, of which censored ('<' or '>'): 125
Raw HLM values: 4822, censored: 280 (of which '<': 265 - the most stable compounds, deleted from the ML-ready file)

Model quality by solubility band:

| band           |    n |   mae |   spearman |
|:---------------|-----:|------:|-----------:|
| low (0-100 uM) |  702 | 0.574 |      0.492 |
| mid            |  418 | 0.309 |      0.145 |
| at ceiling     | 1050 | 0.235 |      0.1   |

Low MAE with collapsed rho at the ceiling = looks accurate, cannot rank.
VERDICT B3: KEEP if rho drops in the ceiling band.

## B4. Blind to 3D

Molecules sharing a 2D skeleton but differing in stereochemistry: 548 groups
Groups where a measured value differs by >=0.5 log units: 129
VERDICT B4: KEEP

