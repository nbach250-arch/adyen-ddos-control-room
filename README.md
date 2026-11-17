# Adyen-inspired DDoS Control Room — Interactive Classroom Prototype

This is a **simulation**, not Adyen software. The three providers, traffic, attacks, prices, and payment results are fictional. There is no real network traffic, no external provider integration, and no actual payment processing.

## Start on macOS (Python 3.9)

1. Extract the ZIP and open the **adyen_ddos_control_room** folder in Finder.
2. Right-click the folder → **New Terminal at Folder**. Or in Terminal use `cd` into that folder.
3. Install dependencies if needed: `python3 -m pip install -r requirements.txt`.
4. Run: `python3 app.py`.
5. Open http://127.0.0.1:5000 in Safari or Chrome.
6. Keep Terminal open. To stop the server, press Control+C in Terminal.

If you receive **Address already in use**: the old version is still running. Go to the old Terminal window and press **Control+C**. Then run this version again.

## Hands-on demonstration (about 2 minutes)

1. Begin with all three providers healthy; show Shield A is active.
2. Choose **Volumetric DDoS flood**, target **Shield A**, set intensity to **130%**, press **Launch attack**.
3. Observe its used capacity, error rate, failed payments, and performance chart.
4. After **three unhealthy checks**, automatic failover attempts to route to a healthy backup with available capacity; watch the event timeline.
5. Toggle **Automatic failover OFF** and use the **Route here** buttons to compare manual control.
6. Change filter strength, reserved capacity, and customer traffic. Discuss the limits of the alternatives.
7. Click **Stop attack** and **Reset simulation** to repeat.

## Assumptions and limitations

- Flask runs locally and manages a synthetic per-tick model. The browser requests a simulation tick approximately every 2 seconds. Only one shared demo session is supported.
- Provider capacities are simulated as requests per second, and DDoS filtering reduces untrusted request load.
- A provider is unhealthy when fewer than 95% of payments succeed or its simulated latency reaches 230 ms.
- Three consecutive unhealthy samples trigger failover if automatic switching is enabled and a healthy alternate exists. A cooldown helps limit flapping.
- The simulation may instantly change the selected provider after a decision; it does **not** model real DNS/BGP propagation or full stateful traffic-switching delays.
- The numerical model is illustrative; it is not a verified performance model of Adyen, any DDoS product, or a particular attack.
- It does not prevent overload inside Adyen’s own payment processing systems.

## Files

- `app.py`: Flask routes, synthetic traffic model, automatic-switching decision logic.
- `templates/index.html`: browser interface.
- `static/style.css`: dashboard styling.
- `static/app.js`: interactive controls, live chart, and UI state.
- `requirements.txt`: Flask only.
