#!/usr/bin/env python

import os
import sys
import json
from osgeo import ogr, osr
from shapely.geometry import Point, LineString, box

from pyrtree import RTree, Rect

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
		# add geometry to geoJSON-geometry-dummy
		geojson = feauture_dummy.copy()
		geojson['geometry']['type'] = geom.geometryType()
		# cleaning for GeoJSON...by replacing '(...)' with '[...]'
		geojson_points = []
		if geom.type == 'Point' or geom.type == 'LineString':
			coords = list(geom.coords)
		elif geom.type == 'Polygon':
			coords = list(geom.exterior.coords)
		for coord in coords:
			geojson_points.append([coord[0],coord[1]])
		# make GeoJSON
		if geom.geometryType() == 'Point':
			geojson['geometry']['coordinates'] = geojson_points[0]
		elif geom.geometryType() == 'LineString':
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

	'''t = RTree()
   	t.insert(some_kind_of_object,Rect(min_x,min_y,max_x,max_y))
   	point_res = t.query_point( (x,y) )
   	rect_res = t.query_rect( Rect(x,y,xx,yy) )'''

   	t = RTree()
   	rectangles = []
   	for line_ in lines:
   		#print dir(line_)
   		#print line_.bounds
   		b = box(line_.bounds[0],line_.bounds[1],line_.bounds[2],line_.bounds[3])
   		rectangles.append(b)
   		#print list(b.exterior.coords)
   		t.insert(line_,Rect(line_.bounds[0],line_.bounds[1],line_.bounds[2],line_.bounds[3]))

   	intersection_points = []
   	buffered_points = []
   	for point_ in points:
   		#print dir(point_)
   		#print point_.x, point_.y
   		#point_res = t.query_point( (point_.x,point_.y) )
   		#print point_res
   		real_point_res = [r.leaf_obj() for r in t.query_point( (point_.x,point_.y) ) if r.is_leaf()]
   		#Point(ogr_geometry.GetX(),ogr_geometry.GetY())
   		distance = real_point_res[0].project(point_)
   		#print distance
   		buffered_point = point_.buffer(0.09)
   		print real_point_res[0].intersects(buffered_point)
   		buffered_points.append(buffered_point)
   		'''if line_.intersects(buffered_point):
   			intersection = line_.intersection(buffered_point)
   			#print dir(intersection)
   			intersection_point = intersection.interpolate(distance+1.5)
   			intersection_points.append(intersection_point)
'''

	intersection_points = findCPointBySimpleBuffer(lines, points, 0.05)

	#saveToGeoJSON('points.json',points)
	#saveToGeoJSON('lines.json',lines)
	#saveToGeoJSON('intersection_points.json',intersection_points)

	saveToGeoJSON('rectangles.json',rectangles)
	saveToGeoJSON('buffered_points.json',buffered_points)

	os.system("topojson -o all_features_topo.json points.json lines.json intersection_points.json rectangles.json buffered_points.json");

if __name__ == "__main__":
    sys.exit(main())
