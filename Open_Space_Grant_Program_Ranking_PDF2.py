print """
#----------------------------------------------------------------------------------------------------------#
# Name:        Open_Space_Grant_Program_Ranking_PDF2                                                       #
#                                                                                                          #
# Purpose:     Tool designed to select a particular parcel by it's 13-digit PIDN number and rank the       #
#              parkland or natural area significant of that property. The output of this tool will provide #
#              a particular score associated the property. The score will be based off numberous criteria. #
#              The tool allows the user to choose between natural area and parkland questions. Can be run  #
#              as many times needed. Data is coming from our Enterprise SDE so results can vary depending  #
#              on the time and frequency.                                                                  #
#                                                                                                          #
#                                                                                                          #
# Authors:     Joseph Simora - York County Planning                                                        #
#                                                                                                          #
# Created:     June 2020                                                                                   #
# Revised:                                                                                                 #
# Copyright:   (c) York County Planning Commission                                                         #
#----------------------------------------------------------------------------------------------------------#
"""

# Module section
import sys, os, arcpy, datetime, time, zipfile, ftplib, shutil, traceback, glob, requests, PyPDF2
from arcpy import env
from datetime import date, timedelta
from fpdf import FPDF

# Directory section
Working_Folder = r"\\YCPCFS1\GIS_Projects\IS\Scripts\Python\OpenSpace"
Layer_Folder = r"\\YCPCFS1\gisdata\Layer_Files"
Project_Folder = r"\\YCPCFS1\GIS_Projects\IS\Projects\Open_Space_Grant_Program_Ranking"

# Set Environmental Workspace/Set arpy overwrite option
arcpy.env.workspace = Working_Folder
arcpy.env.overwriteOutput = True

# Mark starting time in order to calculate total processing time
start = time.clock()
start1 = time.clock()
dt_now = datetime.datetime.today()
Date = time.strftime("%Y%m%d",time.localtime())
currentTime = datetime.datetime.now()
dateToday2 = currentTime.strftime("%Y-%m-%d_%H-%M")

# Create text file for logging results of script
# Update to directory on SCTF server
file = r'\\YCPCFS1\GIS_projects\IS\Scripts\Python\Logs\Open_Space_Grant_Program_Ranking_{}.txt'.format(dateToday2)
# Open text file in write mode and log results of script
report = open(file,'w')

# Define functions
# Write messages to a log file
def message(report,message):
    """ Write a message to a text file
        report is the text file to write the messages to
        report should be defined as report = open(path to file, mode)
         message is the string to write to the file
    """
    timeStamp = time.strftime("%b %d %Y %H:%M:%S")
    report.write("{} {} \n \n".format(timeStamp,message))
    #print "{}: ".format(timeStamp) + message

################################### SCRIPT VARIABLE SECTION #############################################################################################################
#Variable List:
# Enterprise Inputs:
York_SDE= r"\\YCPCFS1\GIS_Projects\IS\GIS_Connections\GIS@York.sde"
York_SDE_Landbase = r"\\YCPCFS1\GIS_Projects\IS\GIS_Connections\GIS@York.sde\York.GIS.Land_Base"

# Landbase Database
Parcels = os.path.join(York_SDE_Landbase,"York.GIS.Parcels")
Parks = os.path.join(York_SDE_Landbase,"York.GIS.Parks")
Cons_Easements = os.path.join(York_SDE_Landbase, "York.GIS.Conservation_Easements")

#Environmental Input
Bird_Area = os.path.join(York_SDE, "York.GIS.ENVIR_Important_Birding_Areas")
NAI_Area = os.path.join(York_SDE, "York.GIS.ENVIR_Natural_Areas_Inventory")
Unique_Geology = os.path.join(York_SDE, "York.GIS.ENVIR_Unique_Features")

#Hydro Inputs
Streams = os.path.join(York_SDE, "York.GIS.HYDRO_Streams")
Impaired_Streams = os.path.join(York_SDE, "York.GIS.HYDRO_Streams_Impaired")
Lake_Pond = os.path.join(York_SDE, "York.GIS.HYDRO_Lakes_Ponds")
Floodplains = os.path.join(York_SDE, "York.GIS.HYDRO_Floodplains")
Wetlands = os.path.join(York_SDE, "York.GIS.HYDRO_Wetlands")

#Planning Inputs
Greenways = os.path.join(York_SDE, "York.GIS.PLANNING_Greenways")
Focus_Areas = os.path.join(York_SDE, "York.GIS.PLANNING_Focus_Areas")

#Landuse Inputs
Landcover = os.path.join(York_SDE, "York.GIS.LANDUSE_Landcover")

#Soil Inputs
Soils = os.path.join(York_SDE, "York.GIS.Soils")

#Wellhead Inputs
Wellheads = os.path.join(York_SDE, "York.GIS.PLANNING_WHP")

#Park_Acres Population
Park_GDB = os.path.join(Project_Folder, os.path.join("~ParkAcres","ParkAcres_Population.gdb"))
Park_Acres = os.path.join(Park_GDB, "ParkAcres_Population")

#Zoning Inputs
Zoning = os.path.join(York_SDE, "York.GIS.Zoning")

############################################### SETTING UP WORKING GDB #################################################################################################
arcpy.AddMessage("STARTING OPEN SPACE GRANT PROGRAM RANKING PROCESS\n")
message (report,"STARTING OPEN SPACE GRANT PROGRAM RANKING PROCESS\n")

# Deleting existing workspaces prior to running script
workspaces = arcpy.ListWorkspaces("*", "FileGDB")
for workspace in workspaces:
    arcpy.Delete_management(workspace)

arcpy.env.workspace = Project_Folder

# variable for Parcel Layer
feature_select = "Feature_Select"

# Python List to append PIDN
PIDN = []

#Set feature select
arcpy.MakeFeatureLayer_management(Parcels, feature_select, "")

#Variable used to set PIDN chances in while loop
chance = 0

# While loop. Runs multiple times on PIDN input. Have 5 chances to submit correct PIDN before script exits.
while chance <= 4:
    Test = raw_input("ENTER 13 DIGIT PIDN.....  ")
    arcpy.AddMessage("VERIFYING IF PIDN {} EXISTS.....\n".format(Test))
    message (report,"VERIFYING IF PIDN {} EXISTS.....\n".format(Test) )
    arcpy.SelectLayerByAttribute_management(feature_select, "NEW_SELECTION", "PIDN = '{}'".format(Test))
    #arcpy.SelectLayerByAttribute_management(feature_select, "NEW_SELECTION", "PIDN = '90000EK007000'")
    count1 = int(arcpy.GetCount_management(feature_select).getOutput(0))
    chance = chance + 1
    if count1 == 0:
        tryagain = 5 - chance
        arcpy.AddError("No features selected! \n Double-check PIDN and try again. \n You have {} more attempts\n".format(tryagain))
    else:
        with arcpy.da.SearchCursor(feature_select, ["PIDN"]) as cursor:
            for row in cursor:
                PIDN.append(str(row[0]))
        break
else:
    arcpy.AddError("\nCan't Identify PIDN after multiple attempts. Quitting the Open Space Grant Program Ranking Tool \n")
    sys.exit()

arcpy.AddMessage("CREATING PROJECT DIRECTORY AND WORKING GDB.....")
message (report,"CREATING PROJECT DIRECTORY AND WORKING GDB.....")

# Set Project Folder
directory = "Project_{}_{}".format(PIDN[0], dateToday2)

# Set Project Path
path = os.path.join(arcpy.env.workspace, directory)

#Creates Project Folder
os.mkdir(path)

# Create Working GDB
arcpy.CreateFileGDB_management(Working_Folder, "WorkingGDB_{}.gdb".format(PIDN[0]))

Working_GDB = os.path.join(Working_Folder, "WorkingGDB_{}.gdb".format(PIDN[0]))

# Create Selected Parcel from Parcel Layer to Working GDB
arcpy.Select_analysis(feature_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])))

arcpy.AddMessage("CREATING BUFFERS.....\n")
message (report,"CREATING BUFFERS.....\n")

# Create 1/2 Mile Buffer Layer from Selected Parcel
arcpy.Buffer_analysis(os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Working_GDB, "ParcelBuffer_{}_HalfMile".format(PIDN[0])), ".5 Mile", "OUTSIDE_ONLY", "ROUND", "LIST", "PIDN", "PLANAR")

# Create Mile Buffer Layer from Selected Parcel
arcpy.Buffer_analysis(os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Working_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])), "1 Mile", "OUTSIDE_ONLY", "ROUND", "LIST", "PIDN", "PLANAR")

#Variable used in below for loop
TName = "Y"

# TName for loop. Set whether want to run Parkland or Natural Area Question
for t in TName:
    Type = raw_input("Want to determine Parkland Question (Y/N)")
    if Type == t:
        Type = "Parkland Question"
    else:
        if Type != t:
            Type = raw_input("Natural Areas Questions (Y/N)")
            if Type == t:
                Type = "Natural Areas Questions"
            else:
                arcpy.AddMessage("\nInput was not 'Y' for either Natural Area or Parkland Question. Try Ranking Tool again\n")

############################################### PARKLAND QUESTION SECTION #################################################################################################

