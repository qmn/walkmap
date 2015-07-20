#!/usr/bin/env python2.7

import json
import colorsys
import math
import sys

cambridge_streets_fn = "cambridge_streets.json"
cambridge_redline_fn = "cambridge_redline.json"

def download_json():
    import urllib2
    streets = "http://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A25%5D%3B%28way%5B%22highway%22%7E%22%28primary%7Csecondary%7Ctertiary%7Cresidential%29%22%5D%2842%2E3531%2C%2D71%2E1322%2C42%2E4005%2C%2D71%2E0731%29%3B%29%3Bout%20body%3B%3E%3Bout%20skel%20qt%3B%0A"
    redline = "http://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A25%5D%3B%28node%5B%22railway%22%3D%22subway%5Fentrance%22%5D%2842%2E3531%2C%2D71%2E1322%2C42%2E4005%2C%2D71%2E0731%29%3Bway%5B%22railway%22%3D%22subway%22%5D%2842%2E3531%2C%2D71%2E1322%2C42%2E4005%2C%2D71%2E0731%29%3B%29%3Bout%20body%3B%3E%3Bout%20skel%20qt%3B%0A"
    with open(cambridge_streets_fn, "w") as f:
        f.write(urllib2.urlopen(streets).read())
    with open(cambridge_redline_fn, "w") as f:
        f.write(urllib2.urlopen(redline).read())

if len(sys.argv) > 1:
    cmd = sys.argv[1]
    if cmd == "get":
        download_json()
    else:
        print "Do \"%s get\" to get json files"
        print "Otherwise, leave no argument to create map"
    quit()

# Latitude and longitude of the map bounds
bound_coords = {"north": 42.4005, "east": -71.0731, "south": 42.3531, "west": -71.1322}
lon_range = bound_coords["east"] - bound_coords["west"]
lat_range = bound_coords["north"] - bound_coords["south"]

# Size of the map bounds
x_dist = 4.8581 # km
y_dist = 5.2764 # km

# Largest pixel position (x, y) on the map
pixel_scale = 100

max_x = x_dist * pixel_scale
max_y = y_dist * pixel_scale


print "Loading JSON...",
d = json.load(open(cambridge_streets_fn))
print "done"

# Human walking speed (km/h)
walk_speed = 3.6

# Elements
e = d["elements"]

# Streets
s = [x for x in e if "tags" in x and "highway" in x["tags"]]

# Nodes
n = [x for x in e if x["type"] == "node"]

def is_subway_entrance(x):
    return "tags" in x and "railway" in x["tags"] and x["tags"]["railway"] == "subway_entrance"

def nearby_node(x, r):
    for nn in n:
        if distance(x, nn) < r:
            return nn
    return None

# Load red line elements
rl = json.load(open(cambridge_redline_fn))
rle = rl["elements"]
rls = [x for x in rle if is_subway_entrance(x)]

print "Generated streets, nodes"

# mass_ave = [x for x in s if "name" in x["tags"] and x["tags"]["name"] == "Massachusetts Avenue"]
# print mass_ave

# Converts latitude/longitude pair to x, y
def scale(coord):
    x = (coord["lon"] - bound_coords["west"]) / lon_range * max_x
    y = max_y - ((coord["lat"] - bound_coords["south"]) / lat_range * max_y)
    return (x, y)

def draw_street(street, stroke="black"):
    points = conv_street(street)
    pts = " ".join(["%2.5f,%2.5f" % point for point in points])
    return """\t<polyline fill="none" stroke="{}" stroke-width="3" points="{}"/>""".format(stroke, pts)

def draw_edge(na, nb):
    x1, y1 = scale(na)
    x2, y2 = scale(nb)
    t = max(na["dist"], nb["dist"])
    # print t, "min"
    col = heat_hsv(t)
    
    return """\t<line x1="%f" y1="%f" x2="%f" y2="%f" stroke-width="3" stroke="%s"/>""" % (x1, y1, x2, y2, col)

def conv_street(street):
    points = []
    for node in street["nodes"]:
        for nn in n:
            if nn["id"] == node:
                points.append(scale(nn))

    return points

def street_name_is(s, n):
    return "name" in s["tags"] and s["tags"]["name"] == n

def heat(dist):
    if dist < 0:
        return "black"
    elif dist < 5:
        return "blue"
    elif dist < 10:
        return "lightblue"
    elif dist < 15:
        return "green"
    elif dist < 20:
        return "yellow"
    elif dist < 25:
        return "orange"
    elif dist < 30:
        return "red"
    else:
        return "gray"

def heat_hsv(dist):
    min_hue = 2./3.
    max_hue = 0.
    max_dist = 60.
    if dist > max_dist:
        dist = max_dist

    fract = float(dist) / max_dist
    hue = min_hue - (min_hue * fract)
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    r = math.floor(255 * r)
    g = math.floor(255 * g)
    b = math.floor(255 * b)

    return "#%02x%02x%02x" % (r, g, b)

def get_node(node_id):
    for node in n:
        if node["id"] == node_id:
            return node
    return None

stata_node = 61317291
sn = get_node(stata_node)

red_line = {
"davis"      :   61181950,
"central"    :   61317423,
"harvard"    :   61329621,
"porter"     : 1077645749,
"kendall_mit": 1678319187
}

red_line_dist = {
    "davis": {"porter": 2},
    "central": {"harvard": 3, "kendall_mit": 2},
    "harvard": {"central": 3, "porter": 3},
    "porter": {"harvard": 3, "davis": 2},
    "kendall_mit": {"central": 3}
}

def on_red_line(na, nb):
    stations = red_line.values()
    return na["id"] in stations and nb["id"] in stations and na != nb

