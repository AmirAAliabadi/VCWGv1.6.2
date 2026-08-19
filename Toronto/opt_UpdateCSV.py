# Update the Rvalue in the CSV file
# Xuan Chen
# Atmospheric Innovations Research (AIR) Laboratory, University of Guelph, Guelph, Canada
# last update: 21 July 2022

import os
import pandas

def Update_LocationSummary(buildingtype, opt_RvalWall, opt_RvalRoof):
    DIR_CURR = os.path.abspath(os.path.dirname(__file__))
    DIR_DOE_PATH = os.path.join(DIR_CURR,"resources","DOERefBuildings")
    file_doe_name_location = os.path.join("{}".format(DIR_DOE_PATH), "BLD{}".format(buildingtype),"BLD{}_LocationSummary.csv".format(buildingtype))
    print (file_doe_name_location)
    df = pandas.read_csv(file_doe_name_location)

    # Only over write R values if the variable was chosen in the variable space
    if opt_RvalWall != None:
        df.iloc[14, -1] = opt_RvalWall
    if opt_RvalRoof != None:
        df.iloc[16, -1] = opt_RvalRoof

    # Save the revised version of the CSV file
    df.to_csv(file_doe_name_location, index=False)