if Type == "Parkland Question":
    arcpy.AddMessage("\nSTARTING PARKLAND QUESTION CRITERIA. PROCESS WILL TAKE APPROX. 2-3 MINUTES TO COMPLETE\n")
    message (report,"\nSTARTING PARKLAND QUESTION CRITERIA. PROCESS WILL TAKE APPROX. 2-3 MINUTES TO COMPLETE\n")
    arcpy.AddMessage("CREATING PROJECT WORKING LAYERS.....")
    message (report,"CREATING PROJECT WORKING LAYERS.....")

    # Create Hydro Named Streams Layer
    arcpy.Select_analysis(Streams, os.path.join(Working_GDB, "Hydro_Streams_Named"), "NAMED = 'YES'")

    # Update Hydro_Named Layer with Steam_Rank Field, Rank Steam Types
    arcpy.AddField_management(os.path.join(Working_GDB, "Hydro_Streams_Named"), "STREAM_RANK", "TEXT", "", "", 1, "STREAM_RANK", "NULLABLE", "")
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Hydro_Streams_Named"), "Hydro_Streams_Named", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "STREAM_TYPE = 'MAJOR'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "1", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "STREAM_TYPE = 'SECONDARY'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "2", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "STREAM_TYPE = 'TRIBUTARY'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "3", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management("Hydro_Streams_Named", "CLEAR_SELECTION")

    # The following inputs are layers or table views: "Hydro_Streams_Named"
    arcpy.Sort_management("Hydro_Streams_Named", os.path.join(Working_GDB, "Hydro_Streams_Sorted"), [["STREAM_RANK", "ASCENDING"]], "UR")

    # Create Zoning Area Layer
    arcpy.Clip_analysis(Zoning, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Working_GDB, "Zoning_Clip"), "")
    arcpy.Dissolve_management(os.path.join(Working_GDB, "Zoning_Clip"), os.path.join(Working_GDB, "Zoning_Dsslv"), "ZNAME", "", "MULTI_PART", "DISSOLVE_LINES")

    # Create Greenway/Focus Area Union Layer
    arcpy.Union_analysis(""+Greenways+";"+Focus_Areas+"", os.path.join(Working_GDB, "FocusArea_Greenway_Union"), "ALL", "", "GAPS")

    # Create Project GDB
    arcpy.AddMessage("CREATING PROJECT GDB AND SCHEMA FOR PARCEL {}.....".format(PIDN[0]))
    message (report,"CREATING PROJECT GDB AND SCHEMA FOR PARCEL {}.....".format(PIDN[0]))
    Project_GDB = os.path.join(path, "Parkland_{}.gdb".format(PIDN[0]))
    arcpy.CreateFileGDB_management(path, "Parkland_{}.gdb".format(PIDN[0]))

    # Creates 1 mile Buffer Layer on Parcel Select
    arcpy.Select_analysis(feature_select, os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])))
    arcpy.Select_analysis(os.path.join(Working_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])), os.path.join(Project_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])))

    # Deletes unneeded fields within Project Parcel Layer
    arcpy.DeleteField_management(os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])),\
    "FEA_CODE;\
    BLOCK;\
    MAP;\
    PARCEL;\
    PARCEL_MAJOR;\
    PARCEL_MINOR;\
    LEASEHD;\
    CREATE_DATE;\
    MODIFY_DATE;\
    EDIT_NAME;\
    EDIT_TYPE;\
    DEED_BK;\
    DEED_PG;\
    SITE_ST_NO;\
    SITE_ST_DIR;\
    SITE_ST_NAME;\
    SITE_ST_SUF;\
    OWN_NAME1;\
    OWN_NAME2;\
    MAIL_ADDR_FULL;\
    MAIL_ADDR1;\
    MAIL_ADDR2;\
    MAIL_ADDR3;\
    PREV_OWNER;\
    STYLE;\
    NUM_STORIE;\
    RES_LIVING_AREA;\
    YRBLT;\
    CLEAN_GREEN;\
    HEATSYS;\
    FUEL;\
    UTILITY;\
    APRLAND;\
    APRBLDG;\
    APRTOTAL;\
    SALEDT;\
    PRICE;\
    PREV_PRICE;\
    SCHOOL_DIS;\
    COMM_STRUC;\
    COMM_YEAR_BUILT;\
    COMM_BUILDING_SQ_FT;\
    GRADE;\
    CDU")

    # List with all fields that need added to Project Parcel Layer
    fieldNames = ["GIS_ACRES", "OPEN_SPACE", "PARKLAND", "PER_PARKLAND", "ZONING", "FOCUS_GREENWAY", "WATER_ACCESS", "TOTAL_SCORE"]

    # for loop on fieldnames list
    for f in fieldNames:
        if f == "GIS_ACRES":
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "DOUBLE", "", "", 50, f, "NULLABLE", "")
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), "GIS_ACRES", "!Shape_Area! / 43560", "PYTHON", "")
        elif f == "PER_PARKLAND":
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "TEXT", "", "", 50, f, "NULLABLE", "")
        elif f == "ZONING":
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "TEXT", "", "", 250, f, "NULLABLE", "")
        else:
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "DOUBLE", "", "", 10, f, "NULLABLE", "")

        del f

    # Create update cursor for feature class
        with arcpy.da.UpdateCursor(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), ["DISTRICT"]) as cursor:
            for row in cursor:
                if (row[0] == "01"):
                    row[0] = "10"
                if (row[0] == "02"):
                    row[0] = "10"
                if (row[0] == "03"):
                    row[0] = "10"
                if (row[0] == "04"):
                    row[0] = "10"
                if (row[0] == "05"):
                    row[0] = "10"
                if (row[0] == "06"):
                    row[0] = "10"
                if (row[0] == "07"):
                    row[0] = "10"
                if (row[0] == "08"):
                    row[0] = "10"
                if (row[0] == "09"):
                    row[0] = "10"
                if (row[0] == "11"):
                    row[0] = "10"
                if (row[0] == "12"):
                    row[0] = "10"
                if (row[0] == "13"):
                    row[0] = "10"
                if (row[0] == "14"):
                    row[0] = "10"
                if (row[0] == "15"):
                    row[0] = "10"

                # Update the cursor with the updated list
                cursor.updateRow(row)

        del row

######################################################### PRESERVED/PROTECTED OPEN SPACE ####################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO PRESERVED/PROTECTED OPEN SPACE.....")
    message (report,"RANKING PROXIMITY TO PRESERVED/PROTECTED OPEN SPACE.....")
    Easement_select = "Easement_select"
    Easement_Check = 'No'
    arcpy.MakeFeatureLayer_management(Cons_Easements, Easement_select, "")
    arcpy.SelectLayerByLocation_management(Easement_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Easement_Count = str(arcpy.GetCount_management(Easement_select)[0])
    #print Easement_Count
    if Easement_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' PRESERVED/PROTECTED ADJACENT TO PROPERTY.....".format(Easement_Count))
        message (report,"\tTHERE ARE \'{}\' PRESERVED/PROTECTED ADJACENT TO PROPERTY.....".format(Easement_Count))
        arcpy.Select_analysis(Easement_select, os.path.join(Project_GDB, "Conservation_Easement"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[1], "\"10\"", "PYTHON", "")
        Easement_Check = 'Yes'

    if Easement_Check == 'No':
        arcpy.SelectLayerByLocation_management(Easement_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), ".5 Mile", "NEW_SELECTION", "NOT_INVERT")
        Easement_Count = str(arcpy.GetCount_management(Easement_select)[0])
        #print Easement_Count
        if Easement_Count >= "1":
            arcpy.AddMessage("\tTHERE ARE \'{}\' PRESERVED/PROTECTED WITHIN 1/2 MILE FROM PROPERTY.....".format(Easement_Count))
            message (report,"\tTHERE ARE \'{}\' PRESERVED/PROTECTED WITHIN 1/2 MILE FROM PROPERTY.....".format(Easement_Count))
            arcpy.Select_analysis(Easement_select, os.path.join(Project_GDB, "Conservation_Easement"))
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[1], "\"5\"", "PYTHON", "")

############################################################### EXISTING PARKLAND ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING PARKLAND.....")
    message (report,"RANKING PROXIMITY TO EXISTING PARKLAND.....")
    parkland_select = "parkland_select"
    Parkland_Check = 'No'
    arcpy.MakeFeatureLayer_management(Parks, parkland_select, "")
    arcpy.SelectLayerByLocation_management(parkland_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Parkland_Count = str(arcpy.GetCount_management(parkland_select)[0])
    #print Parkland_Count
    if Parkland_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' PARKLANDS ADJACENT TO PROPERTY.....".format(Parkland_Count))
        message (report,"\tTHERE ARE \'{}\' PARKLANDS ADJACENT TO PROPERTY.....".format(Parkland_Count))
        arcpy.Select_analysis(parkland_select, os.path.join(Project_GDB, "Parkland"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[2], "\"10\"", "PYTHON", "")
        Parkland_Check = 'Yes'

    if Parkland_Check == 'No':
        arcpy.SelectLayerByLocation_management(parkland_select, "INTERSECT", os.path.join(Working_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])), "", "NEW_SELECTION", "NOT_INVERT")
##        arcpy.SelectLayerByLocation_management(parkland_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "100 Mile", "NEW_SELECTION", "NOT_INVERT")
##        arcpy.SelectLayerByLocation_management(parkland_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "1 Mile", "SWITCH_SELECTION", "NOT_INVERT")
        Parkland_Count = str(arcpy.GetCount_management(parkland_select)[0])
        #print Parkland_Count
        if Parkland_Count == "0":
            arcpy.AddMessage("\tTHERE ARE \'{}\' PARKLANDS OUTSIDE 1 MILE FROM PROPERTY.....".format(Parkland_Count))
            message (report,"\tTHERE ARE \'{}\' PARKLANDS OUTSIDE 1 MILE FROM PROPERTY.....".format(Parkland_Count))
            #arcpy.Select_analysis(parkland_select, os.path.join(Project_GDB, "Parkland"))
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[2], "\"10\"", "PYTHON", "")

