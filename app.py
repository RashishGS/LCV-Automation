from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import math
import folium
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lcv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class LCV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<LCV {self.id}>'


# Initialize the database and create tables
with app.app_context():
    db.create_all()

# Constants
AVERAGE_SPEED_KMPH = 30
FILLING_RATE_KG_PER_MIN = 5  # Filling rate in kg per minute

# Example data
filling_stations = [
    {'name': 'CGS', 'coords': (17.59705278, 78.54384722), 'filling_points': 5},
    {'name': 'TSRTC MEDCHAL', 'coords': (17.63378611, 78.48694167), 'filling_points': 3},
    {'name': 'ONUS HAFIZPET', 'coords': (17.48957778, 78.35370556), 'filling_points': 2},
    {'name': 'HI-TECH HAFIZPET', 'coords': (17.48598333, 78.35795), 'filling_points': 2},
]

daughter_stations = [
    {'name': 'M/s. Bhagyanagar Gas Limited - 3/Hakimpet', 'coords': (17.54600556, 78.53618056), 'average_sales': 3349.26},
    {'name': 'M/s. Bhagyanagar Gas Limited - 4/Cantonment', 'coords': (17.44771111, 78.49821389), 'average_sales': 0.0},
    {'name': 'M/s. Bhagyanagar Gas Limited - 5/COCO/Saroornagar', 'coords': (17.35567222, 78.54513889), 'average_sales': 6416.56},
    {'name': 'M/s. Lalitha Devi Petrol Pump/R.P Road', 'coords': (17.43283333, 78.4929), 'average_sales': 1364.8},
    {'name': 'M/s. Sapthagiri Filling Station/Meerpet', 'coords': (17.31770556, 78.51848333), 'average_sales': 1563.17},
    {'name': 'M/s. Chakra Filling Station/Nampally', 'coords': (17.38844722, 78.4754), 'average_sales': 1787.03},
    {'name': 'M/s. KVS Service Station/Bowenpally', 'coords': (17.47365, 78.47380278), 'average_sales': 1738.18},
    {'name': 'M/s. Auto Prime/Chadarghat', 'coords': (17.37726111, 78.48684167), 'average_sales': 1335.65},
    {'name': 'M/s. Sri Radha Raman Service Station/Narayanaguda', 'coords': (17.39345, 78.48931389), 'average_sales': 1345.44},
    {'name': 'M/s. Ramesh Fuel Point/Dhoolpet', 'coords': (17.370125, 78.46109444), 'average_sales': 1052.65},
    {'name': 'M/s. Habeeb Service Station/Langer House', 'coords': (17.37808333, 78.42043333), 'average_sales': 1006.39},
    {'name': 'M/s. Hy-tech Fuel Station/Kishanbagh', 'coords': (17.35903889, 78.44270833), 'average_sales': 1546.91},
    {'name': 'M/s. Rajashree Service Station/Bahadurpura', 'coords': (17.34860278, 78.45203889), 'average_sales': 746.5},
    {'name': 'M/s. Pendhota Brothers Filling Station/Katedan', 'coords': (17.30740833, 78.431625), 'average_sales': 937.97},
    {'name': 'M/s. Sri Balaji Kailash Filling station/Hasthinapuram', 'coords': (17.32982778, 78.55284167), 'average_sales': 624.21},

]

