
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get current weather for a location"""
    return {
        "temperature": 25,
        "weather_description": "Sunny",
        "humidity": 60,
        "wind_speed": 10
    }