"""
This script aggregates the Master, Demographic, Clinical, Laboratory, and Viral 
Sequencing data available for an initial cohort of Ebola patients from the 2014 outbreak 
in West Africa, and treated at the Kenema Government Hospital in Sierra Leone. This data
has initially been described in the following papers:

1) Genomic surveillance elucidates Ebola virus origin and transmission during the 2014 outbreak
http://www.sciencemag.org/content/345/6202/1369.short

2) Clinical Illness and Outcomes in Patients with Ebola in Sierra Leone
http://www.nejm.org/doi/full/10.1056/NEJMoa1411680

The aggregation results in a single dataset specially formatted for loading into the 
visualization tool Mirador (http://fathom.info/mirador)

@copyright: Harvard University 2014-15
"""

import sys, csv, os, codecs, shutil, math, time, re, vcf
import collections
import xml.dom.minidom
from time import mktime

def write_xml_line(line, xml_file, xml_strings):
    ascii_line = ''.join(char for char in line if ord(char) < 128)
    if len(ascii_line) < len(line):
        print("  Warning: non-ASCII character found in line: '" + line.encode('ascii', 'ignore') + "'")
    xml_file.write(ascii_line + "\n")
    xml_strings.append(ascii_line + "\n")

"""Returns a list of patient ids to ignore in the aggregation

:param filename: file holding the list of ids (one per line)
"""
def load_ignore(filename):
    list = []
    with open(filename, 'r') as file:
       lines = file.readlines()
       for line in lines:
           list.append(line.strip())
    return list
    
"""Reads the master table and adds its entries to src_data

:param filename: csv file containing the master table
"""
def load_master(filename):
    reader = csv.reader(open(filename, "r"), dialect="excel")
    next(reader)
    for row in reader:
        id = row[1]
        if id in ignore_id: continue
        idx = row[3]
        date = row[5]
        vload = row[8]
        result = row[9]
        group = row[10]
        if not group: continue
        if id in src_data:
            series = src_data[id]["qpcr"]
        else:
            data = {}
            src_data[id] = data
            data["group"] = group
            data["outcome"] = None
            data["sex"] = None            
            data["demo"] = None
            data["case"] = None
            data["pico"] = None
            series = []
            data["qpcr"] = series 
        series.append([idx,date,vload])

"""Reads the demographics table and adds its entries to src_data

:param filename: csv file containing the demographics table
"""
def load_demo(filename):
    reader = csv.reader(open(filename, "r"), dialect="excel")
    next(reader)
    for row in reader:
        id = row[1]
        if not id in src_data: continue
        sex = row[3]
        outcome = row[7]
        src_data[id]["outcome"] = outcome
        src_data[id]["sex"] = sex
        src_data[id]["demo"] = row    

"""Reads the case notification (clinical symptoms) table and adds its entries to src_data

:param filename: csv file containing the demographics table
"""
def load_case(filename):
    reader = csv.reader(open(filename, "r"), dialect="excel")
    next(reader)
    for row in reader:
        id = row[0]
        if not id in src_data: continue  
        src_data[id]["case"] = row

"""Reads the Piccolo (metabolic panel) table and adds its entries to src_data

:param filename: csv file containing the Piccolo table
"""
def load_pico_data(filename): 
    reader = csv.reader(open(filename, "r"), dialect="excel")
    next(reader)
    for row in reader:
        id = row[3]
        if not id in src_data: continue 
        if not src_data[id]["pico"] == None:
            pico_series = src_data[id]["pico"]
        else:
            pico_series = []
            src_data[id]["pico"] = pico_series
        pico_series.append(row)                           

