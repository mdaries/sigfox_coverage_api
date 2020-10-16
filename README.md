## Table of contents
* [General info](#general-info)
* [Screenshots](#screenshots)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#features)
* [Status](#status)
* [Contact](#contact)

## General info
* Check Sigfox coverage from a list of lat,lng
* Output a csv results with margins and link quality indicator for each lcoation
* Generate a html result map, displaying coverage dots

## Screenshots
![Map result](./result_map.jpg)

## Technologies
Project is created with:
* Python 3.7
* Using sigfox API v2 : https://support.sigfox.com/apidocs#tag/Coverages

## Setup
Install packages
* pip install aiohttp
* pip install folium
* pip install requests
* pip install tqdm

Sigfox API credentials
*To create your Sigfox API credential check the following support page => https://support.sigfox.com/docs/api-credential-creation
* Fill in your Sigfox API credentials in the example file "credentials_empty" and rename it "credentials"
Ex: 
"myApi": { "login":"123456", "password": "abcdef", "group": "56789"}

Location input file
*Create the csv input file listing the location to be tested
Format is : latitude,longitude     without headers
Ex: 
-34.921403,-54.945659
-33.382523,-70.584099
45.454582,-122.585197


## Usage Examples
Examples of usage:

Execute script with credentials "myApi"
python3.7 check_coverage.py -c myApi

Build map with clustering, gather locations in cluster to optimize display
python3.7 check_coverage.py -c myApi -cl

Check coverage for a Class U1 device
python3.7 check_coverage.py -c myApi -d 1

Check coverage for a device located inside a building (adding 20dB margin) => check https://support.sigfox.com/docs/global-coverage-api for more details
python3.7 check_coverage.py -c myApi -e indoor


## Features
List of features ready and TODOs for future development
* Coverage result in csv file
* Coverage result displayed on a map
* Filter by LQI on the map
* Asynchronous API call optimized for large location batch

To-do list:
* improve http error mgmt
* improve read csv : pull error line + CONTINUE
* document osm api

## Status
Project is: _in progress_

