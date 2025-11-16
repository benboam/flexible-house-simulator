# ⚡ Axle Energy – Flex Optimisation Demo  
_A lightweight prototype showing how Axle’s optimisation could be surfaced to partners_

This app is a **simple, time-boxed demo** that illustrates how Axle Energy could present value to OEMs, charger companies, energy suppliers, and battery providers.

The goal is **not** to replicate Axle’s real optimisation engine, orchestration layer, or market integrations — but to show, at a product level, how partners might experience:

- lower wholesale exposure  
- EV charging “ready when needed”  
- heating shifted into cleaner hours  
- portfolio-level savings  
- customer value that requires **no behaviour change**  

It uses real UK grid + price data to make the experience feel grounded in reality.

---

## ⚠️ Important Simplifications / Assumptions

This demo makes several **deliberate simplifying assumptions** to stay within a very tight build window:

### **1. No battery optimisation implemented**
Battery modelling was excluded for time reasons.  
The UI includes placeholders only.

### **2. No orchestration, market participation, or device realism**
The demo **does not** represent:

- device latency / firmware quirks  
- orchestration at scale  
- P415 / ESO / DSO market logic  
- constraints Axle handles in production  
- comfort curves or heat pump thermal modelling  
- FFR, wholesale, intraday, or capacity logic  

### **3. All homes acting identically would create unrealistic spikes**
If this exact optimisation were applied to thousands of homes simultaneously, the result would be:

- large price-reactive load spikes  
- unrealistic clustering of charging events  
- unhappy DSOs  

The demo intentionally ignores these constraints to keep the model simple and fast.

### **4. Optimisation is only heuristic**
This is **not** Axle’s optimiser — it’s a small Python model that:

- reschedules EV charging  
- shifts heat pump load inside comfort windows  
- evaluates price + carbon  
- preserves total energy needs  

Useful for **storytelling**, not real flexibility control.

---

## 🎯 What This Demo *Is* Meant to Show

- how partners could **offer customers lower bills without behaviour change**  
- how load can be shifted out of peak hours  
- how cleaner/cheaper periods differ through the day  
- how Axle enables differentiated tariffs or EV propositions  
- how savings scale from **one home → a full customer base**

It is a **product exploration**, not a backend simulation.

---

## 📊 Data Sources

All data is real and publicly accessible:

### **Carbon Intensity**
National Grid ESO Carbon Intensity API  
https://api.carbonintensity.org.uk/

### **Electricity Generation Mix**
National Grid ESO mix endpoints  
https://www.carbonintensity.org.uk/

### **Price Data**
Octopus Agile tariff API (when available for that date)  
https://docs.octopus.energy/rest/guides/endpoints

### **Timestamps & resolution**
All data is normalised into 30-minute settlement periods.


