import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.*;

/**
 * RideBookingQA - Automated test suite for validating the RideBooking system.
 */
public class RideBookingQA {

    private RideBookingService bookingService;

    @BeforeEach
    void setUp() {
        // Initialize service and mock state before each test
        bookingService = new RideBookingService();
        bookingService.registerDriver("D101", VehicleType.SEDAN, true);
        bookingService.registerDriver("D102", VehicleType.SUV, true);
        bookingService.registerDriver("D103", VehicleType.LUXURY, false); // Unavailable driver
    }

    @Test
    @DisplayName("Normal booking: Standard trip during regular hours")
    void testNormalBooking() {
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(2)
                .setDistanceKm(10.0)
                .setBookingTime("14:00") // Off-peak
                .setVehicleType(VehicleType.SEDAN)
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertTrue(response.isSuccess());
        assertNotNull(response.getAssignedDriverId());
        assertEquals(15.00, response.getFinalFare(), 0.01);
    }

    @Test
    @DisplayName("Peak-hour booking: Applies surge multiplier")
    void testPeakHourBooking() {
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(1)
                .setDistanceKm(10.0)
                .setBookingTime("08:30") // Peak morning hour
                .setVehicleType(VehicleType.SEDAN)
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertTrue(response.isSuccess());
        assertEquals(1.5, response.getSurgeMultiplier());
        assertEquals(22.50, response.getFinalFare(), 0.01);
    }

    @Test
    @DisplayName("Night booking: Applies night fare surcharge")
    void testNightBooking() {
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(1)
                .setDistanceKm(10.0)
                .setBookingTime("23:30") // Night time
                .setVehicleType(VehicleType.SEDAN)
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertTrue(response.isSuccess());
        assertTrue(response.isNightSurchargeApplied());
        assertEquals(18.00, response.getFinalFare(), 0.01);
    }

    @ParameterizedTest
    @ValueSource(doubles = {0.0, -1.0, -15.5})
    @DisplayName("Invalid distance: Rejects zero or negative distances")
    void testInvalidDistance(double invalidDistance) {
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(1)
                .setDistanceKm(invalidDistance)
                .setBookingTime("12:00")
                .setVehicleType(VehicleType.SEDAN)
                .build();

        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            bookingService.bookRide(request);
        });

        assertEquals("Distance must be greater than zero.", exception.getMessage());
    }

    @ParameterizedTest
    @ValueSource(ints = {0, -1, 7})
    @DisplayName("Invalid passenger count: Rejects out-of-bounds passenger numbers")
    void testInvalidPassengerCount(int invalidPassengers) {
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(invalidPassengers)
                .setDistanceKm(5.0)
                .setBookingTime("12:00")
                .setVehicleType(VehicleType.SEDAN)
                .build();

        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            bookingService.bookRide(request);
        });

        assertTrue(exception.getMessage().contains("Invalid passenger count"));
    }

    @Test
    @DisplayName("Unavailable driver: Rejects booking when vehicle type driver is offline")
    void testUnavailableDriver() {
        // Luxury driver D103 is marked offline in setup
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(2)
                .setDistanceKm(5.0)
                .setBookingTime("12:00")
                .setVehicleType(VehicleType.LUXURY)
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertFalse(response.isSuccess());
        assertEquals("No available drivers for requested vehicle type.", response.getErrorMessage());
    }

    @Test
    @DisplayName("Maximum discount: Caps total promo discount at maximum limit")
    void testMaximumDiscount() {
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(1)
                .setDistanceKm(100.0) // High fare to trigger max cap
                .setBookingTime("12:00")
                .setVehicleType(VehicleType.SEDAN)
                .setPromoCode("FLAT50PERCENT") // Raw discount would be $75
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertTrue(response.isSuccess());
        assertEquals(30.00, response.getDiscountAmount()); // Max discount cap is $30.00
        assertEquals(120.00, response.getFinalFare(), 0.01);
    }

    @Test
    @DisplayName("Multiple vehicle types: Correct base rates for different vehicles")
    void testMultipleVehicleTypes() {
        BookingRequest sedanRequest = new BookingRequest.Builder()
                .setPassengerCount(1).setDistanceKm(10.0).setBookingTime("12:00")
                .setVehicleType(VehicleType.SEDAN).build();

        BookingRequest suvRequest = new BookingRequest.Builder()
                .setPassengerCount(1).setDistanceKm(10.0).setBookingTime("12:00")
                .setVehicleType(VehicleType.SUV).build();

        BookingResponse sedanResponse = bookingService.bookRide(sedanRequest);
        BookingResponse suvResponse = bookingService.bookRide(suvRequest);

        assertTrue(suvResponse.getFinalFare() > sedanResponse.getFinalFare());
    }

    @Test
    @DisplayName("Boundary fare values: Minimum fare application")
    void testBoundaryFareValues() {
        // Very short trip (0.1 km) should trigger minimum trip fare threshold ($5.00)
        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(1)
                .setDistanceKm(0.1)
                .setBookingTime("12:00")
                .setVehicleType(VehicleType.SEDAN)
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertTrue(response.isSuccess());
        assertEquals(5.00, response.getFinalFare(), 0.01);
    }

    @Test
    @DisplayName("Driver allocation logic: Assigns nearest available driver")
    void testDriverAllocationLogic() {
        // Register drivers at different locations relative to pickup point (0,0)
        bookingService.registerDriverWithLocation("D201", VehicleType.SEDAN, true, 10.0, 10.0); // Far
        bookingService.registerDriverWithLocation("D202", VehicleType.SEDAN, true, 1.0, 1.0);   // Near

        BookingRequest request = new BookingRequest.Builder()
                .setPassengerCount(1)
                .setDistanceKm(5.0)
                .setBookingTime("12:00")
                .setVehicleType(VehicleType.SEDAN)
                .setPickupLocation(0.0, 0.0)
                .build();

        BookingResponse response = bookingService.bookRide(request);

        assertTrue(response.isSuccess());
        assertEquals("D202", response.getAssignedDriverId()); // Closest driver selected
    }
}