############################################################### % OF EXISTING PARKLAND PER CURRENT POPULATION ###########################################################################
    arcpy.AddMessage("RANKING % OF EXISTING PARKLAND PER CURRENT POPULATION.....")
    message (report,"RANKING % OF EXISTING PARKLAND PER CURRENT POPULATION.....")
    Parcel_Select = "Parcel_Select"
    arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])), Parcel_Select, "")

    # Process: Add Join
    arcpy.AddJoin_management(Parcel_Select, "DISTRICT", Park_Acres, "DISTRICT", "KEEP_ALL")
    arcpy.CalculateField_management(Parcel_Select, "Parcel_{}.PER_PARKLAND".format(PIDN[0]), "\"Park Acres per 1,000 residents = \" + str(!ParkAcres_Population.ACRES_1000!)", "PYTHON", "")

    with arcpy.da.SearchCursor(Parcel_Select, ["Parcel_"+PIDN[0]+".PIDN","ParkAcres_Population.MUNI","ParkAcres_Population.POP_2019","ParkAcres_Population.MUNI_ACRES","ParkAcres_Population.PARK_ACRES","ParkAcres_Population.ACRES_1000"]) as cursor:
        for row in cursor:
            file2 = os.path.join(Project_Folder,'Project_{}_{}\Project_{}_{}.txt'.format(PIDN[0],dateToday2,PIDN[0],dateToday2))
            # Open text file in write mode and log results of script
            report2 = open(file2,'w')

            def message2(report,message):
                """ Write a message to a text file
                report is the text file to write the messages to
                report should be defined as report = open(path to file, mode)
                message is the string to write to the file
                """
                timeStamp = time.strftime("%b %d %Y %H:%M:%S")
                #report2.write("{} {} \n \n".format(timeStamp,message))
                report2.write("{} \n \n".format(message))
                print "{}".format(message)

            #arcpy.AddMessage("\nPIDN {} resides in {}. The Census estimates there is {} people living in the district.\n\ The District has a total of {} acres.\n\ Out of the total acres, {} acres resides in a Park giving a Population/Park Ratio of {}\n".format(row[0],row[1],round(row[2]),round(row[3]),round(row[4], 2),round(row[5], 2)))
            message2 (report2,"\nPIDN {} resides in {}. The Census estimates there is {} people living in the district.\n\
The District has a total of {} acres. Out of the total acres, {} acres resides in a Park giving\n\
a Population/Park Ratio of {}\n".format(row[0],row[1],round(row[2]),round(row[3]),round(row[4], 2),round(row[5], 2)))

            report2.close()

    arcpy.RemoveJoin_management(Parcel_Select)

############################################################### ZONING SECTION ###########################################################################

    arcpy.AddMessage("ZONING INFORMATION FOR {}.....".format(PIDN[0]))
    message (report,"ZONING INFORMATION FOR {}.....".format(PIDN[0]))
    zoning_select = "zoning_select"
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Zoning_Dsslv"), zoning_select, "")
    Zoning_Count = str(arcpy.GetCount_management(zoning_select)[0])

    if Zoning_Count == "1":
        with arcpy.da.SearchCursor(zoning_select, ["ZNAME"]) as cursor:
            for row in cursor:
                    arcpy.AddMessage("\tCALCULATING ZONING INFORMATION.....")
                    message (report,"\tCALCULATING ZONING INFORMATION.....")
                    zoning_str = str(row[0])
                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[4], "\"{}\"".format(zoning_str), "PYTHON", "")
                    arcpy.Select_analysis(zoning_select, os.path.join(Project_GDB, "Zoning_Clip"))

    if Zoning_Count > "1":
                zoning_name = []
                with arcpy.da.SearchCursor(zoning_select, ["ZNAME"]) as cursor:
                    for row in cursor:
                        arcpy.AddMessage("\tCALCULATING ZONING INFORMATION.....")
                        message (report,"\tCALCULATING ZONING INFORMATION.....")
                        #zoning_str = str(row[0])
                        zoning_name.append(row[0])

                zoning_list = '/'.join(zoning_name)
                arcpy.AddMessage("\t{}.....".format(zoning_list))
                arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[4], "\"{}\"".format(zoning_list[:250]), "PYTHON", "")

                arcpy.Select_analysis(zoning_select, os.path.join(Project_GDB, "Zoning_Clip"))

############################################################### LAND LOCATED IN FOCUS AREA OR GREENWAY ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO FOCUS AREAS/GREENWAYS.....")
    message (report,"RANKING PROXIMITY TO FOCUS AREAS/GREENWAYS.....")
    focus_select = "focus_select"
    Focus_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "FocusArea_Greenway_Union"), focus_select, "")
    arcpy.SelectLayerByLocation_management(focus_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Focus_Count = str(arcpy.GetCount_management(focus_select)[0])
    #print Focus_Count

    if Focus_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' FOCUS AREA/GREENWAY ADJACENT TO PROPERTY.....".format(Focus_Count))
        message (report,"\tTHERE ARE \'{}\' FOCUS AREA/GREENWAY ADJACENT TO PROPERTY.....".format(Focus_Count))
        with arcpy.da.SearchCursor(focus_select, ["FID_PLANNING_Focus_Areas","FID_PLANNING_Greenways"]) as cursor:
            for row in cursor:
                if (row[0] >= 0):
                    arcpy.AddMessage("\tPIDN IS WITHIN FOCUS AREA.....")
                    message (report,"\tPIDN IS WITHIN FOCUS AREA.....")
                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[5], "\"10\"", "PYTHON", "")
                    arcpy.Select_analysis(focus_select, os.path.join(Project_GDB, "Focus_Greenway"))
                    Focus_Check = 'Yes'
                if (row[1] >= 0):
                    arcpy.AddMessage("\tPIDN IS WITHIN GREENWAY.....")
                    message (report,"\tPIDN IS WITHIN GREENWAY.....")
                    if arcpy.Exists(os.path.join(Project_GDB, "Focus_Greenway")):
                        pass
                    else:
                        arcpy.Select_analysis(focus_select, os.path.join(Project_GDB, "Focus_Greenway"))

                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[5], "!"+fieldNames[4]+"! + 7", "PYTHON", "")
                    Focus_Check = 'Yes'


    if Focus_Check == 'No':
        arcpy.SelectLayerByLocation_management(focus_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), ".25 Mile", "NEW_SELECTION", "NOT_INVERT")
        Focus_Count = str(arcpy.GetCount_management(focus_select)[0])
        #print Focus_Count
        if Focus_Count >= "1":
            arcpy.AddMessage("\tTHERE ARE \'{}\' FOCUS AREAS/GREENWAYS WITHIN 1/4 MILE FROM PROPERTY.....".format(Focus_Count))
            message (report,"\tTHERE ARE \'{}\' FOCUS AREAS/GREENWAYS WITHIN 1/4 MILE FROM PROPERTY.....".format(Focus_Count))
            arcpy.Select_analysis(focus_select, os.path.join(Project_GDB, "Focus_Greenway"))
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[5], "\"5\"", "PYTHON", "")


############################################################### LAND ADJACENCY/ACCESS TO RIVER OR STREAM ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO RIVER OR STREAMS.....")
    message (report,"RANKING PROXIMITY TO RIVER OR STREAMS.....")
    hydro_select = "hydro_select"
    Hydro_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Hydro_Streams_Sorted"), hydro_select, "")
    arcpy.SelectLayerByLocation_management(hydro_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Hydro_Count = str(arcpy.GetCount_management(hydro_select)[0])
    #print Hydro_Count

    if Hydro_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' NAMED STREAM ADJACENT TO PROPERTY.....".format(Hydro_Count))
        message (report,"\tTHERE ARE \'{}\' NAMED STREAM ADJACENT TO PROPERTY.....".format(Hydro_Count))
        with arcpy.da.SearchCursor(hydro_select, ["STREAM_TYPE"]) as cursor:
            for row in cursor:
                if Hydro_Check == 'No':
                    if row[0] == 'MAJOR':
                        arcpy.AddMessage("\tPROPERTY HAS ACCESS TO MAJOR STREAM.....")
                        message (report,"\tPROPERTY HAS ACCESS TO MAJOR STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"5\"", "PYTHON", "")
                        arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "Hydro_Clip"), "")
                        Hydro_Check = 'Yes'

                if Hydro_Check == 'No':
                    if row[0] == 'SECONDARY':
                        arcpy.AddMessage("\tPROPERTY HAS ACCESS TO SECONDARY STREAM.....")
                        message (report,"\tPROPERTY HAS ACCESS TO SECONDARY STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"3\"", "PYTHON", "")
                        arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "Hydro_Clip"), "")
                        Hydro_Check = 'Yes'


############################################################### CLEANUP/FINISHING STEPS FOR PARKLAND QUESTION ###########################################################################
    arcpy.AddMessage("CLEANUP/FINISHING STEPS FOR PARKLAND QUESTION.....")
    message (report,"CLEANUP/FINISHING STEPS FOR PARKLAND QUESTION.....")

    with arcpy.da.UpdateCursor(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames) as cursor:
        for row in cursor:
            if (row[1] == None):
                row[1] = "0"
            if (row[2] == None):
                row[2] = "0"
            if (row[3] == None):
                row[3] = "N/A"
            if (row[5] == None):
                row[5] = "0"
            if (row[6] == None):
                row[6] = "0"

            # Update the cursor with the updated list
            cursor.updateRow(row)

        del row

    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[7], "!"+fieldNames[1]+"! + !"+fieldNames[2]+"! + !"+fieldNames[5]+"! + !"+fieldNames[6]+"!", "PYTHON", "")

