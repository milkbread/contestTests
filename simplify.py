#!/usr/bin/env python

import sys
from osgeo import ogr
from shapely.geometry import Point, LineString

#to_replace1 = '<gml:LineString srsName="EPSG:54004" xmlns:gml="http://www.opengis.net/gml"><gml:coordinates decimal="." cs="," ts=" ">'
#to_replace2 = "</gml:coordinates></gml:LineString>"

lines_input = open('lines_out.txt', 'r')
points_input = open('points_out.txt', 'r')

def readInput(data):
	geometries = []
	for line in data.readlines():
		# check if we have to remove two or three chars from line
		index_ = 2 if line[1:2]==':' else 3
		# remove first 'index'-chars
		gml_ = line[index_:]
		# convert to ogr-geometry
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

