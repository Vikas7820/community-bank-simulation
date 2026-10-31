import unittest

from bank_simulation import OPEN_MINUTES, TELLER_COUNT, simulate_bank


class BankSimulationTests(unittest.TestCase):
    def test_seed_makes_the_simulation_reproducible(self):
        first = simulate_bank(seed=17)
        second = simulate_bank(seed=17)
        self.assertEqual(first, second)

    def test_customers_arrive_during_open_hours_and_use_valid_tellers(self):
        result = simulate_bank(seed=17)
        self.assertGreater(result.served_count, 0)
        self.assertTrue(all(0 <= customer.arrival < OPEN_MINUTES for customer in result.customers))
        self.assertTrue(all(0 <= customer.teller < TELLER_COUNT for customer in result.customers))

    def test_waits_and_teller_busy_time_are_valid(self):
        result = simulate_bank(seed=17)
        self.assertTrue(all(customer.wait >= 0 for customer in result.customers))
        self.assertGreaterEqual(result.worst_wait, result.average_wait)
        self.assertTrue(
            all(0 <= minutes <= OPEN_MINUTES for minutes in result.teller_busy_minutes)
        )

    def test_queue_and_active_customer_counts_match_a_time_snapshot(self):
        result = simulate_bank(seed=17)
        minute = 120.0
        expected_queue = sum(
            customer.arrival <= minute < customer.service_start
            for customer in result.customers
        )
        self.assertEqual(result.queue_length(minute), expected_queue)
        self.assertLessEqual(len(result.active_customers(minute)), TELLER_COUNT)

    def test_teller_busy_time_grows_only_as_service_is_performed(self):
        result = simulate_bank(seed=17)
        self.assertEqual(result.teller_busy_minutes_through(0), (0.0, 0.0))
        self.assertEqual(
            result.teller_busy_minutes_through(OPEN_MINUTES),
            result.teller_busy_minutes,
        )


if __name__ == "__main__":
    unittest.main()
