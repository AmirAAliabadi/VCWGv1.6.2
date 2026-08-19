import os
import numpy
import multiprocessing
from UWG import UWG
from BEMMonthly import BEMMonthly
from BEMDiurnal import BEMDiurnal

def simulate_month(args_list):
    """
    Run simulation for one month.
    """
    (month, ene_mode, opt_A_PV, opt_A_WT, opt_Infil, opt_Vent,
     opt_AlbRoof, opt_Glz, opt_SHGC, opt_V_BITES, opt_A_ST,
     opt_m_dot_st_f, opt_m_dot_he_st, opt_T_melt, opt_V_pcm,
     initialization_name, case_name, epw_filename) = args_list

    # Define month strings and output data types
    Months = ['Jan.txt', 'Feb.txt', 'Mar.txt', 'Apr.txt', 'May.txt', 'Jun.txt',
              'Jul.txt', 'Aug.txt', 'Sep.txt', 'Oct.txt', 'Nov.txt', 'Dec.txt']
    OutputData = ['BEM', 'q_profiles', 'Tepw', 'TKE_profiles', 'Tr_profiles',
                  'Tu_profiles', 'U_profiles', 'V_profiles']

    # Advanced energy heat mode for 12 months: Heating (1), Cooling (0), etc.
    Adv_ene_heat_mode = [1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1]

    # Create the initialization filename for this month
    param_filename = initialization_name + '_' + str(month) + '.uwg'
    Month_name = Months[month - 1].split('.')[0]  # Extracting the month name from the file name (removing the '.txt' extension)

    # Create the UWG object and run the simulation for this month
    uwg = UWG(ene_mode, opt_A_PV, opt_A_WT, opt_Infil, opt_Vent, opt_AlbRoof,
              opt_Glz, opt_SHGC, opt_V_BITES, opt_A_ST, opt_m_dot_st_f,
              opt_m_dot_he_st, opt_T_melt, opt_V_pcm,
              epw_filename, Month_name, param_filename, '', '', '', '')
    uwg.run()

    # Run the monthly and diurnal building energy models
    GasConsumpHeat, ElecHeatDemand, ElecCoolDemand, GasConsumpWaterHeat, \
        ElecDomesticDemand, ElecProducedPV, ElecProducedWT = \
        BEMMonthly(Adv_ene_heat_mode[month - 1],
                   'Output/Perf-Metrics-' + case_name + '-' + Months[month - 1],Months[month - 1])
    BEMDiurnal(Adv_ene_heat_mode[month - 1],
               "Output/Perf-Metrics-Diurnal-" + case_name + '-' + Months[month - 1],Months[month - 1])

    # Copy some variables for use by other functions
    alb_roof = uwg.alb_roof     # Roof albedo [-]
    V_pcm = uwg.V_pcm           # Phase change material per building foot print area [m^3 m^-2]
    A_st = uwg.A_st             # Solar thermal area per building foot print area [m^2 m^-2]
    V_bites = uwg.V_bites       # Building thermal storage volume per building foot print area [m^3 m^-2]
    A_wt = uwg.A_wt             # Swept wind area per building foot print area [m^2 m^-2]
    A_pv = uwg.A_pv             # Solar photovoltaic area per building foot print area [m^2 m^-2]

    # Return all the required outputs including the new variables
    return (GasConsumpHeat, ElecHeatDemand, ElecCoolDemand, GasConsumpWaterHeat,
            ElecDomesticDemand, ElecProducedPV, ElecProducedWT,
            alb_roof, V_pcm, A_st, V_bites, A_wt, A_pv, case_name)


def opt_VCWG(ene_mode, opt_A_PV, opt_A_WT, opt_Infil, opt_Vent, opt_AlbRoof, opt_Glz,
             opt_SHGC, opt_V_BITES, opt_A_ST, opt_m_dot_st_f, opt_m_dot_he_st,
             opt_T_melt, opt_V_pcm, k, i, i_pop,SSPScenario,Year):
    """
    Run the 12-month simulation concurrently and aggregate the results.
    """
    epw_filename = 'Toronto_ssp{}_{}.epw'.format(SSPScenario,Year)
    initialization_name = 'initialize_Toronto'
    case_name = "Toronto-OuterIter" + str(k) + "InnerIter" + str(i) + "Idv" + str(i_pop)

    # Create a list of month indices (1 to 12)
    months = list(range(1, 13))
    # Build the argument list for each month
    args_list = [(month, ene_mode, opt_A_PV, opt_A_WT, opt_Infil, opt_Vent,
                  opt_AlbRoof, opt_Glz, opt_SHGC, opt_V_BITES, opt_A_ST,
                  opt_m_dot_st_f, opt_m_dot_he_st, opt_T_melt, opt_V_pcm,
                  initialization_name, case_name, epw_filename) for month in months]

    # Create the pool manually (Python 2)
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

    # Use pool.map to process each month, passing in arguments as a tuple
    monthly_results = pool.map(simulate_month, args_list)

    # Close and join the pool to ensure all processes finish
    pool.close()
    pool.join()

    # Aggregate monthly results into annual totals
    GasConsumpHeat_arr     = numpy.array([res[0] for res in monthly_results])
    ElecHeatDemand_arr     = numpy.array([res[1] for res in monthly_results])
    ElecCoolDemand_arr     = numpy.array([res[2] for res in monthly_results])
    GasConsumpWaterHeat_arr = numpy.array([res[3] for res in monthly_results])
    ElecDomesticDemand_arr = numpy.array([res[4] for res in monthly_results])
    ElecProducedPV_arr     = numpy.array([res[5] for res in monthly_results])
    ElecProducedWT_arr     = numpy.array([res[6] for res in monthly_results])

    TotalGasConsumpHeatSys  = numpy.sum(GasConsumpHeat_arr)
    TotalGasConsumpWaterHeatSys = numpy.sum(GasConsumpWaterHeat_arr)
    TotalElecHeatDemandSys  = numpy.sum(ElecHeatDemand_arr)
    TotalElecCoolDemandSys  = numpy.sum(ElecCoolDemand_arr)
    TotalElecProducedPVSys  = numpy.sum(ElecProducedPV_arr)
    TotalElecProducedWTSys  = numpy.sum(ElecProducedWT_arr)
    TotalElecDomesticDemand = numpy.sum(ElecDomesticDemand_arr)

    # Extract the non-aggregated variables (alb_roof, V_pcm, A_st, V_bites, A_wt, A_pv)
    alb_roof = numpy.mean([res[7] for res in monthly_results])
    V_pcm = numpy.mean([res[8] for res in monthly_results])
    A_st = numpy.mean([res[9] for res in monthly_results])
    V_bites = numpy.mean([res[10] for res in monthly_results])
    A_wt = numpy.mean([res[11] for res in monthly_results])
    A_pv = numpy.mean([res[12] for res in monthly_results])

    # Return the aggregated annual results along with the case name
    return TotalGasConsumpHeatSys, TotalGasConsumpWaterHeatSys, TotalElecHeatDemandSys, \
           TotalElecCoolDemandSys, TotalElecProducedPVSys, TotalElecProducedWTSys, \
           TotalElecDomesticDemand, alb_roof, V_pcm, A_st, V_bites, A_wt, A_pv, case_name
