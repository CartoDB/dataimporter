from io import TextIOWrapper
import csv

with open(inFile,"r") as f:
    reader = csv.reader(f,delimiter = ",")
    data = list(reader)
    row_count = len(data)
