
from Psychrometrics import psychrometrics, moist_air_density
import logging
import numpy
import math

"""
Calculate building characteristics
Developed by Mojtaba Safdari, Mohsen Moradi, Amir A. Aliabadi
Atmospheric Innovations Research (AIR) Laboratory, University of Guelph, Guelph, Canada
Last update: 2024-09-06
"""
class Building(object):

    TEMPERATURE_COEFFICIENT_CONFLICT_MSG = "FATAL ERROR!"

    def __init__(self,floorHeight,intHeatNight,intHeatDay,intHeatFRad,\
            intHeatFLat,infil,vent,glazingRatio,uValue,shgc,\
            condType,cop,coolSetpointDay,coolSetpointNight,\
            heatSetpointDay,heatSetpointNight,coolRHSetpointDay, coolRHSetpointNight,\
            heatRHSetpointDay, heatRHSetpointNight,coolCap,heatEff,initialTemp,initialHum):

            self.floorHeight =float(floorHeight)            # floor height
            self.intHeat = intHeatNight                     # timestep internal sensible heat gain per unit floor area [W m^-2]
            self.intHeatNight = intHeatNight                # nighttime internal heat gain per unit floor area [W m^-2]
            self.intHeatDay = intHeatDay                    # daytime internal heat gain per unit floor area [W m^-2]
            self.intHeatFRad = intHeatFRad                  # internal gain radiant fraction
            self.intHeatFLat = intHeatFLat                  # internal gain latent fraction
            self.infilBase = infil                          # Infiltration Air Change per Hour (ACH) [hr^-1] (excludes natural ventilation)
            self.infil = infil                              # Infiltration Air Change per Hour (ACH) [hr^-1] (includes natural ventilation if enabled)
            self.vent = vent                                # Ventilation rate per unit floor area [m^3 s^-1 m^-2]
            self.glazingRatio = glazingRatio                # glazing ratio
            self.uValue = uValue                            # window U-value [W m^-2 K^-1] including film coefficient
            self.shgc = shgc                                # window Solar Heat Gain Coefficient (SHGC), fraction of radiation that is admitted through a window
            self.condType = condType                        # cooling condensation system type: AIR, WATER
            self.cop = cop                                  # COP of cooling system (nominal)
            self.coolSetpointDay = coolSetpointDay          # daytime indoor cooling setpoint [K]
            self.coolSetpointNight = coolSetpointNight      # nighttime indoor heating setpoint [K]
            self.heatSetpointDay = heatSetpointDay          # daytimge indoor heating setpoint [K]
            self.heatSetpointNight = heatSetpointNight      # nighttime indoor heating setpoint [K]
            self.coolRHSetpointDay = coolRHSetpointDay      # daytime indoor cooling RH setpoint [%]
            self.coolRHSetpointNight = coolRHSetpointNight  # nighttime indoor heating RH setpoint [%]
            self.heatRHSetpointDay = heatRHSetpointDay      # daytimge indoor heating RH setpoint [%]
            self.heatRHSetpointNight = heatRHSetpointNight  # nighttime indoor heating RH setpoint [%]
            self.heatEff = heatEff                          # heating system capacity (-)
            self.indoorTemp = initialTemp                   # Indoor Air Temperature [K]
            self.indoorHum = initialHum                     # Indoor specific humidity [kgv kga^-1]
            self.copAdj = cop                               # adjusted COP per temperature
            self.canyon_fraction = 1.0                      # Default canyon fraction

            self.Type = "null"                              # DOE reference building type
            self.Era = "null"                               # pre80, pst80, new
            self.Zone = "null"                              # Climate zone number

            # Advanced Renewable Energy Parameters
            self.T_st_f_i = initialTemp                # ST working fluid inlet initial temperature [K]
            self.T_st_f_o = initialTemp                # ST working fluid outlet initial temperature [K]
            self.T_he_st_i = initialTemp               # ST heat exchanger air inlet initial temperature [K]
            self.T_he_st_o = initialTemp               # ST heat exchanger air outlet initial temperature [K]
            self.T_bites = initialTemp                 # BITES initial temperature [K]
            self.Q_st = 0                              # Heat flux from ST [W m^-2]
            self.Q_he_st = 0                           # Heat flux from ST heat exchanger [W m^-2]
            self.Q_bites = 0                           # Heat flux from BITES [W m^-2]
            self.Q_hp = 0                              # Heat flux from auxiliary HP [W m^-2]
            self.Q_recovery = 0                        # Recovery heat [W m^-2]
            self.W_hp = 0                              # Electricity consumed by auxiliary HP [W m^-2]
            self.W_pv = 0                              # Electricity produced by PV [W m^-2]
            self.W_wt = 0                              # Electricity produced by wind turbine [W m^-2]
            self.COP_hp = 1                            # COP of auxiliary HP
            self.Frac_Q_hp = 0                         # Fraction sensible heating demand satisfied by auxiliary HP
            self.f_pcm = 0.5                           # Fraction of PCM melted
            self.Q_waterSaved = 0                      # Heat flux saved for water heating [W m^-2]
            self.Q_ground = 0                          # Ground heat flux from deep soil to BITES [W m^-2]
            self.Q_waterRecovery = 0                   # Recovery heat from domestic water (heating mode) [W m^-2]

            # Logger will be disabled by default unless explicitly called in tests
            self.logger = logging.getLogger(__name__)

    def __repr__(self):
        return "BuildingType: {a}, Era: {b}, Zone: {c}".format(
            a=self.Type,
            b=self.Era,
            c=self.Zone
            )

    def is_near_zero(self,val,tol=1e-14):
        return abs(float(val)) < tol

    def BEMCalc(self, UCM, BEM, forc, parameter, simTime, bx, by,
                beta_st, A_st, U_st, FR_st, tau_alpha_e_st, eta_he_st, V_bites, c_bites, m_dot_st_f,
                c_st_f, m_dot_he_st, theta_Z, zeta_S, T_a_roof, Adv_ene_heat_mode,
                beta_pv, A_pv, eta_pv, COP_hp_min, COP_hp_max, T_hp_min, T_hp_max,
                A_wt, eta_wt, S_wt_min, S_wt_max, WindRoof, V_pcm, l_pcm, T_melt, rural, hvacflag, vx, vy, dz, windowList):

        self.logger.debug("Logging at {} {}".format(__name__, self.__repr__()))

        # Building Energy Model
        self.ElecTotal = 0.0                            # total electricity consumption - [W m^-2] of floor
        self.nFloor = max(UCM.bldHeight/float(self.floorHeight),1)   # At least one floor
        self.sensCoolDemand = 0.0                       # building sensible cooling demand per unit building footprint area [W m^-2]
        self.sensHeatDemand = 0.0                       # building sensible heating demand per unit building footprint area [W m^-2]
        self.sensWaterHeatDemand = 0.0                  # building sensible water heating demand per unit building footprint area [W m^-2]
        self.coolConsump  = 0.0                         # cooling energy consumption per unit building footprint area OR per unit floor area [W m^-2]
        self.heatConsump  = 0.0                         # heating energy consumption per unit floor area [W m^-2]
        self.waterHeatConsump = 0.0                     # water heating consumption [W m^-2]
        self.sensWaste = 0.0                            # Total Sensible waste heat per unit building footprint area including cool, heat, dehum, water, and gas [W m^-2]
        self.sensWasteCoolHeatLatent = 0.0              # Sensible waste heat per unit building footprint area only including cool, heat, and dehum [W m^-2]
        self.latentDemand = 0.0                         # Latent demand per unit building footprint area [W m^-2]
        self.dehumDemand  = 0.0                         # Latent demand (dehumidification) per unit building footprint area [W m^-2]
        self.humDemand = 0.0                            # Latent demand (humidification) per unit building footprint area [W m^-2]
        self.Qhvac = 0.0                                # Total heat removed (sensible + latent)
        self.elecDomesticDemand = 0.0                   # Electricity demand for appliances and lighting (not for energy) per building footprint area [W m^-2]
        self.Q_st = 0                                   # Heat flux from ST [W m^-2]
        self.Q_he_st = 0                                # Heat flux from ST heat exchanger [W m^-2]
        self.Q_bites = 0                                # Heat flux from BITES [W m^-2]
        self.Q_hp = 0                                   # Heat flux from auxiliary HP [W m^-2]
        self.Q_recovery = 0                             # Recovery heat [W m^-2]
        self.W_hp = 0                                   # Electricity consumed by auxiliary HP [W m^-2]
        self.W_pv = 0                                   # Electricity produced by PV [W m^-2]
        self.W_wt = 0                                   # Electricity produced by wind turbine [W m^-2]
        self.COP_hp = 1                                 # COP of auxiliary HP
        self.Q_waterSaved = 0                           # Heat flux saved for water heating [W m^-2]
        self.Q_ground = 0                               # Ground heat flux from deep soil to BITES [W m^-2]
        self.Q_waterRecovery = 0                        # Recovery heat from domestic water (heating mode) [W m^-2]
        # [kgv m^-3] Moist air density given dry bulb temperature, humidity ratio, and pressure
        dens =  moist_air_density(forc.pres,self.indoorTemp,self.indoorHum)
        evapEff = 1.                                    # evaporation efficiency in the condenser for evaporative cooling devices
        volVent = self.vent * self.nFloor               # total ventilation volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
        self.infil = self.infilBase                     # Infiltration Air Change per Hour (ACH) [hr^-1] (excludes natural ventilation)
        volInfil = self.infilBase * UCM.bldHeight/3600. # total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
        T_wall = BEM.wall.layerTemp[-1]                 # Inner layer
        massFlowRateSWH = BEM.SWH * self.nFloor/3600.   # Solar water heating per building footprint area per hour [kg s^-1 m^-2] (Change of units [hr^-1] to [s^-1]
        T_ceil = BEM.roof.layerTemp[-1]                 # Inner layer
        T_mass = BEM.mass.layerTemp[0]                  # Outer layer
        T_indoor = self.indoorTemp                      # Indoor temp (initial)

        # Normalize areas to building foot print [m^2 m^-2]
        facArea = 2*UCM.bldHeight/numpy.sqrt(bx*by)     # Facade (exterior) area per unit building footprint area [m^2 m^-2]
        wallArea = facArea*(1.-self.glazingRatio)       # Wall area per unit building footprint area [m^2 m^-2]
        winArea = facArea*self.glazingRatio             # Window area per unit building footprint area [m^2 m^-2]
        massArea = 2*self.nFloor-1                      # ceiling and floor (top & bottom) per unit building footprint area [m^2 m^-2]
        ceilingArea = 1                                 # ceiling area per unit building footprint area [m^2 m^-2]; must be equal to 1; we are geneous!

        # Set temperature set points according to night/day set points in building schedule & simTime; need the time in [hr]
        isEqualNightStart = self.is_near_zero((simTime.secDay/3600.) - parameter.nightSetStart)
        if simTime.secDay/3600. < parameter.nightSetEnd or (simTime.secDay/3600. > parameter.nightSetStart or isEqualNightStart):
            self.logger.debug("{} Night set points @{}".format(__name__,simTime.secDay/3600.))

            # Set point temperatures [K] and relative humidity [%]
            T_cool = self.coolSetpointNight
            T_heat = self.heatSetpointNight
            RH_cool = self.coolRHSetpointNight
            RH_heat = self.heatRHSetpointNight

            # Internal heat per unit building footprint area [W m^-2]
            self.intHeat = self.intHeatNight * self.nFloor
        else:
            self.logger.debug("{} Day set points @{}".format(__name__,simTime.secDay/3600.))

            # Set point temperatures [K] and relative humidity [%]
            T_cool = self.coolSetpointDay
            T_heat = self.heatSetpointDay
            RH_cool = self.coolRHSetpointDay
            RH_heat = self.heatRHSetpointDay

            # Internal heat per unit building footprint area [W m^-2]
            self.intHeat = self.intHeatDay*self.nFloor

        # Set point specific humidities [kgv kga^-1]
        # Tetens equation: Pg = 610.78 exp(17.27 T / (T+237.3)) with Pg [Pa] ant T [C]
        # Saturation pressure [Pa]
        Pg_cool = 610.78 * math.exp(17.27 * (T_cool - 273.15) / ((T_cool - 273.15) + 237.3))
        Pg_heat = 610.78 * math.exp(17.27 * (T_heat - 273.15) / ((T_heat - 273.15) + 237.3))
        # Specific humidity set points [kgv kga^-1]
        q_cool = 0.622 * (RH_cool/100) * Pg_cool / (forc.pres - (RH_cool/100) * Pg_cool)
        q_heat = 0.622 * (RH_heat/100) * Pg_heat / (forc.pres - (RH_heat/100) * Pg_heat)

        # Indoor convection heat transfer coefficients
        # wall convective heat transfer coefficient [W m^-2 K^-1]
        zac_in_wall = 3.076
        # other surfaces convective heat transfer coefficient [W m^-2 K^-1]
        zac_in_mass = 0.948
        zac_in_ceil = 0.948
        # Specific heat of air on a mass basis [J kg^-1 K^-1]
        cp_air = 1004
        # Specific heat of air on a volume basis [J m^-3 K^-1]
        cv_air = 1208
        # Maximum and minimum temperature of BITES [K]
        T_bites_max = T_hp_max
        T_bites_min = T_hp_min

        # Calculate deep soil temperature, deep soil depth, and deep soil thermal resistance
        Tdeep = rural.layerTemp[-1]
        Rdeep = numpy.sum(rural.layerThickness) / rural.layerThermalCond[-1]

        # Canyon temperature and specific humidity
        self.Tcanyon = UCM.canTemp
        self.qcanyon = UCM.canHum

        # -------------------------------------------------------------
        # Heat fluxes [W m^-2]
        # -------------------------------------------------------------

        # If there is renewable energy, calculate electricty produced by PV
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1) or (Adv_ene_heat_mode == 3):
            # Calculate normal incident shortwave radiation flux on the PV system
            I_dir = forc.dir * math.cos(zeta_S * numpy.pi / 180) * math.cos((theta_Z - beta_pv) * numpy.pi / 180)
            self.W_pv = max(eta_pv * A_pv * I_dir, 0)

        # If there is renewable energy, calculate ground heat flux from soil to BITES
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            self.Q_ground = (Tdeep - self.T_bites) / Rdeep

        # If there is renewable energy, calculate electricity produced by wind turbine
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1) or (Adv_ene_heat_mode == 3):
            if (WindRoof >= S_wt_min) and (WindRoof <= S_wt_max):
                self.W_wt = 0.5 * eta_wt * dens * A_wt * WindRoof**3
            else:
                self.W_wt = 0

        # If there is renewable energy
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            # Calculate heat flux absorbed by the ST collector per building footprint area [W m^-2] (Smith and Weiss 1977)
            if simTime.secDay / 3600. < parameter.nightSetEnd or (
                    simTime.secDay / 3600. > parameter.nightSetStart or isEqualNightStart):
                # Night
                # Omit shortwave radiation flux from collector equation (Smith and Weiss 1977)
                self.Q_st = FR_st * A_st * (- U_st * (self.T_st_f_i - T_a_roof))
            else:
                # Day
                # Calculate normal incident shortwave radiation flux on the ST system
                I = forc.dir * math.cos(zeta_S * numpy.pi / 180) * math.cos((theta_Z-beta_st) * numpy.pi / 180) + forc.dif
                # Calculate any available energy flux from the ST system.
                self.Q_st = FR_st * A_st * (tau_alpha_e_st * I - U_st * (self.T_st_f_i - T_a_roof))

        if Adv_ene_heat_mode == 1:
            # If available solar thermal energy is positive store it in the BITES system
            if self.Q_st > 0:
                # Calculate output temperature of working fluid out of the ST system
                self.T_st_f_o = self.Q_st / (m_dot_st_f * c_st_f) + self.T_st_f_i
                # Calculate output temperature of air out of ST system heat exchanger
                self.T_he_st_o = (m_dot_st_f * c_st_f) / (m_dot_he_st * cp_air) * eta_he_st * (self.T_st_f_o - self.T_he_st_i) + self.T_he_st_i
                # Calculate input temperature of working fluid into ST system using energy balance for the heat exchanger
                self.T_st_f_i = self.T_st_f_o - (m_dot_he_st * cp_air) / (m_dot_st_f * c_st_f) * (self.T_he_st_o - self.T_he_st_i)

                # Check if PCM can be utilized
                self.Q_he_st = m_dot_he_st * cp_air * (self.T_he_st_o - self.T_he_st_i)
                if (self.T_bites >= T_melt) and (self.f_pcm < 1):
                    V_melt = self.Q_he_st * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm + V_melt/V_pcm
                else:
                    # Calculate heat storage and change in temperature of BITES
                    Delta_T_bites = self.Q_he_st * simTime.dt / (V_bites * c_bites)
                    self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
            else:
                self.T_st_f_i = T_a_roof
                self.Q_he_st = 0
        elif Adv_ene_heat_mode == 0:
            # If ST collector can reject heat, reject some heat from the BITES system
            if self.Q_st < 0:
                # Calculate output temperature of working fluid out of the ST system
                self.T_st_f_o = self.Q_st / (m_dot_st_f * c_st_f) + self.T_st_f_i
                # Calculate output temperature of air out of ST system heat exchanger
                self.T_he_st_o = (m_dot_st_f * c_st_f) / (m_dot_he_st * cp_air) * eta_he_st * (self.T_st_f_o - self.T_he_st_i) + self.T_he_st_i
                # Calculate input temperature of working fluid into ST system using energy balance for the heat exchanger
                self.T_st_f_i = self.T_st_f_o - (m_dot_he_st * cp_air) / (m_dot_st_f * c_st_f) * (self.T_he_st_o - self.T_he_st_i)

                # Check if PCM can be utilized
                self.Q_he_st = m_dot_he_st * cp_air * (self.T_he_st_o - self.T_he_st_i)
                if (self.T_bites <= T_melt) and (self.f_pcm > 0):
                    V_melt = -self.Q_he_st * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm - V_melt/V_pcm
                else:
                    # Calculate heat storage and change in temperature of BITES
                    Delta_T_bites = self.Q_he_st * simTime.dt / (V_bites * c_bites)
                    self.T_bites = max(self.T_bites + Delta_T_bites, T_bites_min)
            else:
                self.T_st_f_i = T_a_roof
                self.Q_he_st = 0

        # Solar Heat Gain on windows per building footprint area [W m^-2]:
        # = radiation intensity [W m^-2] * Solar Heat Gain Coefficient (SHGC) * window area per unit building foot print area [m^2 m^-2]
        winTrans = (BEM.wall.solRec * self.shgc * winArea)

        # Note: at the moment the infiltration and system air temperatures are considered to be the same
        # This is a serious limitation.
        # Future versions of UWG must calculate the system temperature based on HVAC system parameters
        # Heat/Cooling load per unit building footprint area [W m^-2], if any
        self.sensCoolDemand = max(
            wallArea*zac_in_wall*(T_wall - T_cool) +            # wall load per unit building footprint area [W m^-2]
            massArea*zac_in_mass*(T_mass - T_cool) +            # other surfaces load per unit building footprint area [W m^-2]
            winArea*self.uValue*(self.Tcanyon-T_cool) +         # window load due to temperature difference per unit building footprint area [W m^-2]
            ceilingArea*zac_in_ceil *(T_ceil-T_cool) +          # ceiling load per unit building footprint area [W m^-2]
            self.intHeat +                                      # internal load per unit building footprint area [W m^-2]
            volInfil*dens*parameter.cp*(self.Tcanyon-T_cool) +  # infiltration load per unit building footprint area [W m^-2]
            volVent*dens*parameter.cp*(self.Tcanyon-T_cool) +   # ventilation load per unit building footprint area [W m^-2]
            winTrans,                                           # solar load through window per unit building footprint area [W m^-2]
            0.)

        self.sensHeatDemand = max(
            -(wallArea*zac_in_wall*(T_wall-T_heat) +            # wall load per unit building footprint area [W m^-2]
            massArea*zac_in_mass*(T_mass-T_heat) +              # other surfaces load per unit building footprint area [W m^-2]
            winArea*self.uValue*(self.Tcanyon-T_heat) +         # window load due to temperature difference per unit building footprint area [W m^-2]
            ceilingArea*zac_in_ceil*(T_ceil-T_heat) +           # ceiling load per unit building footprint area [W m^-2]
            self.intHeat +                                      # internal load per unit building footprint area [W m^-2]
            volInfil*dens*parameter.cp*(self.Tcanyon-T_heat) +  # infiltration load per unit building footprint area [W m^-2]
            volVent*dens*parameter.cp*(self.Tcanyon-T_heat) +   # ventilation load per unit building footprint area [W m^-2]
            winTrans),                                          # solar load through window per unit building footprint area [W m^-2]
            0.)

        # Now consider natural ventilation and recalculate sensible cooling/heating demand if needed
        for i in range(0, len(windowList)):
            windowList[i].state = 0.0

        # Cooling mode
        if self.sensCoolDemand > 0.0 and UCM.canTemp > 288.0:

            # Consider natural ventilation if hvacflag == 1 and indoor/outdoor temperatures are in range 0-35 C
            if (hvacflag == 1) and (T_indoor > 273 and T_indoor < 308) and (self.Tcanyon > 273 and self.Tcanyon < 308):

                # Apply natural ventilation
                if (((self.Tcanyon < T_indoor) and (T_cool < T_indoor))):

                    if ((self.indoorHum > q_cool) and (UCM.canHum < self.indoorHum)) or (
                            (self.indoorHum < q_cool) and (UCM.canHum > self.indoorHum)):

                        # ASHRAE Fundamentals (2017): Chapter 16 Equation 37
                        windowACH = 0
                        zoneVolume = UCM.bldHeight * bx * by
                        for i in range(0, len(windowList)):
                            thisbaseline = windowList[i].effectiveness * (windowList[i].openAreaFraction * windowList[i].width * windowList[i].height) * 3600
                            windowLoc = numpy.round(windowList[i].zCoord / dz).astype(int)
                            if (windowList[i].face == 'X'):
                                # X face window
                                windSpeed = vx[windowLoc]
                            else:
                                # Y face window
                                windSpeed = vy[windowLoc]

                            windowList[i].state = 1.0
                            windowACH = windowACH + numpy.abs(thisbaseline * windSpeed) / zoneVolume

                        # Total infiltration in ACH [hr^-1]
                        self.infil = self.infilBase + windowACH
                        # total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
                        volInfil = self.infil * UCM.bldHeight / 3600.

                        # Recalculate sensible cooling demand
                        # Heat/Cooling load per unit building footprint area [W m^-2], if any
                        self.sensCoolDemand = max(wallArea * zac_in_wall * (T_wall - T_cool) +      # wall load per unit building footprint area [W m^-2]
                                        massArea * zac_in_mass * (T_mass - T_cool) +                # other surfaces load per unit building footprint area [W m^-2]
                                        winArea * self.uValue * (self.Tcanyon - T_cool) +           # window load due to temperature difference per unit building footprint area [W m^-2]
                                        ceilingArea * zac_in_ceil * (T_ceil - T_cool) +             # ceiling load per unit building footprint area [W m^-2]
                                        self.intHeat +                                              # internal load per unit building footprint area [W m^-2]
                                        volInfil * dens * parameter.cp * (self.Tcanyon - T_cool) +  # infiltration load per unit building footprint area [W m^-2]
                                        volVent * dens * parameter.cp * (self.Tcanyon - T_cool) +   # ventilation load per unit building footprint area [W m^-2]
                                        winTrans,
                                        # solar load through window per unit building footprint area [W m^-2]
                                        0.)

                # No natural ventilation
                else:
                    # Total infiltration in ACH [hr^-1]
                    self.infil = self.infilBase
                    # Total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
                    volInfil = self.infil * UCM.bldHeight / 3600.
                    for i in range(0, len(windowList)):
                        windowList[i].state = 0.0

            # Do not consider natural ventilation when hvacflag == 0
            else:
                # Total infiltration in ACH [hr^-1]
                self.infil = self.infilBase
                # Total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
                volInfil = self.infil * UCM.bldHeight / 3600.
                for i in range(0, len(windowList)):
                    windowList[i].state = 0.0

            # Latent heat per unit floor area [W m^-2] from infiltration & ventilation from
            # volInfil and volVent: volumetric rate of infiltration or ventilation per unit area [m^3 s^-1 m^-2]
            # parameter.lv: latent heat of evaporation [J kgv^-1]
            # dens: density [kga m^-3]
            # qcanyon: canyon specific humidity [kgv kga^-1]
            # q_cool: set point specific humidity [kgv kga^-1]
            # Latent heat per building footprint area [W m^-2]
            QLinfil = volInfil * dens * parameter.lv * (self.qcanyon - q_cool)
            QLvent = volVent * dens * parameter.lv * (self.qcanyon - q_cool)

        # Heating mode
        elif self.sensHeatDemand > 0.0 and UCM.canTemp < 288.0:

            # Consider natural ventilation if hvacflag == 1 and indoor/outdoor temperatures are in range 0-35 C
            if (hvacflag == 1) and (T_indoor > 273 and T_indoor < 308) and (self.Tcanyon > 273 and self.Tcanyon < 308):

                # Apply natural ventilation
                if (((self.Tcanyon > T_indoor) and (T_heat > T_indoor))):

                    if ((self.indoorHum > q_heat) and (UCM.canHum < self.indoorHum)) or (
                            (self.indoorHum < q_heat) and (UCM.canHum > self.indoorHum)):

                        # ASHRAE Fundamentals (2017): Chapter 16 Equation 37
                        windowACH = 0
                        zoneVolume = UCM.bldHeight * bx * by
                        for i in range(0, len(windowList)):
                            thisbaseline = windowList[i].effectiveness * (windowList[i].openAreaFraction * windowList[i].width * windowList[i].height) * 3600
                            windowLoc = numpy.round(windowList[i].zCoord / dz).astype(int)
                            if (windowList[i].face == 'X'):
                                # X face window
                                windSpeed = vx[windowLoc]
                            else:
                                # Y face window
                                windSpeed = vy[windowLoc]

                            windowList[i].state = 1.0
                            windowACH = windowACH + numpy.abs(thisbaseline * windSpeed) / zoneVolume

                        # Total infiltration in ACH [hr^-1]
                        self.infil = self.infilBase + windowACH
                        # total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
                        volInfil = self.infil * UCM.bldHeight / 3600.

                        # Recalculate sensible heating demand
                        # Heat/Cooling load per unit building footprint area [W m^-2], if any
                        self.sensHeatDemand = max(-(wallArea * zac_in_wall * (T_wall - T_heat) +  # wall load per unit building footprint area [W m^-2]
                              massArea * zac_in_mass * (T_mass - T_heat) +                        # other surfaces load per unit building footprint area [W m^-2]
                              winArea * self.uValue * (self.Tcanyon - T_heat) +                   # window load due to temperature difference per unit building footprint area [W m^-2]
                              ceilingArea * zac_in_ceil * (T_ceil - T_heat) +                     # ceiling load per unit building footprint area [W m^-2]
                              self.intHeat +                                                      # internal load per unit building footprint area [W m^-2]
                              volInfil * dens * parameter.cp * (self.Tcanyon - T_heat) +          # infiltration load per unit building footprint area [W m^-2]
                              volVent * dens * parameter.cp * (self.Tcanyon - T_heat) +           # ventilation load per unit building footprint area [W m^-2]
                              winTrans),                                                          # solar load through window per unit building footprint area [W m^-2]
                            0.)

                # No natural ventilation
                else:
                    # Total infiltration in ACH [hr^-1]
                    self.infil = self.infilBase
                    # Total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
                    volInfil = self.infil * UCM.bldHeight / 3600.
                    for i in range(0, len(windowList)):
                        windowList[i].state = 0.0

            # Do not consider natural ventilation when hvacflag == 0
            else:
                # Total infiltration in ACH [hr^-1]
                self.infil = self.infilBase
                # Total infiltration volumetric flow rate per building footprint area [m^3 s^-1 m^-2]
                volInfil = self.infil * UCM.bldHeight / 3600.
                for i in range(0, len(windowList)):
                    windowList[i].state = 0.0

            # Latent heat per unit floor area [W m^-2] from infiltration & ventilation from
            # volInfil and volVent: volumetric rate of infiltration or ventilation per unit area [m^3 s^-1 m^-2]
            # parameter.lv: latent heat of evaporation [J kgv^-1]
            # dens: density [kga m^-3]
            # qcanyon: canyon specific humidity [kgv kga^-1]
            # q_heat: set point specific humidity [kgv kga^-1]
            # Latent heat per building footprint area [W m^-2]
            QLinfil = volInfil * dens * parameter.lv * (self.qcanyon - q_heat)
            QLvent = volVent * dens * parameter.lv * (self.qcanyon - q_heat)

        # QL: Latent heat per unit floor area [W m^-2] from internal sources (occupants)
        # Latent heat load per unit building footprint area [W m^-2]
        QLintload = self.intHeat * self.intHeatFLat

        # -------------------------------------------------------------
        # HVAC system (cooling demand = [W m^-2] bld footprint)
        # -------------------------------------------------------------
        # If the canyon air temperature is greater than 288 K building energy system is under cooling mode and HVAC enabled
        if self.sensCoolDemand > 0.0 and UCM.canTemp > 288.0:

            # Reduce building sensible cooling demand if possible, update BITES temperature,
            # must be within allowable range of auxiliary HP temperature
            if (Adv_ene_heat_mode == 0) and (self.T_bites > T_hp_min) and (self.T_bites < T_hp_max):
                # Interpolate a COP_hp based on BITES temperature
                self.COP_hp = COP_hp_min + ((COP_hp_max - COP_hp_min)/(T_hp_max - T_hp_min)) * (self.T_bites - T_hp_min)
                # Calculate the absolute value of heat to be rejected into BITES
                self.Q_hp = self.sensCoolDemand
                self.W_hp = self.Q_hp / self.COP_hp
                self.Q_bites = self.Q_hp + self.W_hp
                self.sensCoolDemand = 0

                # Check if PCM can be utilized
                if (self.T_bites >= T_melt) and (self.f_pcm < 1):
                    V_melt = self.Q_bites * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm + V_melt/V_pcm
                else:
                    Delta_T_bites = self.Q_bites * simTime.dt / (V_bites * c_bites)
                    self.T_bites = max(self.T_bites + Delta_T_bites, T_bites_min)
            else:
                self.Q_bites = 0
                self.Q_hp = 0
                self.W_hp = 0

            # Calculate latent demand from infiltration, ventilation, and internal sources
            self.latentDemand = QLinfil + QLvent + QLintload

            self.dehumDemand = max(self.latentDemand, 0.0)
            self.humDemand = max(-self.latentDemand, 0.0)

            # Calculate input work required by the refrigeration cycle per unit building footprint area [W m^-2]
            # COP = QL/Win or Win = QL/COP
            self.coolConsump = (max(self.sensCoolDemand+self.dehumDemand,0.0))/self.copAdj

            # Calculate waste heat from HVAC system per unit building footprint area [W m^-2]
            # Using 1st law of thermodynamics QH = Win + QL
            if (self.condType == 'AIR'):
                self.sensWasteCoolHeatLatent = max(self.sensCoolDemand+self.dehumDemand,0)+self.coolConsump
                self.latWaste = 0.0
            # We have not tested this option; it must be investigated further
            elif (self.condType == 'WAT'):
                self.sensWasteCoolHeatLatent = max(self.sensCoolDemand+self.dehumDemand,0)+self.coolConsump*(1.-evapEff)
                self.latWaste = max(self.sensCoolDemand+self.dehumDemand,0)+self.coolConsump*evapEff

            self.sensHeatDemand = 0.

        # -------------------------------------------------------------
        # HVAC system (heating demand = [W m^-2] bld footprint)
        # -------------------------------------------------------------
        # If the canyon air temperature is less than 288 K building energy system is under heating mode with HVAC enabled
        # Under heating mode, there is no dehumidification
        elif self.sensHeatDemand > 0.0 and UCM.canTemp < 288.0:

            # Reduce building sensible heating demand if possible, update BITES temperature,
            # must be within allowable range of auxiliary HP temperature
            if (Adv_ene_heat_mode == 1) and (self.T_bites > T_hp_min) and (self.T_bites < T_hp_max):
                # Interpolate a COP_hp based on BITES temperature
                self.COP_hp = COP_hp_min + ((COP_hp_max - COP_hp_min) / (T_hp_max - T_hp_min)) * (
                        self.T_bites - T_hp_min)

                # Calculate fraction of sensHeatDemand from HP, linearly interpolate from 0 to 100 %
                self.Frac_Q_hp = (1 / (T_hp_max - T_hp_min)) * (self.T_bites - T_hp_min)

                # Calculate the absolute value of heat from BITES
                self.Q_hp = self.Frac_Q_hp * self.sensHeatDemand
                self.sensHeatDemand = self.sensHeatDemand - self.Q_hp
                self.W_hp = self.Q_hp / self.COP_hp
                self.Q_bites = self.Q_hp - self.W_hp

                # Check if PCM can be utilized
                if (self.T_bites <= T_melt) and (self.f_pcm > 0):
                    V_melt = self.Q_bites * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm - V_melt/V_pcm
                else:
                    Delta_T_bites = - self.Q_bites * simTime.dt / (V_bites * c_bites)
                    self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
            else:
                self.Q_bites = 0
                self.Q_hp = 0
                self.W_hp = 0

            # Calculate latent demand from infiltration, ventilation, and internal sources
            self.latentDemand = QLinfil + QLvent + QLintload

            self.dehumDemand = max(self.latentDemand, 0.0)
            self.humDemand = max(-self.latentDemand, 0.0)

            # Calculate the energy consumption of the heating system per unit building footprint area [W m^-2] from heating demand divided by efficiency
            self.heatConsump  = (self.sensHeatDemand + self.humDemand) / self.heatEff
            # Calculate waste heat from HVAC system per unit building footprint area [W m^-2]
            # Excess heat generated by the heating system is rejected to the environment
            self.sensWasteCoolHeatLatent = self.heatConsump - (self.sensHeatDemand + self.humDemand)

            self.sensCoolDemand = 0.0

        # -------------------------------------------------------------
        # Evolution of the internal temperature and humidity
        # -------------------------------------------------------------
        # Rearrange the building sensible heat load equation to solve for the indoor air temperature
        # Explicit terms which either do not contain Tin or contain Tin from previous iteration
        if Adv_ene_heat_mode == 0:
            Q = -self.intHeat - winTrans - self.sensHeatDemand + self.sensCoolDemand + self.Q_hp
        if Adv_ene_heat_mode == 1:
            Q = -self.intHeat - winTrans - self.sensHeatDemand + self.sensCoolDemand - self.Q_hp
        if (Adv_ene_heat_mode == 2) or (Adv_ene_heat_mode == 3):
            Q = -self.intHeat - winTrans - self.sensHeatDemand + self.sensCoolDemand
        H1 = (T_wall*wallArea*zac_in_wall +
            T_mass*massArea*zac_in_mass +
            T_ceil*ceilingArea*zac_in_ceil +
            self.Tcanyon*winArea*self.uValue +
            self.Tcanyon*volInfil * dens * parameter.cp +
            self.Tcanyon*volVent * dens * parameter.cp)
        # Implicit terms which directly contain coefficient for newest Tin to be solved
        H2 = (wallArea*zac_in_wall +
            massArea*zac_in_mass +
            ceilingArea*zac_in_ceil +
            winArea*self.uValue +
            volInfil * dens * parameter.cp +
            volVent * dens * parameter.cp)
        # Calculate indoor air temperature [K]
        self.indoorTemp = (H1 - Q)/H2

        # Rearrange the building latent heat load equation to solve for the indoor air specific humidity
        # QLinfil + QLvent = self.latentDemand - QLintload (left hand side has qin but right hand side does not)
        # Explicit terms which either do not contain qin or contain qin from previous iteration
        QL = self.latentDemand - QLintload
        HL1 = volInfil * dens * parameter.lv * self.qcanyon + volVent * dens * parameter.lv * self.qcanyon
        # Implicit terms which directly contain coefficient for newest qin to be solved
        HL2 = volInfil * dens * parameter.lv + volVent * dens * parameter.lv
        # Calculate indoor specific humidity [kgv kga^-1]
        self.indoorHum = (HL1 - QL) / HL2

        # Calculate relative humidity ((Pw/Pws)*100) using pressure, indoor temperature, humidity
        _Tdb, _w, _phi, _h, _Tdp, _v = psychrometrics(self.indoorTemp, self.indoorHum, forc.pres)
        # Indoor relative humidity
        self.indoorRhum = _phi

        # Heat fluxes of elements [W m^-2]
        # (will be used for element calculation)
        # Wall heat flux per unit wall area [W m^-2]
        self.fluxWall = zac_in_wall * (T_indoor - T_wall)
        # Top ceiling heat flux per unit ceiling or building footprint area [W m^-2]
        self.fluxRoof = zac_in_ceil * (T_indoor - T_ceil)
        # Inner horizontal heat flux per unit floor area [W m^-2]
        self.fluxMass = zac_in_mass * (T_indoor - T_mass) + self.intHeat * self.intHeatFRad/massArea

        # Calculate heat fluxes per unit floor area [W m^-2] (These are for record keeping only)
        self.fluxSolar = winTrans/self.nFloor
        self.fluxWindow = winArea * self.uValue *(self.Tcanyon - T_indoor)/self.nFloor
        self.fluxInterior = self.intHeat * self.intHeatFRad *(1.-self.intHeatFLat)/self.nFloor
        self.fluxInfil= volInfil * dens * parameter.cp *(self.Tcanyon - T_indoor)/self.nFloor
        self.fluxVent = volVent * dens * parameter.cp *(self.Tcanyon - T_indoor)/self.nFloor

        # Total Electricity consumption per unit floor area [W m^-2] which is equal to
        # cooling consumption + electricity consumption + lighting
        self.ElecTotal = self.coolConsump/self.nFloor + BEM.Elec + BEM.Light

        # electricity deman other than cooling consumption per building footprint area [W m^-2]
        self.elecDomesticDemand = self.nFloor * (BEM.Elec + BEM.Light)

        CpH20 = 4200.           # heat capacity of water [J Kg^-1 K^-1]
        T_hot = 49 + 273.15     # Service water temp (assume no storage) [K]

        # Sensible hot water heating demand
        self.sensWaterHeatDemand = massFlowRateSWH * CpH20 * (T_hot - forc.waterTemp)

        # The renewable energy case
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            if self.sensWaterHeatDemand > 0:
                if self.T_bites > forc.waterTemp:
                    self.Q_waterSaved = massFlowRateSWH * CpH20 * (self.T_bites - forc.waterTemp)
                    self.Q_waterSaved = min(self.sensWaterHeatDemand, self.Q_waterSaved)
                    self.sensWaterHeatDemand = self.sensWaterHeatDemand - self.Q_waterSaved

                    # Check if PCM can be utilized
                    if (self.T_bites <= T_melt) and (self.f_pcm > 0):
                        V_melt = self.Q_waterSaved * simTime.dt / l_pcm
                        self.f_pcm = self.f_pcm - V_melt/V_pcm
                    else:
                        Delta_T_bites = - self.Q_waterSaved * simTime.dt / (V_bites * c_bites)
                        if (Adv_ene_heat_mode == 1):
                            self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
                        elif (Adv_ene_heat_mode == 0):
                            self.T_bites = max(self.T_bites + Delta_T_bites, T_bites_min)

        # Water heating waste heat
        self.QWater = (1 / self.heatEff - 1.) * self.sensWaterHeatDemand

        # The renewable energy case
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            # Can we recover coolness from building ventilation exhaust into BITES
            if (self.T_bites > T_indoor) and (Adv_ene_heat_mode == 0):
                self.Q_recovery = volVent * cv_air * (self.T_bites - T_indoor)

                # Check if PCM can be utilized
                if (self.T_bites <= T_melt) and (self.f_pcm > 0):
                    V_melt = self.Q_recovery * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm - V_melt / V_pcm
                else:
                    Delta_T_bites = - self.Q_recovery * simTime.dt / (V_bites * c_bites)
                    self.T_bites = max(self.T_bites + Delta_T_bites, T_bites_min)
            else:
                self.Q_recovery = 0

        # The renewable energy case
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            # Can we recover heat from building ventilation exhaust into BITES
            if (self.T_bites < T_indoor) and (Adv_ene_heat_mode == 1):
                self.Q_recovery = volVent * cv_air * (T_indoor - self.T_bites)

                # Check if PCM can be utilized
                if (self.T_bites >= T_melt) and (self.f_pcm < 1):
                    V_melt = self.Q_recovery * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm + V_melt / V_pcm
                else:
                    Delta_T_bites = self.Q_recovery * simTime.dt / (V_bites * c_bites)
                    self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
            else:
                self.Q_recovery = 0

        # The renewable energy case
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            # Heat recovery from domestic water under heating mode, assuming water is 20C lower than T_hot
            if (self.T_bites < T_hot - 20) and (Adv_ene_heat_mode == 1):
                self.Q_waterRecovery = massFlowRateSWH * CpH20 * (T_hot - 20 - self.T_bites)

                # Check if PCM can be utilized
                if (self.T_bites >= T_melt) and (self.f_pcm < 1):
                    V_melt = self.Q_waterRecovery * simTime.dt / l_pcm
                    self.f_pcm = self.f_pcm + V_melt / V_pcm
                else:
                    Delta_T_bites = self.Q_waterRecovery * simTime.dt / (V_bites * c_bites)
                    self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
            else:
                self.Q_waterRecovery = 0

        # The renewable energy case
        if (Adv_ene_heat_mode == 0) or (Adv_ene_heat_mode == 1):
            # Account for ground heat flux
            # Positive ground heat flux from soil to BITES
            if self.Q_ground > 0:
                # Heating mode
                if Adv_ene_heat_mode == 1:
                    # Check if PCM can be utilized
                    if (self.T_bites >= T_melt) and (self.f_pcm < 1):
                        V_melt = self.Q_ground * simTime.dt / l_pcm
                        self.f_pcm = self.f_pcm + V_melt/V_pcm
                    else:
                        Delta_T_bites = self.Q_ground * simTime.dt / (V_bites * c_bites)
                        self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
                # Cooling mode
                else:
                    # Check if PCM can be utilized
                    if (self.T_bites >= T_melt) and (self.f_pcm < 1):
                        V_melt = self.Q_ground * simTime.dt / l_pcm
                        self.f_pcm = self.f_pcm + V_melt/V_pcm
                    else:
                        Delta_T_bites = self.Q_ground * simTime.dt / (V_bites * c_bites)
                        self.T_bites = max(self.T_bites + Delta_T_bites, T_bites_min)
            # Negative ground heat flux from soil to BITES
            else:
                # Heating mode
                if Adv_ene_heat_mode == 1:
                    # Check if PCM can be utilized
                    if (self.T_bites <= T_melt) and (self.f_pcm > 0):
                        V_melt = - self.Q_ground * simTime.dt / l_pcm
                        self.f_pcm = self.f_pcm - V_melt/V_pcm
                    else:
                        Delta_T_bites = self.Q_ground * simTime.dt / (V_bites * c_bites)
                        self.T_bites = min(self.T_bites + Delta_T_bites, T_bites_max)
                # Cooling mode
                else:
                    # Check if PCM can be utilized
                    if (self.T_bites <= T_melt) and (self.f_pcm > 0):
                        V_melt = - self.Q_ground * simTime.dt / l_pcm
                        self.f_pcm = self.f_pcm - V_melt/V_pcm
                    else:
                        Delta_T_bites = self.Q_ground * simTime.dt / (V_bites * c_bites)
                        self.T_bites = max(self.T_bites + Delta_T_bites, T_bites_min)

            # Calculate input temperature of air into ST system heat exchanger
            self.T_he_st_i = self.T_bites

        # Calculate water heating consumption
        self.waterHeatConsump = self.sensWaterHeatDemand / self.heatEff

        self.QGas = BEM.Gas * (1 - self.heatEff) * self.nFloor

        # Calculate total sensible waste heat to canyon per unit building footprint area [W m^-2]
        # which can be determined from sensible waste to canyon, energy consumption for domestic hot water and gas consumption
        self.sensWaste = self.sensWasteCoolHeatLatent + self.QWater + self.QGas
        # Calculate total gas consumption per unit floor area [W m^-2] which is equal to gas consumption per unit floor area +
        # energy consumption for domestic hot water per unit floor area + energy consumption of the heating system per unit floor area
        self.GasTotal = BEM.Gas + (massFlowRateSWH*CpH20*(T_hot - forc.waterTemp)/self.nFloor)/self.heatEff + self.heatConsump/self.nFloor
