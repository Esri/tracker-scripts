# Tracker Scripts
A set of Python scripts and notebooks to help administer track views and analyze track data

### Features

Several example Jupyter notebooks and scripts are provided to demonstrate some more advanced workflows that are possible via the ArcGIS API for Python and Tracker.

Notebooks:
- [Quickstart Guide](notebooks/examples/Quickstart%20Guide.ipynb)
- [Basic Track Analysis](notebooks/examples/Basic%20Track%20Analysis.ipynb)
- [Basic Track Analysis - PySpark](notebooks/examples/Basic%20Track%20Analysis%20-%20Pyspark.ipynb)
- [Location Tracking Status](notebooks/examples/Location%20Tracking%20Status.ipynb)
- [Creating Track Lines](notebooks/examples/Create%20Track%20Lines%20From%20Points.ipynb)
- [Visualize Route Deviance](notebooks/examples/Visualize%20Route%20Deviance.ipynb)
- [Identify Inspected Buildings](notebooks/examples/Identify%20Inspected%20Buildings.ipynb)
- [Find Dwell Times at Polygons](notebooks/examples/Find%20Dwell%20Times%20at%20Polygons.ipynb)
- [Proximity Tracing](notebooks/examples/Proximity%20Tracing.ipynb)
- [Create an Aggregated Map Service](notebooks/examples/Create%20an%20Aggregated%20Map%20Service.ipynb)

Scripts:
- [Check Edit Location](scripts/check_edit_location.py) - [README here](check_edit_location.md)
- [Mirror LKL Layer](scripts/mirror_lkl_layer.py) - [README here](mirror_lkl_layer.md)
- [Polygon Cleanup Tracks](scripts/polygon_cleanup_tracks.py) - [README here](polygon_cleanup_tracks.md)
- [Generate User-based Arcade Expression](scripts/generate_users_arcade_expression.py) - [README here](generate_user_based-arcade_expression.md)


### Instructions

1. Install [Anaconda](https://www.anaconda.com/distribution)
2. Run `conda env create --file environment.yml` to create the virtual environment with the correct dependencies
3. Run `conda activate tracker-scripts` to activate the environment
4. Start the jupyter server using `jupyter notebook` or run the Python script from command line
5. Open the notebook, modify it, and then it run it

### Requirements
- [Anaconda](https://www.anaconda.com/distribution) must be installed
- Web browser capable of running jupyter notebooks

## Resources

 * [ArcGIS API for Python](https://developers.arcgis.com/python)
 * [Tracker for ArcGIS](https://www.esri.com/en-us/arcgis/products/tracker-for-arcgis/overview)

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone.
Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing

Copyright 2020 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's
[LICENSE](License.txt) file.