"""Prints some summary counts for debugging
"""
def print_summary():
    count_total = len(src_data)
    count_pos = 0
    count_neg = 0
    count_case = 0
    count_pos_pico = 0
    count_neg_pico = 0
    count_known_out = 0
    count_vload = 0
    count_pos_male = 0
    count_pos_fem = 0
    count_pos_unk = 0    
    count_neg_male = 0
    count_neg_fem = 0
    count_neg_unk = 0
    count_novload_fatal = 0  
    count_novload_nonfatal = 0    
    
    for id in src_data:
        data = src_data[id]
        if data["group"] == "Epos":
            count_pos = count_pos + 1
            if data["sex"] == "Male":
                count_pos_male = count_pos_male + 1
            elif data["sex"] == "Female":
                count_pos_fem = count_pos_fem + 1
            else:
                count_pos_unk = count_pos_unk + 1
            if data["outcome"]:                
                count_known_out = count_known_out + 1
                if data["case"]: count_case = count_case + 1            
                if data["pico"]: count_pos_pico = count_pos_pico + 1            
                series = data["qpcr"]
                vload = False
                for qpcr in series:
                    if qpcr[2]: vload = True
                if vload:
                    count_vload = count_vload + 1
                else:
                    if data["outcome"] == "Died":
                        count_novload_fatal = count_novload_fatal + 1
                    elif data["outcome"] == "Discharged":
                         count_novload_nonfatal = count_novload_nonfatal + 1                
        else:
            count_neg = count_neg + 1
            if data["sex"] == "Male":
                count_neg_male = count_neg_male + 1
            elif data["sex"] == "Female":
                count_neg_fem = count_neg_fem + 1
            else:
                count_neg_unk = count_neg_unk + 1             
            if data["pico"]: count_neg_pico = count_neg_pico + 1           
    
    print("Cases evaluated for Ebola virus infection:", count_total) 
    print("  Ebola virus disease cases:",count_pos)
    print("    Ebola virus disease cases, female:",count_pos_fem )
    print("    Ebola virus disease cases, male:",count_pos_male)
    print("    Ebola virus disease cases, unknown gender:",count_pos_unk) 
    print("    Ebola virus disease cases with known outcome:",count_known_out) 
    print("      Cases with Ebola virus load (qPCR):",count_vload)
    print("      Cases with clinical chart (signs/symptoms):",count_case) 
    print("      Cases with metabolic panel:",count_pos_pico) 
    print("      Cases with no Ebola virus load, fatal:",count_novload_fatal) 
    print("      Cases with no Ebola virus load, non fatal:",count_novload_nonfatal) 
    print("  Non Ebola cases disease illness patients:",count_neg) 
    print("    Non Ebola cases disease illness patients, female:",count_neg_fem)
    print("    Non Ebola cases disease illness patients, male:",count_neg_male) 
    print("    Non Ebola cases disease illness patients, unknown gender:",count_neg_unk) 
    print("    Non Ebola cases disease illness patients with metabolic panel:",count_neg_pico) 

"""Returns a dictionary file, where each entry holds the metadata for a variable (short name,
long name or alias, group and table it belongs to, and type (int, float, etc).

:param filename: csv file containing the dictionary table
"""
def load_dict(filename):
    dict = collections.OrderedDict()
    reader = csv.reader(open(filename, "r"), dialect="excel")    
    for row in reader:
        col = int(row[0])
        info = {"name":row[1], "alias":row[2], "group": row[3], "table":row[4], "type":row[5]}
        if len(row) == 7: 
            rstr = row[6]
            info["ranges"] = rstr
            parts = rstr.split(";")
            idict = {"":""}
            for p in parts:
                if p:
                    [value, key] = p.split(":")
                    idict[key] = value
            info["idict"] = idict                        
        dict[col] = info
    return dict

"""Returns information about the variables measured in the metabolic panel: name, 
gender-dependent ranges, and location in the Piccolo table.

:param filename: csv file containing the Piccolo metadata
"""
def load_pico_info(filename):
    pico_names = []
    pico_info = {}
    reader = csv.reader(open(filename, "r"), dialect="excel")
    next(reader)
    for row in reader:
        name = row[0]
        [rstr, unit] = row[3].split(" ", 1)
        parts = rstr.split(":")
        if len(parts) == 1:        
            rangem = rangef = [float(x) for x in parts[0].split("-")]
        else:
            rangef = [float(x) for x in parts[0].split("-")]
            rangem = [float(x) for x in parts[1].split("-")]
            
        title = row[1] + " [" + unit + "]"
        col = int(row[5])
        pico_names.append(name)
        pico_info[name] = {"title":title, "range-female":rangef, "range-male":rangem, "column":col}

    return [pico_names, pico_info]

