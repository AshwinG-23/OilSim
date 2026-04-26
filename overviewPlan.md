# 🛢️ Product Description

## **Project Name:** Hormuz Supply Chain Resilience Simulator

---

# 1. 🎯 Purpose of the System

This product is a **discrete-event simulation (DES) engine** designed to model and analyze the resilience of India’s crude oil import supply chain under **geopolitical disruptions**.

The system simulates:

* Multi-source oil imports
* Maritime transport through chokepoints
* Inventory dynamics at ports/refineries
* Strategic reserve usage
* Decision-making policies under uncertainty

---

# 2. 🧠 Core Objective

The system is built to answer:

> **How different supply strategies perform under varying disruption scenarios, and at what point each strategy fails or becomes suboptimal.**

This is NOT a simple optimization system.

It is a **scenario-based policy evaluation engine** that reveals:

* Tradeoffs between cost and resilience
* Nonlinear failure points
* Cascading disruption effects

---

# 3. 🏗️ System Overview

The simulator models a **multi-layer supply network** consisting of:

### A. Supply Sources

* Gulf (Hormuz-dependent)
* Russia (Suez/Red Sea dependent)
* Africa / Americas (Cape route)

---

### B. Transport Network

* Hormuz Strait (primary chokepoint)
* Red Sea / Suez (secondary chokepoint)
* Cape of Good Hope (fallback route)

Each route has:

* Capacity constraints
* Congestion behavior
* Dynamic disruptions

---

### C. Fleet System

* Finite pool of oil tankers
* Ships transition through states:

  * Idle
  * In transit
  * Waiting (queueing at chokepoints/ports)

---

### D. Ports / Refineries

* Inventory storage (buffers)
* Continuous demand consumption
* Throughput limits (unloading constraints)

---

### E. Strategic Petroleum Reserve (SPR)

* Emergency buffer
* Controlled release policies
* Finite capacity and refill dynamics

---

# 4. ⚙️ Simulation Type

* **Discrete Event Simulation (DES)** using SimPy
* Time progresses in **events**, not fixed steps
* Granularity: ~hourly resolution
* Simulation horizon: configurable (e.g., 200–365 days)

---

# 5. 🔁 Core Simulation Dynamics

The system evolves through interactions between:

---

## 5.1 Supply Flow

1. Orders are placed by ports
2. Tankers are assigned
3. Tankers traverse routes (subject to constraints)
4. Oil is delivered to ports

---

## 5.2 Demand Flow

* Each port consumes oil continuously
* Inventory decreases over time
* Shortage occurs when inventory reaches zero

---

## 5.3 Transport Constraints

### Chokepoints behave as:

* Capacity-limited resources
* Queue-forming systems

Effects:

* Waiting delays
* Congestion buildup
* Throughput reduction during disruption

---

## 5.4 Fleet Constraints

* Limited number of ships globally
* Longer routes → ships unavailable longer
* Leads to:

  * Increased lead times
  * System-wide slowdown

---

## 5.5 Congestion Feedback Loop (Critical Behavior)

Disruption triggers:

1. Reduced capacity
2. Queue formation
3. Increased transit times
4. Late deliveries
5. Inventory depletion
6. Increased ordering
7. More congestion

👉 This creates **nonlinear collapse behavior**

---

## 5.6 Substitution Dynamics

When one source fails:

* Demand shifts to others
* Those routes become congested
* Costs increase

👉 Creates **interdependency between supply routes**

---

## 5.7 Information & Reaction Delay

* Decisions are based on observed inventory
* There is delay between:

  * shortage signal
  * order placement
  * delivery

👉 Causes:

* overshoot
* panic ordering
* oscillations

---

# 6. 🌍 Disruption Modeling

The system includes **stochastic geopolitical events**:

---

## 6.1 Primary Disruptions

### Hormuz Disruption

* Partial (reduced capacity)
* Severe (near-blocked)
* Total closure

---

### Red Sea / Suez Disruption

* Forces rerouting via Cape
* Adds significant delay

---

## 6.2 Secondary Effects

### Fleet Shock

* Ships tied up in longer routes
* Global availability decreases

---

### Freight & Cost Shock

* Transport costs increase dynamically

---

### Risk / Insurance Shock

* Some routes become partially unusable

---

### Pipeline Bypass Activation

* Limited alternate flow from Gulf
* Delayed activation
* Partial compensation only

---

## 6.3 Cascade Effects (Key Feature)

Disruptions interact:

* Hormuz disruption → increases global tanker demand
* → worsens congestion elsewhere
* → amplifies system-wide failure

---

# 7. 🧠 Decision Layer (Strategies)

The simulation evaluates different **decision policies** used by refiners.

---

## 7.1 Decision Variables

* Source selection (where to import from)
* Order timing
* Order size
* Emergency sourcing
* SPR usage

---

## 7.2 Strategy Types

### 1. Cost-Focused Strategy

* Prioritizes cheapest source
* Minimal diversification
* Low baseline cost, high risk

---

### 2. Diversified Strategy

* Mix of sources
* Balanced cost and resilience

---

### 3. Resilient Strategy

* Prioritizes safer routes
* Higher cost, lower risk

---

## 7.3 Adaptive Behavior

Strategies can:

* Respond to disruptions
* Shift sourcing dynamically

---

# 8. 📊 Simulation Outputs

The system produces both **time-series data** and **aggregated metrics**.

---

## 8.1 Operational Metrics

* Inventory levels over time
* Demand fulfillment rate
* Shortage duration (deficit hours)
* Recovery time

---

## 8.2 Economic Metrics

* Total procurement cost
* Cost per barrel
* Cost volatility

---

## 8.3 System Metrics

* Average transit time
* Queue lengths at chokepoints
* Fleet utilization

---

## 8.4 Resilience Metrics

* Time to failure
* Time to recovery
* Performance degradation under stress

---

# 9. 🧪 Experiment Design

The system runs structured experiments:

---

## 9.1 Scenario Dimension

* No disruption
* Short conflict
* Medium blockade
* Long war

---

## 9.2 Strategy Dimension

* Cost-focused
* Diversified
* Resilient

---

## 9.3 Simulation Runs

* Each (scenario, strategy) pair is run multiple times
* Results are averaged to handle randomness

---

## 9.4 Output Analysis

The system identifies:

* Best-performing strategy per scenario
* Failure thresholds
* Cost vs resilience tradeoffs

---

# 10. 🎯 Key Insights Generated

The simulator enables answering:

---

### 1. Strategy Performance

Which strategy works best under which disruption?

---

### 2. Tipping Points

At what disruption duration does each strategy fail?

---

### 3. Tradeoff Curve

How much cost must be paid for resilience?

---

### 4. Cascade Impact

How much worse does combined disruption become?

---

### 5. Robust Strategy

Which strategy performs reasonably well across all scenarios?

---

# 11. 🧭 System Philosophy

This system is designed to model:

> **A constrained, adaptive supply network under uncertainty and adversarial shocks**

It captures:

* Nonlinear dynamics
* Resource competition
* Cascading failures
* Strategic decision-making

---

# 12. 🚀 Final Deliverable

The final product is:

* A configurable DES simulation engine
* Capable of running multiple scenarios and strategies
* Producing quantitative comparisons
* Supporting policy-level insights

---

# 🧠 One-Line Summary

> **A simulation engine that models how oil supply chains behave under disruption—and reveals when and why different strategies succeed or fail.**

