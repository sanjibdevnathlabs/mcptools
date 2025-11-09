"""Mock OpenWeather API server for testing weather MCP.

This server mimics the OpenWeather API responses to avoid:
- Rate limits on the real API
- Network dependency in tests
- API key requirements
- Service availability issues
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock OpenWeather API")

# Mock weather data for various cities
MOCK_WEATHER_DATA = {
    "Mumbai": {
        "coord": {"lon": 72.8479, "lat": 19.0144},
        "weather": [
            {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}
        ],
        "base": "stations",
        "main": {
            "temp": 28.5,
            "feels_like": 31.2,
            "temp_min": 27.0,
            "temp_max": 30.0,
            "pressure": 1013,
            "humidity": 75,
        },
        "visibility": 10000,
        "wind": {"speed": 5.5, "deg": 270},
        "clouds": {"all": 20},
        "dt": int(datetime.now().timestamp()),
        "sys": {
            "type": 1,
            "id": 9052,
            "country": "IN",
            "sunrise": 1609823400,
            "sunset": 1609865400,
        },
        "timezone": 19800,
        "id": 1275339,
        "name": "Mumbai",
        "cod": 200,
    },
    "Delhi": {
        "coord": {"lon": 77.2167, "lat": 28.6667},
        "weather": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
        ],
        "base": "stations",
        "main": {
            "temp": 25.0,
            "feels_like": 24.5,
            "temp_min": 22.0,
            "temp_max": 27.0,
            "pressure": 1015,
            "humidity": 60,
        },
        "visibility": 10000,
        "wind": {"speed": 3.5, "deg": 180},
        "clouds": {"all": 0},
        "dt": int(datetime.now().timestamp()),
        "sys": {
            "type": 1,
            "id": 9165,
            "country": "IN",
            "sunrise": 1609823400,
            "sunset": 1609865400,
        },
        "timezone": 19800,
        "id": 1273294,
        "name": "Delhi",
        "cod": 200,
    },
    "Bangalore": {
        "coord": {"lon": 77.6033, "lat": 12.9762},
        "weather": [
            {"id": 500, "main": "Rain", "description": "light rain", "icon": "10d"}
        ],
        "base": "stations",
        "main": {
            "temp": 22.0,
            "feels_like": 22.5,
            "temp_min": 20.0,
            "temp_max": 24.0,
            "pressure": 1010,
            "humidity": 85,
        },
        "visibility": 8000,
        "wind": {"speed": 4.0, "deg": 90},
        "clouds": {"all": 75},
        "dt": int(datetime.now().timestamp()),
        "sys": {
            "type": 1,
            "id": 9206,
            "country": "IN",
            "sunrise": 1609823400,
            "sunset": 1609865400,
        },
        "timezone": 19800,
        "id": 1277333,
        "name": "Bangalore",
        "cod": 200,
    },
}


def generate_forecast_data(city_name: str, coord: dict) -> dict:
    """Generate realistic 5-day forecast data."""
    base_temp = MOCK_WEATHER_DATA.get(city_name, {}).get("main", {}).get("temp", 25.0)

    forecast_list = []
    now = datetime.now()

    # Generate forecasts for next 5 days, every 3 hours (40 entries)
    for i in range(40):
        forecast_time = now + timedelta(hours=i * 3)
        temp_variation = (i % 8 - 4) * 2  # Temperature variation throughout day
        temp = base_temp + temp_variation

        forecast_list.append(
            {
                "dt": int(forecast_time.timestamp()),
                "main": {
                    "temp": round(temp, 2),
                    "feels_like": round(temp + 1.5, 2),
                    "temp_min": round(temp - 2, 2),
                    "temp_max": round(temp + 2, 2),
                    "pressure": 1013,
                    "humidity": 70 + (i % 20),
                },
                "weather": [
                    {
                        "id": 800 + (i % 4),
                        "main": "Clear" if i % 3 == 0 else "Clouds",
                        "description": "clear sky" if i % 3 == 0 else "few clouds",
                        "icon": "01d" if i % 3 == 0 else "02d",
                    }
                ],
                "clouds": {"all": i % 50},
                "wind": {"speed": 3.0 + (i % 5), "deg": 180 + (i % 180)},
                "visibility": 10000,
                "pop": 0.1 * (i % 10),
                "sys": {"pod": "d" if 6 <= forecast_time.hour < 18 else "n"},
                "dt_txt": forecast_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return {
        "cod": "200",
        "message": 0,
        "cnt": 40,
        "list": forecast_list,
        "city": {
            "id": int(coord["lat"] * 10000 + coord["lon"] * 1000),
            "name": city_name,
            "coord": coord,
            "country": "IN",
            "population": 1000000,
            "timezone": 19800,
            "sunrise": int((now.replace(hour=6, minute=0)).timestamp()),
            "sunset": int((now.replace(hour=18, minute=30)).timestamp()),
        },
    }


@app.get("/data/2.5/weather")
async def get_current_weather(
    q: Optional[str] = Query(
        None, description="City name with country code (e.g., Mumbai,IN)"
    ),
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    appid: str = Query(..., description="API key"),
    units: str = Query("metric", description="Units of measurement"),
):
    """Mock current weather endpoint."""
    # Validate API key (accept any non-empty key in mock)
    if not appid or appid == "invalid_key":
        raise HTTPException(
            status_code=401,
            detail={
                "cod": 401,
                "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.",
            },
        )

    # Handle city query
    if q:
        city_name = q.split(",")[0].strip()  # Extract city name
        if city_name in MOCK_WEATHER_DATA:
            return JSONResponse(content=MOCK_WEATHER_DATA[city_name])
        else:
            # City not found
            raise HTTPException(
                status_code=404,
                detail={"cod": "404", "message": f"city not found: {city_name}"},
            )

    # Handle coordinates query
    if lat is not None and lon is not None:
        # Find closest city (simplified - just return Mumbai for any coords)
        return JSONResponse(content=MOCK_WEATHER_DATA["Mumbai"])

    raise HTTPException(
        status_code=400,
        detail={"cod": "400", "message": "Nothing to geocode"},
    )


@app.get("/data/2.5/forecast")
async def get_forecast(
    q: Optional[str] = Query(
        None, description="City name with country code (e.g., Mumbai,IN)"
    ),
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    appid: str = Query(..., description="API key"),
    units: str = Query("metric", description="Units of measurement"),
):
    """Mock 5-day forecast endpoint."""
    # Validate API key
    if not appid or appid == "invalid_key":
        raise HTTPException(
            status_code=401,
            detail={
                "cod": 401,
                "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.",
            },
        )

    # Handle city query
    if q:
        city_name = q.split(",")[0].strip()
        if city_name in MOCK_WEATHER_DATA:
            coord = MOCK_WEATHER_DATA[city_name]["coord"]
            forecast_data = generate_forecast_data(city_name, coord)
            return JSONResponse(content=forecast_data)
        else:
            raise HTTPException(
                status_code=404,
                detail={"cod": "404", "message": f"city not found: {city_name}"},
            )

    # Handle coordinates query
    if lat is not None and lon is not None:
        coord = {"lat": lat, "lon": lon}
        # For coords, return forecast for nearest city (simplified - use Mumbai)
        forecast_data = generate_forecast_data("Mumbai", coord)
        return JSONResponse(content=forecast_data)

    raise HTTPException(
        status_code=400,
        detail={"cod": "400", "message": "Nothing to geocode"},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Mock OpenWeather API is running"}


def run_mock_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the mock server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="error")


if __name__ == "__main__":
    run_mock_server()