"""Normalizes a patient id string by adding a slash between the character and numeric portions.

:param id: original id to normalize
"""
def normalize_id(id):
    res = re.search("\d", id)
    if res:
        pos = res.start()
        new_id = id[:pos] + '-' + id[pos:]
        return new_id
    else:
        print("  Warning: patient ID is malformed: " + id)
        return id

"""Returns SNP data stored in the provided VCF file, in the form of the list of SNPs, and
a binary indicator per each patient for whom there was viral sequencing data available.

:param filename: vcf file containing SNP data
"""
def load_snp_data(filename):
    snp_vars = collections.OrderedDict()
    snp_data = {}
    vcf_reader = vcf.Reader(open(filename, "r"))
    for record in vcf_reader:
        # Info per SNP: record.CHROM, record.POS
        pos = str(record.POS)
        name = "SNP" + pos
        alias = "SNP @" + pos
        snp_vars[name] = alias
        dict = {}
        for s in record.samples:
            id = normalize_id(s.sample.split("_")[2])
            dict[id] = "1" if s.data.GT == "1" else "0"
        snp_data[name] = dict
    return [snp_vars, snp_data]

"""Returns Allele Frequency data stored in the provided VCF file, in the form of the list 
of SNPs, and the AF per each patient for whom such data available was available.

:param filename: vcf file containing AF data
:param inc_snp: list of SNPs to include in the returned lists, empty list to include alls
"""
def load_af_data(filename, inc_snp = None):
    af_vars = collections.OrderedDict()
    af_data = {}
    vcf_reader = vcf.Reader(open(filename, "r"))
    for record in vcf_reader:
        if inc_snp and not record.POS in inc_snp: continue
        pos = str(record.POS)
        name = "AF" + pos
        alias = "Allele Frequency @" + pos
        af_vars[name] = alias
        dict = {}
        for s in record.samples:
            id0 = s.sample.split("_")[2]
            id = normalize_id(id0.split(".")[0])
            dict[id] = str(s.data.AF)
        af_data[name] = dict
    return [af_vars, af_data]     

"""Returns the viral sequence clustering data for patients with SNP data available. This 
information comprises cluster and subcluster the patient belongs to, as well as the 
intra-cluster and intra-subcluster distances for each individual.

:param filename: csv file containing the cluster data
"""
def load_cluster_data(filename):
    cl_vars = collections.OrderedDict()
    cl_vars["CLUST"] = "Cluster"
    cl_vars["MCLUST"] = "# mutations from cluster"
    cl_vars["SCLUST"] = "Sub-cluster"
    cl_vars["MSCLUST"] = "# mutations from sub-cluster"
    cl_data = {}
    cl_data["CLUST"] = {}    
    cl_data["MCLUST"] = {}
    cl_data["SCLUST"] = {}    
    cl_data["MSCLUST"] = {}
    reader = csv.reader(open(filename, "r"), dialect="excel-tab")
    next(reader)
    for row in reader:
        id = normalize_id(row[0])
        cvalue = ""
        cmutat = ""
        svalue = ""
        smutat = ""            
        parts = row[2].split(".")
        cvalue = parts[0]
        extra = parts[1]
        if 0 < len(extra):
            cmutat = extra[0]
            if 1 < len(extra):
                svalue = extra[1]
                smutat = '0'
                if 2 < len(extra):
                    smutat = extra[2]                     
        cl_data["CLUST"][id] = cvalue
        cl_data["MCLUST"][id] = cmutat
        cl_data["SCLUST"][id] = svalue
        cl_data["MSCLUST"][id] = smutat

    return [cl_vars, cl_data]