############################################################### CREATING PARKLAND PROJECT MXD ###########################################################################

    arcpy.AddMessage("CREATING PROJECT MXD.....")
    message (report,"CREATING PROJECT MXD.....")
    mxd = arcpy.mapping.MapDocument(os.path.join(arcpy.env.workspace, "OpenSpace_Template" + ".mxd"))
    for df in arcpy.mapping.ListDataFrames(mxd):
        mxd.activeView = df.name
        mxd.title = df.name

        arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])), "ParcelBuffer_{}".format(PIDN[0]))
        Project_PIDNBuffer = arcpy.mapping.Layer("ParcelBuffer_{}".format(PIDN[0]))
        arcpy.mapping.AddLayer(df, Project_PIDNBuffer, "AUTO_ARRANGE")
        for lyr in arcpy.mapping.ListLayers(mxd, "ParcelBuffer_{}".format(PIDN[0]), df):
            if lyr.name == "ParcelBuffer_{}".format(PIDN[0]):
                lyr.visible = False
                lyr.transparency = 50
                #symbologyLayer = os.path.join(Layer_Folder,"Selected_Parcel.lyr")
                #arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Conservation_Easement")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Conservation_Easement"), "Conservation_Easement")
            Project_Consv = arcpy.mapping.Layer("Conservation_Easement")
            arcpy.mapping.AddLayer(df, Project_Consv, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Conservation_Easement", df):
                if lyr.name == "Conservation_Easement":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Conservation Easements.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Conservation Easements.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Parkland")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Parkland"), "Parkland")
            Project_Parkland = arcpy.mapping.Layer("Parkland")
            arcpy.mapping.AddLayer(df, Project_Parkland, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Parkland", df):
                if lyr.name == "Parkland":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Parks By Type.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Parks By Type.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Zoning_Clip")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Zoning_Clip"), "Zoning_Clip")
            Project_Zoning = arcpy.mapping.Layer("Zoning_Clip")
            arcpy.mapping.AddLayer(df, Project_Zoning, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Zoning_Clip", df):
                if lyr.name == "Zoning_Clip":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(os.path.join(Layer_Folder, "Zoning"),"Generalized Zoning Classifications.lyr")):
                        symbologyLayer = os.path.join(os.path.join(Layer_Folder, "Zoning"),"Generalized Zoning Classifications.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Focus_Greenway")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Focus_Greenway"), "Focus_Greenway")
            Project_Focus = arcpy.mapping.Layer("Focus_Greenway")
            arcpy.mapping.AddLayer(df, Project_Focus, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Focus_Greenway", df):
                if lyr.name == "Focus_Greenway":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Focus_Greenway.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Focus_Greenway.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Hydro_Clip")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Hydro_Clip"), "Hydro_Clip")
            Project_Hydro = arcpy.mapping.Layer("Hydro_Clip")
            arcpy.mapping.AddLayer(df, Project_Hydro, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Hydro_Clip", df):
                if lyr.name == "Hydro_Clip":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(Layer_Folder,"Streams.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Streams.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])), "Parcel_{}".format(PIDN[0]))
        Project_PIDN = arcpy.mapping.Layer("Parcel_{}".format(PIDN[0]))
        arcpy.mapping.AddLayer(df, Project_PIDN, "TOP")
        for lyr in arcpy.mapping.ListLayers(mxd, "Parcel_{}".format(PIDN[0]), df):
            if lyr.name == "Parcel_{}".format(PIDN[0]):
                lyr.visible = True
                lyr.transparency = 0
                symbologyLayer = os.path.join(Layer_Folder,"Selected_Parcel.lyr")
                arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        mxd.saveACopy(os.path.join(path, "ParklandRanking_" + PIDN[0] + ".mxd"))

    del mxd

    mxd2 = arcpy.mapping.MapDocument(os.path.join(path, "ParklandRanking_" + PIDN[0] + ".mxd"))
    dataFrame = arcpy.mapping.ListDataFrames(mxd2)[0] # the first data frame
    MapLayers = arcpy.mapping.ListLayers(mxd2,"ParcelBuffer*",dataFrame)
    Layer = MapLayers[0]
    Layer.definitionQuery = "PIDN = '{}'".format(PIDN[0])
    Extent = Layer.getExtent(True) # visible extent of layer of

    dataFrame.extent = Extent
    arcpy.RefreshActiveView() # redraw the map
    mxd2.save()

    arcpy.AddMessage("CREATING PROJECT PDFS.....")
    message (report,"CREATING PROJECT PDFS.....")

    file_url = "https://arcweb.ycpc.org/PDFPrint/TaxParcel_{}00000.pdf".format(PIDN[0])

    r = requests.get(file_url, stream = True)

    with open(os.path.join(Project_Folder,'Project_{}_{}\TaxParcel_{}00000.pdf'.format(PIDN[0],dateToday2,PIDN[0])),"wb") as pdf:
        for chunk in r.iter_content(chunk_size=1024):

            # writing one chunk at a time to pdf file
            if chunk:
                pdf.write(chunk)

    # Create update cursor for feature class
    with arcpy.da.SearchCursor(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames) as cursor:
        for row in cursor:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 30)
            pdf.cell(200,10, txt = "PARCEL NUMBER: {}".format(PIDN[0]), ln = 1, align = 'L')
            pdf.cell(200,10, txt = "", ln =2, align = 'L')
            pdf.set_font("Arial", 'U', size = 15)
            pdf.cell(200,10, txt = "PARKLAND AREA CRITERIA", ln = 3, align = 'L')
            pdf.set_font("Arial", size = 15)
            pdf.cell(200,10, txt = "GIS ACRES = {}".format(round(row[0], 2)), ln = 3, align = 'L')
            pdf.cell(200,10, txt = "OPEN SPACE = {}".format(round(row[1])), ln = 4, align = 'L')
            pdf.cell(200,10, txt = "PARKLAND = {}".format(round(row[2])), ln = 5, align = 'L')
            pdf.cell(200,10, txt = "PER PARKLAND = {}".format(row[3]), ln = 6, align = 'L')
            pdf.cell(200,10, txt = "ZONING = {}".format(row[4]), ln = 7, align = 'L')
            pdf.cell(200,10, txt = "FOCUS/GREENWAY = {}".format(round(row[5])), ln = 8, align = 'L')
            pdf.cell(200,10, txt = "WATER ACCESS = {}".format(round(row[6])), ln = 9, align = 'L')
            pdf.cell(200,10, txt = "TOTAL SCORE = {}".format(round(row[7])), ln = 10, align = 'L')
            pdf.output(os.path.join(path,"Parcel_{}_ParkLand_ScoreTable.pdf".format(PIDN[0])))


    os.startfile(os.path.join(path, "TaxParcel_{}00000.pdf".format(PIDN[0])))
    os.startfile(os.path.join(path, "Parcel_{}_ParkLand_ScoreTable.pdf".format(PIDN[0])))

    try:
        os.startfile(os.path.join(path, "ParklandRanking_" + PIDN[0] + ".mxd"))
    except:
        pass

    del mxd2


############################################### NATURAL AREAS QUESTION SECTION #################################################################################################

if Type == "Natural Areas Questions":
    arcpy.AddMessage("\nSTARTING NATURAL AREAS QUESTION CRITERIA. PROCESS WILL TAKE APPROX. 5-6 MINUTES TO COMPLETE\n")
    message (report,"\nSTARTING NATURAL AREAS QUESTION CRITERIA. PROCESS WILL TAKE APPROX. 5-6 MINUTES TO COMPLETE\n")

    arcpy.AddMessage("CREATING PROJECT WORKING LAYERS.....")
    message (report,"CREATING PROJECT WORKING LAYERS.....")
    # Create Unique Geology Buffer Layer
    arcpy.Buffer_analysis(os.path.join(Unique_Geology), os.path.join(Working_GDB, "UniqueGeology_100FTBuffer"), "100 FEET", "FULL", "ROUND", "ALL")
    # Create Hydric Soils Layer
    arcpy.Select_analysis(Soils, os.path.join(Working_GDB, "Hydric_Soils"), "HYDRCRATNG = 'ALL HYDRIC' OR HYDRCRATNG = 'PARTIALLY HYDRIC'" )
    # Create Steep Slopes Layer
    arcpy.Select_analysis(Soils, os.path.join(Working_GDB, "Steep_Slopes"), "REP_SLOPE >= '25'")
    # Create 100yr Floodplains
    arcpy.Select_analysis(Floodplains, os.path.join(Working_GDB, "Floodplains_100yrs"), "FLD_ZONE = 'A' OR FLD_ZONE = 'AE'")
    # Create Forested Layer
    arcpy.Select_analysis(Landcover, os.path.join(Working_GDB, "Forested_Area"), "LC_CODE = '410' OR LC_CODE = '411' OR LC_CODE = '420' OR LC_CODE = '421' OR LC_CODE = '430' OR LC_CODE = '431'")
    # Create Greenway/Focus Area Union Layer
    arcpy.Union_analysis(""+Greenways+";"+Focus_Areas+"", os.path.join(Working_GDB, "FocusArea_Greenway_Union"), "ALL", "", "GAPS")
    # Create Greenway/Focus Area Union Layer
    arcpy.Union_analysis(""+Wetlands+";"+os.path.join(Working_GDB,"Hydric_Soils")+"", os.path.join(Working_GDB, "Wetland_SoilHydric_Union"), "ALL", "", "GAPS")
    # Create Zoning Area Layer
    arcpy.Clip_analysis(Zoning, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Working_GDB, "Zoning_Clip"), "")
    arcpy.Dissolve_management(os.path.join(Working_GDB, "Zoning_Clip"), os.path.join(Working_GDB, "Zoning_Dsslv"), "ZNAME", "", "MULTI_PART", "DISSOLVE_LINES")

    # Execute Delete
    arcpy.Delete_management(os.path.join(Working_GDB, "Hydric_Soils"))

    # Create Hydro Named Streams Layer
    arcpy.Select_analysis(Streams, os.path.join(Working_GDB, "Hydro_Streams_Named"), "NAMED = 'YES'")

    # Update Hydro_Named Layer with Steam_Rank Field, Rank Destinated Uses
    arcpy.AddField_management(os.path.join(Working_GDB, "Hydro_Streams_Named"), "STREAM_RANK", "TEXT", "", "", 1, "STREAM_RANK", "NULLABLE", "")
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Hydro_Streams_Named"), "Hydro_Streams_Named", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "DES_USE = 'EV'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "1", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "DES_USE = 'HQ-CWF'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "2", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "DES_USE = 'CWF'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "3", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "DES_USE = 'TSF'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "4", "PYTHON", "")
    arcpy.SelectLayerByAttribute_management ("Hydro_Streams_Named", "NEW_SELECTION", "DES_USE = 'WWF'")
    arcpy.CalculateField_management("Hydro_Streams_Named", "STREAM_RANK", "5", "PYTHON", "")

    arcpy.SelectLayerByAttribute_management("Hydro_Streams_Named", "CLEAR_SELECTION")

    # The following inputs are layers or table views: "Hydro_Streams_Named"
    arcpy.Sort_management("Hydro_Streams_Named", os.path.join(Working_GDB, "Hydro_Streams_Sorted"), [["STREAM_RANK", "ASCENDING"]], "UR")

    # Create Project GDB
    arcpy.AddMessage("CREATING PROJECT GDB AND SCHEMA FOR PARCEL {}.....".format(PIDN[0]))
    message (report,"CREATING PROJECT GDB AND SCHEMA FOR PARCEL {}.....".format(PIDN[0]))
    Project_GDB = os.path.join(path, "NaturalArea_{}.gdb".format(PIDN[0]))
    arcpy.CreateFileGDB_management(path, "NaturalArea_{}.gdb".format(PIDN[0]))

    arcpy.Select_analysis(feature_select, os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])))
    arcpy.Select_analysis(os.path.join(Working_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])), os.path.join(Project_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])))

    arcpy.DeleteField_management(os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])),\
    "FEA_CODE;\
    BLOCK;\
    MAP;\
    PARCEL;\
    PARCEL_MAJOR;\
    PARCEL_MINOR;\
    LEASEHD;\
    CREATE_DATE;\
    MODIFY_DATE;\
    EDIT_NAME;\
    EDIT_TYPE;\
    DEED_BK;\
    DEED_PG;\
    SITE_ST_NO;\
    SITE_ST_DIR;\
    SITE_ST_NAME;\
    SITE_ST_SUF;\
    OWN_NAME1;\
    OWN_NAME2;\
    MAIL_ADDR_FULL;\
    MAIL_ADDR1;\
    MAIL_ADDR2;\
    MAIL_ADDR3;\
    PREV_OWNER;\
    STYLE;\
    NUM_STORIE;\
    RES_LIVING_AREA;\
    YRBLT;\
    CLEAN_GREEN;\
    HEATSYS;\
    FUEL;\
    UTILITY;\
    APRLAND;\
    APRBLDG;\
    APRTOTAL;\
    SALEDT;\
    PRICE;\
    PREV_PRICE;\
    SCHOOL_DIS;\
    COMM_STRUC;\
    COMM_YEAR_BUILT;\
    COMM_BUILDING_SQ_FT;\
    GRADE;\
    CDU")

    fieldNames = ["GIS_ACRES", "ZONING", "OPEN_SPACE", "FOCUS_GREENWAY", "NAI", "UNIQUE_GEO", "QUALITY_STREAM", "IMPAIRED_STREAM", "FORESTED", "WETLAND_HYDRIC", "FLOOD_100", "BIRD_AREA", "WELLHEAD", "STEEP_SLOPE", "TOTAL_SCORE"]

    for f in fieldNames:
        if f == "GIS_ACRES":
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "DOUBLE", "", "", 50, f, "NULLABLE", "")
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), "GIS_ACRES", "!Shape_Area! / 43560", "PYTHON", "")
        elif f == "ZONING":
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "TEXT", "", "", 250, f, "NULLABLE", "")
        else:
            arcpy.AddField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), f, "DOUBLE", "", "", 10, f, "NULLABLE", "")

        del f

