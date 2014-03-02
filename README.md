
# Documentation

Basic call
```python
python simplify.py
```

Transform coordinates to geographical coordinates by adding the 'EPSG' of the original data

*Currently, this is [54004](http://spatialreference.org/ref/esri/54004/)*
```python
python simplify.py 54004
```

## Dependencies

### System

*Have to be installed locally on the system*

* [osgeo](http://trac.osgeo.org/gdal/wiki/GdalOgrInPython)
* [shapely](https://pypi.python.org/pypi/Shapely)

### Included
* [pyrtree](http://code.google.com/p/pyrtree/)

# Contest

Homepage: http://mypages.iit.edu/~xzhang22/GISCUP2014/index.php

## Readme of Dataset

This zip file contains 3 txt files, one .png file and this README file.

lines_out.txt: This file contains the input Line geometries that form the
               boundary of the counties in NH state, USA.
points_out.txt: This file contains input Point geometries  that are used to
                constrain the line simplification process.
                Notice the relationship of each point to the input set of
                line geometries. After simplification this relationship
                should be preserved.

lines_simple_out.txt: This file containes the result of a valid simplification.
               The resulting file should only contain the Line geometries as
               only these are changed as part of the simplification process.
               The output file should be formatted the same way as the input
               file using the same IDs for each simplified line geometry.

training_data.png: This file shows two images: one for the input set of
         lines with the constraining points and the second image with
         the simplified lines along with the points.

Input lines geometries have a total of 992 vertices and the simplified
 line geometries have a total of 109 vertices.


