#!/usr/bin/env python

import os
import sys
import json
from osgeo import ogr, osr
from shapely.geometry import Point, LineString

def transform(geom, epsg):
	source = osr.SpatialReference()
	source.ImportFromEPSG(int(epsg))

	target = osr.SpatialReference()
	target.ImportFromEPSG(4326)

	transformation = osr.CoordinateTransformation(source, target)

	geom.Transform(transformation)
	return geom

def readInput(data, transform_ = None):
	geometries = []
	for line in data.readlines():
		# check if we have to remove two or three chars from line
		index_ = 2 if line[1:2]==':' else 3
		# remove first 'index'-chars
		gml_ = line[index_:]
		# convert to ogr-geometry
		if transform_:
			ogr_geometry = transform(ogr.CreateGeometryFromGML(gml_), transform_)
		else:
			ogr_geometry = ogr.CreateGeometryFromGML(gml_)
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

def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		transform_ = argv[1]
	except:
		transform_ = None

	lines_input = open('lines_out.txt', 'r')
	points_input = open('points_out.txt', 'r')

	lines = readInput(lines_input, transform_)
	points = readInput(points_input, transform_)

	buffer_distance = 0.05
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

	saveToGeoJSON('points.json',points)
	saveToGeoJSON('lines.json',lines)
	saveToGeoJSON('intersection_points.json',intersection_points)

	os.system("topojson -o all_features_topo.json points.json lines.json intersection_points.json");

if __name__ == "__main__":
    sys.exit(main())
