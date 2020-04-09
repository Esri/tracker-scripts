## Cleanup tracks based on spatial relationship with a polygon feature layer

This script allows cleanup of track points from a tracks layer based on a spatial relationship to polygon geometry. You provide the script with a feature layer containing polygons, whether or not you want to delete track points inside or outside the polygons, and the script will perform a spatial intersection and delete any necessary features.

Location Tracking must be enabled for your organization to use this script. You must be an admin to use this script. 

Supports Python 3.6+

----

Other than the authentication arguments (username, password, org) the script uses the following parameters:

- -layer-url <layer_url> - The feature service URL for your polygon feature layer with features that will be spatially intersected with track points. This is required.
- -where <where_clause> - The where clause used to filter out only certain polygons for the spatial comparison (for example, OBJECTID > 1). Defaults to 1=1 (all features are used for comparison)
- -delete-inside <delete_inside> - A boolean on whether or not features should be deleted if they are inside the polygons. If True, delete track points inside the polygons. If False, delete track points outside the polygon. This is required. 

Example Usage 1  - Check whether the three workers (admin_tracker, user_james, and user_aaron) were within 100 meters of the assignment location any time in the 10 minutes before and 10 minutes after the assignment was completed:
```python
python polygon_cleanup_tracks.py -u username -p password -org https://arcgis.com -delete-inside True -where 'OBJECTID > 6' -layer-url https://services.arcgis.com/a910db6b36ff4066a3d4131fccc3da9b/arcgis/rest/services/polygons_ad9af2fc00314fa79ce79ec7d7317acc/FeatureServer/0
```

## What it does

 1. First the script uses the provided credentials to authenticate with AGOL to get the required token
 2. Then the feature layer to be validated is fetched
 3. Then the location feature layers are fetched
 4. Union the geometry of all polygons together
 5. Compare the track points against your unioned polygon geometry
 6. Delete features that do or do not intersect the polygon (based on whether you have set inside or outside)