"""Adds a new variable to include in the Mirador dataset.

:param name: variable name
:param title: variable title (long name or alias)
:param type: variable type (int, float, date, category, string)
:param gname: name of group containing the variable
:param tname: name of table containing the variable
"""
def add_variable(name, title, type, gname, tname):
    variables.append(name)
    var_titles[name] = title
    var_types[name] = type
    
    if gname in var_groups: 
        group = var_groups[gname]
    else:
        group = collections.OrderedDict()
        var_groups[gname] = group
    
    if tname in group:
        table = group[tname]
    else:
        table = []
        group[tname] = table
            
    table.append(name)
    
"""Sets the range of values for a variable already added to the dataset.

:param name: variable name
:param ranges: range string
"""    
def set_var_ranges(name, ranges):
    var_ranges[name] = ranges
        
"""Adds the demographics data to the Mirador dataset
"""
def add_demo_data():
    add_variable("GID", "Patient ID", "String", "Demographics", "Basic Information") 
    set_var_ranges("GID", "label")
    add_variable("DIAG", "Diagnosis", "category", "Demographics", "Basic Information") 
    set_var_ranges("DIAG", "1:Positive;0:Negative")
            
    for col in demo_dict:
        var = demo_dict[col]
        add_variable(var["name"], var["alias"], var["type"], var["group"], var["table"]) 
        if "ranges" in var:
            set_var_ranges(var["name"], var["ranges"])

    for id in src_data:
        data = src_data[id]
        diag = "1" if data["group"] == "Epos" else "0"
        row = [id, diag]
        for col in demo_dict:
            var = demo_dict[col]
            if data["demo"]:
                val = data["demo"][col]
            else:
                val = ""
            if "idict" in var: 
                if val in var["idict"]:
                    val = var["idict"][val]
                else:
                    val = ""


            row.append(val)
        mira_data[id] = row        

"""Adds the case notification (clinical symptoms) data to the Mirador dataset
"""
def add_case_data():
    for col in case_dict:
        var = case_dict[col]
        add_variable(var["name"], var["alias"], var["type"], var["group"], var["table"]) 
        if "ranges" in var:
            set_var_ranges(var["name"], var["ranges"])

    for id in src_data:
        data = src_data[id]
        row = mira_data[id]
        for col in case_dict:
            var = case_dict[col]
            if data["case"]:
                val = data["case"][col]
            else:
                val = ""
            if "idict" in var: 
                val = var["idict"][val]
            row.append(val)     

"""Adds the Piccolo (metabolic panel) data to the Mirador dataset
"""
def add_pico_data():
    # Calculating the maximum length of a series of metabolic panels
    max_len = 0
    for id in src_data:
        data = src_data[id]  
        series = data["pico"]        
        if series:
            max_len = max(max_len, len(series))

    # Total number of variables added to store metabolic panel data
    count = max_len * (1 + len(pico_names))
    for i in range(1, max_len + 1):
        add_variable("DOPANEL_" + str(i), "Date of metabolic panel " + str(i), "date", "Laboratory", "Metabolic Panel Day " + str(i))
        for name in pico_names:
            info = pico_info[name]
            add_variable(name + "_" + str(i), info["title"] + " day " + str(i), "float", "Laboratory", "Metabolic Panel Day " + str(i))
    
    for id in src_data:
        data = src_data[id]
        series = data["pico"]
        row = mira_data[id]
        if series:
            count1 = len(series)
            for pico in series:
                row.append(pico[6])
                for name in pico_names:
                    col = pico_info[name]["column"]
                    row.append(pico[col])
            row.extend(["\\N"] * (count - count1 * (1 + len(pico_names)))) # Adding missing days
        else:
            row.extend(["\\N"] * count)

