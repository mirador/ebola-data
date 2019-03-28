## Creating Ebola dataset for Mirador

1) Requirements:
   - PyVCF package: https://pyvcf.readthedocs.org/en/latest/

2) Convert the MasterDataListandEBOVResults, DemographicsFromSim, CaseNotification, and FinalPiccoloData Excel spreadsheets into csv format using [csvkit](https://csvkit.readthedocs.org/en/0.9.0/scripts/in2csv.html):

```bash
in2csv sources/xls/MasterDataListandEBOVResults.xlsx --sheet Ebola_js1 > sources/csv/MasterDataListandEBOVResults.csv
in2csv sources/xls/DemographicsFromSim_schieffelin.xlsx > sources/csv/DemographicsFromSim_schieffelin.csv
in2csv sources/xls/CaseNotification_schieffelin.xlsx > sources/csv/CaseNotification_schieffelin.csv
in2csv sources/xls/FinalPiccoloData_schieffelin.xlsx --sheet FinalSummary1 > sources/csv/FinalPiccoloData_schieffelin-FinalSummary1.csv
``` 

3) Run the makedataset.py script that will generate the aggregated dataset in Mirador's 
format and will store it in the mirador folder.

```bash
python makemira.py
```

The arguments -seq needs to be added in order to aggregate the sequencing data into the Mirador's dataset,
and -log can be used to convert the viral loads into log units using the formula log(1 + qpcr) where qpcr is
the qPCR measurement:

```bash
python makemira.py -log -seq
```

## Creating Ebola dataset as single CSV file

The Mirador dataset can be converted into a single CSV file that can be more convenient for loading into other tools by running the following script:

```bash
python makecsv.py -in mirador -out csv/ebola-data.csv
```

This can be done only after generating the Mirador dataset, and will generate an ebola-data.csv in the csv folder.

## Creating SPSS dataset

The Mirador dataset can also be converted into an SPSS-compatible format, loadable from 
repositories like the [Dataverse](http://dataverse.org/), using the makespss script:

```bash
python makespss.py -in mirador -out csv/ebola-data.csv
```

, which also saves a [SPSS-style control card](http://thedata.harvard.edu/guides/dataverse-user-main.html#csv-data-spss-style-control-card) 
in csv/ebola-data.spss.

## SNP, iSNV and cluster data

The aggregated Mirador file includes the Single Nucleotide Polymorphism (SNP) data for the viral sequences in some of the patients, as originally reported in the Gire et al. Science paper:

http://www.sciencemag.org/content/345/6202/1369.short

and deposited at:

http://www.ncbi.nlm.nih.gov/nuccore/KM034562.1

It also includes the Single Nucleotide Variation (SNV) data per site, and the genetic cluster classification per patient, as described in the Sciente paper above.
