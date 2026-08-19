#Calculate monthly building performance metrics and save to file
import random
import sys
import os
import numpy
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def BEMMonthly(Adv_ene_heat_mode, outputFileName,Input_file):

    #Input file name
    fileName = "Output/BEM_hourly_{}".format(Input_file)

    #Constants
    HeatingValue = 37000            # Energy in a cubic meter of natural gas [kJ m^-3]
    SpinUpDays = 3                  # Number of days to ignore data
    SpinUpHours = SpinUpDays * 24   # Number of hours to ignore data

    #Load all data in a matrix
    data = numpy.loadtxt(fileName)

    Hour = data[:,0]
    sensWaste = data[:,1]
    dehumDemand = data[:,2]
    humDemand = data[:,3]
    QWater = data[:,4]
    QGas = data[:,5]
    sensCoolDemand = data[:,6]
    coolConsump = data[:,7]
    sensHeatDemand = data[:,8]
    heatConsump = data[:,9]
    waterHeatConsump = data[:,10]
    Q_st = data[:,11]
    Q_he_st = data[:,12]
    Q_bites = data[:,13]
    Q_hp = data[:,14]
    Q_recovery = data[:,15]
    W_hp = data[:,16]
    W_pv = data[:,17]
    COP_hp = data[:,18]
    indoorTemp = data[:,19]
    T_st_f_i = data[:,20]
    T_st_f_o = data[:,21]
    T_he_st_i = data[:,22]
    T_he_st_o = data[:,23]
    T_bites = data[:,24]
    W_wt = data[:,25]
    f_pcm = data[:,26]
    Q_waterSaved = data[:,27]
    sensWaterHeatDemand = data[:,28]
    Q_ground = data[:,29]
    elecDomesticDemand = data[:,30]
    Q_waterRecovery = data[:,31]
    TCanyon = data[:,32]
    infil = data[:,33]
    vent = data[:,34]
    hvac_flag = data[:,35]
    window_state = data[:,36]

    #Averaging some of above variables over a months (skipping spinuphours)
    TCanyon_average = numpy.mean(TCanyon[SpinUpHours:])
    infil_average = numpy.mean(infil[SpinUpHours:])
    vent_average = numpy.mean(vent[SpinUpHours:])
    hvac_flag_average = numpy.mean(hvac_flag[SpinUpHours:])
    window_state_average = numpy.mean(window_state[SpinUpHours:])

    # No renewable energy system
    if Adv_ene_heat_mode == 2:

        # heating demand is partitioned into Q_hp or sensible heating demand
        # so to calculate total building sensible heating demand they must be added
        TotalSensHeatDemand = (numpy.sum(sensHeatDemand[SpinUpHours:])) / 1000
        TotalGasConsumpHeat = ((numpy.sum(heatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue
        TotalElecHeatDemand = 0

        TotalSensCoolDemand = numpy.sum(sensCoolDemand[SpinUpHours:])/1000
        TotalElecCoolDemand = numpy.sum(coolConsump[SpinUpHours:])/1000

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate total building sensible water heating demand they must be added
        TotalSensWaterHeatDemand = (numpy.sum(sensWaterHeatDemand[SpinUpHours:])) / 1000
        TotalGasConsumpWaterHeat = ((numpy.sum(waterHeatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue

        TotalElecDomesticDemand = numpy.sum(elecDomesticDemand[SpinUpHours:]) / 1000
        TotalElecProducedPV = 0
        TotalElecProducedWT = 0

    # PV and wind energy only
    if Adv_ene_heat_mode == 3:

        # heating demand is partitioned into Q_hp or sensible heating demand
        # so to calculate total building sensible heating demand they must be added
        TotalSensHeatDemand = (numpy.sum(sensHeatDemand[SpinUpHours:])) / 1000
        TotalGasConsumpHeat = ((numpy.sum(heatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue
        TotalElecHeatDemand = 0

        TotalSensCoolDemand = numpy.sum(sensCoolDemand[SpinUpHours:])/1000
        TotalElecCoolDemand = numpy.sum(coolConsump[SpinUpHours:])/1000

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate total building sensible water heating demand they must be added
        TotalSensWaterHeatDemand = (numpy.sum(sensWaterHeatDemand[SpinUpHours:])) / 1000
        TotalGasConsumpWaterHeat = ((numpy.sum(waterHeatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue

        TotalElecDomesticDemand = numpy.sum(elecDomesticDemand[SpinUpHours:]) / 1000
        TotalElecProducedPV = numpy.sum(W_pv[SpinUpHours:]) / 1000
        TotalElecProducedWT = numpy.sum(W_wt[SpinUpHours:]) / 1000

    # Renewable energy system under heating mode
    if Adv_ene_heat_mode == 1:

        # heating demand is partitioned into Q_hp or sensible heating demand
        # so to calculate total building sensible heating demand they must be added
        TotalSensHeatDemand = (numpy.sum(sensHeatDemand[SpinUpHours:])) / 1000 + (numpy.sum(Q_hp[SpinUpHours:])) / 1000
        TotalGasConsumpHeat = ((numpy.sum(heatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue
        TotalElecHeatDemand = numpy.sum(W_hp[SpinUpHours:]) / 1000

        TotalSensCoolDemand = numpy.sum(sensCoolDemand[SpinUpHours:])/1000
        TotalElecCoolDemand = numpy.sum(coolConsump[SpinUpHours:])/1000

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate total building sensible water heating demand they must be added
        TotalSensWaterHeatDemand = (numpy.sum(sensWaterHeatDemand[SpinUpHours:])) / 1000 + (numpy.sum(Q_waterSaved[SpinUpHours:])) / 1000
        TotalGasConsumpWaterHeat = ((numpy.sum(waterHeatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue

        TotalElecDomesticDemand = numpy.sum(elecDomesticDemand[SpinUpHours:]) / 1000
        TotalElecProducedPV = numpy.sum(W_pv[SpinUpHours:]) / 1000
        TotalElecProducedWT = numpy.sum(W_wt[SpinUpHours:]) / 1000

    # Renewable energy system under cooling mode
    elif Adv_ene_heat_mode == 0:

        TotalSensHeatDemand = numpy.sum(sensHeatDemand[SpinUpHours:]) / 1000
        TotalGasConsumpHeat = ((numpy.sum(heatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue
        TotalElecHeatDemand = 0

        # cooling demand is entirely partitioned into Q_hp or sensible cooling demand
        # so to calculate total building sensible cooling demand they must be added
        TotalSensCoolDemand = (numpy.sum(sensCoolDemand[SpinUpHours:])) / 1000 + (numpy.sum(Q_hp[SpinUpHours:])) / 1000
        TotalElecCoolDemand = numpy.sum(coolConsump[SpinUpHours:]) / 1000 + numpy.sum(W_hp[SpinUpHours:]) / 1000

        # sensible water heating demand is partitioned into Q_waterSaved or sensible water heating demand
        # so to calculate total building sensible water heating demand they must be added
        TotalSensWaterHeatDemand = (numpy.sum(sensWaterHeatDemand[SpinUpHours:])) / 1000 + (numpy.sum(Q_waterSaved[SpinUpHours:])) / 1000
        TotalGasConsumpWaterHeat = ((numpy.sum(waterHeatConsump[SpinUpHours:])) / 1000) * 3600 / HeatingValue

        TotalElecDomesticDemand = numpy.sum(elecDomesticDemand[SpinUpHours:]) / 1000
        TotalElecProducedPV = numpy.sum(W_pv[SpinUpHours:]) / 1000
        TotalElecProducedWT = numpy.sum(W_wt[SpinUpHours:]) / 1000

    outputFile = open(outputFileName, "w")

    # Write header
    outputFile.write("#0: TotalSensHeatDemand [kW hr m-2] \t 1: TotalGasConsumpHeat [m3 m-2] \t 2: TotalElecHeatDemand [kW hr m-2] \t \
                                3: TotalSensCoolDemand [kW hr m-2] \t 4: TotalElecCoolDemand [kW hr m-2] \t \
                                5: TotalSensWaterHeatDemand [kW hr m-2] \t 6: TotalGasConsumpWaterHeat [m3 m-2] \t \
                                7: TotalElecDomesticDemand [kW hr m-2] \t 8: TotalElecProducedPV [kW hr m-2] \t 9: TotalElecProducedWT [kW hr m-2] \
                                10: CanyonTemp [k] \t 11: Infiltration [ACH] \t 12: Ventilation [m3 s-1 m-2] \t 13: HVACFlag [-] \t 14: WindowState [-] \n")

    # Write data
    outputFile.write("%f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \n"
                     % (TotalSensHeatDemand, TotalGasConsumpHeat, TotalElecHeatDemand,
                        TotalSensCoolDemand, TotalElecCoolDemand,
                        TotalSensWaterHeatDemand, TotalGasConsumpWaterHeat,
                        TotalElecDomesticDemand, TotalElecProducedPV, TotalElecProducedWT,
                        TCanyon_average, infil_average, vent_average, hvac_flag_average, window_state_average))

    outputFile.close()
    return TotalGasConsumpHeat, TotalElecHeatDemand, TotalElecCoolDemand, TotalGasConsumpWaterHeat, \
           TotalElecDomesticDemand, TotalElecProducedPV, TotalElecProducedWT