############################################################### ZONING SECTION ###########################################################################

    arcpy.AddMessage("ZONING INFORMATION FOR {}.....".format(PIDN[0]))
    message (report,"ZONING INFORMATION FOR {}.....".format(PIDN[0]))
    zoning_select = "zoning_select"
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Zoning_Dsslv"), zoning_select, "")
    Zoning_Count = str(arcpy.GetCount_management(zoning_select)[0])

    if Zoning_Count == "1":
        with arcpy.da.SearchCursor(zoning_select, ["ZNAME"]) as cursor:
            for row in cursor:
                    arcpy.AddMessage("\tCALCULATING ZONING INFORMATION.....")
                    message (report,"\tCALCULATING ZONING INFORMATION.....")
                    zoning_str = str(row[0])
                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[1], "\"{}\"".format(zoning_str), "PYTHON", "") ####"\"{}\"".format(str(row[0]))
                    arcpy.Select_analysis(zoning_select, os.path.join(Project_GDB, "Zoning_Clip"))

    if Zoning_Count > "1":
                zoning_name = []
                with arcpy.da.SearchCursor(zoning_select, ["ZNAME"]) as cursor:
                    for row in cursor:
                        #arcpy.AddMessage("\tCALCULATING ZONING INFORMATION.....")
                        #message (report,"\tCALCULATING ZONING INFORMATION.....")
                        #zoning_str = str(row[0])
                        zoning_name.append(row[0])

                zoning_list = '/'.join(zoning_name)
                arcpy.AddMessage("\tMULTIPLE ZONING LAYERS DETECTED: {}.....".format(zoning_list))
                message (report,"\tMULTIPLE ZONING LAYERS DETECTED: {}.....".format(zoning_list))
                arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[1], "\"{}\"".format(zoning_list[:250]), "PYTHON", "")

                arcpy.Select_analysis(zoning_select, os.path.join(Project_GDB, "Zoning_Clip"))


######################################################### PRESERVED/PROTECTED OPEN SPACE ####################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO PRESERVED/PROTECTED OPEN SPACE.....")
    message (report,"RANKING PROXIMITY TO PRESERVED/PROTECTED OPEN SPACE.....")
    Easement_select = "Easement_select"
    Easement_Check = 'No'
    arcpy.MakeFeatureLayer_management(Cons_Easements, Easement_select, "")
    arcpy.SelectLayerByLocation_management(Easement_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Easement_Count = str(arcpy.GetCount_management(Easement_select)[0])
    #print Easement_Count
    if Easement_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' PRESERVED/PROTECTED ADJACENT TO PROPERTY.....".format(Easement_Count))
        message (report,"\tTHERE ARE \'{}\' PRESERVED/PROTECTED ADJACENT TO PROPERTY.....".format(Easement_Count))
        arcpy.Select_analysis(Easement_select, os.path.join(Project_GDB, "Conservation_Easement"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[2], "\"10\"", "PYTHON", "")
        Easement_Check = 'Yes'

    if Easement_Check == 'No':
        arcpy.SelectLayerByLocation_management(Easement_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), ".5 Mile", "NEW_SELECTION", "NOT_INVERT")
        Easement_Count = str(arcpy.GetCount_management(Easement_select)[0])
        #print Easement_Count
        if Easement_Count >= "1":
            arcpy.AddMessage("\tTHERE ARE \'{}\' PRESERVED/PROTECTED WITHIN 1/2 MILE FROM PROPERTY.....".format(Easement_Count))
            message (report,"\tTHERE ARE \'{}\' PRESERVED/PROTECTED WITHIN 1/2 MILE FROM PROPERTY.....".format(Easement_Count))
            arcpy.Select_analysis(Easement_select, os.path.join(Project_GDB, "Conservation_Easement"))
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[2], "\"5\"", "PYTHON", "")

