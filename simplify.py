#!/usr/bin/env python

import sys
from osgeo import ogr


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
		ogr_geometry = ogr.CreateGeometryFromGML(gml_)
		geometries.append(ogr_geometry)
	return geometries

lines = readInput(lines_input)
points = readInput(points_input)


