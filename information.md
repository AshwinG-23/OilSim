### **Fleet**

1. **Number of tankers India uses for crude imports at any given time**  
   India’s oil marketing companies (IOCL, BPCL, HPCL, MRPL, GAIL) typically use on the order of **~100–150 crude‑tanker vessels** at sea and in rotation for imports, not a fixed 25.  
   Source: Reporting on Indian‑owned and chartered crude‑tanker fleet size and chartering activity points to roughly this scale of active crude‑oil tanker use. [tribuneindia](https://www.tribuneindia.com/news/business/india-to-build-own-fleet-of-oil-tankers-aims-to-cut-usd-8-billion-charter-costs-hardeep-puri/)

2. **Typical cargo size; % breakdown by VLCC, Suezmax, Aframax**  
   - VLCC: typ. **~1.8–2.0 million bbl** per vessel. [eia](https://www.eia.gov/todayinenergy/detail.php?id=17991)
   - Suezmax: **~0.8–1.2 million bbl**. [oilcapacitycheck](https://oilcapacitycheck.com/capacity-by-vehicle/how-much-oil-tanker-capacity)
   - Aframax: **~0.4–0.8 million bbl**, with many around **~0.5–0.75 million bbl**. [septrans](http://septrans.in/liquid-cargo-vessels/)

   India’s crude‑import mix is **VLCC‑heavy** but increasingly uses Suezmax and Aframax for smaller / more flexible volumes. A rough working split for India’s crude‑tanker demand is:  
   - **VLCC**: **~50–60%** of cargo volume  
   - **Suezmax**: **~25–35%**  
   - **Aframax**: **~10–20%**  
   (This is inferred from global tanker‑class capacity shares and India’s known preference for VLCCs plus recent Suezmax/Aframax growth in the Gulf–India trade.) [kpler](https://www.kpler.com/blog/q1-2026-tanker-market-outlook-shadow-fleet-disruption-and-mid-size-strength)

3. **Ownership vs chartering of tankers (fixed vs elastic fleet)**  
   India **does not own most of the crude‑tanker fleet**; instead, it **charter‑in** vessels from global owners.  
   - State‑owned refiners currently rely predominantly on **time‑chartered foreign‑flagged VLCCs, Suezmax and Aframax**. [timesofindia.indiatimes](https://timesofindia.indiatimes.com/city/mumbai/indias-oil-psus-spent-8bn-on-chartered-ships-in-5-years-amount-could-have-funded-tanker-fleet-minister/articleshow/124907869.cms)
   - There is a government plan to build or acquire **around 100–112 Indian‑owned crude‑tankers** by 2040, but this fleet is still in the early stages of build‑up. [myind](https://myind.net/Home/viewArticle/india-plans-to-buy-over-100-make-in-india-crude-oil-tankers-worth10billion)

   For modeling, treat the *current* crude‑tanker “fleet” as **highly elastic** via the charter market, not a fixed owned fleet.

***

### **Voyage times (one‑way)**

4. **Gulf (Saudi/UAE/Iraq) → India — days at sea**  
   Typical one‑way voyage time for a crude‑tanker from the Gulf to major west‑coast Indian ports (e.g., Mumbai, Mundra, Kandla) is about **10–14 days at sea**, depending on port and exact routing.  
   This is consistent with Gulf–Asia crude‑tanker routes that average 14–20 days one‑way including variability; for Gulf–Japan, VLCCs take ~20 days, so Gulf–India is somewhat shorter. [mol-service](https://www.mol-service.com/blog/vessel-speed-and-sailing-days)

5. **Russia → India via Baltic/Black Sea → Suez (a)**  
   From Baltic/Black‑Sea ports (e.g., Primorsk, Novorossiysk) to the west coast of India via Suez, the **total sea leg is roughly 25–35 days one way**, depending on delays, Suez‑transit queues, and weather.  
   Reports on India–Russia cargo routes and crude‑tanker flows indicate roughly **~3–4 weeks** of sailing time for this route. [sber.bank](https://sber.bank.in/media/publications/pathways-of-cooperation-russia-india-cargo-routes?type=trends)

6. **Russia (ESPO Pacific) → India direct (b)**  
   For ESPO‑Pacific crude from ports like Kozmino (Pacific) sailing directly to Indian ports, the **one‑way voyage is roughly 12–18 days at sea**, depending on speed and weather.  
   Comparable ESPO‑Pacific runs to China take 8–12 days; India is a bit farther, so the marginally longer range is reasonable. [datamarnews](https://datamarnews.com/noticias/more-russian-tankers-forced-to-wait-or-reroute-after-washington-tightens-sanctions/)

7. **West Africa (Nigeria/Angola) → India — days at sea**  
   A typical one‑way voyage from West Africa (e.g., Nigeria) to Indian ports is about **20–25 days at sea**, given the Cape‑of‑Good‑Hope‑type routing.  
   This fits with crude‑tanker market data on West Africa–Asia routes of a similar length. [hellenicshippingnews](https://www.hellenicshippingnews.com/wp-content/uploads/2022/08/2022-08-Crude-Tanker-Outlook.pdf)

8. **Loading time at source terminal (VLCC)**  
   A VLCC typically spends **about 1.0–2.0 days** at the loading berth, depending on pipeline throughput and terminal congestion.  
   Industry descriptions of loading times for very‑large crude carriers on Gulf‑type terminals support this range. [oilcapacitycheck](https://oilcapacitycheck.com/capacity-by-vehicle/how-much-oil-tanker-capacity)

9. **Unloading time at Indian port (discharge)**  
   Indian ports commonly report crude‑discharge operations for a large tanker taking **about 1.5–2.5 days** (i.e., 36–60 hours) at the berth.  
   For example, a recent VLCC discharge at Mumbai under normal conditions was scheduled for **about 36 hours**. [splash247](https://splash247.com/india-receives-first-fully-laden-vlcc-at-mundra/)

***

### **Port inventory and storage**

10. **Total crude storage capacity across Indian import terminals (million barrels)**  
   Total crude‑storage capacity (commercial + SPR) is estimated at **roughly 100–120 million barrels equivalent** when combining all major import‑terminal tanks and SPR caverns.  
   - Kpler‑based analysis notes that India’s **combined crude stocks (tanks + SPR + ships en route)** can cover about 40–45 days of demand, implying total physical and “in‑transit” storage on the order of **~100 million barrels**. [dailyexcelsior](https://www.dailyexcelsior.com/indias-100-mn-barrel-crude-stocks-could-cover-40-45-days-if-hormuz-flows-disrupted/)
   - SPR alone is about **5.33 million tonnes ≈ 40 million barrels** and is a small subset of the total system. [linkedin](https://www.linkedin.com/posts/business-today-india_exclusive-indias-strategic-oil-reserves-activity-7442134553873440768-v8nz)

11. **Typical operating inventory level (days of forward cover)**  
   Under normal conditions, India holds **on the order of 40–70 days of forward cover** of crude in total (including SPR, commercial tanks, and ships en route), depending on the scenario used in energy‑security studies.  
   - Kpler‑linked analysis suggests that current stocks can cover **~40–45 days** of demand if Hormuz‑flows are disrupted; this is slightly above “normal” but within the same ballpark. [dailyexcelsior](https://www.dailyexcelsior.com/indias-100-mn-barrel-crude-stocks-could-cover-40-45-days-if-hormuz-flows-disrupted/)
   - Broader government‑quoted **total oil‑storage coverage (crude + products)** is about **74 days**, implying a crude‑only cover in the **~40–60 day** range. [ndtv](https://www.ndtv.com/india-news/india-strategic-petroleum-reserve-how-much-petrol-stock-does-india-have-india-crude-oil-reserves-indias-strategic-crude-oil-reserves-2-3rd-full-11258389)

12. **Inventory level that feels “tight” (triggers emergency procurement)**  
   India starts to feel “tight” when the **forward cover of crude drops toward ~20–30 days** of demand, especially if the Strait of Hormuz is threatened or tanker‑availability is constrained.  
   This is inferred from energy‑security commentary indicating that 40–45 days is already treated as a “buffer” scenario; going below 30 days would be a clear stress signal. [ndtv](https://www.ndtv.com/india-news/india-strategic-petroleum-reserve-how-much-petrol-stock-does-india-have-india-crude-oil-reserves-indias-strategic-crude-oil-reserves-2-3rd-full-11258389)

***

### **Demand (imports specifically)**

13. **India’s crude oil import volume (million barrels per day)**  
   India’s total oil demand is about **~4.5–5.0 million barrels per day (bpd)**, but **imports are roughly in the 3.5–4.5 million bpd** range, depending on the year and domestic production.  
   - Recent energy‑demand reports state that India’s **oil demand is surging to 4.5 million bpd**, with high import dependence. [energy.economictimes.indiatimes](https://energy.economictimes.indiatimes.com/news/oil-and-gas/indias-oil-demand-surges-to-4-5-million-barrels-per-day-aims-for-top-demand-hub-by-2030/110192162)
   - Given India’s **import dependence of ~85–90%**, crude imports are typically **~4.0–4.5 million bpd** in recent years. [seair.co](https://www.seair.co.in/blog/oil-imports-in-india.aspx)

***

### **SPR**

14. **India’s SPR capacity (Visakhapatnam, Padur, Mangaluru) in million barrels**  
   Total SPR capacity across the three underground caverns is **5.33 million tonnes**, which is about **40 million barrels** (using a rough 7.5 barrels per tonne).  
   - Multiple sources state **5.33 million tonnes** for the three SPR sites. [pmfias](https://www.pmfias.com/indias-strategic-petroleum-reserves/)

15. **Current SPR fill level (percent full)**  
   Recent disclosures indicate the SPR is about **64% full**, or roughly **two‑thirds of capacity**.  
   - Government statements and energy‑policy analyses put current SPR stocks at **~3.37 million tonnes**, which is **~64% of 5.33 million tonnes**. [linkedin](https://www.linkedin.com/posts/business-today-india_exclusive-indias-strategic-oil-reserves-activity-7442134553873440768-v8nz)

16. **Maximum SPR release rate (million barrels per day)**  
   Publicly available data does **not give a precise release rate in million bbl/day**, so treat this as a **soft parameter**.  
   - However, SPR‑release capacity is typically calibrated to cover **a few hundred thousand to about 1 million bbl/day** in a coordinated emergency, depending on pipeline‑throughput constraints; using **0.7–1.0 million bbl/day** as a plausible upper bound is reasonable for modeling. [iocl](https://www.iocl.com/MediaDetails/55101)

17. **Is SPR counted separately from commercial storage?**  
   Yes: the **SPR is managed separately from commercial tank storage** and is treated as a **strategic, government‑held reserve**.  
   - Policy documentation and energy‑security reports distinguish **SPR (government‑owned, underground)** from **commercial refinery and terminal storage**. [pmfias](https://www.pmfias.com/indias-strategic-petroleum-reserves/)

***

### **Transport costs**

18. **Freight rate, Gulf → India ($/bbl or $/tonne)**  
   In normal conditions, ocean freight from the Arab Gulf to major Indian ports is on the order of **~$1.5–3.0 per barrel** (or roughly **$15–30 per metric tonne**).  
   - Historical PPAC‑type price‑build‑up sheets show **Gulf–Indian‑port freight around $2–2.5 per barrel** for some products; crude‑tanker freight is broadly in this band. [bharatpetroleum](https://www.bharatpetroleum.in/pdf/petropricesheet/pp_9_pricebuildupsensitiveproducts_1_2_3.pdf)

19. **Freight rate, Russia → India (post‑2022 discounted Urals implicit “cost”)**  
   For Russia‑to‑India routes, the **freight‑plus‑insurance premium** has varied widely.  
   - Recent commentary notes that freight and related costs for Russian Urals to India have risen to the **$10–15 million per cargo** level (i.e., **~$10–20 per barrel** for large cargoes), compared with much lower pre‑2022 levels. [scanx](https://scanx.trade/stock-market-news/commodities/indian-refiners-purchase-millions-of-barrels-of-russian-crude-oil-cargoes/34279543)
   - Modelers can use **~$10–20 per barrel** as a current‑era Russia‑to‑India “all‑in” transport‑plus‑risk add‑on for Urals‑type crude, on top of the discounted FOB price. [scanx](https://scanx.trade/stock-market-news/commodities/indian-refiners-purchase-millions-of-barrels-of-russian-crude-oil-cargoes/34279543)

20. **Freight rate, Africa → India**  
   West Africa‑to‑India crude‑tanker freight typically runs in the **$3–6 per barrel** range under normal conditions, depending on vessel size and charter market.  
   - This is consistent with global crude‑tanker‑rate commentary for West Africa–Asia routes and tanker‑market analyses that place Aframax/Suezmax freight in this band when trade is stable. [kpler](https://www.kpler.com/blog/q1-2026-tanker-market-outlook-shadow-fleet-disruption-and-mid-size-strength)

21. **Disruption war‑risk premium (Hormuz partial block) – % of base freight**  
   In high‑risk periods, **war‑risk and insurance surcharges can add 100–300% of the base freight rate** for ships transiting the Gulf/Red Sea/Hormuz area.  
   - Trade‑insurance reports note that war‑cover premiums for ships in the Red Sea and Gulf can **double or triple** the normal freight‑related insurance costs, especially during spikes in regional tensions. [economictimes](https://economictimes.com/industry/transportation/shipping-/-transport/crisis-in-west-asia-drives-up-shipping-insurance-premiums-raising-costs-for-freight-carriers/articleshow/128967522.cms)

***

### **Source mix**

22. **India’s crude import breakdown by origin (% of total)**  
   Post‑2022, the crude‑import mix has tilted heavily toward Russia; a plausible 2023–2025 split is:  
   - **Russia**: **~35–40%**  
   - **Gulf (Iraq, Saudi, UAE, Kuwait, etc.)**: **~30–40%**  
   - **Africa (Nigeria, Angola, etc.)**: **~10–15%**  
   - **Americas (US, Brazil, etc.)**: **~5–10%**  
   These ranges are based on recent import‑share data showing Russian crude reaching **about one‑third to two‑fifths** of total imports, with Gulf and Africa still significant contributors. [knnindia.co](https://knnindia.co.in/news/newsdetails/sectors/india-increases-crude-oil-imports-from-us-and-brazil-in-first-half-of-2025)

23. **Is any single source capped (e.g., Russia by tanker availability)?**  
   Russia is **not capped by diplomatic constraints**, but practical constraints do exist:  
   - **Tanker‑availability and shadow‑fleet capacity** limit how much Russian crude can be moved at once; bottlenecks at Russian ports and limited sanctioned‑compliant shipping can create de‑facto caps. [kpler](https://www.kpler.com/blog/q1-2026-tanker-market-outlook-shadow-fleet-disruption-and-mid-size-strength)
   - Geopolitical sanctions and insurance‑exclusion policies mean India cannot scale Russian volumes without a sufficient pool of compliant tankers and insurance, so **“effective” capacity is tanker‑ and logistics‑limited rather than strictly policy‑limited**. [economictimes](https://economictimes.com/industry/transportation/shipping-/-transport/crisis-in-west-asia-drives-up-shipping-insurance-premiums-raising-costs-for-freight-carriers/articleshow/128967522.cms)

***

### **Ordering behaviour**

24. **How far in advance India typically contracts crude? Spot vs long‑term split**  
   Indian refiners use a **mix of long‑term contracts and spot purchases**, likely in the ballpark of:  
   - **Long‑term contracts**: **~40–60%** of volumes  
   - **Spot/short‑term purchases**: **~40–60%**  
   This reflects the fact that India’s oil‑basket is diversified and refiners actively trade cargoes to exploit discounts, especially for Russian‑type crude. [vajiramandravi](https://vajiramandravi.com/current-affairs/indias-oil-basket-how-geopolitics-reshaped-crude-imports/)

25. **Lead time from “order placed” to “oil in tank”**  
   For a typical crude‑cargo ordered from the Gulf, the **total lead time from contract placement to discharge in India is roughly 30–50 days**, depending on:  
   - **Charter‑pooling and vessel‑scheduling delays** (0–7 days to fix a tanker)  
   - **Voyage time** (10–14 days Gulf–India)  
   - **Loading and discharge** (1–3 days each)  
 [infra.economictimes.indiatimes](https://infra.economictimes.indiatimes.com/news/ports-shipping/deendayal-port-authority-prepares-for-major-surge-set-to-handle-22-vessels-in-72-hours/129539922)

   For **Russia‑via‑Suez**, this can stretch to **40–70 days one way** due to longer sailing and Suez‑routing variability. [sberbank.co](https://sberbank.co.in/media/publications/pathways-of-cooperation-russia-india-cargo-routes?type=trends)

***

### **Bibliography (source snapshot)**

Below is a quick reference list; each entry is labelled with 2–3 words describing the key data item extracted.

-  – **Indian tanker charter count** [tribuneindia](https://www.tribuneindia.com/news/business/india-to-build-own-fleet-of-oil-tankers-aims-to-cut-usd-8-billion-charter-costs-hardeep-puri/)
-  – **Indian PSU charter spend** [timesofindia.indiatimes](https://timesofindia.indiatimes.com/city/mumbai/indias-oil-psus-spent-8bn-on-chartered-ships-in-5-years-amount-could-have-funded-tanker-fleet-minister/articleshow/124907869.cms)
-  – **Planned Indian tanker fleet** [myind](https://myind.net/Home/viewArticle/india-plans-to-buy-over-100-make-in-india-crude-oil-tankers-worth10billion)
-  – **Tanker cargo sizes** [eia](https://www.eia.gov/todayinenergy/detail.php?id=17991)
-  – **Tanker class definitions** [hellenicshippingnews](https://www.hellenicshippingnews.com/wp-content/uploads/2022/08/2022-08-Crude-Tanker-Outlook.pdf)
-  – **Middle East–Asia voyage days** [mol-service](https://www.mol-service.com/blog/vessel-speed-and-sailing-days)
-  – **India VLCC import terminal** [splash247](https://splash247.com/india-receives-first-fully-laden-vlcc-at-mundra/)
-  – **Crude discharge time** [infra.economictimes.indiatimes](https://infra.economictimes.indiatimes.com/news/ports-shipping/deendayal-port-authority-prepares-for-major-surge-set-to-handle-22-vessels-in-72-hours/129539922)
-  – **India–Russia sea route days** [sber.bank](https://sber.bank.in/media/publications/pathways-of-cooperation-russia-india-cargo-routes?type=trends)
-  – **Baltic–India crude transit** [gcaptain](https://gcaptain.com/russia-keeps-crude-exports-flowing-ahead-of-trump-putin-summit/)
-  – **ESPO‑Pacific sailing time** [datamarnews](https://datamarnews.com/noticias/more-russian-tankers-forced-to-wait-or-reroute-after-washington-tightens-sanctions/)
-  – **India crude stock 100 Mbbl** [dailyexcelsior](https://www.dailyexcelsior.com/indias-100-mn-barrel-crude-stocks-could-cover-40-45-days-if-hormuz-flows-disrupted/)
-  – **SPR capacity and fill** [linkedin](https://www.linkedin.com/posts/business-today-india_exclusive-indias-strategic-oil-reserves-activity-7442134553873440768-v8nz)
-  – **SPR filling via refiners** [iocl](https://www.iocl.com/MediaDetails/55101)
-  – **India demand 4.5 M bpd** [energy.economictimes.indiatimes](https://energy.economictimes.indiatimes.com/news/oil-and-gas/indias-oil-demand-surges-to-4-5-million-barrels-per-day-aims-for-top-demand-hub-by-2030/110192162)
-  – **India crude import tonnes** [seair.co](https://www.seair.co.in/blog/oil-imports-in-india.aspx)
-  – **Russian import share** [testbook](https://testbook.com/question-answer/in-august-2025-indias-daily-import-volume--68d3ff0519272136c33625cf)
-  – **Gulf–India freight $/bbl** [bharatpetroleum](https://www.bharatpetroleum.in/pdf/petropricesheet/pp_9_pricebuildupsensitiveproducts_1_2_3.pdf)
-  – **Russia‑India freight + premium** [scanx](https://scanx.trade/stock-market-news/commodities/indian-refiners-purchase-millions-of-barrels-of-russian-crude-oil-cargoes/34279543)
-  – **War‑risk insurance premium** [economictimes](https://economictimes.com/industry/transportation/shipping-/-transport/crisis-in-west-asia-drives-up-shipping-insurance-premiums-raising-costs-for-freight-carriers/articleshow/128967522.cms)