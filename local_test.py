import csv

def reorderLatLng(inValue):
    listCoords = []
    for i in inValue.split(','):
        i = i.replace('((','').replace('))','').replace('POLYGON','')
        i = i.split(' ')
        inPair = i[1].replace("'",'')+' '+i[0].replace("'",'')
        listCoords.append(inPair)
    print 'listCoords:',listCoords
    return "POLYGON(("+','.join(listCoords)+"))"

with open('data/example.csv','rU') as csvinput:
    with open('data/test_example.csv', 'w') as csvoutput:
        writer = csv.writer(csvoutput, lineterminator='\n')
        reader = csv.reader(csvinput)

        all = []
        row = next(reader)
        row.append('the_geom')
        all.append(row)

        for row in reader:
            row.append(reorderLatLng(row[11]))
            all.append(row)

        writer.writerows(all)