############################################################### LAND LOCATED IN FOCUS AREA OR GREENWAY ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO FOCUS AREAS/GREENWAYS.....")
    message (report,"RANKING PROXIMITY TO FOCUS AREAS/GREENWAYS.....")
    focus_select = "focus_select"
    Focus_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "FocusArea_Greenway_Union"), focus_select, "")
    arcpy.SelectLayerByLocation_management(focus_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Focus_Count = str(arcpy.GetCount_management(focus_select)[0])
    #print Focus_Count

    if Focus_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' FOCUS AREA/GREENWAY ADJACENT TO PROPERTY.....".format(Focus_Count))
        message (report,"\tTHERE ARE \'{}\' FOCUS AREA/GREENWAY ADJACENT TO PROPERTY.....".format(Focus_Count))
        with arcpy.da.SearchCursor(focus_select, ["FID_PLANNING_Focus_Areas","FID_PLANNING_Greenways"]) as cursor:
            for row in cursor:
                if (row[0] >= 0):
                    arcpy.AddMessage("\tPIDN IS WITHIN FOCUS AREA.....")
                    message (report,"\tPIDN IS WITHIN FOCUS AREA.....")
                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[3], "\"10\"", "PYTHON", "")
                    arcpy.Select_analysis(focus_select, os.path.join(Project_GDB, "Focus_Greenway"))
                    Focus_Check = 'Yes'
                if (row[1] >= 0):
                    arcpy.AddMessage("\tPIDN IS WITHIN GREENWAY.....")
                    message (report,"\tPIDN IS WITHIN GREENWAY.....")
                    if arcpy.Exists(os.path.join(Project_GDB, "Focus_Greenway")):
                        pass
                    else:
                        arcpy.Select_analysis(focus_select, os.path.join(Project_GDB, "Focus_Greenway"))

                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[3], "!"+fieldNames[2]+"! + 7", "PYTHON", "")
                    Focus_Check = 'Yes'

    if Focus_Check == 'No':
        arcpy.SelectLayerByLocation_management(focus_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), ".25 Mile", "NEW_SELECTION", "NOT_INVERT")
        Focus_Count = str(arcpy.GetCount_management(focus_select)[0])
        #print Focus_Count
        if Focus_Count >= "1":
            arcpy.AddMessage("\tTHERE ARE \'{}\' FOCUS AREAS/GREENWAYS WITHIN 1/4 MILE FROM PROPERTY.....".format(Focus_Count))
            message (report,"\tTHERE ARE \'{}\' FOCUS AREAS/GREENWAYS WITHIN 1/4 MILE FROM PROPERTY.....".format(Focus_Count))
            arcpy.Select_analysis(focus_select, os.path.join(Project_GDB, "Focus_Greenway"))
            arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[3], "\"5\"", "PYTHON", "")

