import folium
import logging
import os
from statistics import mean
from folium.plugins import MarkerCluster


#doc clustering https://nbviewer.jupyter.org/github/python-visualization/folium/blob/master/examples/MarkerCluster.ipynb
#doc popup https://nbviewer.jupyter.org/github/python-visualization/folium/blob/master/examples/Popups.ipynb
#list of icon https://fontawesome.com/icons?d=gallery&c=computers,status&m=free
#customize cluster https://github.com/Leaflet/Leaflet.markercluster#customising-the-clustered-markers

#TO DO : create object cov_point instead of using dict
# implement fit bounds + function to dtermine max SW NE
# add legend for color marker + number covered/ not covered
# test circle markers
##################################
# colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'];

current_folder = os.path.dirname(__file__)

if __name__ == "__main__":
    output_map = os.path.join(current_folder,"osm_result_test.html")
else:
    output_map = os.path.join(current_folder,"map_result.html")

global_center_lat = 0
global_center_lng = 0
global_lqi_scale = ["Not Covered","Limit","Poor","Average","Good","Very good","Excellent"]
color_scale = ["black","darkred","red","orange", "darkgreen", "lightgreen", "green"]

#red Orange Yellow light green, green dark green

def coverage_loc_marker(lat,lng,covered,margins,lqi):
    if(covered == True):
         #put the link quality indic
        popup_text = f"<i>{global_lqi_scale[lqi]}</i><br><i>Margin1 : {margins[0]}</i><br><i>Margin2 : {margins[1]}</i><br><i>Margin3 : {margins[2]}</i>"
        popup = folium.Popup(popup_text,parse_html=False,max_width='100')
        icon="ok-sign"
    else:
        popup_text = '<i>Not Covered</i>'
        popup='<i>Not Covered</i>'
        icon="remove-sign"

    tooltip = f"{global_lqi_scale[lqi]}"
    #color=color_scale[lqi]
    marker = folium.Marker(
        [lat, lng],
        popup=popup,
        tooltip=tooltip,
        icon=folium.Icon(
            color=color_scale[lqi],
            icon=icon,
        #icon_color='#fcba03',
        # icon='fa-signal',
        # prefix='fa'
        )
    )
    return marker

def get_center_map(list_result): #to be optimised by extracting dict_result and create list in obj class
    lat = []
    lng = []
    #print(list_result)
    for result in list_result:
        #print(result["pos"][0])
        lat.append(float(result["pos"][0]))
        lng.append(float(result["pos"][1]))
        # print(i)
        # print(lat)
        # print(lng)
    return (mean(lat),mean(lng))

