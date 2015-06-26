import pytest

from thermostat.demand import get_cooling_demand
from thermostat.demand import get_heating_demand

from thermostat import Thermostat

import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

RTOL = 1e-6
ATOL = 1e-6

@pytest.fixture
def valid_thermostat_id():
    return "10912098123"

@pytest.fixture
def valid_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=400)

@pytest.fixture
def valid_temperature_setpoint(valid_datetimeindex):
    return pd.Series(np.zeros((400,)),index=valid_datetimeindex)

def test_get_cooling_demand_deltaT(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.tile(90,(400,)),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    deltaT = get_cooling_demand(thermostat_type_2,cooling_season,method="deltaT")
    assert_allclose(deltaT,np.tile(-20,(384,)),rtol=RTOL,atol=ATOL)

def test_get_heating_demand_deltaT(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.tile(50,(400,)),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    deltaT = get_heating_demand(thermostat_type_2,heating_season,method="deltaT")
    assert_allclose(deltaT,np.tile(20,(384,)),rtol=RTOL,atol=ATOL)

def test_get_cooling_demand_dailyavgCDD(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)

    hourly_alpha = 20
    daily_alpha = hourly_alpha * 24

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    dailyavgCDD, deltaT_base_estimate, alpha_estimate, error = \
            get_cooling_demand(thermostat_type_2,cooling_season,method="dailyavgCDD",column_name="ss_heat_pump_cooling")

    assert_allclose(dailyavgCDD.values,[ 10.288, 10.889, 11.491, 12.092, 12.694,
                                         13.295, 13.897, 14.498, 15.100, 15.701,
                                         16.303, 16.904, 17.506, 18.107, 18.709,
                                         19.310], rtol=0.01, atol=0.01)
    assert_allclose(deltaT_base_estimate, 70, rtol=1, atol=.01)
    assert_allclose(alpha_estimate, daily_alpha, rtol=RTOL, atol=ATOL)
    assert error < 50000

def test_get_heating_demand_dailyavgHDD(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)

    hourly_alpha = 20
    daily_alpha = hourly_alpha * 24

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    dailyavgHDD, deltaT_base_estimate, alpha_estimate, error = \
            get_heating_demand(thermostat_type_2,heating_season,method="dailyavgHDD",column_name="ss_heat_pump_heating")

    assert_allclose(dailyavgHDD.values,[ 10.288, 10.889, 11.491, 12.092, 12.694,
                                         13.295, 13.897, 14.498, 15.100, 15.701,
                                         16.303, 16.904, 17.506, 18.107, 18.709,
                                         19.310], rtol=0.01, atol=0.01)
    assert_allclose(deltaT_base_estimate, 70, rtol=1, atol=.01)
    assert_allclose(alpha_estimate, daily_alpha, rtol=RTOL, atol=ATOL)
    assert error < 50000

def test_get_cooling_demand_hourlysumCDD(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)

    hourly_alpha = 20
    daily_alpha = 24 * hourly_alpha

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    hourlysumCDD, deltaT_base_estimate, alpha_estimate, error = \
            get_cooling_demand(thermostat_type_2,cooling_season,method="hourlysumCDD",column_name="ss_heat_pump_cooling")

    assert_allclose(hourlysumCDD.values,[ 10.288, 10.889, 11.491, 12.092, 12.694,
                                          13.295, 13.897, 14.498, 15.100, 15.701,
                                          16.303, 16.904, 17.506, 18.107, 18.709,
                                          19.310], rtol=0.01, atol=0.01)
    assert_allclose(deltaT_base_estimate, 70, rtol=1, atol=.01)
    assert_allclose(alpha_estimate, daily_alpha, rtol=0.01, atol=0.01)
    assert error < 550000

def test_get_heating_demand_hourlysumHDD(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)

    hourly_alpha = 20
    daily_alpha = 24 * hourly_alpha

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    hourlysumHDD, deltaT_base_estimate, alpha_estimate, error = \
            get_heating_demand(thermostat_type_2,heating_season,method="hourlysumHDD",column_name="ss_heat_pump_heating")

    assert_allclose(hourlysumHDD.values,[ 10.288, 10.889, 11.491, 12.092, 12.694,
                                          13.295, 13.897, 14.498, 15.100, 15.701,
                                          16.303, 16.904, 17.506, 18.107, 18.709,
                                          19.310], rtol=0.01, atol=0.01)
    assert_allclose(deltaT_base_estimate, 70, rtol=1, atol=.01)
    assert_allclose(alpha_estimate, daily_alpha, rtol=0.01, atol=0.01)
    assert error < 550000
