# Calculate Annualized Marginal Cost and GHG Emissions
# Ali Madadizadeh, Amir A. Aliabadi
# Atmospheric Innovations Research (AIR) Laboratory, University of Guelph, Guelph, Canada
# last update: 2024-02-28

import random
import sys
import os
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd

def EconomicGHGAnalysis(RvalRoofBase, RvalWallBase, opt_RvalWall, opt_RvalRoof, opt_A_PV, opt_A_WT,
                                        opt_Infil, opt_Vent, opt_AlbRoof, opt_Glz, opt_SHGC, opt_V_BITES, opt_A_ST,
                                        opt_m_dot_st_f, opt_m_dot_he_st, opt_T_melt, opt_V_pcm,
                                        alb_roof, V_pcm, A_st, V_bites, A_wt, A_pv,case_name,Base_case_name, ElecPriceInc, GasPriceInc,
                                        opt_Rebate, opt_Loan, opt_IntRate, opt_Fuel_Tax, opt_Elec_Tax):

        # 1:ON,Toronto (Zone = 5), 2:BC,Vancouver (Zone = 4), 3:AB_Calgary, 4:NL_StJohns, 5:MB Winnipeg (Zone = 7A), 6:SK_Saskatoon, 7:PE, 8:NS,Halifax (Zone = 6), 9:NB, 10:QC_Montreal, 11:YT_Withhorse, 12:NT Yellowknife (Zone = 8), 13:NU
        Region = 1
        City = 'Toronto'
        #Input
        #Diurnal
        PerfMetricsDiurnalFileNameBase = r"Output/Perf-Metrics-Diurnal-{}-{}.txt".format(Base_case_name,{})
        PerfMetricsDiurnalFileNameRetrofit = r"Output/Perf-Metrics-Diurnal-{}-{}.txt".format(case_name,{})

        # Electricity price rates
        ON_TOU_Electricity_Rates = pd.read_csv('resources/Economics/ON_TOU_Electricity_Rates.txt', delimiter=',')
        CarbonIntensityProjection = pd.read_csv('resources/Economics/carbon_intensity_projection.txt', delimiter=',')

        # Gas price rates
        ON_NG_Residential_Rates = pd.read_csv('resources/Economics/ON_NG_Residential_Rates.txt',  delimiter=',')

        outputFileNameMultiYearPayback = 'Output/{}_MultiYearPayback.txt'.format(case_name)
        outputFileNameMultiYearOperationalCO2Sav = 'Output/{}_MultiYearOperationalCO2Sav.txt'.format(case_name)


        # CO2 savings with the reduction of electricity consumption from the grid
        # ElecEmissionIntensity [gCO2e kW-h^-1]
        ElecEmissionIntensity = pd.read_csv('resources/Economics/ElecEmissionIntensity.txt', delimiter=',')

        #Social Carbon Cost [$ Tonne CO2^-1]
        SCC = pd.read_csv('resources/Economics/SocialCarbonCost.txt', delimiter=',')


        # Building envelope information
        A_building = 130  # Building footprint area [m^2]
        A_walls = 274  # Area of wall envelope [m^2]
        A_Roof = A_building / (np.cos(18.4 * np.pi/180))      # Area of full roof [m^2]
        # Area of full roof [m^2]
        CoolRoofAlbedoCutOff = 0.5                              # Albedo cut off for cool roof [-]

        # CO2 uptake
        # 1: 10.52 [kg coniferous tree^-1 year^-10]
        # 2: 17.24 [kg deciduous tree^-10]
        # 3: 13.88 [kg Tree^-1] on average

        CO2UptakeTree10Years = 13.88  # [kgCO2 10-years-1]

        MWCH4 = 12 + 4  # molecular weight of CH4 [gCH4 mol^-1]
        MWCO2 = 44  # molecular weight of CO2 [gCO2 mol^-1]
        rhoCH4 = 0.668  # density of methane [kgCH4 m^-3] at 293 K and 1 ATM

        # Embodied carbon factors
        ECF_PV = 150  # kg CO2e m-2 (embodied carbon factor for photovoltaic panels)
        ECF_WT = 100  # kg CO2e m-2 (embodied carbon factor for wind turbines)
        ECF_BITES = 30  # kg CO2e m-3 (embodied carbon factor for BITES system)
        ECF_ST = 40  # kg CO2e m-3 (embodied carbon factor for solar thermal)
        ECF_PCM = 25  # kg CO2e m-3 (embodied carbon factor for PCM)
        ECF_Insulation = 10  # kg CO2e m-2 (embodied carbon factor for insulation materials)
        ECF_CoolRoof = 5  # kg CO2e m-2 (embodied carbon factor for cool roofing)
        ECF_HP = 600  # kg CO2e per unite (embodied carbon factor for heat pump)

        # Economic input
        # Annual inflation rate: https://www.macrotrends.net/countries/CAN/canada/inflation-rate-cpi
        InfRate = 0.0217
        # Annual interest rate: https://www150.statcan.gc.ca
        IntRate = 0.0393

        CIniBase = 5        # Marginal initial installation cost now per building foot print area [$ m^-2]
        CAnnOMBase = 1      # Marginal annual operation and maintenance cost now per building foot print area [$ m^-2] 0.9
        Nyears = 20         # Number of years for economic analysis
        # Marginal costs of base system without renewable energy
        # These costs are additional to the base cost of a system without renewable energy

        # Initial investment Prices
        PVPrice = 384                # PV price per collector area now (i.e portion of roof area) [$ m^-2]
        WTPrice = 490 * 2            # WT price per swept area now [$ m^-2] assuming 1 additional replacement
        STPrice = 340                # ST price per collector area [$ m^-2]
        BITESPrice = 200             # BITES price per unit volume [$ m^-3]
        PCMPrice = 1930 * 2          # PCM price per unit volume [$ m^-3] assuming 1 additional replacement
        HPPrice = 38 * 2             # HP price per building footprint area [$ m^-2] assuming 1 additional replacement
        TreePrice = 200              # Tree price per tree now
        CRPrice = 8 * 2              # Cool Roof price per roof area now [$ m^-2] assuming 1 additional coat
        AirTPrice = 1500 * 2         # Air tightness price per building [$ test^-1] (Assume 2 tests)
        RvalueWallPrice = 40         # Price of insulation of unit R value change for wall [$ m^-4 K^-1 W]
        RvalueRoofPrice = 40         # Price of insulation of unit R value change for roof [$ m^-4 K^-1 W]

        SalFactorBase = 0.03         # Fraction of initial investment of equipment that can be salvaged
        SalFactor = 0.05             # Fraction of initial investment of equipment that can be salvaged

        # Operation maintenance cost
        OMPV = 0.01 * PVPrice                # Operation maintenance cost for PV per collector area now [$ m^-2]
        OMWT = 0.02 * WTPrice                # Operation maintenance cost for WT per swept area now [$ m^-2]
        OMST = 0.01 * STPrice                # Operation maintenance cost for ST per collector area [$ m^-2]
        OMBITES = 0.01 * BITESPrice          # Operation maintenance cost for BITES per unit volume [$ m^-3]
        OMPCM = 0.01 * PCMPrice              # Operation maintenance cost for PCM per unit volume [$ m^-3]
        OMHP = 0.05 * HPPrice                # Operation maintenance cost for HP per building footprint area [$ m^-2]
        OMVeg = 130                          # Operation maintenance cost for tree care per 0.5 LAI [m^2 m^-2] added (~ 1 tree)
        OMCR = 0.1 * CRPrice                 # Operation maintenance cost for keeping Cool Roof clean now [$]

        LoanNyears = 20

        # Number of additional trees, each extra tree adds 0.5 LAI [m^2 m^-2]
        Additional_Trees = 0

        # Optimization case and initial case parameter information

        # Check which variables are being included in the optimization
        '''opt_A_PV, opt_A_WT, opt_Infil, opt_Vent, opt_AlbRoof, opt_Glz, opt_SHGC,
        opt_V_BITES, opt_A_ST, opt_m_dot_st_f, opt_m_dot_he_st, opt_T_melt, opt_V_pcm'''

        # Area of PV [m^2]
        if opt_A_PV is not None:
            A_pv = opt_A_PV * A_building
        else:
            A_pv = A_pv * A_building

        # Swept area of wind turbine [m^2]
        if opt_A_WT is not None:
            A_wt = opt_A_WT * A_building
        else:
            A_wt = A_wt * A_building

        # Volume of Bites [m^3]
        if opt_V_BITES is not None:
            V_BITES = opt_V_BITES * A_building
            HPSwitch = 1
        else:
            V_BITES = V_bites * A_building
            HPSwitch = 0

        # Area of ST [m^2]
        if opt_A_ST is not None:
            A_ST = opt_A_ST * A_building
        else:
            A_ST = A_st * A_building

        # Volume of PCM [m^3]
        if opt_V_pcm is not None:
            V_pcm = opt_V_pcm * A_building
        else:
            V_pcm = V_pcm * A_building

        # R-value change from base case [m^2 K W^-1]
        if opt_RvalWall is not None:
            RvalueWall_quantity = np.abs(float(opt_RvalWall) - float(RvalWallBase))
        else:
            RvalueWall_quantity = 0

        # R-value change from base case [m^2 K W^-1]
        if opt_RvalRoof is not None:
            RvalueRoof_quantity = np.abs(float(opt_RvalRoof) - float(RvalRoofBase))
        else:
            RvalueRoof_quantity = 0

        # Area of cool roof [m^2]
        if opt_AlbRoof is not None:
            A_CR = A_Roof
        elif alb_roof > CoolRoofAlbedoCutOff:
            A_CR = A_Roof
        else:
            A_CR = 0

        # High performance envelop price [$]
        EnvPrice = A_walls * RvalueWall_quantity * RvalueWallPrice + A_Roof * RvalueRoof_quantity * RvalueRoofPrice

        # Compute annualized system cost
        EffIntRate = (IntRate - InfRate) / (1 + InfRate)
        PWFFullPeriod = 1 / ((1 + EffIntRate) ** Nyears)
        CRFFullPeriod = EffIntRate / (1 - (1 + EffIntRate) ** (-Nyears))

        CAnnOMRetrofit = A_pv * OMPV + A_wt * OMWT + A_st * OMST + V_bites * OMBITES +\
                  V_pcm * OMPCM + OMHP + OMCR + Additional_Trees * OMVeg

        # Capital investment for the retrofitted system for the entire footprint of the house [$]
        CIniRetrofit = ((A_pv * PVPrice + A_wt * WTPrice + A_st * STPrice + V_bites * BITESPrice +\
                         V_pcm * PCMPrice + A_CR * CRPrice) + HPSwitch * HPPrice * A_building + EnvPrice +\
                        AirTPrice + TreePrice * Additional_Trees -(opt_Rebate + opt_Loan ))

        CAnnIniBase = CIniBase * A_building * CRFFullPeriod
        CAnnIniRetrofit = CIniRetrofit * CRFFullPeriod

        # Total embodied carbon
        TotalEmbodiedCO2 = A_pv * ECF_PV + A_wt * ECF_WT + V_BITES * ECF_BITES + A_ST * ECF_ST + V_pcm * ECF_PCM\
                              + RvalueWall_quantity * A_walls * ECF_Insulation + RvalueRoof_quantity * A_Roof * ECF_Insulation\
                              + A_CR * ECF_CoolRoof + HPSwitch * ECF_HP
        # CO2 savings with the addition of vegetation [kg]
        # EPA 2021 - Greenhouse Gases Equivalencies Calculator - Calculations and References
        AnnVegCO2Saving = Additional_Trees * (CO2UptakeTree10Years / 10)

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        MultiYearPayback = []
        MultiYearOperationalCO2Sav = []

        (PresBaseGasCost, PresRetrofitGasCost, PresBaseElecCost, PresRetrofitElecCost, TotalGasConsumpHeatBase,\
        TotalGasConsumpWaterHeatBase, TotalGasConsumpHeatRetrofit, TotalGasConsumpWaterHeatRetrofit, TotalElecCoolDemandBase, \
        TotalElecDomesticDemandBase, TotalElecCoolDemandRetrofit, TotalElecHeatDemandRetrofit, TotalElecDomesticDemandRetrofit, \
        TotalElecProducedPVRetrofit, TotalElecProducedWTRetrofit, PresBaseOMCost, PresRetrofitOMCost, SumAnnualCostDiff, \
        TotalDiurnalDehumDemandRetrofit, TotalDiurnalHumDemandRetrofit, TotalDiurnalDehumDemandBase, TotalDiurnalHumDemandBase, \
        PresSCCSav, TotalOperationalCO2Sav, PresLoanPayment)= [0] * 25

        TotalCO2Sav = -TotalEmbodiedCO2
        PresSCCSav = (-TotalEmbodiedCO2/1000) * SCC.iloc[0,1] # [$]

        for year in range(1, Nyears + 1):
            
            AnnualOperationalCO2Sav = 0
            
            for month_idx, month in enumerate(months, start=0):
                # Construct the file names based on the template
                FilePathRetrofitDiurnal = PerfMetricsDiurnalFileNameRetrofit.format(month)
                FilePathBaseDiurnal = PerfMetricsDiurnalFileNameBase.format(month)

                # Check if the file exists before attempting to load
                if os.path.exists(FilePathRetrofitDiurnal) and os.path.exists(FilePathBaseDiurnal) :
                    # Load data from the file
                    #Diurnal
                    PerfMetricsDiurnalBase = pd.read_csv(FilePathBaseDiurnal, delimiter=',')
                    PerfMetricsDiurnalRetrofit = pd.read_csv(FilePathRetrofitDiurnal, delimiter=',')

                    # Total Energy Consumtion
                    MonthlyDiffFuelConsump =  PerfMetricsDiurnalBase.iloc[:, 2].sum() +PerfMetricsDiurnalBase.iloc[:, 7].sum() - \
                                      PerfMetricsDiurnalRetrofit.iloc[:, 2].sum() - PerfMetricsDiurnalRetrofit.iloc[:,7].sum()

                    MonthlyDiffElecConsump = PerfMetricsDiurnalBase.iloc[:,5].sum() + PerfMetricsDiurnalBase.iloc[:,10].sum() - \
                        (PerfMetricsDiurnalRetrofit.iloc[:,5].sum() + PerfMetricsDiurnalRetrofit.iloc[:,3].sum() + PerfMetricsDiurnalRetrofit.iloc[:,10].sum() - \
                         PerfMetricsDiurnalRetrofit.iloc[:,8].sum() -  PerfMetricsDiurnalRetrofit.iloc[:,9].sum())

                    # Saved CO2 [kg]
                    FuelCO2Saving = (MonthlyDiffFuelConsump) *  A_building * rhoCH4 * MWCO2 / MWCH4
                    ElecCO2Saving = (MonthlyDiffElecConsump) * A_building * (CarbonIntensityProjection.iloc[year + 2,1] /100) *\
                                    ElecEmissionIntensity.iloc[8, Region] / 1000

                    TotalOperationalCO2Sav = TotalOperationalCO2Sav + FuelCO2Saving + ElecCO2Saving
                    
                    AnnualOperationalCO2Sav = AnnualOperationalCO2Sav + FuelCO2Saving + ElecCO2Saving

                    TotalCO2Sav = TotalCO2Sav + FuelCO2Saving + ElecCO2Saving + AnnVegCO2Saving/12

                    #Social Cost of Carbon
                    PresSCCSav = PresSCCSav + ((FuelCO2Saving + ElecCO2Saving + AnnVegCO2Saving/12) / 1000) * SCC.iloc[year-1,1] * \
                                  1 / ((1 + EffIntRate) ** year)

                    # Gas Consumption Cost
                    PresBaseGasCost = PresBaseGasCost + (((PerfMetricsDiurnalBase.iloc[:,2] + PerfMetricsDiurnalBase.iloc[:,7]) * \
                       ON_NG_Residential_Rates.iloc[0,2]/100).sum() * A_building) *(1 + GasPriceInc) ** year * 1 / ((1 + EffIntRate) ** year)

                    PresRetrofitGasCost = PresRetrofitGasCost + (((PerfMetricsDiurnalRetrofit.iloc[:,2] + PerfMetricsDiurnalRetrofit.iloc[:,7]) * \
                                           ON_NG_Residential_Rates.iloc[0,2]/100).sum() * A_building) *(1 + GasPriceInc) ** year * 1 / ((1 + EffIntRate) ** year)

                    # Electricity Consumption Cost
                    if month is 'May 'or 'Jun' or 'Jul'or 'Aug' or'Sep' or'Oct':
                        PresBaseElecCost = PresBaseElecCost + (((PerfMetricsDiurnalBase.iloc[:,5] + PerfMetricsDiurnalBase.iloc[:,10]) *
                             ON_TOU_Electricity_Rates.iloc[:,1]/100).sum() * A_building) *  (1 + ElecPriceInc) ** year * 1 / ((1 + EffIntRate) ** year)

                        PresRetrofitElecCost = PresRetrofitElecCost + (((PerfMetricsDiurnalRetrofit.iloc[:,3] + PerfMetricsDiurnalRetrofit.iloc[:,5] + PerfMetricsDiurnalRetrofit.iloc[:,10]- \
                                 PerfMetricsDiurnalRetrofit.iloc[:,8] - PerfMetricsDiurnalRetrofit.iloc[:,9]) * ON_TOU_Electricity_Rates.iloc[:,1]/100).sum() * A_building) * \
                                          (1 + ElecPriceInc) ** year * 1 / ((1 + EffIntRate) ** year)

                    if month is 'Jan' or 'Feb' or 'Mar' or 'Apr' or 'Nov' or 'Dec':
                        PresBaseElecCost = PresBaseElecCost + (((PerfMetricsDiurnalBase.iloc[:,5] + PerfMetricsDiurnalBase.iloc[:,10]) *\
                                        ON_TOU_Electricity_Rates.iloc[:,2]/100).sum() * A_building) * \
                                          (1 + ElecPriceInc) ** year * 1 / ((1 + EffIntRate) ** year)

                        PresRetrofitElecCost = PresRetrofitElecCost + (((PerfMetricsDiurnalRetrofit.iloc[:,3] + PerfMetricsDiurnalRetrofit.iloc[:,5] + PerfMetricsDiurnalRetrofit.iloc[:,10] - \
                            PerfMetricsDiurnalRetrofit.iloc[:,8] - PerfMetricsDiurnalRetrofit.iloc[:,9]) * ON_TOU_Electricity_Rates.iloc[:,2]/100).sum() * A_building) * \
                                          (1 + ElecPriceInc) ** year * 1 / ((1 + EffIntRate) ** year)
                else:
                    print('There are no building energy performance metrics files!')
            #Fuel Tax Savings
            PresFuelTaxSav =  (PresBaseGasCost - PresRetrofitGasCost) * opt_Fuel_Tax/100

            #Elec Tax Savings
            PresElecTaxSav = (PresBaseElecCost - PresRetrofitElecCost) * opt_Elec_Tax/100

            if opt_IntRate != 0:
                # opt_Loan
                PresLoanPayment = PresLoanPayment + (
                        opt_Loan * ((opt_IntRate / 100) * (1 + (opt_IntRate / 100)) ** LoanNyears) / \
                        ((1 + (opt_IntRate / 100)) ** LoanNyears - 1)) * (1 / ((1 + EffIntRate) ** year))
                
            # Calculate the payback period
            PresBaseOMCost = PresBaseOMCost + CAnnOMBase * A_building * 1 / ((1 + EffIntRate) ** year)
            PresRetrofitOMCost = PresRetrofitOMCost + CAnnOMRetrofit * 1 / ((1 + EffIntRate) ** year)

            SumAnnualCostDiff = (PresLoanPayment + PresRetrofitGasCost +
                PresRetrofitElecCost + PresRetrofitOMCost - PresSCCSav) - (PresBaseGasCost + PresBaseElecCost + PresBaseOMCost)

            PaybackDiff = SumAnnualCostDiff + CIniRetrofit - CIniBase * A_building
            print('Year, PaybackDiff = ', year, round(PaybackDiff))
            

            MultiYearPayback.append(round(PaybackDiff))
            MultiYearOperationalCO2Sav.append (round(AnnualOperationalCO2Sav))

        #Tax
        CAnnTaxSav = (PresFuelTaxSav + PresElecTaxSav) * CRFFullPeriod

        #Total Loan Payment
        PresLoanPayment = PresLoanPayment

        CAnnLoanPaymentOwner = PresLoanPayment * CRFFullPeriod

        CAnnFuelBase = PresBaseGasCost * CRFFullPeriod
        CAnnFuelRetrofit = PresRetrofitGasCost * CRFFullPeriod

        CAnnElecBase = PresBaseElecCost * CRFFullPeriod
        CAnnElecRetrofit = PresRetrofitElecCost * CRFFullPeriod

        CSalBase = SalFactorBase * CIniBase * A_building * PWFFullPeriod
        CSalRetrofit = SalFactor * CIniRetrofit * PWFFullPeriod

        CAnnSalBase = CSalBase * CRFFullPeriod
        CAnnSalRetrofit = CSalRetrofit * CRFFullPeriod

        CAnnSCCSav = PresSCCSav * CRFFullPeriod

        CAnnBase = CAnnIniBase + CAnnFuelBase + CAnnElecBase + CAnnOMBase * A_building - CAnnSalBase
        CAnnRetrofit = CAnnIniRetrofit + CAnnFuelRetrofit + CAnnElecRetrofit + CAnnOMRetrofit + CAnnLoanPaymentOwner - CAnnTaxSav - CAnnSalRetrofit - CAnnSCCSav
        CAnnGovtSav = -opt_Rebate * CRFFullPeriod - opt_Loan * CRFFullPeriod - CAnnTaxSav + CAnnLoanPaymentOwner

        # Cost saving
        TotalAnnCostSaving = CAnnBase - CAnnRetrofit

        PercAnnSaving = 100 * (CAnnBase - CAnnRetrofit) / CAnnBase
        
        # Write data to files
        with open(outputFileNameMultiYearPayback, "w") as outputFile:
            outputFile.write("# 0: Year, 1: Cost Difference [Dollars]\n")
            for year, payback in zip(range(1, len(MultiYearPayback) + 1), MultiYearPayback):
                outputFile.write("%d \t %.0f\n" % (year, payback))

            # Writing CO2Saving Data
        with open(outputFileNameMultiYearOperationalCO2Sav, "w") as outputFile:
            outputFile.write("# 0: Year, 1: Operational CO2 Savings [kg]\n")
            for year, CO2Saving in zip(range(1, len(MultiYearOperationalCO2Sav) + 1), MultiYearOperationalCO2Sav):
                outputFile.write("%d \t %.0f\n" % (year, CO2Saving))

        return CAnnBase, TotalAnnCostSaving, PercAnnSaving, TotalOperationalCO2Sav,TotalEmbodiedCO2, TotalCO2Sav, CAnnSCCSav, CAnnGovtSav, CIniRetrofit
