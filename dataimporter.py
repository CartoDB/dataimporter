from cartodb import CartoDBAPIKey, FileImport  # CartoDBException, FileImport
# import pandas as pd #remove pandas b/c dokku doesn't seem to support numpy's C dependencies
import csv
from datetime import datetime
from io import TextIOWrapper
# import StringIO
# import os
# from requests import request
# from flask import render_template   # Flask, send_file, render_template


# def csvLineCount(inCSV):
#     # read csv
#     with open(inCSV, "r") as f:
#         reader = csv.reader(f, delimiter=",")
#         data = list(reader)
#         row_count = len(data)
#     return row_count
# #
#
def testExceedLimits(inCSVLen, limit):
    # does the input file have rows > 499,999
    # limit = 499999
    if inCSVLen > limit:
        return True
    elif inCSVLen <= limit:
        return False
    else:
        return 'Error'
#
#
# def cartoImporter(inFile, inFileName, username, apikey):
#     cl = CartoDBAPIKey(apikey, username)
#     ouFile = 'data/_send/'+ouFileName+'.csv'
#     # Import csv file, set privacy as 'link' and create a default viz
#     fi = FileImport(ouFile, cl, create_vis='false', privacy='link', content_guessing='false', type_guessing='false')
#     fi.run()
#     return fi


# Below here is from other app, may be deleted.

#
# def reorderLatLng(inValue):
#     listCoords = []
#     for i in inValue.split(','):
#         i = i.replace('((', '').replace('))', '').replace('POLYGON', '')
#         i = i.split(' ')
#         inPair = i[1].replace("'", '')+' '+i[0].replace("'", '')
#         listCoords.append(inPair)
#     print 'listCoords:', listCoords
#     return "POLYGON(("+','.join(listCoords)+"))"


def readFileImport(inFile, inFileName, username, apikey, rowLimit):
    curTime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    ouFileName = inFileName.replace('.csv', '')
    # ouFile = 'data/ninth_decimal_'+curTime+'.csv'
    ouFile = 'data/_send/'+ouFileName+'.csv'

    with open(ouFile, 'w') as csvoutput:
        writer = csv.writer(csvoutput, lineterminator='\n')

        # This code opens our bytestream with \r as the newline
        newline_wrapper = TextIOWrapper(inFile, newline=None)  # newline='\r')

        reader = csv.reader(newline_wrapper)  # , delimiter = ',')#, lineterminator='\r')

        all = []
        row = next(reader)

        # row.append('the_geom') REMOVE
        all.append(row)

        # geoFenceColLoc = row.index('geofence') REMOVE

        for row in reader:
            # row.append(reorderLatLng(row[geoFenceColLoc])) REMOVE
            all.append(row)

        writer.writerows(all)

        fileLen = len(all)

        exceedTest = testExceedLimits(fileLen, rowLimit)

    cl = CartoDBAPIKey(apikey, username)

    # Import csv file, set privacy as 'link' and create a default viz
    fi = FileImport(ouFile, cl, create_vis='false', privacy='link', content_guessing='false', type_guessing='false')
    fi.run()
    return fi, fileLen, exceedTest
