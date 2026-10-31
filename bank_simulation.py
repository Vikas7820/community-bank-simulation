from __future__ import annotations

import random
from dataclasses import dataclass

import simpy


OPEN_MINUTES = 480
TELLER_COUNT = 3
MEAN_INTERARRIVAL_MINUTES = 3.0
MEAN_SERVICE_MINUTES = 4.0


@dataclass(frozen=True)
class Customer:
    customer_id: int
    arrival: float
    service_start: float
    departure: float
    teller: int

    @property
    def wait(self) -> float:
        return self.service_start - self.arrival


@dataclass(frozen=True)
class SimulationResult:
    customers: tuple[Customer, ...]
    teller_busy_minutes: tuple[float, ...]
    average_wait: float
    worst_wait: float
    arrival_times: tuple[float, ...]

    @property
    def served_count(self) -> int:
        return len(self.customers)

    def queue_length(self, minute: float) -> int:
        return sum(
            customer.arrival <= minute < customer.service_start
            for customer in self.customers
        )

    def active_customers(self, minute: float) -> tuple[Customer, ...]:
        return tuple(
            customer
            for customer in self.customers
            if customer.service_start <= minute < customer.departure
        )

    def teller_busy_minutes_through(self, minute: float) -> tuple[float, ...]:
        elapsed = max(0.0, min(minute, OPEN_MINUTES))
        return tuple(
            sum(
                max(0.0, min(customer.departure, elapsed) - customer.service_start)
                for customer in self.customers
                if customer.teller == teller
            )
            for teller in range(len(self.teller_busy_minutes))
        )


def arrival_times_for_day(seed: int) -> tuple[float, ...]:
    """Return a reproducible arrival schedule independent of teller count."""
    rng = random.Random(seed)
    arrivals: list[float] = []
    minute = 0.0
    while True:
        minute += rng.expovariate(1 / MEAN_INTERARRIVAL_MINUTES)
        if minute >= OPEN_MINUTES:
            break
        arrivals.append(minute)
    return tuple(arrivals)


def simulate_bank(seed: int = 42, teller_count: int = TELLER_COUNT) -> SimulationResult:
    """Simulate one open day, then let all customers who arrived before closing finish."""
    if teller_count < 1:
        raise ValueError("teller_count must be at least 1")

    env = simpy.Environment()
    tellers = simpy.Resource(env, capacity=teller_count)
    completed: list[Customer] = []
    arrival_schedule = arrival_times_for_day(seed)
    service_rng = random.Random(seed ^ 0x5EED5EED)

    def customer_process(identifier: int, arrival: float):
        with tellers.request() as request:
            yield request
            service_start = env.now
            teller = tellers.users.index(request)
            service_duration = service_rng.expovariate(1 / MEAN_SERVICE_MINUTES)
            yield env.timeout(service_duration)
            completed.append(
                Customer(
                    customer_id=identifier,
                    arrival=arrival,
                    service_start=service_start,
                    departure=env.now,
                    teller=teller,
                )
            )

    def generate_arrivals():
        for customer_id, arrival in enumerate(arrival_schedule, start=1):
            yield env.timeout(arrival - env.now)
            env.process(customer_process(customer_id, arrival))

    env.process(generate_arrivals())
    env.run()
    completed.sort(key=lambda customer: customer.customer_id)

    if completed:
        waits = [customer.wait for customer in completed]
        average_wait = sum(waits) / len(waits)
        worst_wait = max(waits)
    else:
        average_wait = 0.0
        worst_wait = 0.0

    teller_busy_minutes = tuple(
        sum(
            max(0.0, min(customer.departure, OPEN_MINUTES) - customer.service_start)
            for customer in completed
            if customer.teller == teller
        )
        for teller in range(teller_count)
    )

    return SimulationResult(
        customers=tuple(completed),
        teller_busy_minutes=teller_busy_minutes,
        average_wait=average_wait,
        worst_wait=worst_wait,
        arrival_times=arrival_schedule,
    )
