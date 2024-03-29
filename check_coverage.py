import os
import csv
import json
import logging
import argparse
import time

import requests
from requests.auth import HTTPBasicAuth


import osm_api

# TO DO
#implement legacy link quality indicator to render on the map
#test location as object
#improve read csv : pull error line + CONTINUE
#add permissionError mgmt in write result when file is open
#create result in a folder/ add location file as an input
#function to automatically set number of retry + delay between retry depending on #of location

DEBUG = True

#param to be added
request_type = "coverage_async"

#default params
default_credname = "root"
default_env_type = "outdoor"
default_dev_class = 0

#default input and output filepath
current_folder = os.path.dirname(__file__)
default_input_csv = os.path.join(current_folder,"location.csv")
cred_file = os.path.join(current_folder,"credentials")
default_output_csv = os.path.join(current_folder,"coverage_result.csv")

#default get response param
max_retry = 60
delay_retry = 30

#Logger Settings
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')


base_url={
    "coverage":"https://backend.sigfox.com/api/v2/coverages/global/predictions",
    "coverage_async":"https://api.sigfox.com/v2/coverages/global/predictions/bulk/"
}

#lqi algo constants
no_upper_bound = 200
global_ranking_list = [[10,50,no_upper_bound,3,6],[8,40,50,3,5],[10,50,no_upper_bound,2,5],[40,50,no_upper_bound,1,5],[6,30,40,3,4],[8,30,50,2,4],[25,25,40,1,4],[4,12,30,2,3],[8,8,25,1,3],[4,8,12,2,2],[0,0,no_upper_bound,0,1]]
global_lqi_scale = ["Not Covered","Limit","Poor","Average","Good","Very good","Excellent"]

# Product class attenuation U0=0dB, U1=6dB, U2=11, U3=16
dev_atten = [0,6,11,16]
env_atten = {"outdoor":0,"incar":10,"indoor":20,"underground":30}

#d Check if a position (latitude,longitude) is correct
def is_coord(lat,lng,linecount):
    try:
        lat = float(lat)
        lng = float(lng)
        if lat <-90 or lat>90:
            logging.error(f"Line {linecount+1}: Incorrect latitude {lat}")
            raise ValueError
        if lng <-180 or lng>180:
            logging.error(f"Line {linecount+1}: Incorrect longitude {lng}")
            raise ValueError
        else:
            return True
    except ValueError:
        return False

#Read from file and check credentials with test_cred
def read_cred(filename,cred_name,request_type):
    try:
        if os.path.exists(filename) and os.path.isfile(filename):
            with open(filename,"r") as cred_file:
                cred_json = json.loads(cred_file.read())
                cred = cred_json[cred_name]
                valid = test_cred(cred_name,request_type,cred)
                if valid:
                    logging.info("Credentials OK")
                    return cred
        else:
            logging.critical(f"File not found {filename}")
            raise SystemExit
    except KeyError as e:
        logging.critical(f"Credentials {cred_name} not found in credential file")
        raise SystemExit
    except ValueError as e:
        logging.critical(f"Invalid JSON in credentials : {e}")
        raise SystemExit
    except Exception as e:
        logging.critical("Unexpected error while opening credentials")
        logging.critical(f"System returned {e.__class__.__name__}, {e}")
        raise SystemExit


#Test credentials with an HTTP request
#update the test with post
def test_cred(cred_name,request_type,cred):
    if cred["login"] and cred["password"]:
        if request_type == "coverage" or request_type == "coverage_async":
            #Sigfox HQ lat,lng for test
            parameters = {"lat": 43.543925, "lng": 1.511323, "radius": 200}
            try:
                response = requests.get(
                base_url["coverage"],
                auth=HTTPBasicAuth(cred["login"],cred["password"]),
                params = parameters
                )
                response.raise_for_status()
                if response.ok:
                    return True
            except requests.HTTPError as e:
                logging.error(f"HTTP error {e}")
                raise SystemExit
            except requests.ConnectionError as e:
                logging.error(f"Connection error {e}")
                raise SystemExit
        else:
            logging.error(f"Wrong request type {request_type}")
            raise SystemExit
    else:
        logging.critical(f"Credential {cred_name} empty ")
        raise SystemExit


