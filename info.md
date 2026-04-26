# Scenario Guide

## 1. `no_disruption`

Nothing happens. Normal operations for the full 100 days.

This is the baseline used to verify that the system works and to measure the peacetime cost of each strategy.

## 2. `short_conflict`

On day 30, Hormuz drops to 50% capacity for 30 days, then recovers.

This models a brief regional flare-up. Ships can still pass, but transit time doubles and queues build up.

## 3. `medium_blockade`

On day 30, Hormuz drops to 20% capacity for 90 days.

This is a more serious blockade. Ships take roughly 5x longer to transit. This is where `cost_focused` starts to fail because it does not react early enough.

## 4. `long_war`

A full regional war that escalates in stages:

- Day 15: Hormuz nearly closes at 5% capacity
- Day 25: Red Sea also nearly closes at 10%
- Day 30: 15 tankers are permanently destroyed, reducing the fleet from 120 to 105

Both major chokepoints become effectively unusable. Only the Africa route remains viable.

## 5. `all_out_war`

This is the worst-case scenario. Everything hits at once:

- Day 0: Russia is sanctioned and fully cut off
- Day 7: Hormuz nearly closes at 2%
- Day 10: Red Sea nearly closes at 2%
- Day 14: 65 tankers are destroyed, reducing the fleet from 120 to 55

Only the Africa route remains, but 55 tankers are not enough to cover full demand. In practice, every strategy fails here.

## 6. `cape_disruption`

This scenario is designed to stress the Africa "safe route":

- Day 0: Africa route is completely shut down
- Day 0: Hormuz falls to 15%
- Day 0: Red Sea falls to 20%

There is no safe route left. Gulf and Russia are both disrupted, and Africa is unavailable. If enabled, the UAE pipeline would be the only clean option.

## 7. `houthi_red_sea`

This is directly inspired by the 2024 Houthi attacks.

The Red Sea drops to 5% capacity from day 0 for the full duration. Russian oil moving via Suez is badly affected. Gulf shipments are unaffected because they use Hormuz rather than the Red Sea.

## 8. `russia_sanctions`

Russia remains available for the first 60 days, then is fully cut off for the remaining 40 days.

There are no chokepoint disruptions here. The issue is purely political. This tests whether Gulf plus Africa capacity can cover the gap.

## 9. `tanker_strike`

This is a combined shock on day 30:

- Hormuz drops to 30%
- 25 tankers are permanently destroyed

This tests whether the fleet can absorb a sudden capacity loss while a chokepoint is also congested.

## 10. `stochastic_conflict`

This scenario has no fixed events. Disruptions happen randomly throughout the simulation.

The randomness is controlled by three parameters:

| Parameter | Value | Meaning |
| --- | --- | --- |
| Mean interval | 60 days | On average, a new disruption occurs every 60 days. It may happen sooner or later because the timing is random. |
| Severity range | `0.1-0.7` | Each disruption can range from mild to severe. You do not know how bad it will be until it happens. |
| Mean duration | 45 days | Each disruption lasts about 45 days on average, again with random variation. |

The affected chokepoint is also random. In one replication you might get a mild Red Sea disruption on day 40. In another, you might get a severe Hormuz blockade on day 10.

That is why the simulation uses 40 replications: to average out the randomness.

This is the most realistic scenario because geopolitical disruptions do not follow a fixed schedule. It is also the scenario where the adaptive strategy performs best, because it reacts to what actually happens instead of one predetermined event.

# Feature Flags

## 1. Tanker Breakdowns

- Flag: `enable_tanker_breakdowns`
- Default: `OFF`

Ships break down randomly during voyages. The breakdown rate is controlled by MTBF (Mean Time Between Failures), with a default of 8,760 hours, or about once per year per tanker. When a breakdown happens, the tanker is out of service for a random repair period with a default mean of 14 days.

This makes the fleet behave more realistically instead of as a perfect machine.

Sub-parameters:

- `tanker_mtbf_hours`: lower values mean more frequent breakdowns
- `tanker_repair_mean_hours`: average repair duration; default 336 hours

## 2. Demand Elasticity

- Flag: `enable_demand_elasticity`
- Default: `OFF`

When inventory gets low, demand automatically falls to model rationing and substitution:

- Inventory above 30% of max: full 4.2M bbl/day demand
- Inventory between 10% and 30% of max: demand falls to 85%
- Inventory below 10% of max: demand falls to 60%

Without this flag, the model assumes India always consumes 4.2M bbl/day, even when stocks are nearly empty.

## 3. Seasonal Weather

- Flag: `enable_seasonal_weather`
- Default: `OFF`

This models Indian Ocean monsoon effects from roughly May to November. Transit times increase gradually, peak around September, and can become up to 30% slower.

Outside the monsoon window, there is no weather effect.

## 4. Panic Ordering

- Flag: `enable_panic_ordering`
- Default: `OFF`

This models the bullwhip effect. When a chokepoint disruption is detected, the system sends far more tankers than usual in a single order cycle.

By default, the multiplier is 3, so a normal dispatch of 3 tankers can become 9.

Although this may sound helpful, it often makes outcomes worse by creating order surges, inventory overshoots, and later crashes.

Sub-parameter:

- `panic_multiplier`: multiplier on the normal dispatch rate

## 5. Information Delay

- Flag: `enable_information_delay`
- Default: `OFF`

This simulates stale operational data. The ordering policy does not see the current inventory level; it sees the level from some number of hours earlier.

Sub-parameter:

- `information_delay_hours`: data staleness; default 24 hours

This causes delayed reactions. If inventory is dropping quickly, replenishment orders can be placed too late.

## 6. SPR Auto-Refill

- Flag: `enable_spr_refill`
- Default: `OFF`

By default, the Strategic Petroleum Reserve only declines during emergencies. With this flag enabled, it refills automatically during calm periods whenever commercial inventory is healthy and the SPR is not full.

The refill rate is 500K bbl/day, which is much slower than the emergency release rate.

## 7. Freight Dynamics

- Flag: `enable_freight_dynamics`
- Default: `OFF`

This adds a shipping cost premium when fleet utilization rises above 70%.

At 70% utilization there is no premium. As utilization approaches 100%, the premium rises quadratically and can push freight cost to roughly 3x the base rate.

This models crisis-period charter market pricing.

## 8. Pipeline Bypass (UAE)

- Flag: `enable_pipeline_bypass`
- Default: `OFF`

This enables the real UAE ADCOP pipeline as a supply source that bypasses Hormuz.

It does not activate immediately. The model waits until Hormuz has stayed below 30% status for 10 days, then enables the pipeline.

Once active, it provides oil at `$4.00/bbl` with no chokepoint risk, but with smaller deliveries of 500K barrels instead of tanker-sized 1.5M barrel shipments.

Without this flag, `Gulf_Pipeline` remains disabled and contributes zero deliveries in baseline results.
