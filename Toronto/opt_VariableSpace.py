# Variable space for the optimization
# Developed by Xuan Chen and Amir A. Aliabadi
# Atmospheric Innovations Research (AIR) Laboratory, University of Guelph, Guelph, Canada
# last update: 22 December 2022

import numpy
import pandas

def Space():

    # PV area per building footprint area [m2 m-2]
    lPV = 0.1
    hPV = 0.6
    intervalPV = 0.1

    # WT area per building footprint area [m2 m-2]
    lWT = 0.05
    hWT = 0.2
    intervalWT = 0.025

    # R_roof value [m2 K W-1]
    # Minimum R value
    # ASHRAE 90.1 Table 5.5-5 (non-residential, residential)
    # NECB Table 3.2.2.2
    # ASHRAE: R min = 5.3 for zone 5; NECB: R min = 5.464 for Zone 5;
    lRroof = 5.46
    hRroof = 11.5
    intervalRroof = 0.5

    # R_wall value [m2 K W-1]
    # Minimum R value
    # ASHRAE 90.1 Table 5.5-5 (non-residential, residential)
    # NECB Table 3.2.2.2
    # ASHRAE: R min = 2.3 for zone 5; NECB: R min = 3.597 for Zone 5;
    lRwall = 3.6
    hRwall = 7
    intervalRwall = 0.5

    # Infiltration  rate [ACH]
    # ASHRAE 90.1 Sentence C3.5.5.3 (non-residential)
    # ASHRAE 90.2 Sentence 6.3.2 (residential)
    # ASHRAE: I max = 3 [ACH] (residential), 2.03 [L s-1 m-2] = 3.65 [ACH] (non-residential) for zone 5;
    # Note: 1 [l s-1 m-2] = 1.8 [ACH] assuming floor height of 2 [m]
    # the base case in DOE BLD 6 is 0.64 ACH, in ASHRAE 90.1 is 1.218 ACH,
    lI = 0.5
    hI = 1.5
    intervalI = 0.25

    # Ventilation rate [L s-1 m-2]
    # ASHRAE 62.1 Table 6.1
    # ASHRAE 62.2 Table 4-1b
    # ASHRAE: V min = 0.3 (non-residential), ~0.3 (residential)
    lV = 0.3
    hV = 0.4
    intervalV = 0.02

    # Roof albedo [-]
    # Minimum albedo is associated with normal roofs (e.g. ashfalt, shingle)
    # normal ashfalt albedo 0.05 - 0.2
    lAlbRoof = 0.1
    hAlbRoof = 0.7
    intervalAlbRoof = 0.1

    # Glazing ratio [-]
    # Maximum glazing ratio
    # ASHRAE 90.1 Table 5.5-5 (non-residential)
    # NECB Table A-3.2.1.4(1): Fenestration and Door area to gross Wall area Ratio (FDWR)
    # FDWR = 0.4 for Heating Degree Days HDD <= 4000 (Zone 5 HDD: 3000 - 4000)
    lGlz = 0.1
    hGlz = 0.4
    intervalGlz = 0.05

    # Solar heat gain coefficient (SHGC) [-]
    # Maximum SHGC
    # ASHRAE 90.1 Table 5.5-5 (non-residential)
    # ASHRAE 90.2 Table 6-2 (residential)
    # NECB Table 3.2.2.3
    # Not required for Zone 5 (residential); but max = 0.4 for Zone 5 (non-residential)
    # ASHRAE: u-value max = 1.82 [W m-2 K-1] for zone 5
    # NECB: u-value max = 2.2 [W m-2 K-1] for zone 5
    lSHGC = 0.1
    hSHGC = 0.7
    intervalSHGC = 0.1

    # Volume of BITES per building footprint area [m^3 m^-2]
    # The lower limit must be positive, not zero
    lVBITES = 0.05
    hVBITES = 0.25
    intervalVBITES = 0.04

    # Area of ST per building footprint area [m^2 m^-2]
    lAST = 0.1
    hAST = 0.6
    intervalAST = 0.1

    # Mass flow rate of working fluid in ST [kg s^-1 m^-2]
    # The lower limit must be positive, not zero
    lmfST = 0.0002
    hmfST = 0.002
    intervalmfST = 0.0002

    # Mass flow rate of air in ST heat exchanger [kg s^-1 m^-2]
    # The lower limit must be positive, not zero
    lmaST = 0.002
    hmaST = 0.02
    intervalmaST = 0.002

    # Melting temperature of PCM [K]
    # Check! for Inorganic Salt Hydrate 299 in the initialization file
    lTmelt = 290
    hTmelt = 310
    intervalTmelt = 4

    # Volume of PCM per building footprint area [m^3 m^-2]
    # The lower limit must be positive, not zero
    lVpcm = 0.02
    hVpcm = 0.20
    intervalVpcm = 0.02

    # ---------------------------Policy________________________
    # Rebates for PV
    lRebate = 20000
    hRebate = 50000
    intervalRebate = 5000

    # Loans for PV
    lloan = 0
    hloan = 10000
    intervalloan = 2000

    # Interste rate for loan
    lIntRate = 0.25
    hIntRate = 1.5
    intervalIntRate = 0.25

    # Fuel Taxes
    lfueltax = 0
    hfueltax = 10
    intervalfueltax = 2

    # Elec Taxes
    lelectax = 0
    helectax = 10
    intervalelectax = 2

    # Discretize the variable space
    optPV = numpy.arange(lPV, hPV + intervalPV, intervalPV)
    optWT = numpy.arange(lWT, hWT + intervalWT, intervalWT)

    optRroof = numpy.arange(lRroof, hRroof + intervalRroof, intervalRroof)
    optRwall = numpy.arange(lRwall, hRwall + intervalRwall, intervalRwall)

    optI = numpy.arange(lI, hI + intervalI, intervalI)
    optV = numpy.arange(lV, hV + intervalV, intervalV)

    optAlbRoof = numpy.arange(lAlbRoof, hAlbRoof + intervalAlbRoof, intervalAlbRoof)
    optGlz = numpy.arange(lGlz, hGlz + intervalGlz, intervalGlz)
    optSHGC = numpy.arange(lSHGC, hSHGC + intervalSHGC, intervalSHGC)

    opt_V_BITES  = numpy.arange(lVBITES, hVBITES + intervalVBITES, intervalVBITES)
    opt_A_ST = numpy.arange(lAST, hAST + intervalAST, intervalAST)
    opt_m_dot_st_f = numpy.arange(lmfST, hmfST + intervalmfST, intervalmfST)
    opt_m_dot_he_st = numpy.arange(lmaST, hmaST + intervalmaST, intervalmaST)
    opt_T_melt = numpy.arange(lTmelt, hTmelt + intervalTmelt, intervalTmelt)
    opt_V_pcm = numpy.arange(lVpcm, hVpcm + intervalVpcm, intervalVpcm)


    optRebate = numpy.arange(lRebate, hRebate + intervalRebate, intervalRebate)
    optloan = numpy.arange(lloan, hloan + intervalloan, intervalloan)


    optIntRate = numpy.arange(lIntRate, hIntRate + intervalIntRate, intervalIntRate)

    optfueltax = numpy.arange(lfueltax, hfueltax + intervalfueltax, intervalfueltax)
    optelectax = numpy.arange(lelectax, helectax + intervalelectax, intervalelectax)



    space = {'A_PV': optPV, 'A_WT': optWT, 'Rvalue_roof': optRroof, 'Rvalue_wall': optRwall,
             'Infiltration': optI, 'Ventilation': optV, 'Albedo_roof': optAlbRoof, 'Glazing': optGlz, 'SHGC': optSHGC,
             'V_bites': opt_V_BITES, 'A_ST': opt_A_ST, 'm_dot_st_f': opt_m_dot_st_f, 'm_dot_he_st': opt_m_dot_he_st, 'T_melt': opt_T_melt, 'V_pcm': opt_V_pcm,
             'Rebate': optRebate, 'Loan': optloan, 
             'IntRate': optIntRate, 'Fueltax': optfueltax, 'Electax': optelectax}

    return space, lRroof, lRwall

