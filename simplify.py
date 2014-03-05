#!/usr/bin/env python

import os
import sys
import json
from osgeo import ogr, osr
from shapely.geometry import Point, LineString, box

from pyrtree import RTree, Rect

def findCPointByRTree(points, r_tree, buffer_distance=0):

	intersections = []
   	buffered_points = []
   	for point_ in points:

   		resulting_lines = [r.leaf_obj() for r in r_tree.query_point( (point_.x,point_.y) ) if r.is_leaf()]
   		# print 'Number of resulting lines:', len(resulting_lines)

   		for line in resulting_lines:
	   		# distance = line.project(point_)
	   		distance = line.distance(point_)
	   		# prevent too big buffer distances ('failure' in RTree)
	   		if buffer_distance < distance:
	   			distance = buffer_distance
	   		buffered_point = point_.buffer(distance*1.1)
	   		buffered_points.append(buffered_point)
   			intersects = line.intersects(buffered_point)
   			# print intersects
   			if line.intersects(buffered_point):
   				intersection = line.intersection(buffered_point)
   				intersections.append(intersection)

   	return intersections, buffered_points

def findCPointBySimpleBuffer(lines, points, buffer_distance=0):
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
	return intersection_points

def transform(geom, epsg):
	source = osr.SpatialReference()
	source.ImportFromEPSG(int(epsg))

	target = osr.SpatialReference()
	target.ImportFromEPSG(4326)

	transformation = osr.CoordinateTransformation(source, target)

	geom.Transform(transformation)
	return geom

def readInput(data, transform_ = None):
	r_tree = RTree()
	geometries = []
	real_index_list = []
	for line in data.readlines():
		# check if we have to remove two or three chars from line
		index_ = 2 if line[1:2]==':' else 3
		# remove first 'index'-chars
		gml_ = line[index_:]
		real_index_list.append(line[:index_].replace(':',''))
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
			r_tree.insert(shapely_geometry,Rect(shapely_geometry.bounds[0],shapely_geometry.bounds[1],shapely_geometry.bounds[2],shapely_geometry.bounds[3]))

		geometries.append(shapely_geometry)
	if ogr_geometry.GetGeometryType() == 1:
		return geometries, real_index_list
	elif ogr_geometry.GetGeometryType() == 2:
		return geometries, real_index_list, r_tree

def getOnePointFromIntersection(intersection):
	# ToDo:: replace this method with a more convenient
	return intersection.representative_point()

def saveToGeoJSON(filename, geometries, indizes=None):
	featcoll_dummy = {
	    "type": "FeatureCollection",
	    "features": []
	}

	features = []
	for i in range(len(geometries)):
		id = indizes[i] if indizes else i
		geom = geometries[i]

		feauture_dummy = {
		  "type": "Feature",
		  "geometry": {
		    "type": "",
		    "coordinates": []
		  },
		  "properties": {
		  	'id':None
		  }
		}
		# add geometry to geoJSON-geometry-dummy
		geojson = feauture_dummy.copy()
		geojson['properties']['id'] = id
		geojson['geometry']['type'] = geom.geometryType()
		# cleaning for GeoJSON...by replacing '(...)' with '[...]'
		geojson_points = []
		# print geom.type
		if geom.type == 'Point' or geom.type == 'LineString':
			coords = list(geom.coords)
			for coord in coords:
				geojson_points.append([coord[0],coord[1]])
		elif geom.type == 'Polygon':
			coords = list(geom.exterior.coords)
			for coord in coords:
				geojson_points.append([coord[0],coord[1]])
		elif geom.type == 'MultiLineString':
			# print geom.type
			for geom_ in geom.geoms:
				coords = geom_.coords
				geojson_points_ = []
				for coord in coords:
					geojson_points_.append([coord[0],coord[1]])
				geojson_points.append(geojson_points_)
			# print geojson_points
		# make GeoJSON
		if geom.geometryType() == 'Point':
			geojson['geometry']['coordinates'] = geojson_points[0]
		elif geom.geometryType() == 'LineString' or geom.geometryType() == 'MultiLineString':
			geojson['geometry']['coordinates'] = geojson_points
		elif geom.geometryType() == 'Polygon':
			geojson['geometry']['coordinates'] = [geojson_points]
		features.append(geojson)
	# add features to feature-collection-dummy
	featurecoll_geojson = featcoll_dummy.copy()
	featurecoll_geojson['features'] = features
	# save geoJSON to file
	with open(filename, "w") as file:
		file.write(json.dumps(featurecoll_geojson, indent=4))
	file.close()

def exportRectangles(lines):
	rectangles = []
	for line_ in lines:
		b = box(line_.bounds[0],line_.bounds[1],line_.bounds[2],line_.bounds[3])
		rectangles.append(b)
	return rectangles

def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		transform_ = argv[1]
	except:
		transform_ = None
	try:
		buffer_ = int(argv[2])
	except:
		buffer_ = 0.05

	lines_input = open('training_data/lines_out.txt', 'r')
	points_input = open('training_data/points_out.txt', 'r')

	lines, lines_indizes, lines_r_tree = readInput(lines_input, transform_)
	points, points_indizes = readInput(points_input, transform_)

	intersections_r_tree, buffered_points = findCPointByRTree(points, lines_r_tree, buffer_)

	intersection_points = findCPointBySimpleBuffer(lines, points, buffer_)

	saveToGeoJSON('results/points.json',points, points_indizes)
	saveToGeoJSON('results/lines.json',lines, lines_indizes)
	saveToGeoJSON('results/intersection_points.json',intersection_points)
	saveToGeoJSON('results/intersections_r_tree.json',intersections_r_tree)

	saveToGeoJSON('results/rectangles.json',exportRectangles(lines), lines_indizes)
	saveToGeoJSON('results/buffered_points.json',buffered_points)

	os.system("topojson --id-property id \
		 -o results/all_features_topo.json \
		 -s 0.00000005 \
		 results/points.json \
		 results/lines.json \
		 results/intersection_points.json \
		 results/intersections_r_tree.json \
		 results/rectangles.json \
		 results/buffered_points.json");

if __name__ == "__main__":
    sys.exit(main())
