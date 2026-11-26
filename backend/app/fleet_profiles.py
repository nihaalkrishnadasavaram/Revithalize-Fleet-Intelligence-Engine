from dataclasses import dataclass

ELECTRICITY_TARIFF_INR_PER_KWH = 9.0
TYPICAL_UTILIZATION = 0.62


@dataclass(frozen=True)
class VehicleProfile:
    annual_km: float
    monthly_capacity_km: float
    energy_kwh_per_100km: float
    monthly_fixed_cost_inr: float
    annual_maintenance_cost_inr: float
    average_trip_km: float
    battery_capacity_options_kwh: tuple
    fleet_share: float

    @property
    def cost_per_km_inr(self):
        electricity = ELECTRICITY_TARIFF_INR_PER_KWH * self.energy_kwh_per_100km / 100
        fixed = self.monthly_fixed_cost_inr / (self.monthly_capacity_km * TYPICAL_UTILIZATION)
        return electricity + fixed


VEHICLE_PROFILES = {
    "Scooter": VehicleProfile(9000, 1200, 3.2, 400, 3500, 12, (1.8, 2.4, 3.0, 3.6), 0.60),
    "Motorcycle": VehicleProfile(11000, 1500, 4.6, 550, 4500, 22, (3.0, 3.6, 4.5, 5.0), 0.40),
}


def get_profile(vehicle_type):
    try:
        return VEHICLE_PROFILES[vehicle_type]
    except KeyError:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}") from None
