#!/usr/bin/env python

import sys
import json
from osgeo import ogr, osr
from shapely.geometry import Point, LineString

#to_replace1 = '<gml:LineString srsName="EPSG:54004" xmlns:gml="http://www.opengis.net/gml"><gml:coordinates decimal="." cs="," ts=" ">'
#to_replace2 = "</gml:coordinates></gml:LineString>"

lines_input = open('lines_out.txt', 'r')
points_input = open('points_out.txt', 'r')

def transform(geom):
	source = osr.SpatialReference()
	source.ImportFromEPSG(54004)

	target = osr.SpatialReference()
	target.ImportFromEPSG(4326)

	transform = osr.CoordinateTransformation(source, target)

	geom.Transform(transform)
	return geom
	
def readInput(data):
	geometries = []
	for line in data.readlines():
		# check if we have to remove two or three chars from line
		index_ = 2 if line[1:2]==':' else 3
		# remove first 'index'-chars
		gml_ = line[index_:]
		# convert to ogr-geometry
		test = transform(ogr.CreateGeometryFromGML(gml_))
		ogr_geometry = test#ogr.CreateGeometryFromGML(gml_)
		# convert to shapely-geometry
		if ogr_geometry.GetGeometryType() == 1:
			shapely_geometry = Point(ogr_geometry.GetX(),ogr_geometry.GetY())
		elif ogr_geometry.GetGeometryType() == 2:
			shapely_geometry = LineString(ogr_geometry.GetPoints())
		geometries.append(shapely_geometry)
	return geometries

def getOnePointFromIntersection(intersection):
	# ToDo:: replace this method with a more convenient
	return intersection.representative_point()

lines = readInput(lines_input)
points = readInput(points_input)

buffer_distance = 5000
intersection_points = []
count0 = 0
for line in lines:
	count = 0
	for point in points:
		#print 'Point: ', count, 'Line:', count0
		buffered_point = point.buffer(buffer_distance)
		if line.intersects(buffered_point):
			intersection = line.intersection(buffered_point)
			intersection_points.append(getOnePointFromIntersection(intersection))
		count += 1
	count0 += 1

def saveToGeoJSON(filename, geometries):
	featcoll_dummy = {
	    "type": "FeatureCollection",
	    "features": []
	}

	features = []
	for geom in geometries:
		feauture_dummy = {
		  "type": "Feature",
		  "geometry": {
		    "type": "",
		    "coordinates": []
		  },
		  "properties": {}
		}
		# cleaning for GeoJSON...by replacing '(...)' with '[...]'
		geojson_points = []
		for coord in list(geom.coords):
			geojson_points.append([coord[0],coord[1]])
		# add geometry to geoJSON-geometry-dummy
		geojson = feauture_dummy.copy()
		geojson['geometry']['type'] = geom.geometryType()
		if geom.geometryType() == 'Point':
			geojson['geometry']['coordinates'] = geojson_points[0]
		elif geom.geometryType() == 'LineString':
			geojson['geometry']['coordinates'] = geojson_points
		features.append(geojson)
	# add features to feature-collection-dummy
	featurecoll_geojson = featcoll_dummy.copy()
	featurecoll_geojson['features'] = features
	# save geoJSON to file
	with open(filename, "w") as file:
		file.write(json.dumps(featurecoll_geojson, indent=4))
	file.close()

saveToGeoJSON('points.json',points)
saveToGeoJSON('lines.json',lines)
saveToGeoJSON('intersection_points.json',intersection_points)
	