def create_map(list_result,clustering=False):
    # icon_create_function = """\
    # function(cluster) {
    #     return L.divIcon({
    #     html: '<b>' + cluster.getChildCount() + '</b>',
    #     className: 'marker-cluster marker-cluster-small',
    #     iconSize: new L.Point(20, 20)
    #     });
    # }"""
    center = get_center_map(list_result)
    osm_map = folium.Map(location=center,zoom_start=3)

    if clustering:
        cov_cluster = MarkerCluster(
            name = 'Covered',
            #icon_create_function=icon_create_function
        )
        not_cov_cluster = MarkerCluster(
            name = 'Not Covered',
            #icon_create_function=icon_create_function
        )

        #covered_group = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Covered')
        group_limit = folium.plugins.FeatureGroupSubGroup(cov_cluster, 'Limit')
        group_poor = folium.plugins.FeatureGroupSubGroup(cov_cluster, 'Poor')
        group_average = folium.plugins.FeatureGroupSubGroup(cov_cluster, 'Average')
        group_good = folium.plugins.FeatureGroupSubGroup(cov_cluster, 'Good')
        group_vgood = folium.plugins.FeatureGroupSubGroup(cov_cluster, 'Very Good')
        group_excellent = folium.plugins.FeatureGroupSubGroup(cov_cluster, 'Excellent')
        
        osm_map.add_child(cov_cluster)
        osm_map.add_child(group_excellent)
        osm_map.add_child(group_vgood)
        osm_map.add_child(group_good)
        osm_map.add_child(group_average)
        osm_map.add_child(group_poor)
        osm_map.add_child(group_limit)
        
        osm_map.add_child(not_cov_cluster)

        logging.info("Start Map creation")
        for result in list_result:
            lat = float(result["pos"][0])
            lng = float(result["pos"][1])
            lqi = int(result["lqi"])
            marker = coverage_loc_marker(lat,lng,result["covered"],result["margins"],lqi)
            if lqi == 0:
                not_cov_cluster.add_child(marker)
            elif lqi == 1:
                group_limit.add_child(marker)
            elif lqi == 2:
                group_poor.add_child(marker)
            elif lqi == 3:
                group_average.add_child(marker)
            elif lqi == 4:
                group_good.add_child(marker)
            elif lqi == 5:
                group_vgood.add_child(marker)
            elif lqi == 6:
                group_excellent.add_child(marker)

    else:
        group_covered = folium.FeatureGroup('Covered')
        #covered_group = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Covered')
        group_limit = folium.plugins.FeatureGroupSubGroup(group_covered, 'Limit')
        group_poor = folium.plugins.FeatureGroupSubGroup(group_covered, 'Poor')
        group_average = folium.plugins.FeatureGroupSubGroup(group_covered, 'Average')
        group_good = folium.plugins.FeatureGroupSubGroup(group_covered, 'Good')
        group_vgood = folium.plugins.FeatureGroupSubGroup(group_covered, 'Very good')
        group_excellent = folium.plugins.FeatureGroupSubGroup(group_covered, 'Excellent')
        group_not_covered = folium.FeatureGroup('Not Covered')

        osm_map.add_child(group_covered)
        osm_map.add_child(group_excellent)
        osm_map.add_child(group_vgood)
        osm_map.add_child(group_good)
        osm_map.add_child(group_average)
        osm_map.add_child(group_poor)
        osm_map.add_child(group_limit)
        
        osm_map.add_child(group_not_covered)

        logging.info("Start Map creation")
        for result in list_result:
            lat = float(result["pos"][0])
            lng = float(result["pos"][1])
            lqi = int(result["lqi"])
            marker = coverage_loc_marker(lat,lng,result["covered"],result["margins"],lqi)
            if lqi == 0:
                group_not_covered.add_child(marker)
            elif lqi == 1:
                group_limit.add_child(marker)
            elif lqi == 2:
                group_poor.add_child(marker)
            elif lqi == 3:
                group_average.add_child(marker)
            elif lqi == 4:
                group_good.add_child(marker)
            elif lqi == 5:
                group_vgood.add_child(marker)
            elif lqi == 6:
                group_excellent.add_child(marker)

    folium.LayerControl().add_to(osm_map)
    osm_map.save(output_map)
    logging.info("Map created")

if __name__ == "__main__":
    list_result = []
    list_result.append({'pos': ['-34.921403', '-54.945659'], 'covered': True, 'margins': [18, 0, 0],"lqi":3})
    list_result.append({'pos': ['-35.921403', '-55.945659'], 'covered': False, 'margins': [0, 0, 0],"lqi":0})
    list_result.append({'pos': ['-16.921403', '-54.945659'], 'covered': True, 'margins': [18, 0, 0],"lqi":1})
    list_result.append({'pos': ['-47.921403', '-55.945659'], 'covered': True, 'margins': [0, 0, 0],"lqi":2})
    list_result.append({'pos': ['-28.921403', '-54.945659'], 'covered': True, 'margins': [18, 0, 0],"lqi":4})
    list_result.append({'pos': ['-39.921403', '-55.945659'], 'covered': True, 'margins': [0, 0, 0],"lqi":5})
    list_result.append({'pos': ['-34.921403', '-58.945659'], 'covered': True, 'margins': [18, 0, 0],"lqi":3})
    list_result.append({'pos': ['-35.921403', '-70.945659'], 'covered': False, 'margins': [0, 0, 0],"lqi":0})
    list_result.append({'pos': ['-16.921403', '-25.945659'], 'covered': True, 'margins': [18, 0, 0],"lqi":1})
    list_result.append({'pos': ['-47.921403', '-34.945659'], 'covered': True, 'margins': [0, 0, 0],"lqi":6})
    list_result.append({'pos': ['-28.921403', '-80.945659'], 'covered': True, 'margins': [18, 0, 0],"lqi":6})
    list_result.append({'pos': ['-39.921403', '-62.945659'], 'covered': True, 'margins': [25, 0, 0],"lqi":6})

    create_map(list_result)
