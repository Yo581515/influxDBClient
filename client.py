from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List


from datetime import datetime
from typing import Optional


from datetime import datetime


class Observation:
    def __init__(
        self,
        time: datetime,

        # node / source metadata (tags)
        node_source: str,
        node_source_id: str,
        
        # sensor / source metadata (tags)
        sensor_source: str,    
        sensor_source_id: str,

        # location (fields)
        latitude: float,
        longitude: float,

        # measurements (fields)
        temperature: float,
        humidity: float,
        salinity: float,

        # units (fields)
        temperature_unit: str,
        humidity_unit: str,
        salinity_unit: str,

        # quality flags (fields)
        quality_codes: List[int]
        
    ):
        self.time = time

        self.node_source = node_source
        self.node_source_id = node_source_id
        
        self.sensor_source = sensor_source
        self.sensor_source_id = sensor_source_id

        self.latitude = latitude
        self.longitude = longitude

        self.temperature = temperature
        self.humidity = humidity
        self.salinity = salinity

        self.temperature_unit = temperature_unit
        self.humidity_unit = humidity_unit
        self.salinity_unit = salinity_unit
        
        self.quality_codes = quality_codes
        
    def __str__(self):
        
        return (
            f"(Observation(time={self.time},\n"
            f"  node_source={self.node_source},\n"
            f"  node_source_id={self.node_source_id},\n"
            f"  sensor_source={self.sensor_source},\n"
            f"  sensor_source_id={self.sensor_source_id},\n"
            f"  latitude={self.latitude}, longitude={self.longitude},\n"
            f"  temperature={self.temperature} {self.temperature_unit},\n"
            f"  humidity={self.humidity} {self.humidity_unit},\n"
            f"  salinity={self.salinity} {self.salinity_unit},\n"
            f"  quality_codes={self.quality_codes}))"
            )
        
    

        
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = "example-org"
url = "http://localhost:8086"
user = "admin"
password = "admin123"



write_client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org,
    username=user,
    password=password
)


def write_observations(observations: List[Observation], bucket: str):
    points = []

    for obs in observations:
        point = (
            Point("observations")
            # tags
            .tag("node_source", obs.node_source)
            .tag("node_source_id", obs.node_source_id)
            .tag("sensor_source", obs.sensor_source)
            .tag("sensor_source_id", obs.sensor_source_id)
            # fields
            .field("temperature", float(obs.temperature))
            .field("humidity", float(obs.humidity))
            .field("salinity", float(obs.salinity))
            .field("temperature_unit", obs.temperature_unit)
            .field("humidity_unit", obs.humidity_unit)
            .field("salinity_unit", obs.salinity_unit)
            .field("latitude", float(obs.latitude))
            .field("longitude", float(obs.longitude))
            .field(
                "quality_codes",
                "[" + ",".join(str(q) for q in obs.quality_codes) + "]"
            )
            .time(obs.time, WritePrecision.NS)
        )
        points.append(point)
        
    
    try:
        with write_client.write_api(write_options=SYNCHRONOUS) as write_api:
            write_api.write(bucket=bucket, record=points)
    except Exception as e:
        print(f"Error writing observations: {e}")
        raise e

        
            

if __name__ == "__main__":
    import time
    from datetime import datetime, timezone
    from pprint import pprint
    import random
    
    
    def utc_now(delta):
        return datetime.now(timezone.utc) - timedelta(hours=delta)
    
    observations = []
    # insert 1000 different observations
    i = 1
    range_end = 100
    for i in range(range_end):
        
        obs = Observation(
            time=utc_now(range_end - i   ),
            node_source="test_node",
            node_source_id="node_123",
            latitude=40.7128 + (i * 0.001),
            longitude=-74.0060 + (i * 0.001),
            sensor_source="test_sensor",
            sensor_source_id="sensor_456",
            temperature=25.5 + (i % 10) - 5,
            humidity=60.0 + (i % 20) - 10,
            salinity=35.0 + (i % 5) - 2.5,
            temperature_unit="C",
            humidity_unit="%",
            salinity_unit="ppt",
            quality_codes= random.sample(range(6), random.randint(1, 6))
        )
        observations.append(obs)
        print(f"Created observation: {i}")
        i += 1
        time.sleep(0.01)  # slight delay to ensure different timestamps
    
    tables = None
    try:
        write_observations(observations, bucket="example-bucket")
        
        query_api = write_client.query_api()

        query = """
        
        from(bucket: "example-bucket")
        |> range(start: -90d)
        |> filter(fn: (r) => r._measurement == "observations")
        |> pivot(
            rowKey: ["_time", "node_source", "node_source_id", "sensor_source_id"],
            columnKey: ["_field"],
            valueColumn: "_value"
            )
        |> limit(n: 100)    

        """
        tables = query_api.query(query, org=org)    
    except Exception as e:
        print(f"Error writing observation: {e}")
    finally:
        write_client.close()
        
        
        
    print()
    print()
    print()
    print()
    print("Queried observations:")
    
    # for ti, table in enumerate(tables):
    #     field = table.records[0].values.get("_field") if table.records else None
    #     print("table_index:", ti, "field:", field, "records:", len(table.records))
    
    observations = []
    for table in tables:
        for record in table.records:
            # pprint(record.values)
            print()
            obs = Observation(
                time=record.values.get("_time"),
                node_source=record.values.get("node_source"),
                node_source_id=record.values.get("node_source_id"),
                sensor_source=record.values.get("sensor_source"),
                sensor_source_id=record.values.get("sensor_source_id"),
                latitude=float(record.values.get("latitude", 0)),
                longitude=float(record.values.get("longitude", 0)),
                temperature=float(record.values.get("temperature", 0)),
                humidity=float(record.values.get("humidity", 0)),
                salinity=float(record.values.get("salinity", 0)),
                temperature_unit=record.values.get("temperature_unit", ""),
                humidity_unit=record.values.get("humidity_unit", ""),
                salinity_unit=record.values.get("salinity_unit", ""),
                quality_codes=[int(q) for q in record.values.get("quality_codes", "[]").strip("[]").split(",") if q]
            )
            observations.append(obs)
    
    print(f"Total observations retrieved: {len(observations)}")
    for obs in observations:
        print(obs)
        print()