"""Adds the viral load (qPCR) data to the Mirador dataset
"""            
def add_qpcr_data():
    # Calculating the maximum length of a series of qPCR samples
    max_len = 0
    for id in src_data:
        data = src_data[id]  
        series = data["qpcr"]        
        if series:
            max_len = max(max_len, len(series))

    count = 4 + max_len * 2
    log_str = " (log units)" if convert_qpcr_log else ""
    add_variable("PCR", "First measured viral load" + log_str, "float", "Laboratory", "Viral Load (qPCR) summary")
    add_variable("PCR_MAX", "Maximum measured viral load" + log_str, "float", "Laboratory", "Viral Load (qPCR) summary")
    add_variable("PCR_MIN", "Minimum measured viral load" + log_str, "float", "Laboratory", "Viral Load (qPCR) summary")
    add_variable("PCR_AVE", "Averaged viral load" + log_str, "float", "Laboratory", "Viral Load (qPCR) summary")
    for i in range(1, max_len + 1):
        add_variable("DOPCR_" + str(i), "Date of qPCR " + str(i), "date", "Laboratory", "Viral Load (qPCR) day " + str(i))
        add_variable("PCR_" + str(i), "EBOV copies/mL plasma" + log_str + " day " + str(i), "float", "Laboratory", "Viral Load (qPCR) day " + str(i)) 
        
    for id in src_data:
        data = src_data[id]
        series = data["qpcr"]
        row = mira_data[id]
        if series:
            count1 = len(series)
            first_qpcr = None
            max_qpcr = None
            min_qpcr = None
            ave_qpcr = None
            slen = 0
            for qpcr in series:
                value = qpcr[2]
                if value:
                    if convert_qpcr_log: fval = math.log10(1 + float(value))
                    else: fval = float(value)
                    if first_qpcr: 
                        max_qpcr = max(max_qpcr, fval)
                        min_qpcr = min(min_qpcr, fval)                        
                        ave_qpcr = ave_qpcr + fval
                    else: 
                        first_qpcr = fval
                        max_qpcr = fval
                        min_qpcr = fval 
                        ave_qpcr = fval
                    slen = slen + 1
                    qpcr[2] = str(fval)

            if first_qpcr: 
                row.extend([str(first_qpcr), str(max_qpcr), str(min_qpcr), str(ave_qpcr / slen)])
            else: 
                row.extend(["\\N"] * 4)
                
            for qpcr in series:
                date = qpcr[1]
                value = qpcr[2]
                row.extend([date, value])
                
            row.extend(["\\N"] * (count - 4 - count1 * 2))                
        else:
            row.extend(["\\N"] * count)

"""Adds the sequencing data (SNPs, AF, clustering) to the Mirador dataset
""" 
def add_seq_data():
    for var in snp_vars:
        add_variable(var, snp_vars[var], "category", "Sequencing", "Viral SNPs")
        set_var_ranges(var, "1:Yes;0:No")
    for var in af_vars:
        add_variable(var, af_vars[var], "float", "Sequencing", "Allele Frequencies")
    add_variable("CLUST", cl_vars["CLUST"], "category", "Sequencing", "Clustering")
    set_var_ranges("CLUST", "1:Cluster 1;2:Cluster 2;3:Cluster 3")
    add_variable("MCLUST", cl_vars["MCLUST"], "int", "Sequencing", "Clustering")    
    add_variable("SCLUST", cl_vars["SCLUST"], "category", "Sequencing", "Clustering")
    set_var_ranges("SCLUST", "1:Sub-cluster a;2:Sub-cluster b;3:Sub-cluster c")
    add_variable("MSCLUST", cl_vars["MSCLUST"], "int", "Sequencing", "Clustering")

    for var in snp_vars:
        for id in mira_data:
            row = mira_data[id]
            if id in snp_data[var]:
                row.append(snp_data[var][id])
            else:
                row.append("")

    for var in af_vars:
        for id in mira_data:
            row = mira_data[id]
            if id in af_data[var]:
                row.append(af_data[var][id])
            else:
                row.append("")

    for var in cl_vars:
        for id in mira_data:
            row = mira_data[id]
            if id in cl_data[var]:
                row.append(cl_data[var][id])
            else:
                row.append("")            

