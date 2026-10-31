from __future__ import annotations

import html
import time

import plotly.graph_objects as go
import streamlit as st

from bank_simulation import (
    OPEN_MINUTES,
    SimulationResult,
    arrival_times_for_day,
    simulate_bank,
)


st.set_page_config(page_title="Community Bank Simulation", layout="wide")

st.markdown(
    """
    <style>
    .block-container { max-width: 1120px; padding-top: 1.5rem; }
    .bank-title { text-align: center; color: #233448; font-size: 1.6rem;
                  font-weight: 700; margin: 0 0 1rem; }
    .bank-frame { border: 2px solid #293849; border-radius: 2px;
                  background: #fbfaff; }
    .metric-card { background: #f3f5fa; border: 1px solid #e1e5ef;
                   border-radius: 10px; padding: 1rem 1.15rem; }
    .metric-label { color: #596579; font-size: .9rem; }
    .metric-value { color: #24364a; font-size: 1.5rem; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


def arrival_comparison_chart() -> go.Figure:
    comparisons = (
        ("January 1 · 2 tellers", 1, "#1f77b4"),
        ("January 31 · 2 tellers", 31, "#d46a77"),
        ("January 1 · 3 tellers", 1, "#168b78"),
    )
    figure = go.Figure()
    for label, day, color in comparisons:
        first_hour = [
            minute for minute in arrival_times_for_day(day) if minute <= 60
        ]
        figure.add_trace(
            go.Scatter(
                x=first_hour,
                y=[label] * len(first_hour),
                mode="markers",
                marker=dict(
                    symbol="line-ns",
                    size=16,
                    color=color,
                    line=dict(width=2, color=color),
                ),
                name=label,
                hovertemplate=f"{label}<br>Minute %{{x:.1f}}<extra></extra>",
            )
        )

    figure.update_layout(
        title="First-hour customer arrivals",
        xaxis=dict(title="Minute of the day", range=[0, 60], dtick=15),
        yaxis=dict(title="", categoryorder="array", categoryarray=[
            "January 1 · 3 tellers",
            "January 31 · 2 tellers",
            "January 1 · 2 tellers",
        ]),
        height=270,
        margin=dict(l=20, r=20, t=55, b=35),
        showlegend=False,
        template="plotly_white",
    )
    return figure


def draw_branch(result: SimulationResult, minute: float) -> str:
    queue = [
        customer
        for customer in result.customers
        if customer.arrival <= minute < customer.service_start
    ]
    active = result.active_customers(minute)
    positions = []
    for index, customer in enumerate(queue[:36]):
        row, column = divmod(index, 18)
        x = 145 + column * 31
        y = 266 + row * 42
        positions.append(
            f'<circle cx="{x}" cy="{y}" r="10" fill="#1482b8">'
            f'<title>Customer {customer.customer_id}, waiting '
            f'{customer.wait:.1f} minutes total</title></circle>'
        )

    teller_customers = {customer.teller: customer for customer in active}
    teller_drawings = []
    teller_count = len(result.teller_busy_minutes)
    for teller in range(teller_count):
        center = 400 + (teller - (teller_count - 1) / 2) * 150
        teller_drawings.append(
            f'<rect x="{center - 45}" y="104" width="90" height="52" rx="8" '
            f'fill="#087e82"/><text x="{center}" y="136" class="teller-label">'
            f'TELLER {teller + 1}</text>'
        )
        customer = teller_customers.get(teller)
        if customer:
            teller_drawings.append(
                f'<circle cx="{center}" cy="183" r="13" fill="#e4775d">'
                f'<title>Customer {customer.customer_id}</title></circle>'
            )

    queue_dots = "\n".join(positions)
    teller_shapes = "\n".join(teller_drawings)
    clipped_note = (
        f'<text x="690" y="286" class="small">+{len(queue) - 36} more</text>'
        if len(queue) > 36
        else ""
    )
    return f"""
    <div class="bank-frame">
      <svg viewBox="0 0 800 470" role="img" aria-label="Animated bank branch">
        <style>
          .title {{ font: bold 22px Arial; fill: #28384b; }}
          .label {{ font: 12px Arial; fill: #586579; }}
          .small {{ font: 11px Arial; fill: #586579; }}
          .teller-label {{ font: bold 12px Arial; fill: white; text-anchor: middle; }}
        </style>
        <rect x="95" y="35" width="610" height="360" fill="#fbfaff"
              stroke="#2d3948" stroke-width="3"/>
        <text x="400" y="72" class="title" text-anchor="middle">COMMUNITY BANK</text>
        <rect x="90" y="205" width="20" height="78" fill="#23a6c0"/>
        <text x="106" y="248" class="small" text-anchor="middle"
              transform="rotate(-90 106 248)">ENTRANCE</text>
        <rect x="690" y="230" width="20" height="70" fill="#d97878"/>
        <text x="704" y="266" class="small" text-anchor="middle"
              transform="rotate(-90 704 266)">EXIT</text>
        {teller_shapes}
        <line x1="180" y1="220" x2="620" y2="220" stroke="#a9a9b5"
              stroke-width="3"/>
        <text x="400" y="211" class="label" text-anchor="middle">CUSTOMER QUEUE</text>
        {queue_dots}
        {clipped_note}
        <text x="400" y="350" class="title" text-anchor="middle"
              style="font-size:15px">Minute {minute:.1f} of {OPEN_MINUTES}</text>
        <text x="400" y="374" class="label" text-anchor="middle">
          Waiting: {len(queue)}  |  Tellers busy: {len(active)}/{teller_count}
        </text>
      </svg>
    </div>
    """


def current_minute() -> float:
    base = st.session_state.get("bank_elapsed", 0.0)
    if not st.session_state.get("bank_paused", False):
        base += (time.monotonic() - st.session_state.bank_started_at) * st.session_state.bank_speed
    return min(float(OPEN_MINUTES), base)


def reset_clock() -> None:
    st.session_state.bank_elapsed = 0.0
    st.session_state.bank_started_at = time.monotonic()
    st.session_state.bank_paused = False


if "bank_speed" not in st.session_state:
    st.session_state.bank_speed = 4.0

st.title("Community Bank — Branch Simulation")
day_column, teller_column = st.columns(2)
selected_day = day_column.selectbox(
    "Simulation date in January",
    options=range(1, 32),
    format_func=lambda day: f"January {day}",
)
selected_teller_count = teller_column.selectbox(
    "Number of tellers",
    options=(2, 3),
    index=1,
)

st.caption(
    "Random arrivals every 3 minutes on average · Exponential service time "
    f"of 4 minutes · {selected_teller_count} tellers · "
    "One first-come, first-served queue"
)

st.subheader("Test the random numbers too")
st.plotly_chart(arrival_comparison_chart(), use_container_width=True)
st.caption(
    "January 1 has the same arrival times with 2 or 3 tellers. "
    "January 31 uses a different, repeatable arrival schedule."
)

simulation_config = (selected_day, selected_teller_count)
if st.session_state.get("bank_config") != simulation_config:
    st.session_state.bank_config = simulation_config
    reset_clock()
result: SimulationResult = simulate_bank(
    seed=selected_day,
    teller_count=selected_teller_count,
)


@st.fragment(run_every=0.25)
def simulation_panel() -> None:
    minute = current_minute()
    if minute >= OPEN_MINUTES and not st.session_state.bank_paused:
        st.session_state.bank_elapsed = float(OPEN_MINUTES)
        st.session_state.bank_paused = True

    st.markdown(
        draw_branch(result, minute),
        unsafe_allow_html=True,
    )
    metric_columns = st.columns(4)
    elapsed_busy = result.teller_busy_minutes_through(minute)
    overall_busy = sum(elapsed_busy) / (len(elapsed_busy) * OPEN_MINUTES) * 100
    metrics = (
        ("Average wait", f"{result.average_wait:.1f} min"),
        ("Worst wait", f"{result.worst_wait:.1f} min"),
        ("Queue now", f"{result.queue_length(minute)} customers"),
        ("Teller busy", f"{overall_busy:.1f}%"),
    )
    for column, (label, value) in zip(metric_columns, metrics):
        column.markdown(
            f'<div class="metric-card"><div class="metric-label">{html.escape(label)}'
            f'</div><div class="metric-value">{html.escape(value)}</div></div>',
            unsafe_allow_html=True,
        )

    controls = st.columns([1, 1, 5])
    if st.session_state.bank_paused:
        if controls[0].button("Resume", use_container_width=True):
            st.session_state.bank_started_at = time.monotonic()
            st.session_state.bank_paused = False
            st.rerun()
    elif controls[0].button("Pause", use_container_width=True):
        st.session_state.bank_elapsed = minute
        st.session_state.bank_paused = True
        st.rerun()
    if controls[1].button("Restart", use_container_width=True):
        reset_clock()
        st.rerun()

    speed = controls[2].slider(
        "Playback speed (simulation minutes per real second)",
        min_value=1.0,
        max_value=20.0,
        value=float(st.session_state.bank_speed),
        step=1.0,
    )
    if speed != st.session_state.bank_speed:
        minute = current_minute()
        st.session_state.bank_elapsed = minute
        st.session_state.bank_started_at = time.monotonic()
        st.session_state.bank_speed = speed

    teller_columns = st.columns(selected_teller_count)
    for index, column in enumerate(teller_columns):
        busy = elapsed_busy[index] / OPEN_MINUTES * 100
        column.progress(
            min(100, int(busy)),
            text=f"Teller {index + 1} busy during open hours: {busy:.1f}%",
        )
    st.caption(
        f"{result.served_count} customers arrived during the 8-hour day. "
        "Wait statistics include every customer who arrived before closing."
    )


simulation_panel()
