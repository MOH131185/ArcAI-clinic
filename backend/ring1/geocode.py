from geopy.geocoders import GoogleV3

class Geocoder:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Missing Google API key")
        self.geolocator = GoogleV3(api_key=api_key)

    def geocode_address(self, address: str):
        """
        Turn a free-form address or postcode into
        { latitude, longitude, formatted_address }.
        """
        if not address.strip():
            raise ValueError("Address must not be empty")
        loc = self.geolocator.geocode(address)
        if loc is None:
            raise ValueError(f"Could not geocode '{address}'")
        return {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "formatted_address": loc.address,
        }