# Select "1" for variable to be included in the optimization
# Select "0" for variable to be excluded from the optimization

def Choice(ene_mode):
    # Only PV and WT
    if ene_mode == 3:
        choice =  {'A_PV':          1,
                   'A_WT':          1,
                   'Rvalue_roof':   1,
                   'Rvalue_wall':   1,
                   'Infiltration':  1,
                   'Ventilation':   0,
                   'Albedo_roof':   1,
                   'Glazing':       1,
                   'SHGC':          1}

    # Base model with no renewable/alternative energy
    elif ene_mode == 2:
        choice =  {'Rvalue_roof':   1,
                   'Rvalue_wall':   1,
                   'Infiltration':  1,
                   'Ventilation':   0,
                   'Albedo_roof':   1,
                   'Glazing':       1,
                   'SHGC':          1}

    # Advanced energy mode with heating (1) and cooling (0) options
    # To run fast optimization, do not select more than 9 variables
    elif ene_mode == None:
        choice =  {'A_PV':          1,
                   'A_WT':          0,
                   'Rvalue_roof':   1,
                   'Rvalue_wall':   1,
                   'Infiltration':  1,
                   'Ventilation':   0,
                   'Albedo_roof':   1,
                   'Glazing':       1,
                   'SHGC':          1,
                   'V_bites':       1,
                   'A_ST':          1,
                   'm_dot_st_f':    0,
                   'm_dot_he_st':   0,
                   'T_melt':        0,
                   'V_pcm':         0,
                   'Rebate':        1,
                   'Loan':          1,
                   'IntRate':       1,
                   'Fueltax':       1,
                   'Electax':       1,
                   }

    return choice

# Generate option space and number of variables
def SetOptVar(space, choice):
    choice_items = choice.items()
    choice_list = list(choice_items)
    choice_df = pandas.DataFrame(choice_list, columns=['var_name', 'switch'])
    n_var = choice_df['switch'].sum()
    final_space = []
    final_namelist = []
    for var_name in space:
        if var_name in choice:
            if choice[var_name] == 1:
                print (var_name)
                final_space.append(space[var_name])
                final_namelist.append(var_name)

    # Output is dictionary
    zip_list = zip(final_namelist, final_space)
    options_space = dict(zip_list)

    return options_space, n_var