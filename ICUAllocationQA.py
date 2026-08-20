# Quick execution template for ICUAllocationQA.py
import unittest
from ICUAllocationQA import ICUManager, Patient, InvalidVitalError, DuplicatePatientError

class TestICUAllocation(unittest.TestCase):
    def setUp(self):
        self.icu = ICUManager(total_beds=1)

    def test_invalid_oxygen(self):
        with self.assertRaises(InvalidVitalError):
            Patient(patient_id="P01", oxygen_level=105, heart_rate=75)

    def test_competing_patients_fifo(self):
        p1 = Patient(patient_id="P01", priority=2, timestamp=100)
        p2 = Patient(patient_id="P02", priority=2, timestamp=101)
        self.icu.add_patient(p1)
        self.icu.add_patient(p2)
        allocated = self.icu.allocate_bed()
        self.assertEqual(allocated.patient_id, "P01")

if __name__ == "__main__":
    unittest.main()
