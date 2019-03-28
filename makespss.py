"""
This script aggregates converts a Mirador dataset into a SPSS-compatible dataset with a
SPSS control card holding the metadata.

@copyright: Harvard University 2014-15
"""

import sys, csv, os, shutil

def spss_type(mtype):    
    if mtype == "int": return "F"
    elif mtype == "float": return "f"
    elif mtype == "date": return "DATE"
    else: return "A"    
    
mirador_folder = "./mirador/"
output_filename = "./spss/ebola-data.csv"

for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if arg == "-in": mirador_folder = sys.argv[i + 1]
    elif arg == "-out": output_filename = sys.argv[i + 1]

data_name = ""
dict_name = ""
miss_str = "\\N"
fn = os.path.join(mirador_folder, "config.mira")
print("Reading project file...")
with open(fn) as mira_file:
    lines = mira_file.readlines()
    for line in lines:
        [key, val] = line.strip().split("=")
        if key == "data.source": data_name = val
        if key == "data.dictionary": dict_name = val
        if key == "missing.string": miss_str = val

data_filename = os.path.join(mirador_folder, data_name)
dict_filename = os.path.join(mirador_folder, dict_name)

with open(data_filename, "r") as data_file:
    short_names = data_file.readlines()[0].strip().split(",")
    
print("Reading dictionary file...")
long_names = []
var_types = []
code_dict = []
with open(dict_filename, "r") as dict_file:
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

out_folder, out_name = os.path.split(output_filename)
if not os.path.exists(out_folder): os.makedirs(out_folder)
print("Copying CSV file...")
shutil.copyfile(data_filename, output_filename)
print("Writing SPSS card...")
spss_name = os.path.join(out_folder, out_name.replace(".csv", ".spss"))

# print short_names
# print long_names
# print var_types
# print code_dict
count = len(short_names)

with open(spss_name, "w") as spss_file:    
    spss_file.write("DATA LIST LIST(',') /\n")
    
    # Variable types
    for i in range(0, count):
        spss_file.write("  " + short_names[i] + " " + "(" + spss_type(var_types[i]) + ")" + "\n")    
    spss_file.write("  .\n")
    
    # Variable labels
    spss_file.write("VARIABLE LABELS\n")
    for i in range(0, count):
        spss_file.write('  ' + short_names[i] + ' "' + long_names[i] + '"\n')
    spss_file.write("  .\n")

    # Value labels
    spss_file.write("VALUE labels\n")
    for i in range(0, count):
        if var_types[i] == "category" and code_dict[i]:
            spss_file.write("  " + short_names[i] + " ")
            for key in code_dict[i]:
                spss_file.write('  ' + key + ' "' + code_dict[i][key] + '"\n')
            spss_file.write("  /\n")
    spss_file.write("  .\n")
    # Missing values 
    spss_file.write("MISSING VALUES\n")
    for i in range(0, count):
        spss_file.write("  " + short_names[i] + "(" + miss_str	+ ")" + "\n")
    spss_file.write("  .\n")
    
print("Done.")