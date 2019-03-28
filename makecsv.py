"""
This script aggregates converts a Mirador dataset that including a dictionary with the 
variable metadata into a single csv file that can be loaded from virtually any software.

@copyright: Harvard University 2014-15
"""

import sys, csv, os

mirador_folder = "./mirador/"
output_name = "./csv/ebola-data.csv"
miss_dst = ""

for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if arg == "-in": mirador_folder = sys.argv[i + 1]
    elif arg == "-out": output_name = sys.argv[i + 1]
    elif arg == "-miss": miss_dst = sys.argv[i + 1]
 
print("Reading Mirador data...") 

data_name = ""
dict_name = ""
miss_src = "\\N"
fn = os.path.join(mirador_folder, "config.mira")
print("  " + fn + "...")
with open(fn) as mira_file:
    lines = mira_file.readlines()
    for line in lines:
        [key, val] = line.strip().split("=")
        if key == "data.source": data_name = val
        if key == "data.dictionary": dict_name = val
        if key == "missing.string": miss_src = val

long_names = []
var_types = []
code_dict = []
fn = os.path.join(mirador_folder, dict_name)
print("  " + fn + "...")
with open(fn) as dict_file:
    reader = csv.reader(dict_file)
    for row in reader:
        name = row[0]
        long_names.append(name)
        type = row[1]
        var_types.append(type)
        codes = {}        
        if type.lower() == "category" and 2 < len(row):            
            pieces = row[2].split(";") 
            for piece in pieces:
                parts = piece.split(":")
                codes[parts[0]] = parts[1]
        code_dict.append(codes)
                        
out_data = []
out_data.append(long_names)
fn = os.path.join(mirador_folder, data_name)
print("  " + fn + "...")
with open(fn) as data_file:
    reader = csv.reader(data_file)   
    next(reader)
    for row in reader:
        out_row = []
        for index in range(0, len(row)):
            value = row[index]
            if var_types[index] == "category":
                if value in code_dict[index]:
                    value = code_dict[index][value]
            if value == miss_src: value = miss_dst                    
            out_row.append(value)
        out_data.append(out_row)

print("Done.")

print("Writing CSV file...")
out_folder = os.path.split(output_name)[0]
if not os.path.exists(out_folder): os.makedirs(out_folder)
print("  " + output_name + "...")
with open(output_name, "w") as out_file:
    writer = csv.writer(out_file, dialect="excel")
    for row in out_data:    
        writer.writerow(row)
print("Done.")