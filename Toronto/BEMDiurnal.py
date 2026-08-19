import pandas as pd
import matplotlib.pyplot as plt
import numpy

def BEMDiurnal(Adv_ene_heat_mode, outputFileName,Input_file):

    #Define building energy system characteristics
    HeatingValue = 37000            # Energy in a cubic meter of natural gas [kJ m^-3]
    SpinUpDays = 3                  # Number of days to ignore data
    SpinUpHours = SpinUpDays * 24   # Number of hours to ignore data

    # Read your table into a DataFrame, skipping the first three rows (replace 'your_data_file.txt' with the actual path to your data file)
    df = pd.read_csv('Output/BEM_hourly_{}'.format(Input_file), delimiter=' ', skiprows=SpinUpHours+3, header=None)


    # Convert the first column to integers, handling non-integer and empty values gracefully
    def try_convert_to_int(x):
        try:
            return int(x)
        except (ValueError, TypeError):
            return None

    df[0] = df[0].apply(try_convert_to_int)

    # Calculate the remainder to 24 for the first column
    df['remainder_to_24'] = df[0] % 24

    # Create a list of columns to calculate sums for
    # 8: sensHeatDemand [W m^-2]
    # 6: sensCoolDemand [W m^-2]
    # 7: coolConsump [W m^-2]
    # 9: heatConsump [W m^-2]
    # 10: waterHeatConsump [W m^-2]
    # 14: Q_hp [W m^-2]
    # 16: W_hp [W m^-2]
    # 28: sensWaterHeatDemand [W m^-2]
    # 17: W_pv [W m^-2]
    # 25: W_wt [W m^-2]
    # 27: Q_waterSaved [W m^-2]
    # 30: elecDomesticDemand [W m^-2]
    # 2:  dehumDemand [W m^-2]
    # 3:  :humDemand [W m^-2]

    # Get unique values of 'remainder_to_24' based on the original DataFrame
    Hours = df['remainder_to_24'].unique()

    # No renewable energy system
    if Adv_ene_heat_mode == 2:
        DiurnalSensHeatDemand = df[df.columns[8]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalGasConsumpHeat = ((df[df.columns[9]].groupby(df['remainder_to_24']).sum().values) / 1000) *\
                                3600 / HeatingValue

        TotalElecHeatDemand = 0

        DiurnalSensCoolDemand = df[df.columns[6]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecCoolDemand = df[df.columns[7]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecHeatDemand = 0

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate Diurnal building sensible water heating demand they must be added
        DiurnalSensWaterHeatDemand = df[df.columns[28]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalGasConsumpWaterHeat = (df[df.columns[10]].groupby(df['remainder_to_24']).sum().values/1000) * 3600 / HeatingValue

        DiurnalElecProducedPV = 0
        DiurnalElecProducedWT = 0

        DiurnalElecDomesticDemand = df[df.columns[29]].groupby(df['remainder_to_24']).sum().values/1000

    # PV and wind energy only
    if Adv_ene_heat_mode == 3:

        DiurnalSensHeatDemand = df[df.columns[8]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalGasConsumpHeat = ((df[df.columns[9]].groupby(df['remainder_to_24']).sum().values)/ 1000) *\
                                    3600 / HeatingValue

        TotalElecHeatDemand = 0

        DiurnalSensCoolDemand = df[df.columns[6]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecCoolDemand = df[df.columns[7]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecHeatDemand = 0

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate Diurnal building sensible water heating demand they must be added
        DiurnalSensWaterHeatDemand = df[df.columns[28]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalGasConsumpWaterHeat = (df[df.columns[10]].groupby(df['remainder_to_24']).sum().values/1000) * 3600 / HeatingValue

        DiurnalElecProducedPV= df[df.columns[17]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecProducedWT= df[df.columns[25]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecDomesticDemand= df[df.columns[30]].groupby(df['remainder_to_24']).sum().values/1000

    # Renewable energy system under heating mode
    if Adv_ene_heat_mode == 1:
        DiurnalSensHeatDemand = df[df.columns[8]].groupby(df['remainder_to_24']).sum().values / 1000 +\
                                df[df.columns[14]].groupby(df['remainder_to_24']).sum().values / 1000

        DiurnalGasConsumpHeat = ((df[df.columns[9]].groupby(df['remainder_to_24']).sum().values) / 1000) *\
                                3600 / HeatingValue

        DiurnalElecHeatDemand = df[df.columns[16]].groupby(df['remainder_to_24']).sum().values / 1000

        DiurnalSensCoolDemand = df[df.columns[6]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecCoolDemand = df[df.columns[7]].groupby(df['remainder_to_24']).sum().values/1000

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate Diurnal building sensible water heating demand they must be added
        DiurnalSensWaterHeatDemand = df[df.columns[28]].groupby(df['remainder_to_24']).sum().values / 1000 + \
                                     df[df.columns[27]].groupby(df['remainder_to_24']).sum().values / 1000

        DiurnalGasConsumpWaterHeat = (df[df.columns[10]].groupby(df['remainder_to_24']).sum().values/1000) * 3600 / HeatingValue

        DiurnalElecProducedPV = df[df.columns[17]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecProducedWT = df[df.columns[25]].groupby(df['remainder_to_24']).sum().values/1000
        DiurnalElecDomesticDemand = df[df.columns[30]].groupby(df['remainder_to_24']).sum().values/1000

    # Renewable energy system under cooling mode
    elif Adv_ene_heat_mode == 0:
        DiurnalSensHeatDemand = df[df.columns[8]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalGasConsumpHeat = ((df[df.columns[9]].groupby(df['remainder_to_24']).sum().values)/ 1000) *\
                                3600 / HeatingValue

        DiurnalElecHeatDemand = 0

        DiurnalSensCoolDemand = df[df.columns[6]].groupby(df['remainder_to_24']).sum().values / 1000 + \
                                df[df.columns[14]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalElecCoolDemand = df[df.columns[7]].groupby(df['remainder_to_24']).sum().values / 1000 + \
                                df[df.columns[16]].groupby(df['remainder_to_24']).sum().values / 1000


        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate Diurnal building sensible water heating demand they must be added
        DiurnalSensWaterHeatDemand = df[df.columns[28]].groupby(df['remainder_to_24']).sum().values / 1000 + \
                                     df[df.columns[27]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalGasConsumpWaterHeat = (df[df.columns[10]].groupby(df['remainder_to_24']).sum().values/1000) * 3600 / HeatingValue

        DiurnalElecProducedPV = df[df.columns[17]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalElecProducedWT = df[df.columns[25]].groupby(df['remainder_to_24']).sum().values / 1000
        DiurnalElecDomesticDemand = df[df.columns[30]].groupby(df['remainder_to_24']).sum().values / 1000

        # Create a dictionary to store the data
    data_dict = {
        '#0: Hours': Hours,
        '1: DiurnalSensHeatDemand [kW hr m-2]': DiurnalSensHeatDemand,
        '2: DiurnalGasConsumpHeat [m3 m-2]': DiurnalGasConsumpHeat,
        '3: DiurnalElecHeatDemand [kW hr m-2]': DiurnalElecHeatDemand,
        '4: DiurnalSensCoolDemand [kW hr m-2]': DiurnalSensCoolDemand,
        '5: DiurnalElecCoolDemand [kW hr m-2]': DiurnalElecCoolDemand,
        '6: DiurnalSensWaterHeatDemand [kW hr m-2]': DiurnalSensWaterHeatDemand,
        '7: DiurnalGasConsumpWaterHeat [m3 m-2]': DiurnalGasConsumpWaterHeat,
        '8: DiurnalElecProducedPV [kW hr m-2]': DiurnalElecProducedPV,
        '9: DiurnalElecProducedWT [kW hr m-2]': DiurnalElecProducedWT,
        '10: DiurnalElecDomesticDemand [kW hr m-2]': DiurnalElecDomesticDemand
    }

    # Specify the column order to match the dictionary
    column_order = [
        '#0: Hours',
        '1: DiurnalSensHeatDemand [kW hr m-2]',
        '2: DiurnalGasConsumpHeat [m3 m-2]',
        '3: DiurnalElecHeatDemand [kW hr m-2]',
        '4: DiurnalSensCoolDemand [kW hr m-2]',
        '5: DiurnalElecCoolDemand [kW hr m-2]',
        '6: DiurnalSensWaterHeatDemand [kW hr m-2]',
        '7: DiurnalGasConsumpWaterHeat [m3 m-2]',
        '8: DiurnalElecProducedPV [kW hr m-2]',
        '9: DiurnalElecProducedWT [kW hr m-2]',
        '10: DiurnalElecDomesticDemand [kW hr m-2]'
    ]

    # Save to a CSV file without the index column
    df = pd.DataFrame(data_dict, columns=column_order)
    df.to_csv(outputFileName, index=False)
