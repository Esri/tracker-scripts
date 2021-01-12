## Export tracks from ArcGIS Online

This script provides the ability to export tracks from a location tracking or track view feature service. This script only works for ArcGIS Online. It is designed to be a scheduled task to routinely export track data for storage outside of ArcGIS Online. It generates the CSV file on the server, then downloads it. It supports exporting the last X number of full days of tracks, where a day can be defined in any time zone.

----

The script uses the following parameters:

- -username \<username\> - The username to authenticate with
- -password \<password\> - The password to authenticate with
- -org \<org\> - The organization url to sign in with. Defaults to "https://arcgis.com"
- -track-item \<tracks-item\> - The item id of the location tracking service or track view item. This is required.
- -track-age \<track-age\> - Number of previous full days of tracks to export. Default is 1.
- -time-zone \<time-zone\> - The time zone that defines a "full day". These are defined by [IANA](https://www.iana.org/time-zones) Defaults to "UTC". Other examples: "America/New_York".
- -output-directory \<directory\> - The directory where the CSV file should be stored.
- -log-file \<logFile\> - The log file to use for logging messages. Optional

Example Usage: Last 25 days
```bash
python export_tracks.py -username username -password password -track-age 25 -track-item 0e84dfc7a2a54bb5a7dfc04197b3fa0b -log-file log.txt -output-directory "/Users/exports"
 -time-zone "America/New_York"
```

## What it does

1. First the script uses the provided credentials to authenticate with ArcGIS Online.
2. Then the track item is fetched and exported to a new item using the specified relative date range.
3. Then that item is downloaded to the specified directory and is named using `"tracks_<start-date>_<end-date>.csv`
