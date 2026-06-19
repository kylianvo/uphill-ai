import math
from typing import Dict, Any, List
import gpxpy

class GpxParser:
    @staticmethod
    def parse(file_bytes: bytes, checkpoint_interval_meters: float = 5000.0) -> Dict[str, Any]:
        """
        Parses GPX file bytes and extracts summary statistics, downsampled route 
        points with slope calculations, and structured checkpoint intervals.
        """
        try:
            gpx_str = file_bytes.decode("utf-8", errors="ignore")
            gpx = gpxpy.parse(gpx_str)
        except Exception as e:
            raise ValueError(f"Failed to parse GPX XML: {str(e)}")

        points_data: List[Dict[str, Any]] = []
        cumulative_distance = 0.0
        total_gain = 0.0
        total_loss = 0.0
        
        elevations = []
        
        # We parse all track points sequentially to compute cumulative statistics
        prev_point = None
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    distance_delta = 0.0
                    elevation_delta = 0.0
                    grade = 0.0
                    
                    if prev_point is not None:
                        # Calculate horizontal distance between successive points in meters
                        distance_delta = point.distance_3d(prev_point)
                        if distance_delta is None:
                            distance_delta = point.distance_2d(prev_point) or 0.0
                        
                        cumulative_distance += distance_delta
                        
                        # Elevation differences
                        if point.elevation is not None and prev_point.elevation is not None:
                            elevation_delta = point.elevation - prev_point.elevation
                            if elevation_delta > 0:
                                total_gain += elevation_delta
                            else:
                                total_loss += abs(elevation_delta)
                                
                            # Slope/Grade as percentage (rise / run * 100)
                            if distance_delta > 0.1:
                                grade = (elevation_delta / distance_delta) * 100.0
                    
                    if point.elevation is not None:
                        elevations.append(point.elevation)

                    points_data.append({
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "elevation_meters": point.elevation,
                        "cumulative_distance_meters": cumulative_distance,
                        "grade_percentage": grade
                    })
                    prev_point = point

        # Extract min/max elevations
        min_elev = min(elevations) if elevations else 0.0
        max_elev = max(elevations) if elevations else 0.0

        summary = {
            "total_distance_meters": cumulative_distance,
            "total_elevation_gain_meters": total_gain,
            "total_elevation_loss_meters": total_loss,
            "max_elevation_meters": max_elev,
            "min_elevation_meters": min_elev,
        }

        # Generate Checkpoints (every X meters)
        checkpoints: List[Dict[str, Any]] = []
        next_checkpoint_distance = checkpoint_interval_meters
        
        current_gain = 0.0
        current_loss = 0.0
        prev_checkpoint_pt = None

        for pt in points_data:
            # We track segment-specific elevation gains
            if prev_checkpoint_pt is not None:
                elev_diff = (pt["elevation_meters"] or 0.0) - (prev_checkpoint_pt["elevation_meters"] or 0.0)
                if elev_diff > 0:
                    current_gain += elev_diff
                else:
                    current_loss += abs(elev_diff)
            
            if pt["cumulative_distance_meters"] >= next_checkpoint_distance:
                # Add checkpoint
                cp_num = int(next_checkpoint_distance / checkpoint_interval_meters)
                checkpoints.append({
                    "name": f"KM {next_checkpoint_distance / 1000.0:.1f}",
                    "distance_meters": pt["cumulative_distance_meters"],
                    "elevation_meters": pt["elevation_meters"],
                    "accumulated_gain_meters": total_gain, # Global
                    "accumulated_loss_meters": total_loss, # Global
                    "segment_gain_meters": current_gain,
                    "segment_loss_meters": current_loss,
                    "latitude": pt["latitude"],
                    "longitude": pt["longitude"]
                })
                # Reset segment stats
                current_gain = 0.0
                current_loss = 0.0
                next_checkpoint_distance += checkpoint_interval_meters
                
            prev_checkpoint_pt = pt

        # Append final checkpoint if not exactly matched
        if points_data and (not checkpoints or checkpoints[-1]["distance_meters"] < cumulative_distance):
            checkpoints.append({
                "name": "Finish",
                "distance_meters": cumulative_distance,
                "elevation_meters": points_data[-1]["elevation_meters"],
                "accumulated_gain_meters": total_gain,
                "accumulated_loss_meters": total_loss,
                "segment_gain_meters": current_gain,
                "segment_loss_meters": current_loss,
                "latitude": points_data[-1]["latitude"],
                "longitude": points_data[-1]["longitude"]
            })

        # Downsample coordinates list for UI visualization (~600 points max)
        downsampled_points = points_data
        max_points = 600
        if len(points_data) > max_points:
            step = math.ceil(len(points_data) / max_points)
            downsampled_points = points_data[::step]

        return {
            "summary": summary,
            "points": downsampled_points,
            "checkpoints": checkpoints,
            "total_raw_points": len(points_data)
        }