"""Inits the folder to store the Mirador dataset

:param dir: folder path
""" 
def init_dataset(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    if os.path.isfile(dir + "/data.bin"):
        os.remove(dir + "/data.bin")
    shutil.copyfile('config.mira', dir + '/config.mira')

"""Saves the Mirador dataset into a csv file

:param filename: name of csv file
""" 
def save_data(filename):
    print("Saving data...")
    writer = csv.writer(open(filename, "w"), dialect="excel")
    writer.writerow(variables)
    for id in mira_data:
        row = mira_data[id]
        for i in range(0, len(row)):
            row[i] = str(row[i])
            if not row[i]: row[i] = "\\N"        
        writer.writerow(row)
    print("Done.")
    
"""Saves the dictionary for the Mirador dataset into a csv file

:param filename: name of csv dictionary
""" 
def save_dict(filename):    
    print("Saving dictionary...") 
    writer = csv.writer(open(filename, "w"), dialect="excel")
    for var in variables:
        if var in var_ranges and var_ranges[var]:
            writer.writerow([var_titles[var], var_types[var], var_ranges[var]])
        else:
            writer.writerow([var_titles[var], var_types[var]])
    print("Done.") 
        
"""Saves the group/tables hierarchy for the Mirador dataset into an xml file

:param filename: name of xml file
"""
def save_groups(filename):
    print("Saving groups...")
    # Writing file in utf-8 because the input html files from
    # NHANES website sometimes have characters output the ASCII range.
    xml_file = codecs.open(filename, 'w', 'utf-8')
    xml_strings = []
    write_xml_line('<?xml version="1.0"?>', xml_file, xml_strings)
    write_xml_line('<data>', xml_file, xml_strings)
    for gname in var_groups:
        if gname in ["State", "Weighting", "Land and Cell Raking"]: continue            
        write_xml_line(' <group name="' + gname + '">', xml_file, xml_strings)
        group = var_groups[gname]
        for tname in group:
            write_xml_line('  <table name="' + tname + '">', xml_file, xml_strings)
            table = group[tname]
            for var in table:
                write_xml_line('   <variable name="' + var + '"/>', xml_file, xml_strings)
            write_xml_line('  </table>', xml_file, xml_strings)
        write_xml_line(' </group>', xml_file, xml_strings)
    write_xml_line('</data>', xml_file, xml_strings)
    xml_file.close()

    # XML validation.
    try:
        doc = xml.dom.minidom.parseString(''.join(xml_strings))
        doc.toxml()
        print("Done.")
    except:
        sys.stderr.write("XML validation error:\n")
        raise

##########################################################################################
#
# Main
#
##########################################################################################

aggregate_seq_data = False
convert_qpcr_log = False
for arg in sys.argv[1:]:
    if arg == "-seq":
        aggregate_seq_data = True
    elif arg == "-log":
        convert_qpcr_log = True
    
src_data = collections.OrderedDict()
mira_data = collections.OrderedDict()

variables = []
var_titles = {}
var_types = {}
var_ranges = {}
var_groups = collections.OrderedDict()

print("Loading data...")
ignore_id = load_ignore("idignore")
print("  master table...")
load_master("sources/csv/MasterDataListandEBOVResults.csv")
print("  demographics table...")
load_demo("sources/csv/DemographicsFromSim_schieffelin.csv")
demo_dict = load_dict("demo-dict.csv")
print("  case notification table...")
load_case("sources/csv/CaseNotification_schieffelin.csv")
case_dict = load_dict("case-dict.csv")
print("  metabolic panel table...")
load_pico_data("sources/csv/FinalPiccoloData_schieffelin-FinalSummary1.csv")
[pico_names, pico_info] = load_pico_info("piccolo-expected.csv")
if aggregate_seq_data:
    print("  sequencing data...")
    # Load the SNP data
    [snp_vars, snp_data] = load_snp_data("sources/vcf/SNP-2014.vcf")
    # Load the Allele Frequency data (only for SNP 10218)
    [af_vars, af_data] = load_af_data("sources/vcf/iSNV-all.vcf", [10218])
    # Load the cluster data
    [cl_vars, cl_data] = load_cluster_data("sources/vcf/clusters.tsv")
print("Done.")
print_summary()

print("Aggregating data...")
add_demo_data()
add_case_data()
add_pico_data()
add_qpcr_data()
if aggregate_seq_data:
    add_seq_data()
print("Done.")
    
init_dataset("mirador")
save_data("mirador/data.csv")
save_dict("mirador/dictionary.csv")
save_groups("mirador/groups.xml")