############################################################### EXISTING NATURAL AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING NATURAL AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING NATURAL AREAS.....")
    nai_select = "nai_select"
    NAI_Check = 'No'
    arcpy.MakeFeatureLayer_management(NAI_Area, nai_select, "")
    arcpy.SelectLayerByLocation_management(nai_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    NAI_Count = str(arcpy.GetCount_management(nai_select)[0])
    #print NAI_Count
    if NAI_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' NATURAL AREAS ADJACENT TO PROPERTY.....".format(NAI_Count))
        message (report,"\tTHERE ARE \'{}\' NATURAL AREAS ADJACENT TO PROPERTY.....".format(NAI_Count))
        arcpy.Select_analysis(nai_select, os.path.join(Project_GDB, "Natural_Area"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[4], "\"10\"", "PYTHON", "")
        NAI_Check = 'Yes'

############################################################### EXISTING GEOLOGIC FEATURE ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING GEOLOGIC FEATURE.....")
    message (report,"RANKING PROXIMITY TO EXISTING GEOLOGIC FEATURE.....")
    geo_select = "geo_select"
    GEO_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "UniqueGeology_100FTBuffer"), geo_select, "")
    arcpy.SelectLayerByLocation_management(geo_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    GEO_Count = str(arcpy.GetCount_management(geo_select)[0])
    #print GEO_Count
    if GEO_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' GEOLOGIC FEATURE ADJACENT TO PROPERTY.....".format(GEO_Count))
        message (report,"\tTHERE ARE \'{}\' GEOLOGIC FEATURE ADJACENT TO PROPERTY.....".format(GEO_Count))
        arcpy.Select_analysis(geo_select, os.path.join(Project_GDB, "Geologic_Feature"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[5], "\"10\"", "PYTHON", "")
        GEO_Check = 'Yes'

############################################################### EXISTING HIGH QUALITY STREAM ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING HIGH QUALITY STREAM.....")
    message (report,"RANKING PROXIMITY TO EXISTING HIGH QUALITY STREAM.....")
    quality_select = "quality_select"
    Quality_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Hydro_Streams_Sorted"), quality_select, "")
    arcpy.SelectLayerByLocation_management(quality_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Quality_Count = str(arcpy.GetCount_management(quality_select)[0])
    #print Quality_Count

    if Quality_Count >= "1":
        #arcpy.AddMessage("\tTHERE ARE \'{}\' NAMED STREAM ADJACENT TO PROPERTY.....".format(Hydro_Count))
        with arcpy.da.SearchCursor(quality_select, ["DES_USE"]) as cursor:
            for row in cursor:
                if Quality_Check == 'No':
                    if row[0] == 'EV':
                        arcpy.AddMessage("\tPROPERTY IS ADJACENT TO EXCEPTIONAL VALUE DESTINATED STREAM.....")
                        message (report,"\tPROPERTY IS ADJACENT TO EXCEPTIONAL VALUE DESTINATED STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"10\"", "PYTHON", "")
                        arcpy.Select_analysis(quality_select, os.path.join(Project_GDB, "HighQuality_Stream"))
                        Quality_Check = 'Yes'
                if Quality_Check == 'No':
                    if row[0] == 'HQ-CWF':
                        arcpy.AddMessage("\tPROPERTY IS ADJACENT TO HIGH QUALITY DESTINATED STREAM.....")
                        message (report,"\tPROPERTY IS ADJACENT TO HIGH QUALITY DESTINATED STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"8\"", "PYTHON", "")
                        arcpy.Select_analysis(quality_select, os.path.join(Project_GDB, "HighQuality_Stream"))
                        #arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "ImpairedHYDRO_Clip"), "")
                        Quality_Check = 'Yes'
                if Quality_Check == 'No':
                    if row[0] == 'CWF':
                        arcpy.AddMessage("\tPROPERTY IS ADJACENT TO COLD WATER FISHERY DESTINATED STREAM.....")
                        message (report,"\tPROPERTY IS ADJACENT TO COLD WATER FISHERY DESTINATED STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"5\"", "PYTHON", "")
                        arcpy.Select_analysis(quality_select, os.path.join(Project_GDB, "HighQuality_Stream"))
                        #arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "ImpairedHYDRO_Clip"), "")
                        Quality_Check = 'Yes'
                if Quality_Check == 'No':
                    if row[0] == 'TSF':
                        arcpy.AddMessage("\tPROPERTY IS ADJACENT TO TROUT STOCKED FISHERY DESTINATED STREAM.....")
                        message (report,"\tPROPERTY IS ADJACENT TO TROUT STOCKED FISHERY DESTINATED STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"3\"", "PYTHON", "")
                        arcpy.Select_analysis(quality_select, os.path.join(Project_GDB, "HighQuality_Stream"))
                        #arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "ImpairedHYDRO_Clip"), "")
                        Quality_Check = 'Yes'
                if Quality_Check == 'No':
                    if row[0] == 'WWF':
                        arcpy.AddMessage("\tPROPERTY IS ADJACENT TO WARM WATER FISHERY DESTINATED STREAM.....")
                        message (report,"\tPROPERTY IS ADJACENT TO WARM WATER FISHERY DESTINATED STREAM.....")
                        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[6], "\"1\"", "PYTHON", "")
                        arcpy.Select_analysis(quality_select, os.path.join(Project_GDB, "HighQuality_Stream"))
                        #arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "ImpairedHYDRO_Clip"), "")
                        Quality_Check = 'Yes'

############################################################### EXISTING IMPAIRED STREAM ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING IMPAIRED STREAM.....")
    message (report,"RANKING PROXIMITY TO EXISTING IMPAIRED STREAM.....")
    impaired_select = "impaired_select"
    Impaired_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Hydro_Streams_Named"), impaired_select, "")
    arcpy.SelectLayerByLocation_management(impaired_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    Impaired_Count = str(arcpy.GetCount_management(impaired_select)[0])
    #print Impaired_Count

    if Impaired_Count >= "1":
        #arcpy.AddMessage("\tTHERE ARE \'{}\' NAMED STREAM ADJACENT TO PROPERTY.....".format(Hydro_Count))
        with arcpy.da.SearchCursor(impaired_select, ["IMPAIRED"]) as cursor:
            for row in cursor:
                if row[0] == 'Impaired':
                    arcpy.AddMessage("\tPROPERTY IS LEAST ADJACENT TO 1 IMPAIRED STREAM.....")
                    message (report,"\tPROPERTY IS LEAST ADJACENT TO 1 IMPAIRED STREAM.....")
                    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[7], "\"10\"", "PYTHON", "")
                    arcpy.Select_analysis(impaired_select, os.path.join(Project_GDB, "Impaired_Stream"))
                    #arcpy.Clip_analysis(hydro_select, os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), os.path.join(Project_GDB, "ImpairedHYDRO_Clip"), "")

                break

############################################################### EXISTING FORESTED AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING FORESTED AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING FORESTED AREAS.....")
    forest_select = "forest_select"
    Forest_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Forested_Area"), forest_select, "")
    arcpy.SelectLayerByLocation_management(forest_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    FOREST_Count = str(arcpy.GetCount_management(forest_select)[0])
    #print FOREST_Count
    if FOREST_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' FOREST AREAS ADJACENT TO PROPERTY.....".format(FOREST_Count))
        message (report,"\tTHERE ARE \'{}\' FOREST AREAS ADJACENT TO PROPERTY.....".format(FOREST_Count))
        arcpy.Select_analysis(forest_select, os.path.join(Project_GDB, "Forested_Area"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[8], "\"10\"", "PYTHON", "")
        Forest_Check = 'Yes'

############################################################### EXISTING WETLANDS/HYDRIC SOIL AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING WETLANDS/HYDRIC SOIL AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING WETLANDS/HYDRIC SOIL AREAS.....")
    hydric_select = "hydric_select"
    Hydric_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Wetland_SoilHydric_Union"), hydric_select, "")
    arcpy.SelectLayerByLocation_management(hydric_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    HYDRIC_Count = str(arcpy.GetCount_management(hydric_select)[0])
    #print HYDRIC_Count
    if HYDRIC_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' WETLANDS/HYDRIC SOILS ADJACENT TO PROPERTY.....".format(HYDRIC_Count))
        message (report,"\tTHERE ARE \'{}\' WETLANDS/HYDRIC SOILS ADJACENT TO PROPERTY.....".format(HYDRIC_Count))
        arcpy.Select_analysis(hydric_select, os.path.join(Project_GDB, "HydricSoils_Wetlands"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[9], "\"10\"", "PYTHON", "")
        Hydric_Check = 'Yes'

############################################################### EXISTING 100YR FLOODPLAIN AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING 100YR FLOODPLAIN AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING 100YR FLOODPLAIN AREAS.....")
    flood_select = "flood_select"
    Flood_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Floodplains_100yrs"), flood_select, "")
    arcpy.SelectLayerByLocation_management(flood_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    FLOOD_Count = str(arcpy.GetCount_management(flood_select)[0])
    #print FLOOD_Count
    if FLOOD_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' 100YR FLOODPLAIN ADJACENT TO PROPERTY.....".format(FLOOD_Count))
        message (report,"\tTHERE ARE \'{}\' 100YR FLOODPLAIN ADJACENT TO PROPERTY.....".format(FLOOD_Count))
        arcpy.Select_analysis(flood_select, os.path.join(Project_GDB, "Floodplains_100yrs"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[10], "\"3\"", "PYTHON", "")
        Flood_Check = 'Yes'

############################################################### EXISTING IMPORTANT BIRDING AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING IMPORTANT BIRDING AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING IMPORTANT BIRDING AREAS.....")
    bird_select = "bird_select"
    Bird_Check = 'No'
    arcpy.MakeFeatureLayer_management(Bird_Area, bird_select, "")
    arcpy.SelectLayerByLocation_management(bird_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    BIRD_Count = str(arcpy.GetCount_management(bird_select)[0])
    #print BIRD_Count
    if BIRD_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' IMPORTANT BIRDING AREAS ADJACENT TO PROPERTY.....".format(BIRD_Count))
        message (report,"\tTHERE ARE \'{}\' IMPORTANT BIRDING AREAS ADJACENT TO PROPERTY.....".format(BIRD_Count))
        arcpy.Select_analysis(bird_select, os.path.join(Project_GDB, "ImportantBird_Area"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[11], "\"3\"", "PYTHON", "")
        Bird_Check = 'Yes'

############################################################### EXISTING WELLHEAD PROTECTION AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING WELLHEAD PROTECTION AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING WELLHEAD PROTECTION AREAS.....")
    wellhead_select = "wellhead_select"
    Wellhead_Check = 'No'
    arcpy.MakeFeatureLayer_management(Wellheads, wellhead_select, "")
    arcpy.SelectLayerByLocation_management(wellhead_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    WELL_Count = str(arcpy.GetCount_management(wellhead_select)[0])
    #print WELL_Count
    if WELL_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' WELLHEAD PROTECTION AREA ADJACENT TO PROPERTY.....".format(WELL_Count))
        message (report,"\tTHERE ARE \'{}\' WELLHEAD PROTECTION AREA ADJACENT TO PROPERTY.....".format(WELL_Count))
        arcpy.Select_analysis(wellhead_select, os.path.join(Project_GDB, "WellheadProtection_Area"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[12], "\"3\"", "PYTHON", "")
        Wellhead_Check = 'Yes'

############################################################### EXISTING STEEP SLOPE AREAS ###########################################################################
    arcpy.AddMessage("RANKING PROXIMITY TO EXISTING STEEP SLOPE AREAS.....")
    message (report,"RANKING PROXIMITY TO EXISTING STEEP SLOPE AREAS.....")
    slope_select = "slope_select"
    Slope_Check = 'No'
    arcpy.MakeFeatureLayer_management(os.path.join(Working_GDB, "Steep_Slopes"), slope_select, "")
    arcpy.SelectLayerByLocation_management(slope_select, "INTERSECT", os.path.join(Working_GDB, "Parcel_{}".format(PIDN[0])), "30 Feet", "NEW_SELECTION", "NOT_INVERT")
    SLOPE_Count = str(arcpy.GetCount_management(slope_select)[0])
    #print SLOPE_Count
    if SLOPE_Count >= "1":
        arcpy.AddMessage("\tTHERE ARE \'{}\' STEEP SLOPES ADJACENT TO PROPERTY.....".format(SLOPE_Count))
        message (report,"\tTHERE ARE \'{}\' STEEP SLOPES ADJACENT TO PROPERTY.....".format(SLOPE_Count))
        arcpy.Select_analysis(slope_select, os.path.join(Project_GDB, "Steep_Slopes"))
        arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[13], "\"3\"", "PYTHON", "")
        Slope_Check = 'Yes'

############################################################### CLEANUP/FINISHING STEPS FOR PARKLAND QUESTION ###########################################################################
    arcpy.AddMessage("CLEANUP/FINISHING STEPS FOR PARKLAND QUESTION.....")
    message (report,"CLEANUP/FINISHING STEPS FOR PARKLAND QUESTION.....")
    # Create update cursor for feature class

    with arcpy.da.UpdateCursor(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames) as cursor:
        for row in cursor:# to field 12
            if (row[2] == None):
                row[2] = "0"
            if (row[3] == None):
                row[3] = "0"
            if (row[4] == None):
                row[4] = "0"
            if (row[5] == None):
                row[5] = "0"
            if (row[6] == None):
                row[6] = "0"
            if (row[7] == None):
                row[7] = "0"
            if (row[8] == None):
                row[8] = "0"
            if (row[9] == None):
                row[9] = "0"
            if (row[10] == None):
                row[10] = "0"
            if (row[11] == None):
                row[11] = "0"
            if (row[12] == None):
                row[12] = "0"
            if (row[13] == None):
                row[13] = "0"

            # Update the cursor with the updated list
            cursor.updateRow(row)

        del row

    arcpy.CalculateField_management(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames[14], "!"+fieldNames[2]+"! + !"+fieldNames[3]+"! + !"+fieldNames[5]+"! + !"+fieldNames[6]+"! + !"+fieldNames[7]+"! + !"+fieldNames[8]+"! + !"+fieldNames[9]+"! + !"+fieldNames[10]+"! + !"+fieldNames[11]+"! + !"+fieldNames[12]+"! + !"+fieldNames[13]+"!", "PYTHON", "")

############################################################### CREATING NATURE AREA PROJECT MXD ###########################################################################
    arcpy.AddMessage("CREATING PROJECT MXD.....")
    message (report,"CREATING PROJECT MXD.....")
    mxd = arcpy.mapping.MapDocument(os.path.join(arcpy.env.workspace, "OpenSpace_Template" + ".mxd"))
    for df in arcpy.mapping.ListDataFrames(mxd):
        mxd.activeView = df.name
        mxd.title = df.name

        arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "ParcelBuffer_{}_Mile".format(PIDN[0])), "ParcelBuffer_{}".format(PIDN[0]))
        Project_PIDNBuffer = arcpy.mapping.Layer("ParcelBuffer_{}".format(PIDN[0]))
        arcpy.mapping.AddLayer(df, Project_PIDNBuffer, "AUTO_ARRANGE")
        for lyr in arcpy.mapping.ListLayers(mxd, "ParcelBuffer_{}".format(PIDN[0]), df):
            if lyr.name == "ParcelBuffer_{}".format(PIDN[0]):
                lyr.visible = False
                lyr.transparency = 50
                #symbologyLayer = os.path.join(Layer_Folder,"Selected_Parcel.lyr")
                #arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Zoning_Clip")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Zoning_Clip"), "Zoning_Clip")
            Project_Zoning = arcpy.mapping.Layer("Zoning_Clip")
            arcpy.mapping.AddLayer(df, Project_Zoning, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Zoning_Clip", df):
                if lyr.name == "Zoning_Clip":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(os.path.join(Layer_Folder, "Zoning"),"Generalized Zoning Classifications.lyr")):
                        symbologyLayer = os.path.join(os.path.join(Layer_Folder, "Zoning"),"Generalized Zoning Classifications.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Conservation_Easement")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Conservation_Easement"), "Conservation_Easement")
            Project_Consv = arcpy.mapping.Layer("Conservation_Easement")
            arcpy.mapping.AddLayer(df, Project_Consv, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Conservation_Easement", df):
                if lyr.name == "Conservation_Easement":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Conservation Easements.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Conservation Easements.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Focus_Greenway")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Focus_Greenway"), "Focus_Greenway")
            Project_Focus = arcpy.mapping.Layer("Focus_Greenway")
            arcpy.mapping.AddLayer(df, Project_Focus, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Focus_Greenway", df):
                if lyr.name == "Focus_Greenway":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Focus_Greenway.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Focus_Greenway.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Natural_Area")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Natural_Area"), "Natural Area")
            Project_Natural = arcpy.mapping.Layer("Natural Area")
            arcpy.mapping.AddLayer(df, Project_Natural, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Natural Area", df):
                if lyr.name == "Natural Area":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Natural Areas.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Natural Areas.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Geologic_Feature")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Geologic_Feature"), "Geologic Feature Buffer")
            Project_Geo = arcpy.mapping.Layer("Geologic Feature Buffer")
            arcpy.mapping.AddLayer(df, Project_Geo, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Geologic Feature Buffer", df):
                if lyr.name == "Geologic Feature Buffer":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(Layer_Folder,"Geology - Carbonate Rock Surface.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Geology - Carbonate Rock Surface.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "HighQuality_Stream")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "HighQuality_Stream"), "HighQuality_Stream")
            Project_Quality = arcpy.mapping.Layer("HighQuality_Stream")
            arcpy.mapping.AddLayer(df, Project_Quality, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "HighQuality_Stream", df):
                if lyr.name == "HighQuality_Stream":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(Layer_Folder,"Streams.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Streams.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Impaired_Stream")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Impaired_Stream"), "Impaired_Stream")
            Project_Impaired = arcpy.mapping.Layer("Impaired_Stream")
            arcpy.mapping.AddLayer(df, Project_Impaired, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Impaired_Stream", df):
                if lyr.name == "Impaired_Stream":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(Layer_Folder,"Impaired Stream Causes_NEW.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Impaired Stream Causes_NEW.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Forested_Area")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Forested_Area"), "Forested_Area")
            Project_Forest = arcpy.mapping.Layer("Forested_Area")
            arcpy.mapping.AddLayer(df, Project_Forest, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Forested_Area", df):
                if lyr.name == "Forested_Area":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(Layer_Folder,"Forested_Area.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Forested_Area.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "HydricSoils_Wetlands")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "HydricSoils_Wetlands"), "HydricSoils_Wetlands")
            Project_Hydric = arcpy.mapping.Layer("HydricSoils_Wetlands")
            arcpy.mapping.AddLayer(df, Project_Hydric, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "HydricSoils_Wetlands", df):
                if lyr.name == "HydricSoils_Wetlands":
                    lyr.visible = True
                    lyr.transparency = 0
                    if arcpy.Exists(os.path.join(Layer_Folder,"HydricSoils_Wetlands.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"HydricSoils_Wetlands.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Floodplains_100yrs")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Floodplains_100yrs"), "Floodplains_100yrs")
            Project_Flood = arcpy.mapping.Layer("Floodplains_100yrs")
            arcpy.mapping.AddLayer(df, Project_Flood, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Floodplains_100yrs", df):
                if lyr.name == "Floodplains_100yrs":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Floodplain.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Floodplain.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "ImportantBird_Area")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "ImportantBird_Area"), "ImportantBird_Area")
            Project_Bird = arcpy.mapping.Layer("ImportantBird_Area")
            arcpy.mapping.AddLayer(df, Project_Bird, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "ImportantBird_Area", df):
                if lyr.name == "ImportantBird_Area":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Important_Birding_Areas.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Important_Birding_Areas.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "WellheadProtection_Area")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "WellheadProtection_Area"), "WellheadProtection_Area")
            Project_Wellhead = arcpy.mapping.Layer("WellheadProtection_Area")
            arcpy.mapping.AddLayer(df, Project_Wellhead, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "WellheadProtection_Area", df):
                if lyr.name == "WellheadProtection_Area":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Wellhead Protection Zones By Type.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Wellhead Protection Zones By Type.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        if arcpy.Exists(os.path.join(Project_GDB, "Steep_Slopes")):
            arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Steep_Slopes"), "Steep_Soils")
            Project_Slopes = arcpy.mapping.Layer("Steep_Soils")
            arcpy.mapping.AddLayer(df, Project_Slopes, "AUTO_ARRANGE")
            for lyr in arcpy.mapping.ListLayers(mxd, "Steep_Soils", df):
                if lyr.name == "Steep_Soils":
                    lyr.visible = True
                    lyr.transparency = 50
                    if arcpy.Exists(os.path.join(Layer_Folder,"Soils By Representative Slope.lyr")):
                        symbologyLayer = os.path.join(Layer_Folder,"Soils By Representative Slope.lyr")
                        arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        arcpy.MakeFeatureLayer_management(os.path.join(Project_GDB, "Parcel_{}".format(PIDN[0])), "Parcel_{}".format(PIDN[0]))
        Project_PIDN = arcpy.mapping.Layer("Parcel_{}".format(PIDN[0]))
        arcpy.mapping.AddLayer(df, Project_PIDN, "TOP")
        for lyr in arcpy.mapping.ListLayers(mxd, "Parcel_{}".format(PIDN[0]), df):
            if lyr.name == "Parcel_{}".format(PIDN[0]):
                lyr.visible = True
                lyr.transparency = 0
                symbologyLayer = os.path.join(Layer_Folder,"Selected_Parcel.lyr")
                arcpy.ApplySymbologyFromLayer_management (lyr, symbologyLayer)

        mxd.saveACopy(os.path.join(path, "NaturalAreaRanking_" + PIDN[0] + ".mxd"))

    del mxd

    mxd2 = arcpy.mapping.MapDocument(os.path.join(path, "NaturalAreaRanking_" + PIDN[0] + ".mxd"))
    dataFrame = arcpy.mapping.ListDataFrames(mxd2)[0] # the first data frame
    MapLayers = arcpy.mapping.ListLayers(mxd2,"ParcelBuffer*",dataFrame)
    Layer = MapLayers[0]
    Layer.definitionQuery = "PIDN = '{}'".format(PIDN[0])
    Extent = Layer.getExtent(True) # visible extent of layer

    dataFrame.extent = Extent
    arcpy.RefreshActiveView() # redraw the map
    mxd2.save()

    arcpy.AddMessage("CREATING PROJECT PDF.....")
    message (report,"CREATING PROJECT PDF.....")

    file_url = "https://arcweb.ycpc.org/PDFPrint/TaxParcel_{}00000.pdf".format(PIDN[0])

    r = requests.get(file_url, stream = True)

    with open(os.path.join(Project_Folder,'Project_{}_{}\TaxParcel_{}00000.pdf'.format(PIDN[0],dateToday2,PIDN[0])),"wb") as pdf:
        for chunk in r.iter_content(chunk_size=1024):

            # writing one chunk at a time to pdf file
            if chunk:
                pdf.write(chunk)

    # Create update cursor for feature class
    with arcpy.da.SearchCursor(os.path.join(Project_GDB, 'Parcel_{}'.format(PIDN[0])), fieldNames) as cursor:
        for row in cursor:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 30)
            pdf.cell(200,10, txt = "PARCEL NUMBER: {}".format(PIDN[0]), ln = 1, align = 'L')
            pdf.cell(200,10, txt = "", ln =2, align = 'L')
            pdf.set_font("Arial", 'U', size = 15)
            pdf.cell(200,10, txt = "NATURAL AREA CRITERIA", ln = 3, align = 'L')
            pdf.set_font("Arial", size = 15)
            pdf.cell(200,10, txt = "GIS ACRES = {}".format(round(row[0], 2)), ln = 3, align = 'L')
            pdf.cell(200,10, txt = "ZONING = {}".format(row[1]), ln = 3, align = 'L')
            pdf.cell(200,10, txt = "OPEN SPACE = {}".format(round(row[2])), ln = 4, align = 'L')
            pdf.cell(200,10, txt = "FOCUS/GREENWAY = {}".format(round(row[3])), ln = 5, align = 'L')
            pdf.cell(200,10, txt = "NATURAL AREA = {}".format(row[4]), ln = 6, align = 'L')
            pdf.cell(200,10, txt = "UNIQUE GEOLOGY = {}".format(round(row[5])), ln = 7, align = 'L')
            pdf.cell(200,10, txt = "QUALITY STREAM = {}".format(round(row[6])), ln = 8, align = 'L')
            pdf.cell(200,10, txt = "IMPAIRED STRAMS = {}".format(round(row[7])), ln = 9, align = 'L')
            pdf.cell(200,10, txt = "FORESTED AREA = {}".format(round(row[8])), ln = 10, align = 'L')
            pdf.cell(200,10, txt = "WETLAND/HYDRIC = {}".format(round(row[9])), ln = 11, align = 'L')
            pdf.cell(200,10, txt = "100 YEAR FLOOD = {}".format(round(row[10])), ln = 12, align = 'L')
            pdf.cell(200,10, txt = "BIRD AREA = {}".format(round(row[11])), ln = 13, align = 'L')
            pdf.cell(200,10, txt = "WELLHEAD = {}".format(round(row[12])), ln = 14, align = 'L')
            pdf.cell(200,10, txt = "STEEP SLOPES = {}".format(round(row[13])), ln = 15, align = 'L')
            pdf.cell(200,10, txt = "TOTAL SCORE = {}".format(round(row[14])), ln = 16, align = 'L')
            pdf.output(os.path.join(path,"Parcel_{}_NaturalArea_ScoreTable.pdf".format(PIDN[0])))

    os.startfile(os.path.join(path, "TaxParcel_{}00000.pdf".format(PIDN[0])))
    os.startfile(os.path.join(path, "Parcel_{}_NaturalArea_ScoreTable.pdf".format(PIDN[0])))

    try:
        os.startfile(os.path.join(path, "NaturalAreaRanking_" + PIDN[0] + ".mxd"))
    except:
        pass

    del mxd2

arcpy.AddMessage("OPEN SPACE GRANT PROGRAM RANKING PROCESS IS COMPLETED\n")
message (report,"OPEN SPACE GRANT PROGRAM RANKING PROCESS IS COMPLETED\n")

report.close()
#End of Script