def get_red_line(node_id):
    for station in red_line:
        if red_line[station] == node_id:
            return station
    return None

def red_line_distance(na, nb):
    nai, nbi = get_red_line(na["id"]), get_red_line(nb["id"])
    return red_line_dist[nai][nbi]

def neighbors(node):
    if "d_neighbors" in node:
        return node["d_neighbors"]

    neighbors = []

    # For each way, look in its nodes for neighbors
    for ss in s:
        ssn = ss["nodes"]
        nid = node["id"]
        if nid in ssn:
            i = ssn.index(nid)
            if i > 0:
                neighbors.append(ssn[i - 1])
            if i < len(ssn) - 1:
                neighbors.append(ssn[i + 1])

    # messily implement red line
    if node["id"] == red_line["kendall_mit"]:
        neighbors.append(red_line["central"])
    elif node["id"] == red_line["central"]:
        neighbors.append(red_line["kendall_mit"])
        neighbors.append(red_line["harvard"])
    elif node["id"] == red_line["harvard"]:
        neighbors.append(red_line["central"])
        neighbors.append(red_line["porter"])
    elif node["id"] == red_line["porter"]:
        neighbors.append(red_line["harvard"])
        neighbors.append(red_line["davis"])
    elif node["id"] == red_line["davis"]:
        neighbors.append(red_line["porter"])

    node["d_neighbors"] = neighbors
    return neighbors

# Return the distance from node a to node b,
# assuming a straight-line distance, in km
def linear_distance(na, nb):
    dx = abs(na["lon"] - nb["lon"]) / lon_range * x_dist
    dy = abs(na["lat"] - nb["lat"]) / lat_range * y_dist
    return pow(dx * dx + dy * dy, 0.5)

def distance(na, nb):
    if on_red_line(na, nb):
        return red_line_distance(na, nb)
    # else use the time
    return dist_to_time(linear_distance(na, nb))

def dist_to_time(dist):
    return dist / walk_speed * 60 # distance * hr/km * (60 min/1 hr)

def write_svg():
    dijkstra()
    with open("walkmap.svg", "w") as f:
        f.write("""<?xml version="1.0" standalone="no"?>
<svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg">""" + "\n")

        # Color mass ave red
        for ss in s:
            if street_name_is(ss, "Massachusetts Avenue"):
                f.write(draw_street(ss, "red"))
            else:
                f.write(draw_street(ss))

        for edge in generate_edges():
            na, nb = edge
            if on_red_line(na, nb):
                continue
            f.write(draw_edge(na, nb) + "\n")

        # Write the key
        f.write("""<text x="10" y="600" font-family="Helvetica">key (min):</text>\n""")
        for dist in xrange(0, 60, 5):
            nx = 100 + 5*dist
            f.write("""<text x="%d" y="600" font-family="Helvetica" fill="%s">%d</text>\n""" % (nx, heat_hsv(dist), dist))

        # Copyright notice
        f.write("""<text x="10" y="620" font-family="Helvetica">Map data &#169; OpenStreetMap contributors</text>\n""")

        f.write("</svg>")

def intersection(a, b):
    # Get nodes of ways with names a and b
    a_nodes = [x["nodes"] for x in s if street_name_is(x, a)]
    b_nodes = [x["nodes"] for x in s if street_name_is(x, b)]

    # Flatten
    a_nodes = reduce(lambda x, y: x + y, a_nodes)
    b_nodes = reduce(lambda x, y: x + y, b_nodes)

    intersection = [x for x in a_nodes if x in b_nodes]

    print a, "and", b, "cross at nodes", intersection
    # Main/Vassar: 61317291

def generate_edges():
    print "Generating edges...",
    edges = []
    visited = []
    queued = [sn]
    while len(queued) > 0:
        node = queued.pop(0)
        if node in visited:
            continue
        visited.append(node)

        node_neighbors = neighbors(node)
        for neighbor in node_neighbors:
            nn = get_node(neighbor)
            edges.append((node, nn))
            if nn not in visited:
                queued.append(nn)

        if len(visited) % 100 == 0:
            print "(%d -> %d)" % (len(queued), len(visited))


    print "done"
    return edges

# print "neighbors are:",  neighbors(stata_node)
# for neighbor in neighbors(stata_node):
#    print "distance to", neighbor, "is", dist_to_time(distance(get_node(stata_node), get_node(neighbor))), "min"

# write_svg()
# graph_edges = generate_edges()

# Dijkstra's algorithm
def dijkstra():
    print "Running Dijkstra's..."
    queued = []
    for nn in n:
        queued.append(nn)
        if nn == sn:
            nn["dist"] = 0
        else:
            nn["dist"] = -1

    iters = 0
    while len(queued) > 0:
        iters += 1
        # Get the minimal distance node
        found = False
        for q in xrange(len(queued)):
            qq = queued[q]
            if qq["dist"] != -1:
                min_n = qq
                min_dist = qq["dist"]
                found = True
                break

        if not found:
            break

        for q in xrange(len(queued)):
            qq = queued[q]
            if qq["dist"] == -1:
                continue
            elif qq["dist"] < min_dist:
                min_n = qq
                min_dist = qq["dist"]

        # Delete it from queued
        queued.remove(min_n)
        for nn in neighbors(min_n):
            neighbor = get_node(nn)
            new_dist = min_dist + distance(min_n, neighbor)
            if neighbor["dist"] == -1 or new_dist < neighbor["dist"]:
                neighbor["dist"] = new_dist

        if iters % 100 == 0:
            print "(%d / %d)" % (iters, len(n))


    print "done"

# radius = 0.030
# for station in rls:
#     if "name" in station["tags"]:
#        print station["tags"]["name"], "nearby node:", nearby_node(station, radius)


write_svg()
