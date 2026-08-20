class ICUAllocationSystem:
    def __init__(self, total_beds):
        self.total_beds = total_beds
        self.allocated_beds = {}  # {patient_id: patient_info}
        self.waiting_list = []    # List of patient dicts sorted by priority score
        self.registered_ids = set()

    def calculate_priority_score(self, age, oxygen, heart_rate, bp, temp, existing_conditions):
        """Calculates a numerical risk score based on vital signs and medical history."""
        score = 0
        
        # Oxygen Level scoring
        if oxygen < 90: score += 40
        elif oxygen < 94: score += 20
            
        # Heart Rate scoring (BPM)
        if heart_rate > 120 or heart_rate < 50: score += 25
        elif heart_rate > 100 or heart_rate < 60: score += 10
            
        # Blood Pressure scoring (Systolic estimate)
        if bp < 90 or bp > 180: score += 20
        elif bp < 100 or bp > 140: score += 10
            
        # Temperature scoring (°C)
        if temp > 39.0 or temp < 35.0: score += 15
            
        # Age risk factor
        if age >= 70: score += 15
        elif age >= 50: score += 10
            
        # Existing conditions (5 points per condition, capped at 20)
        score += min(len(existing_conditions) * 5, 20)
        
        return score

    def classify_patient(self, score, is_emergency=False):
        """Classifies patient based on priority score or emergency flag."""
        if is_emergency or score >= 70:
            return "CRITICAL"
        elif score >= 45:
            return "HIGH"
        elif score >= 25:
            return "MEDIUM"
        return "LOW"

    def register_and_allocate(self, patient_id, age, oxygen, heart_rate, bp, temp, 
                              existing_conditions, is_emergency=False):
        # Reject duplicate Patient IDs
        if patient_id in self.registered_ids:
            return f"Error: Patient ID '{patient_id}' already exists in the system."
        
        score = self.calculate_priority_score(age, oxygen, heart_rate, bp, temp, existing_conditions)
        category = self.classify_patient(score, is_emergency)
        
        patient = {
            "id": patient_id,
            "age": age,
            "score": score,
            "category": category,
            "is_emergency": is_emergency
        }
        
        self.registered_ids.add(patient_id)

        # Emergency override logic: displace lowest priority non-critical patient if beds are full
        if is_emergency and len(self.allocated_beds) >= self.total_beds:
            displaceable = [p for p in self.allocated_beds.values() if p["category"] != "CRITICAL"]
            if displaceable:
                # Displace patient with lowest score
                displaceable.sort(key=lambda x: x["score"])
                displaced_patient = displaceable[0]
                
                del self.allocated_beds[displaced_patient["id"]]
                self.waiting_list.append(displaced_patient)
                self.waiting_list.sort(key=lambda x: (x["category"] != "CRITICAL", -x["score"]))
                
                self.allocated_beds[patient_id] = patient
                return f"EMERGENCY OVERRIDE: Patient {patient_id} allocated a bed. Patient {displaced_patient['id']} moved to waiting list."

        # Standard Bed Allocation Logic
        if len(self.allocated_beds) < self.total_beds:
            self.allocated_beds[patient_id] = patient
            return f"Patient {patient_id} ({category}) allocated an ICU bed."
        else:
            self.waiting_list.append(patient)
            # Keep waiting list sorted: CRITICAL first, then by highest score
            self.waiting_list.sort(key=lambda x: (x["category"] != "CRITICAL", -x["score"]))
            return f"No beds available. Patient {patient_id} ({category}) placed on waiting list (Position {len(self.waiting_list)})."

    def release_bed(self, patient_id):
        """Releases a bed and automatically allocates it to the highest priority waiting patient."""
        if patient_id in self.allocated_beds:
            del self.allocated_beds[patient_id]
            msg = f"Bed freed up by Patient {patient_id}."
            
            if self.waiting_list:
                next_patient = self.waiting_list.pop(0)
                self.allocated_beds[next_patient["id"]] = next_patient
                msg += f" Assigned to Patient {next_patient['id']} ({next_patient['category']}) from waiting list."
            return msg
        return f"Patient {patient_id} not found in allocated beds."


# Demonstration / Usage
if __name__ == "__main__":
    system = ICUAllocationSystem(total_beds=2)

    # 1. Register Patient 101 (Medium risk)
    print(system.register_and_allocate("P101", age=45, oxygen=95, heart_rate=80, bp=120, temp=37.0, existing_conditions=[]))

    # 2. Register Patient 102 (Critical risk)
    print(system.register_and_allocate("P102", age=72, oxygen=88, heart_rate=125, bp=85, temp=39.2, existing_conditions=["Diabetes", "Hypertension"]))

    # 3. Duplicate ID test
    print(system.register_and_allocate("P101", age=30, oxygen=99, heart_rate=70, bp=110, temp=36.6, existing_conditions=[]))

    # 4. Beds full: Register Patient 103 (High risk -> goes to waiting list)
    print(system.register_and_allocate("P103", age=60, oxygen=92, heart_rate=105, bp=135, temp=38.0, existing_conditions=["Asthma"]))

    # 5. Emergency Override: Register Patient 104 as emergency (Displaces non-critical bed holder P101)
    print(system.register_and_allocate("P104", age=50, oxygen=91, heart_rate=110, bp=130, temp=37.5, existing_conditions=[], is_emergency=True))

    # 6. Release a bed
    print(system.release_bed("P102"))
