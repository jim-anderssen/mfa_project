# MFA  Project 

This is a repository for analysing material/waste stocks and flows through Eurostat's dataset.

The overarching goal is to provide highly-detailed statistics (as detailed as possible) for generation, treatment and shipment of waste, which will allow for data-driven decision-making for investments in recycling/recovery technology.

## See data/processed for first examples of the type of data intended to be produced in this repo:

- The "Nordic_shipment_economic_potential" dataset is aggregated shipments of disposed waste per EWC-Stat Level 2 code, with mean and std. of yearly shipments (tonnes).
    - Some level-of-magnitude data has been grossly estimated for each Level 2 code, and these can be adjusted when needed to be more accurate.
    - This type of data enables economic modeling of recycling/recovery potential.

- The 2 other datasets are the main interesting shipments from the previous dataset, but all other recorded shipments of the same waste between the same countries. This also includes the 6-digit LoW codes, which are more detailed, and allows for analysing the waste homogeneity. 
    - These will be streamlined in the future for better readability.

- Waste generation shows an example of the top 50 largest recorded waste generations in metal industries (Nace2 = C24,C25)

## See notebooks/show_dataset_structure for other available data from Eurostats datasets


## Project Organization (template)

```
├── LICENSE            <- Open-source license if one is chosen
├── README.md          <- The top-level README for developers using this project
├── data
│   ├── external       <- Data from third party sources
│   ├── interim        <- Intermediate data that has been transformed
│   ├── processed      <- The final, canonical data sets for modeling
│   └── raw            <- The original, immutable data dump
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
└── src                         <- Source code for this project
    │
    ├── __init__.py             <- Makes src a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    │    
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    ├── plots.py                <- Code to create visualizations 
    │
    └── services                <- Service classes to connect with external platforms, tools, or APIs
        └── __init__.py 
```