# Haversine formula to calculate distance between two points on the Earth
def haversine(coord1, coord2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

# OSRM route calculation
def get_osrm_route(starting_point, loading_station, destination):
    try:
        osrm_url = "http://router.project-osrm.org/route/v1/driving/"
        coordinates = f"{starting_point};{loading_station};{destination}"
        url = f"{osrm_url}{coordinates}?overview=full&geometries=geojson&steps=true"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        app.logger.error(f"Error fetching route from OSRM: {e}")
        return None

# Create a folium map with the route
def create_map(route_data, starting_point, loading_station, destination):
    if route_data is None:
        return None
    starting_coords = list(map(float, starting_point.split(',')))
    m = folium.Map(location=starting_coords[::-1], zoom_start=13)
    folium.Marker(starting_coords[::-1], popup="Starting Point", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(list(map(float, loading_station.split(',')))[::-1], popup="Loading Station", icon=folium.Icon(color='blue')).add_to(m)
    folium.Marker(list(map(float, destination.split(',')))[::-1], popup="Customer Station", icon=folium.Icon(color='red')).add_to(m)
    coordinates = route_data['routes'][0]['geometry']['coordinates']
    folium.PolyLine(locations=[coord[::-1] for coord in coordinates], color="blue", weight=5).add_to(m)
    return m

# Function to calculate filling time based on LCV capacity
def calculate_filling_time(lcv_capacity):
    return lcv_capacity / FILLING_RATE_KG_PER_MIN

# Function to allocate LCVs to CGSs and DBSs
def allocate_lcvs(lcvs, filling_stations, daughter_stations):
    used_lcvs = set()
    used_filling_stations = {station['name']: 0 for station in filling_stations}
    allocation_results = []

    # Filter out daughter stations with no indent request
    valid_daughter_stations = [ds for ds in daughter_stations if ds.get('indent_requirement')]

    sorted_daughter_stations = sorted(valid_daughter_stations, key=lambda x: x['average_sales'], reverse=True)

    for daughter_station in sorted_daughter_stations:
        suitable_lcv = None
        best_filling_station = None
        best_total_time = float('inf')

        for lcv in lcvs:
            if lcv['id'] not in used_lcvs and lcv['capacity'] >= daughter_station['indent_requirement']:
                for filling_station in filling_stations:
                    distance_to_filling = haversine(lcv['coords'], filling_station['coords'])
                    distance_to_dbs = haversine(filling_station['coords'], daughter_station['coords'])
                    travel_time_to_filling = distance_to_filling / AVERAGE_SPEED_KMPH * 60
                    travel_time_to_dbs = distance_to_dbs / AVERAGE_SPEED_KMPH * 60

                    filling_time = calculate_filling_time(lcv['capacity'])
                    current_station_waiting_time = filling_time * used_filling_stations[filling_station['name']]

                    if travel_time_to_filling < current_station_waiting_time:
                        total_time = current_station_waiting_time + travel_time_to_dbs
                    else:
                        total_time = travel_time_to_filling + filling_time + travel_time_to_dbs

                    if total_time < best_total_time:
                        suitable_lcv = lcv
                        best_filling_station = filling_station
                        best_total_time = total_time

        if suitable_lcv and best_filling_station:
            used_lcvs.add(suitable_lcv['id'])
            used_filling_stations[best_filling_station['name']] += 1

            allocation_results.append({
                'lcv_id': suitable_lcv['id'],
                'filling_station': best_filling_station['name'],
                'daughter_station': daughter_station['name'],
                'route_map': f"route_map_{suitable_lcv['id']}_{daughter_station['name'].replace('/', '_')}.html"
            })
            route_data = get_osrm_route(
                f"{suitable_lcv['coords'][1]},{suitable_lcv['coords'][0]}",
                f"{best_filling_station['coords'][1]},{best_filling_station['coords'][0]}",
                f"{daughter_station['coords'][1]},{daughter_station['coords'][0]}"
            )
            route_map = create_map(
                route_data,
                f"{suitable_lcv['coords'][1]},{suitable_lcv['coords'][0]}",
                f"{best_filling_station['coords'][1]},{best_filling_station['coords'][0]}",
                f"{daughter_station['coords'][1]},{daughter_station['coords'][0]}"
            )
            if route_map:
                filename = f"static/route_map_{suitable_lcv['id']}_{daughter_station['name'].replace('/', '_')}.html"
                route_map.save(filename)
        else:
            allocation_results.append(f"No suitable LCV found for {daughter_station['name']}.")

    return allocation_results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        for i, station in enumerate(daughter_stations):
            indent_key = f'indent_{i + 1}'
            indent_value = request.form.get(indent_key, type=float)
            station['indent_requirement'] = indent_value

        lcv_data = []
        lcv_count = int(request.form.get('lcv_count'))
        for i in range(lcv_count):
            lcv_id = int(request.form.get(f'lcv_id_{i+1}'))
            lcv_coords = request.form.get(f'lcv_coords_{i+1}')
            lat, lon = map(float, lcv_coords.split(','))
            lcv = LCV.query.get(lcv_id)
            print(f"Retrieved LCV ID: {lcv_id}, Coordinates: {lat}, {lon}")  # Debug output
            if lcv:
                lcv_data.append({'id': lcv.id, 'capacity': lcv.capacity, 'coords': (lat, lon)})
            else:
                print(f"LCV with ID {lcv_id} not found")  # Debug output
                return f'LCV with ID {lcv_id} not found', 400

        allocations = allocate_lcvs(lcv_data, filling_stations, daughter_stations)
        return render_template('results.html', results=allocations)

    return render_template('index.html', daughter_stations=daughter_stations)


@app.route('/indents', methods=['GET', 'POST'])
def indents():
    if request.method == 'POST':
        indents = []
        for i, station in enumerate(daughter_stations):
            indent = request.form.get(f'indent_{i + 1}', '')
            station['indent_requirement'] = int(indent) if indent else 0
            indents.append(indent)
        return redirect(url_for('lcvs'))
    return render_template('indent.html', daughter_stations=daughter_stations)

@app.route('/lcvs', methods=['GET', 'POST'])
def lcvs():
    if request.method == 'POST':
        num_lcvs = int(request.form['num_lcvs'])
        lcvs = []
        for i in range(num_lcvs):
            lcv_id = request.form[f'lcv_id_{i}']
            lcv_coords = list(map(float, request.form[f'lcv_coords_{i}'].split(',')))
            lcv_capacity = int(request.form[f'lcv_capacity_{i}'])
            lcvs.append({'id': lcv_id, 'coords': lcv_coords, 'capacity': lcv_capacity})

        results = allocate_lcvs(lcvs, filling_stations, daughter_stations)
        return render_template('results.html', results=results)

    return render_template('lcvs.html')

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
