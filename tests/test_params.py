from config.params import (
    SIM_DURATION_HOURS, NUM_TANKERS, TANKER_CAPACITY_BBL,
    PORT_INITIAL_INVENTORY_BBL, PORT_MAX_INVENTORY_BBL,
    PORT_DAILY_DEMAND_BBL, PORT_REORDER_POINT_BBL,
    PORT_CRITICAL_INVENTORY_BBL, SPR_INITIAL_LEVEL_BBL,
    SPR_MAX_CAPACITY_BBL, SPR_DAILY_RELEASE_RATE_BBL,
    SOURCES, CHOKEPOINTS, SCENARIOS, STRATEGIES, NUM_REPLICATIONS,
)


def test_sources_have_required_keys():
    for name, cfg in SOURCES.items():
        assert 'base_cost_per_bbl' in cfg
        assert 'loading_time_hours' in cfg
        assert 'return_time_hours' in cfg
        assert 'chokepoints' in cfg
        assert 'cargo_bbl' in cfg


def test_scenarios_have_required_keys():
    for name, cfg in SCENARIOS.items():
        assert 'disruptions' in cfg


def test_all_chokepoint_refs_valid():
    for source_name, cfg in SOURCES.items():
        for cp_name in cfg['chokepoints']:
            assert cp_name in CHOKEPOINTS, f"{source_name} refs unknown chokepoint {cp_name}"


def test_reorder_point_below_initial_inventory():
    assert PORT_REORDER_POINT_BBL < PORT_INITIAL_INVENTORY_BBL


def test_critical_below_reorder():
    assert PORT_CRITICAL_INVENTORY_BBL < PORT_REORDER_POINT_BBL