# Read location (latitude,longitude) from a csv file
def read_location_from_csv(filename):
    if os.path.exists(filename) and os.path.isfile(filename):
        #try to open file
        try:
            with open(filename,"r") as csv_file:
                logging.info(f"Input csv file {filename} opened")
                dialect = csv.Sniffer().sniff(csv_file.read(),delimiters=';,')
                csv_file.seek(0)
                csv_reader = csv.reader(csv_file, dialect)
                line_count = 0
                errors = 0
                dict_pos = {}
                for row in csv_reader:
                    #try if the index exist
                    try:
                        #check if row is a coord
                        if is_coord(row[0],row[1],line_count):
                            dict_pos[line_count] = [row[0],row[1]]
                        else:
                            errors+=1
                            #logging.debug(f"Line {line_count+1}: incorrect value {row[0]},{row[1]}")
                        line_count += 1
                    except IndexError:
                        logging.error(f"file incorrect at line {line_count+1}")
                        raise SystemExit
                #Stop the program and ask to check errors
                if(errors):
                    logging.error(f"Program exit : {errors} errors found in the file, Please check format")
                    raise SystemExit
                elif line_count==0:
                    logging.error(f"No locations was found")
                    raise SystemExit
                else:
                    logging.info(f"{line_count} locations found")
        except IOError:
            logging.error(f"Unable to open file {filename}")
            raise SystemExit
    else:
        logging.error(f"File not found {filename}")
        raise SystemExit

    return dict_pos

#populate result from csv -- to build a map from a result file, call it in main
def read_result_from_csv(filename):
    if os.path.exists(filename) and os.path.isfile(filename):
        with open(filename,"r") as result_csv:
            logging.info("Input result csv file opened")
            csv_reader = csv.reader(result_csv, delimiter=',')
            line_count = 0
            results = []
            #skip headers
            next(csv_reader, None)
            for row in csv_reader:
                #dict_result = {"pos":[lat,lng],"covered":covered,"margins":margins,"lqi":lqi}
                results.append({"pos":[row[1],row[2]],"covered":bool(row[3]),"margins":[int(row[4]),int(row[5]),int(row[6])],"lqi":int(row[7])})
                line_count+=1
            #print(results)
    else:
        logging.error(f"File not found {filename}")
        raise SystemExit

    return results

#write coverage results to output csv file
def write_result_to_csv(filename,results = []):
    with open(filename,"w") as csv_file:
        logging.info("Result csv file opened")
        csv_writer = csv.writer(csv_file, lineterminator='\r')
        #write the columns
        csv_writer.writerow(["id","lat","lng","covered","margin1","margin2","margin3","lqi","API call status"])
        line_count = 0
        for result in results:
            csv_writer.writerow([
                #result["id"],
                result["pos"][0],
                result["pos"][1],
                result["covered"],
                result["margins"][0],
                result["margins"][1],
                result["margins"][2],
                global_lqi_scale[result["lqi"]],
                result["api_call"]
                ])
            line_count += 1
        logging.info(f"Result file created with {line_count} locations")

# Get lqi value for a given location [margin1,margin2,margin3]
def get_lqi(margins):
    # lqi 1->limit, 2->poor, 3->average, 4->good, 5->very good, 6->Excellent
    #global_ranking_list = [min_tresh,lower_boundary,upper_boundary,redundancy,lqi]

    if sum(margins) == 0:
        return 0

    for i in range(0,11):
        min_threshold = global_ranking_list[i][0]
        lower_boundary = global_ranking_list[i][1]
        upper_boundary = global_ranking_list[i][2]
        redundancy_min = global_ranking_list[i][3]

        valid_margins = [i for i in margins if i>=min_threshold]
        valid_redundancy = len(valid_margins)
        sum_margin = sum(valid_margins)

        if sum_margin>=lower_boundary and sum_margin<upper_boundary and valid_redundancy >= redundancy_min:
            lqi = global_ranking_list[i][4]
            break
    return lqi

def retry_code(code: int) -> bool:

        return 500 <= code <= 599 or code in statuses

def build_body(dict_pos):
    locations = []
    for i in dict_pos:
        locations.append({"lat": dict_pos[i][0], "lng": dict_pos[i][1]})

    body_str = {"locations":locations}
    body_json = json.dumps(body_str)

    return body_json

def create_coverage_bulk(body_json,cred,radius=200):
    max_retry = 3
    retry_wait = 1
    global http_error
    headers = {'Content-type': 'application/json'}
    try:
        response = requests.post(
            base_url[request_type],
            data=body_json,
            auth=HTTPBasicAuth(cred["login"], cred["password"]),
            headers=headers
        )
        response.raise_for_status()
        if response.ok:
            job_id = response.json().get("jobId")
            logging.info(f"Coverage job {job_id} created")
            return job_id
        else:
            return -1
    except requests.HTTPError as e:
        logging.error(f"HTTP error {e}")
        raise SystemExit

