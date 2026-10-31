# TSP Challenge and Bank Simulation

This project includes a Traveling Salesman Problem solver and a SimPy bank-branch queue simulation.

## TSP solver

- parses TSPLIB `.tsp` files
- builds an initial tour with Nearest Neighbor
- improves it with a custom 2-opt heuristic
- visualizes the initial and improved tours on a map
- supports benchmark datasets included in the project and file uploads

Run the TSP solver:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Bank simulation

The Community Bank app simulates an eight-hour day with random customer arrivals,
exponential service times, a choice of two or three tellers, and one shared
first-come, first-served queue. Choose any date in January: each date has its own
repeatable arrival schedule, while changing teller count keeps that day's arrivals
identical. A first-hour chart compares January 1 and January 31, including the
same January 1 arrivals with both teller counts. The animated view includes
pause, resume, restart, and playback-speed controls, along with average and worst
wait, current queue length, and teller busy percentages.

Run the bank simulation:

```bash
streamlit run bank_app.py
```

## Notes

- The provided TSPLIB datasets are coordinate-space Euclidean instances, so the solver reports the TSPLIB `EUC_2D` distance units rather than converting them to kilometers.
- The solver deliberately avoids optimizer packages such as OR-Tools, SciPy, or PuLP.
