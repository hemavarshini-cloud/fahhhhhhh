import datetime


class RideBooking:

    VEHICLE_CONFIG = {
        "Bike": {
            "base_fare": 20,
            "rate_per_km": 8,
            "max_passengers": 1
        },
        "Sedan": {
            "base_fare": 50,
            "rate_per_km": 14,
            "max_passengers": 4
        },
        "SUV": {
            "base_fare": 80,
            "rate_per_km": 18,
            "max_passengers": 6
        },
        "Premium": {
            "base_fare": 120,
            "rate_per_km": 25,
            "max_passengers": 4
        },
    }

    def __init__(self, promo_code=None):
        self.promo_code = promo_code

    def validate_booking(self, distance, passengers, vehicle_type,
                         booking_time, drivers_available):
        # 1. Distance check
        if distance <= 0:
            return False, "Invalid distance. Distance must be greater than 0 km."

        # 2. Vehicle type check
        if vehicle_type not in self.VEHICLE_CONFIG:
            return False, f"Invalid vehicle type. Choose from {list(self.VEHICLE_CONFIG.keys())}."

        # 3. Passenger capacity check
        max_cap = self.VEHICLE_CONFIG[vehicle_type]["max_passengers"]
        if passengers <= 0 or passengers > max_cap:
            return False, f"Excessive or invalid passengers. {vehicle_type} allows a maximum of {max_cap} passenger(s)."

        # 4. Time format check
        try:
            time_obj = datetime.datetime.strptime(booking_time,
                                                  "%H:%M").time()
        except ValueError:
            return False, "Invalid booking time format. Please use HH:MM format (e.g., 08:30 or 22:15)."

        # 5. Driver availability check
        if not drivers_available.get(vehicle_type, False):
            return False, f"Booking rejected. No {vehicle_type} drivers are currently available."

        return True, time_obj

    def calculate_fare(self, distance, passengers, vehicle_type, booking_time,
                       promo_code=None):
        config = self.VEHICLE_CONFIG[vehicle_type]

        # Base and Distance-Based Fares
        base_fare = config["base_fare"]
        distance_fare = distance * config["rate_per_km"]

        # Peak-Hour Surcharge (08:00–10:00 and 17:00–20:00 -> 25% on distance fare)
        hour = booking_time.hour
        is_peak = (8 <= hour < 10) or (17 <= hour < 20)
        peak_surcharge = (distance_fare * 0.25) if is_peak else 0.0

        # Night Surcharge (22:00–05:00 -> 20% on subtotal)
        is_night = (hour >= 22) or (hour < 5)
        subtotal_before_night = base_fare + distance_fare + peak_surcharge
        night_surcharge = (subtotal_before_night *
                           0.20) if is_night else 0.0

        # Passenger Surcharge (Additional charge if capacity is nearly full)
        passenger_surcharge = 0.0
        if passengers > 2 and vehicle_type in ["Sedan", "SUV"]:
            passenger_surcharge = (passengers - 2) * 15.0

        # Subtotal before discount
        gross_fare = subtotal_before_night + night_surcharge + passenger_surcharge

        # Promotional Discount (e.g., 'SAVE10' gives 10% off up to 50)
        discount = 0.0
        if promo_code == "SAVE10":
            discount = min(gross_fare * 0.10, 50.0)
        elif promo_code == "FIRST50":
            discount = 50.0

        final_fare = max(0.0, gross_fare - discount)

        return {
            "Base Fare": round(base_fare, 2),
            "Distance Fare": round(distance_fare, 2),
            "Peak-Hour Surcharge": round(peak_surcharge, 2),
            "Night Surcharge": round(night_surcharge, 2),
            "Passenger Surcharge": round(passenger_surcharge, 2),
            "Promotional Discount": round(discount, 2),
            "Final Fare": round(final_fare, 2),
        }

    def allocate_driver(self, vehicle_type, available_driver_list):
        for driver in available_driver_list:
            if driver["vehicle_type"] == vehicle_type and driver["status"] == "Available":
                driver["status"] = "Occupied"
                return driver["driver_id"], driver["driver_name"]
        return None, None

    def process_booking(self, customer_id, pickup, drop, distance, passengers,
                        vehicle_type, booking_time, driver_availability_map,
                        driver_list, promo_code=None):

        print(f"\n--- Processing Booking for Customer ID: {customer_id} ---")

        # Validation
        is_valid, validation_res = self.validate_booking(
            distance, passengers, vehicle_type, booking_time,
            driver_availability_map)

        if not is_valid:
            print(f"❌ BOOKING REJECTED: {validation_res}")
            return None

        parsed_time = validation_res

        # Calculate Fares
        fares = self.calculate_fare(distance, passengers, vehicle_type,
                                    parsed_time, promo_code)

        # Allocate Driver
        driver_id, driver_name = self.allocate_driver(vehicle_type, driver_list)

        # Output Summary
        print("✅ BOOKING CONFIRMED")
        print(f"Route: {pickup} ➔ {drop} ({distance} km)")
        print(f"Time: {booking_time} | Vehicle: {vehicle_type} | Passengers: {passengers}")
        print("\n--- Fare Breakdown ---")
        for key, val in fares.items():
            print(f"{key:<22}: ${val:.2f}")

        print("\n--- Driver Assignment ---")
        print(f"Assigned Driver : {driver_name} (ID: {driver_id})")

        return fares


# ==========================================
# Example Usage & Test Execution
# ==========================================
if __name__ == "__main__":
    app = RideBooking()

    # System States
    driver_availability = {
        "Bike": True,
        "Sedan": True,
        "SUV": False,  # SUVs unavailable in this pool
        "Premium": True
    }

    driver_database = [
        {"driver_id": "D101", "driver_name": "Alex Smith", "vehicle_type": "Sedan", "status": "Available"},
        {"driver_id": "D102", "driver_name": "Rajesh Kumar", "vehicle_type": "Bike", "status": "Available"},
        {"driver_id": "D103", "driver_name": "Elena Rostova", "vehicle_type": "Premium", "status": "Available"}
    ]

    # Test Case 1: Successful Peak Hour Booking
    app.process_booking(
        customer_id="CUST_8892",
        pickup="Downtown",
        drop="Airport",
        distance=18.5,
        passengers=3,
        vehicle_type="Sedan",
        booking_time="08:30",
        driver_availability_map=driver_availability,
        driver_list=driver_database,
        promo_code="SAVE10"
    )

    # Test Case 2: Rejected Booking (Passenger capacity exceeded)
    app.process_booking(
        customer_id="CUST_4412",
        pickup="Central Mall",
        drop="Suburbs",
        distance=12.0,
        passengers=3,  # Bike max cap is 1
        vehicle_type="Bike",
        booking_time="14:00",
        driver_availability_map=driver_availability,
        driver_list=driver_database
    )

    # Test Case 3: Rejected Booking (Vehicle Type Unavailable)
    app.process_booking(
        customer_id="CUST_1109",
        pickup="Hotel Plaza",
        drop="Resort",
        distance=25.0,
        passengers=5,
        vehicle_type="SUV",  # Marked unavailable in availability map
        booking_time="19:00",
        driver_availability_map=driver_availability,
        driver_list=driver_database
    )