def get_job_result(job_id,cred):

    url = base_url[request_type] + str(job_id)

    i = 0
    while i < max_retry :
        i+=1
        logging.info(f"Try {i} ")
        try:
            response = requests.get(
                url=url,
                auth=HTTPBasicAuth(cred["login"], cred["password"])
            )
            response.raise_for_status()
            if response.ok:
                if response.json().get("jobDone"):
                    return response.json()
        except requests.HTTPError as e:
            logging.error(f"HTTP error {e}")
            raise SystemExit
        time.sleep(delay_retry)

def process_response(response):
    results = response.get('results')
    list_results = []
    line_count = 0
    for result in results:
        margins = result.get('margins')
        lat = result.get('lat')
        lng = result.get('lng')
        # apply offset on margins tab
        margins_offset = [m - settings["offset"] if m > settings["offset"] else 0 for m in margins]
        lqi = get_lqi(margins_offset)
        if not lqi:
            covered: bool = False
        else:
            covered = True

        dict_result = {"pos": [lat, lng], "covered": covered, "margins": margins_offset, "lqi": lqi,"api_call": "OK (200)"}
        list_results.append(dict_result)
        line_count += 1

    return list_results


if __name__ == '__main__':

    #Argument parser
    parser = argparse.ArgumentParser(description="Get coverage from location CSV file")
    parser.add_argument("--credname", "-c", required=False, type=str,metavar="cred_name",dest="cred_name",
                        help="Credential to be used for API requests, default name is root")
    parser.add_argument("--clustering", "-cl", required=False,dest="clustering",action="store_true",
                        help="Enable point clustering option on the result map")
    parser.add_argument("--devclass", "-d", required=False,type=int,choices=[0,1,2,3],metavar="dev_class",dest="dev_class",
                        help="Device class to be used for the results (U0, U1, U2 or U3) - U0 by default")
    parser.add_argument("--envtype", "-e", required=False,type=str,choices=["outdoor","incar","indoor","underground"],metavar="env_type",dest="env_type",
                        help="Environment attenuation to be applied incar=10dB, indoor=20dB, underground=30dB - outdoor(0dB) by default")
    parser.add_argument("--input_file", "-i", required=False,type=str,metavar="input_file",dest="input_file",
                        help="CSV input file with location as lat,lng")
    parser.add_argument("--output_file", "-o", required=False,type=str,metavar="output_file",dest="output_file",
                        help="CSV output file with coverage results per location lat,lng")
    parser.add_argument("--verbose", "-v", required=False, dest="verbose", action="store_true",
                        help="increase output verbosity")


    args = parser.parse_args()
    settings = {}

    if args.verbose:
        DEBUG = True
    if args.cred_name:
        settings['credentials'] = read_cred(cred_file,args.cred_name,request_type)
    else:
        settings['credentials'] = read_cred(cred_file,default_credname,request_type)
    if args.clustering:
        settings['clustering'] = True
    else:
        settings['clustering'] = False
    if args.dev_class:
        settings["dev_class"] = args.dev_class
    else:
        settings["dev_class"] = default_dev_class
    if args.env_type:
        settings["env_type"] = args.env_type
    else:
        settings["env_type"] = default_env_type
    if args.input_file:
        settings["input_file"] = os.path.join(current_folder,args.input_file)
    else:
        settings["input_file"] = default_input_csv
    if args.output_file:
        settings["output_file"] = os.path.join(current_folder,args.output_file)
    else:
        settings["output_file"] = default_output_csv

    # offset = device attenuation + environment attenuation
    settings["offset"] = dev_atten[settings["dev_class"]] + env_atten[settings["env_type"]]
    logging.info(f"Product class: U{settings['dev_class']}, Environment: {settings['env_type']} => Attenuation applied = {settings['offset']}dB")

    #read pos from csv
    dict_pos = read_location_from_csv(settings["input_file"])

    #build Json body
    body_json = build_body(dict_pos)

    #HTTP retry statuses
    statuses = {x for x in range(100, 600)}
    statuses.remove(200)
    statuses.remove(429)

    http_error = 0

    job_id = create_coverage_bulk(body_json,settings['credentials'])

    time_start = time.perf_counter()
    response = get_job_result(job_id,settings['credentials'])
    time_end = time.perf_counter()
    logging.info(f"Request processed in  : {time_end-time_start} seconds")


    tab_results=process_response(response)

    #Write results to csv
    write_result_to_csv(settings["output_file"],tab_results)

    #read result from csv
    #responses = read_result_from_csv(input_res_csv)

    # Create map with results
    osm_api.create_map(tab_results,settings['clustering'])