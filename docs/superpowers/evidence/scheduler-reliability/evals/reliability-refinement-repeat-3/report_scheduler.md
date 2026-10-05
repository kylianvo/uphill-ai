# Golden report — scheduler


## scheduler_sequence_healthy_completed

- Gemini+KB latency: **19.1s** (no baseline captured)
- Tier attribution: **gemini**
- New: `{"workout_count": 14, "types": {"Easy": 7, "Tempo": 2, "Rest": 2, "Long Run": 2, "Recovery": 1}, "me_sessions": 0, "me_looks_like_circuit": null}`
- Tier: **sub_elite** (expected sub_elite)
- Week-2 volume: **139.1 km** (expected 115-150)
- Context metrics v2: `{"prompt_identity": {"name": "plan_generation", "version": "6", "source": "langfuse", "sha256": "7a19da8c7e374c0247484ad22bc29703f5b88a3ed345899bec520b580ae36de7"}, "checks": {"arithmetic": true, "access": true, "intensity_accounting": true, "progression": true}, "unavailable_checks": [], "weeks": {"1": {"run_km": 137.5, "hike_km": 0.0, "aerobic_minutes": 565.0, "strength_minutes": 22.0, "passive_minutes": 0.0, "long_run_locomotion_time_share": 0.283, "long_run_distance_share": 0.281, "weekend_locomotion_time_share": 0.442}, "2": {"run_km": 139.1, "hike_km": 0.0, "aerobic_minutes": 575.0, "strength_minutes": 23.0, "passive_minutes": 0.0, "long_run_locomotion_time_share": 0.287, "long_run_distance_share": 0.286, "weekend_locomotion_time_share": 0.452}}, "block_engines": ["gemini", "gemini"], "internal_disclosure": false}`

<details><summary>Gemini+KB output</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Easy Aerobic Run",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 80.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 80.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 19.5,
      "hike_km": 0.0,
      "aerobic_minutes": 80.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 80.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 80.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        }
      ],
      "description": "Run: 80 minutes in Zone 2, pace 4:06/km."
    },
    "distance_km": 19.5,
    "description": "Run: 80 minutes in Zone 2, pace 4:06/km.",
    "target_pace": "4:06 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 1,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Sub-Threshold Tempo Intervals",
    "type": "Tempo",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.15,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.35
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.35
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.35
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.35
      },
      {
        "kind": "run",
        "duration_minutes": 16.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 80.0,
    "target_zone": "Zone 3",
    "prescription": {
      "run_km": 21.1,
      "hike_km": 0.0,
      "aerobic_minutes": 80.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 80.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.15,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.35
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.35
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.35
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.35
        },
        {
          "kind": "run",
          "duration_minutes": 16.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 minutes in Zone 2, pace 4:09/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Run: 3 minutes in Zone 1, pace 4:36/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Run: 3 minutes in Zone 1, pace 4:36/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Run: 3 minutes in Zone 1, pace 4:36/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Cool-down: 16 minutes in Zone 1, pace 4:30/km."
    },
    "distance_km": 21.1,
    "description": "Warm-up: 15 minutes in Zone 2, pace 4:09/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Run: 3 minutes in Zone 1, pace 4:36/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Run: 3 minutes in Zone 1, pace 4:36/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Run: 3 minutes in Zone 1, pace 4:36/km. → Run: 10 minutes in Zone 3, pace 3:21/km. → Cool-down: 16 minutes in Zone 1, pace 4:30/km.",
    "target_pace": "3:21 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 1,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Aerobic Recovery Run & General Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 65.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.45
      },
      {
        "kind": "strength",
        "duration_minutes": 8.0,
        "setting": "indoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 4,
          "reps": 15,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 8.0,
        "setting": "indoor",
        "exercise": {
          "name": "Walking Lunges",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "setting": "indoor",
        "exercise": {
          "name": "Single-Leg Calf Raises",
          "sets": 3,
          "reps": 15,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 87.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 14.6,
      "hike_km": 0.0,
      "aerobic_minutes": 65.0,
      "strength_minutes": 22.0,
      "passive_minutes": 0.0,
      "duration_minutes": 87.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 65.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.45
        },
        {
          "kind": "strength",
          "duration_minutes": 8.0,
          "setting": "indoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 4,
            "reps": 15,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 8.0,
          "setting": "indoor",
          "exercise": {
            "name": "Walking Lunges",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "setting": "indoor",
          "exercise": {
            "name": "Single-Leg Calf Raises",
            "sets": 3,
            "reps": 15,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        }
      ],
      "description": "Run: 65 minutes in Zone 1, pace 4:27/km. → Strength: 8 minutes, Bodyweight Squats: 4 x 15, 60 s rest between sets. → Strength: 8 minutes, Walking Lunges: 3 x 12, 60 s rest between sets. → Strength: 6 minutes, Single-Leg Calf Raises: 3 x 15, 45 s rest between sets."
    },
    "distance_km": 14.6,
    "description": "Run: 65 minutes in Zone 1, pace 4:27/km. → Strength: 8 minutes, Bodyweight Squats: 4 x 15, 60 s rest between sets. → Strength: 8 minutes, Walking Lunges: 3 x 12, 60 s rest between sets. → Strength: 6 minutes, Single-Leg Calf Raises: 3 x 15, 45 s rest between sets.",
    "target_pace": "4:27 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 1,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Aerobic Maintenance Run",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 90.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 22.0,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 90.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        }
      ],
      "description": "Run: 90 minutes in Zone 2, pace 4:06/km."
    },
    "distance_km": 22.0,
    "description": "Run: 90 minutes in Zone 2, pace 4:06/km.",
    "target_pace": "4:06 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 1,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Rest Day",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Sessions < 75 mins: Plain water and optional electrolytes (200-400mg sodium); no exogenous carbs needed.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "setting": "indoor"
        }
      ],
      "description": "Rest."
    },
    "distance_km": 0.0,
    "description": "Rest.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Aerobic Steady Run with Flat Strides",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 70.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.15
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 2.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 2.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 2.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 21.7,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 70.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.15
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 2.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 2.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 2.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5,
          "role": "cooldown"
        }
      ],
      "description": "Run: 70 minutes in Zone 2, pace 4:09/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 2 minutes in Zone 1, pace 4:36/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 2 minutes in Zone 1, pace 4:36/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 2 minutes in Zone 1, pace 4:36/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Cool-down: 10 minutes in Zone 1, pace 4:30/km."
    },
    "distance_km": 21.7,
    "description": "Run: 70 minutes in Zone 2, pace 4:09/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 2 minutes in Zone 1, pace 4:36/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 2 minutes in Zone 1, pace 4:36/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 2 minutes in Zone 1, pace 4:36/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Cool-down: 10 minutes in Zone 1, pace 4:30/km.",
    "target_pace": "4:09 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Aerobic Long Run",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 160.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.15
      }
    ],
    "fueling_tip": "Sessions > 150 mins (Long Runs & Ultra simulation): 60-90g carbohydrates per hour + 500-800mg sodium/hr with 500-750ml fluid/hr. Practice with race-day fuels (energy gels, chews, drink mix).",
    "duration_minutes": 160.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 38.6,
      "hike_km": 0.0,
      "aerobic_minutes": 160.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 160.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 160.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.15
        }
      ],
      "description": "Run: 160 minutes in Zone 2, pace 4:09/km."
    },
    "distance_km": 38.6,
    "description": "Run: 160 minutes in Zone 2, pace 4:09/km.",
    "target_pace": "4:09 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null,
    "is_completed": 1,
    "is_missed": 0
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Easy Aerobic Run",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 80.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 80.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 19.5,
      "hike_km": 0.0,
      "aerobic_minutes": 80.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 80.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 80.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        }
      ],
      "description": "Run: 80 minutes in Zone 2, pace 4:06/km."
    },
    "distance_km": 19.5,
    "description": "Run: 80 minutes in Zone 2, pace 4:06/km.",
    "target_pace": "4:06 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Sub-Threshold Tempo Intervals",
    "type": "Tempo",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.4
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.8
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.4
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.8
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.4
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.8
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.4
      },
      {
        "kind": "run",
        "duration_minutes": 16.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 80.0,
    "target_zone": "Zone 3",
    "prescription": {
      "run_km": 20.5,
      "hike_km": 0.0,
      "aerobic_minutes": 80.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 80.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.4
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.8
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.4
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.8
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.4
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.8
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.4
        },
        {
          "kind": "run",
          "duration_minutes": 16.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 minutes in Zone 1, pace 4:30/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Run: 3 minutes in Zone 1, pace 4:48/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Run: 3 minutes in Zone 1, pace 4:48/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Run: 3 minutes in Zone 1, pace 4:48/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Cool-down: 16 minutes in Zone 1, pace 4:30/km."
    },
    "distance_km": 20.5,
    "description": "Warm-up: 15 minutes in Zone 1, pace 4:30/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Run: 3 minutes in Zone 1, pace 4:48/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Run: 3 minutes in Zone 1, pace 4:48/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Run: 3 minutes in Zone 1, pace 4:48/km. → Run: 10 minutes in Zone 3, pace 3:24/km. → Cool-down: 16 minutes in Zone 1, pace 4:30/km.",
    "target_pace": "3:24 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Aerobic Recovery Run & General Strength",
    "type": "Recovery",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 65.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "setting": "indoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "setting": "indoor",
        "exercise": {
          "name": "Walking Lunges",
          "sets": 3,
          "reps": 10,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "setting": "indoor",
        "exercise": {
          "name": "Single-Leg Calf Raises",
          "sets": 3,
          "reps": 15,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 5.0,
        "setting": "indoor",
        "exercise": {
          "name": "Forearm Plank",
          "sets": 3,
          "reps": 1,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 88.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 14.1,
      "hike_km": 0.0,
      "aerobic_minutes": 65.0,
      "strength_minutes": 23.0,
      "passive_minutes": 0.0,
      "duration_minutes": 88.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 65.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "setting": "indoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "setting": "indoor",
          "exercise": {
            "name": "Walking Lunges",
            "sets": 3,
            "reps": 10,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "setting": "indoor",
          "exercise": {
            "name": "Single-Leg Calf Raises",
            "sets": 3,
            "reps": 15,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 5.0,
          "setting": "indoor",
          "exercise": {
            "name": "Forearm Plank",
            "sets": 3,
            "reps": 1,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        }
      ],
      "description": "Run: 65 minutes in Zone 1, pace 4:36/km. → Strength: 6 minutes, Bodyweight Squats: 3 x 12, 60 s rest between sets. → Strength: 6 minutes, Walking Lunges: 3 x 10, 60 s rest between sets. → Strength: 6 minutes, Single-Leg Calf Raises: 3 x 15, 45 s rest between sets. → Strength: 5 minutes, Forearm Plank: 3 x 1, 45 s rest between sets."
    },
    "distance_km": 14.1,
    "description": "Run: 65 minutes in Zone 1, pace 4:36/km. → Strength: 6 minutes, Bodyweight Squats: 3 x 12, 60 s rest between sets. → Strength: 6 minutes, Walking Lunges: 3 x 10, 60 s rest between sets. → Strength: 6 minutes, Single-Leg Calf Raises: 3 x 15, 45 s rest between sets. → Strength: 5 minutes, Forearm Plank: 3 x 1, 45 s rest between sets.",
    "target_pace": "4:36 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Aerobic Base Run",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 90.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 22.0,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 90.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        }
      ],
      "description": "Run: 90 minutes in Zone 2, pace 4:06/km."
    },
    "distance_km": 22.0,
    "description": "Run: 90 minutes in Zone 2, pace 4:06/km.",
    "target_pace": "4:06 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Full Rest & Tissue Restoration",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Sessions < 75 mins: Plain water and optional electrolytes (200-400mg sodium); no exogenous carbs needed.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "setting": "indoor"
        }
      ],
      "description": "Rest."
    },
    "distance_km": 0.0,
    "description": "Rest.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Aerobic Steady Run with Flat Strides",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 85.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.9
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.9
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 3.1
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.6,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Sessions 75-150 mins: 30-60g carbohydrates per hour + 300-500mg sodium/hr with 400-600ml water/hr.",
    "duration_minutes": 95.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 23.2,
      "hike_km": 0.0,
      "aerobic_minutes": 95.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 95.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 85.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.9
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.9
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 3.1
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.6,
          "role": "cooldown"
        }
      ],
      "description": "Run: 85 minutes in Zone 2, pace 4:06/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 1 minutes in Zone 1, pace 4:54/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 1 minutes in Zone 1, pace 4:54/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Cool-down: 5 minutes in Zone 1, pace 4:36/km."
    },
    "distance_km": 23.2,
    "description": "Run: 85 minutes in Zone 2, pace 4:06/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 1 minutes in Zone 1, pace 4:54/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Run: 1 minutes in Zone 1, pace 4:54/km. → Run: 1 minutes in Zone 4, pace 3:06/km. → Cool-down: 5 minutes in Zone 1, pace 4:36/km.",
    "target_pace": "4:06 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Aerobic Long Run",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 165.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.15
      }
    ],
    "fueling_tip": "Sessions > 150 mins (Long Runs & Ultra simulation): 60-90g carbohydrates per hour + 500-800mg sodium/hr with 500-750ml fluid/hr. Practice with race-day fuels (energy gels, chews, drink mix).",
    "duration_minutes": 165.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 39.8,
      "hike_km": 0.0,
      "aerobic_minutes": 165.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 165.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 165.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.15
        }
      ],
      "description": "Run: 165 minutes in Zone 2, pace 4:09/km."
    },
    "distance_km": 39.8,
    "description": "Run: 165 minutes in Zone 2, pace 4:09/km.",
    "target_pace": "4:09 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>

## scheduler_fixture_vietnam_urban_recreational_no_gym

- Gemini+KB latency: **22.6s** (baseline: 22.1s)
- Tier attribution: **gemini**
- New: `{"workout_count": 14, "types": {"Rest": 4, "Easy": 8, "Long Run": 2}, "me_sessions": 0, "me_looks_like_circuit": null}`
- Ref: `{"workout_count": 9, "types": {"Easy": 4, "Long Run": 2, "Rest": 2, "Muscular Endurance": 1}, "me_sessions": 1, "me_looks_like_circuit": false}`
- Tier: **recreational** (expected recreational)
- Week-2 volume: **66.5 km** (expected 55-73)
- Context metrics v2: `{"prompt_identity": {"name": "plan_generation", "version": "6", "source": "langfuse", "sha256": "7a19da8c7e374c0247484ad22bc29703f5b88a3ed345899bec520b580ae36de7"}, "checks": {"arithmetic": true, "access": true, "intensity_accounting": true, "progression": true}, "unavailable_checks": [], "weeks": {"1": {"run_km": 57.4, "hike_km": 3.3, "aerobic_minutes": 397.1, "strength_minutes": 17.0, "passive_minutes": 16.0, "long_run_locomotion_time_share": 0.378, "long_run_distance_share": 0.329, "weekend_locomotion_time_share": 0.556}, "2": {"run_km": 62.2, "hike_km": 4.3, "aerobic_minutes": 437.8, "strength_minutes": 17.0, "passive_minutes": 22.5, "long_run_locomotion_time_share": 0.388, "long_run_distance_share": 0.338, "weekend_locomotion_time_share": 0.562}}, "block_engines": null, "internal_disclosure": false}`

<details><summary>Gemini+KB output</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Uống nước đều đặn trong ngày. Bổ sung dinh dưỡng cân bằng với đủ lượng đạm và tinh bột để tái tạo cơ bắp sau tuần tập trước.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Easy Run đường bằng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.35,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Buổi chạy dưới 75 phút chỉ cần nước lọc. Bạn có thể thêm 200-400mg Sodium nếu thời tiết Hà Nội nóng ẩm.",
    "duration_minutes": 60.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 10.2,
      "hike_km": 0.0,
      "aerobic_minutes": 60.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 60.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.35,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 45 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km."
    },
    "distance_km": 10.2,
    "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 45 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Easy Run và Strength bổ trợ thân dưới",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 35.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.35,
        "role": "cooldown"
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Walking Lunges",
          "sets": 3,
          "reps": 10,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 5.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Single-leg Calf Raises",
          "sets": 3,
          "reps": 15,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      }
    ],
    "fueling_tip": "Nước lọc bổ sung từng ngụm nhỏ trong khi chạy và bài tập Strength. Không cần nạp thêm Carbs ngoài bữa ăn thông thường.",
    "duration_minutes": 67.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 8.5,
      "hike_km": 0.0,
      "aerobic_minutes": 50.0,
      "strength_minutes": 17.0,
      "passive_minutes": 0.0,
      "duration_minutes": 67.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 35.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.35,
          "role": "cooldown"
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Walking Lunges",
            "sets": 3,
            "reps": 10,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 5.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Single-leg Calf Raises",
            "sets": 3,
            "reps": 15,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        }
      ],
      "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 35 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km. → Strength: 6 phút, Bodyweight Squats: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Walking Lunges: 3 x 10, 60 s nghỉ giữa các set. → Strength: 5 phút, Single-leg Calf Raises: 3 x 15, 45 s nghỉ giữa các set."
    },
    "distance_km": 8.5,
    "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 35 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km. → Strength: 6 phút, Bodyweight Squats: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Walking Lunges: 3 x 10, 60 s nghỉ giữa các set. → Strength: 5 phút, Single-leg Calf Raises: 3 x 15, 45 s nghỉ giữa các set.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Aerobic Run kết hợp Strides phẳng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 50.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.35,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Thời lượng dưới 75 phút chỉ cần nước lọc hoặc điện giải nhẹ. Giữ cơ thể đủ nước trước buổi chạy chiều.",
    "duration_minutes": 72.3,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 11.4,
      "hike_km": 0.0,
      "aerobic_minutes": 66.3,
      "strength_minutes": 0.0,
      "passive_minutes": 6.0,
      "duration_minutes": 72.3,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 50.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.35,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 50 phút ở Zone 2, pace 5:45/km. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Cool-down: 5 phút ở Zone 1, pace 6:21/km."
    },
    "distance_km": 11.4,
    "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 50 phút ở Zone 2, pace 5:45/km. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Cool-down: 5 phút ở Zone 1, pace 6:21/km.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Nghỉ ngơi hoàn toàn",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Nghỉ ngơi và bổ sung đầy đủ carbohydrate phức hợp chuẩn bị cho hai ngày tập cuối tuần trên địa hình dốc.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Chạy Trail dốc và Hill Repeats ngắn",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.0,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.6
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.1,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Thời lượng khoảng 80 phút: nạp 30g Carbs kết hợp 300-400mg Sodium và uống 500ml nước mỗi giờ.",
    "duration_minutes": 80.8,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 10.6,
      "hike_km": 0.0,
      "aerobic_minutes": 70.8,
      "strength_minutes": 0.0,
      "passive_minutes": 10.0,
      "duration_minutes": 80.8,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.0,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.6
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.1,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 7:00/km. → Run: 45 phút ở Zone 2, pace 6:36/km. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Cool-down: 10 phút ở Zone 1, pace 7:06/km."
    },
    "distance_km": 10.6,
    "description": "Warm-up: 15 phút ở Zone 1, pace 7:00/km. → Run: 45 phút ở Zone 2, pace 6:36/km. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Cool-down: 10 phút ở Zone 1, pace 7:06/km.",
    "target_pace": "6:36 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Trail tích lũy độ dốc",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.2,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 65.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.8
      },
      {
        "kind": "hike",
        "duration_minutes": 35.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 10.5
      },
      {
        "kind": "run",
        "duration_minutes": 25.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.7
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.3,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Bài chạy 150 phút: nạp 45-60g Carbs mỗi giờ qua gel hoặc viên ngậm, uống 500-600ml nước cùng 400-500mg Sodium mỗi giờ.",
    "duration_minutes": 150.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 16.7,
      "hike_km": 3.3,
      "aerobic_minutes": 150.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 150.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.2,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 65.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.8
        },
        {
          "kind": "hike",
          "duration_minutes": 35.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 10.5
        },
        {
          "kind": "run",
          "duration_minutes": 25.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.7
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.3,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 7:12/km. → Run: 65 phút ở Zone 2, pace 6:48/km. → Hike: 35 phút ở Zone 2, pace 10:30/km. → Run: 25 phút ở Zone 2, pace 6:42/km. → Cool-down: 10 phút ở Zone 1, pace 7:18/km."
    },
    "distance_km": 20.0,
    "description": "Warm-up: 15 phút ở Zone 1, pace 7:12/km. → Run: 65 phút ở Zone 2, pace 6:48/km. → Hike: 35 phút ở Zone 2, pace 10:30/km. → Run: 25 phút ở Zone 2, pace 6:42/km. → Cool-down: 10 phút ở Zone 1, pace 7:18/km.",
    "target_pace": "6:48 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Uống đủ nước, tập trung nạp đạm và rau xanh để cơ bắp hồi phục sau các bài dốc cuối tuần.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Easy Run đường bằng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 55.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.35,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Thời lượng 70 phút: uống 400ml nước trước và sau buổi chạy, không cần bổ sung Carbs trong bài.",
    "duration_minutes": 70.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 11.9,
      "hike_km": 0.0,
      "aerobic_minutes": 70.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 70.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 55.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.35,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 55 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km."
    },
    "distance_km": 11.9,
    "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 55 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Easy Run và Strength ổn định thân dưới",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 40.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.35,
        "role": "cooldown"
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Reverse Lunges",
          "sets": 3,
          "reps": 10,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 5.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Single-leg Glute Bridges",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      }
    ],
    "fueling_tip": "Bổ sung nước lọc đều đặn trong buổi tập. Uống thêm sữa hạt hoặc whey protein kèm bữa ăn nhẹ sau bài Strength.",
    "duration_minutes": 72.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 9.3,
      "hike_km": 0.0,
      "aerobic_minutes": 55.0,
      "strength_minutes": 17.0,
      "passive_minutes": 0.0,
      "duration_minutes": 72.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 40.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.35,
          "role": "cooldown"
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Reverse Lunges",
            "sets": 3,
            "reps": 10,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 5.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Single-leg Glute Bridges",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        }
      ],
      "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 40 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km. → Strength: 6 phút, Bodyweight Squats: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Reverse Lunges: 3 x 10, 60 s nghỉ giữa các set. → Strength: 5 phút, Single-leg Glute Bridges: 3 x 12, 45 s nghỉ giữa các set."
    },
    "distance_km": 9.3,
    "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 40 phút ở Zone 2, pace 5:45/km. → Cool-down: 5 phút ở Zone 1, pace 6:21/km. → Strength: 6 phút, Bodyweight Squats: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Reverse Lunges: 3 x 10, 60 s nghỉ giữa các set. → Strength: 5 phút, Single-leg Glute Bridges: 3 x 12, 45 s nghỉ giữa các set.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Aerobic Run kết hợp Strides phẳng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 50.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 0.33,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.5
      },
      {
        "kind": "recovery",
        "duration_minutes": 1.5,
        "zone": null,
        "setting": "flat_outdoor"
      },
      {
        "kind": "run",
        "duration_minutes": 5.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 6.35,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Thời lượng dưới 75 phút chỉ cần bù nước lọc. Giữ nhịp thở đều và bổ sung nước ngay sau khi kết thúc.",
    "duration_minutes": 74.1,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 11.4,
      "hike_km": 0.0,
      "aerobic_minutes": 66.6,
      "strength_minutes": 0.0,
      "passive_minutes": 7.5,
      "duration_minutes": 74.1,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 50.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 0.33,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.5
        },
        {
          "kind": "recovery",
          "duration_minutes": 1.5,
          "zone": null,
          "setting": "flat_outdoor"
        },
        {
          "kind": "run",
          "duration_minutes": 5.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 6.35,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 50 phút ở Zone 2, pace 5:45/km. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Cool-down: 5 phút ở Zone 1, pace 6:21/km."
    },
    "distance_km": 11.4,
    "description": "Warm-up: 10 phút ở Zone 1, pace 6:18/km. → Run: 50 phút ở Zone 2, pace 5:45/km. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Run: 0.33 phút ở Zone 4, pace 4:30/km. → Recovery: 1.5 phút. → Cool-down: 5 phút ở Zone 1, pace 6:21/km.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Nghỉ ngơi hoàn toàn",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Ngày nghỉ tĩnh: ăn uống cân bằng, duy trì hydrat hóa tốt chuẩn bị cho hai bài chạy dốc cuối tuần.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Chạy Trail dốc và Hill Repeats",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.0,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 50.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.6
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 4.3
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.5,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.1,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Thời lượng gần 90 phút: dùng 30-40g Carbs kèm 300-400mg Sodium và uống 500ml nước trong quá trình chạy.",
    "duration_minutes": 91.2,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 11.4,
      "hike_km": 0.0,
      "aerobic_minutes": 76.2,
      "strength_minutes": 0.0,
      "passive_minutes": 15.0,
      "duration_minutes": 91.2,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.0,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 50.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.6
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 4.3
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.5,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.1,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 7:00/km. → Run: 50 phút ở Zone 2, pace 6:36/km. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Cool-down: 10 phút ở Zone 1, pace 7:06/km."
    },
    "distance_km": 11.4,
    "description": "Warm-up: 15 phút ở Zone 1, pace 7:00/km. → Run: 50 phút ở Zone 2, pace 6:36/km. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Run: 0.2 phút ở Zone 5, pace 4:18/km. → Recovery: 2.5 phút. → Cool-down: 10 phút ở Zone 1, pace 7:06/km.",
    "target_pace": "6:36 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Trail mô phỏng leo dốc",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.2,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 70.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.8
      },
      {
        "kind": "hike",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 10.5
      },
      {
        "kind": "run",
        "duration_minutes": 30.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.7
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 7.3,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Bài chạy 170 phút: nạp 60g Carbs mỗi giờ từ gel hoặc thanh năng lượng, duy trì 500-600mg Sodium và 500-750ml nước mỗi giờ.",
    "duration_minutes": 170.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 18.2,
      "hike_km": 4.3,
      "aerobic_minutes": 170.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 170.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.2,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 70.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.8
        },
        {
          "kind": "hike",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 10.5
        },
        {
          "kind": "run",
          "duration_minutes": 30.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.7
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 7.3,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 7:12/km. → Run: 70 phút ở Zone 2, pace 6:48/km. → Hike: 45 phút ở Zone 2, pace 10:30/km. → Run: 30 phút ở Zone 2, pace 6:42/km. → Cool-down: 10 phút ở Zone 1, pace 7:18/km."
    },
    "distance_km": 22.5,
    "description": "Warm-up: 15 phút ở Zone 1, pace 7:12/km. → Run: 70 phút ở Zone 2, pace 6:48/km. → Hike: 45 phút ở Zone 2, pace 10:30/km. → Run: 30 phút ở Zone 2, pace 6:42/km. → Cool-down: 10 phút ở Zone 1, pace 7:18/km.",
    "target_pace": "6:48 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>
<details><summary>Captured baseline</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Chạy Trail Cuối Tuần Kèm Hill Sprint",
    "type": "Easy",
    "duration_minutes": 80.0,
    "target_zone": "Zone 2",
    "target_hr_range": "125-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 13.9,
    "elevation_gain_m": 420.0,
    "grade_percent": 3.1,
    "description": "Process: Warm-up 15 min chạy nhẹ Zone 1 → Chạy địa hình đồi dốc tự nhiên 45 min Zone 2 kiểm soát nhịp tim dưới AeT → 6 x 10s Hill Sprint dốc đứng 15%, phục hồi đi bộ thả lỏng hoàn toàn 3 min giữa mỗi rep → Cool-down 8 min đi bộ và thả lỏng cơ thể. Overall: Buổi chạy địa hình mở màn kế hoạch kết hợp kích hoạt thần kinh cơ trên dốc tự nhiên cuối tuần. Bài tập giúp đánh thức các sợi cơ co rút nhanh FTa mà không gây tích tụ lactate toàn thân. Reason: Tận dụng ngày thứ Bảy có địa hình đồi núi ngoài Hà Nội để rèn luyện khả năng phối hợp thần kinh và thích nghi gân khớp. Benefit: Tăng cường khả năng tuyển mộ sợi cơ vận động, cải thiện độ đàn hồi gân Achilles và sức mạnh bộc phát cho bước chạy dốc. Warning: Khi thực hiện Hill Sprint cần chạy dốc tối đa nhưng dừng ngay nếu có dấu hiệu gắt cơ hoặc bước chạy mất kiểm soát; tuyệt đối đi bộ đủ 3 phút giữa các hiệp.",
    "fueling_tip": "Buổi tập 80 phút: nạp 30-40g Carbs mỗi giờ kèm 400-500ml nước chứa 300-400mg Sodium, bắt đầu nhấp từng ngụm nhỏ từ phút 40.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Địa Hình Xây Dựng Base Aerobic",
    "type": "Long Run",
    "duration_minutes": 130.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 22.5,
    "elevation_gain_m": 850.0,
    "grade_percent": 4.0,
    "description": "Process: Warm-up 15 min đi bộ nhanh và chạy nhẹ Zone 1 → Chạy trail tích lũy độ cao 100 min Zone 2, chủ động chuyển sang power-hiking khi độ dốc trên 12% để giữ HR dưới 146 bpm → Cool-down 15 min đi bộ thả lỏng trên đường bằng. Overall: Buổi Long Run địa hình chủ lực cuối tuần nhằm xây dựng sức bền hiếu khí và rèn luyện kỹ thuật di chuyển trên dốc. Chú trọng chuyển đổi mượt mà giữa chạy bước nhỏ và power-hiking. Reason: Cung cấp khối lượng aerobic đặc hiệu cho cự ly 48K với 2100m D+ trong khung thời gian cuối tuần có núi. Benefit: Phát triển mạng lưới mao mạch, tăng sinh ty thể tại các nhóm cơ leo dốc và rèn luyện khả năng oxy hóa chất béo. Warning: Không để nhịp tim vượt qua ngưỡng AeT 146 bpm trên các đoạn dốc gắt; chủ động đi bộ sải dài chống tay lên đùi sớm để bảo toàn năng lượng.",
    "fueling_tip": "Thời lượng 130 phút: nạp 45-60g Carbs mỗi giờ qua Gel hoặc nước điện giải pha Carbs, uống đều 500-600ml nước kèm 400-500mg Sodium mỗi giờ.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Nghỉ Ngơi Phục Hồi Đầu Tuần",
    "type": "Rest",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "target_hr_range": "51-115 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "description": "Process: Nghỉ ngơi hoàn toàn không vận động thể lực → Giãn cơ nhẹ nhàng tại nhà và Foam Rolling bắp chân đùi 15 min nếu cảm thấy căng cứng. Overall: Ngày nghỉ trọn vẹn theo lịch trình nhằm tái tạo hệ cơ xương khớp sau 2 ngày chạy dốc cuối tuần. Hỗ trợ hệ thần kinh trung ương hồi phục hoàn toàn. Reason: Thứ Hai là ngày nghỉ cố định giúp cơ thể hấp thụ khối lượng vận động của tuần trước mà không bị quá tải. Benefit: Phục hồi glycogen cơ bắp, sửa chữa các vi tổn thương sợi cơ và hạ thấp nồng độ cortisol tích tụ. Warning: Tránh đi bộ đường dài hoặc đứng làm việc quá lâu trong ngày nghỉ; duy trì uống đủ nước.",
    "fueling_tip": "Ăn uống bình thường với các bữa ăn giàu đạm cân bằng và carbohydrate phức hợp, duy trì uống đủ 2-2.5 lít nước trong ngày.",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Easy Run Bằng Phẳng Nội Thành",
    "type": "Easy",
    "duration_minutes": 60.0,
    "target_zone": "Zone 2",
    "target_hr_range": "125-144 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 10.4,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Warm-up 10 min chạy rất chậm Zone 1 khởi động khớp → Chạy liên tục đường bằng 45 min Zone 2 giữ nhịp thở đều đặn 3:3 → Cool-down 5 min đi bộ và duỗi cơ tĩnh. Overall: Bài chạy nhẹ nhàng trên địa hình phẳng tại Hà Nội nhằm duy trì thể tích tim và kích thích lưu thông máu. Giữ cảm giác thoải mái và có thể trò chuyện nguyên câu suốt bài. Reason: Thiết lập khối lượng tích lũy aerobic ngày trong tuần phù hợp với điều kiện địa hình đô thị. Benefit: Tăng cường mật độ mao mạch cơ bắp, hỗ trợ đào thải các chất cặn bã chuyển hóa sau chuỗi ngày tập trước. Warning: Kiểm soát chặt chẽ nhịp tim không để vượt quá 146 bpm, không bị cuốn theo Pace người khác chạy cùng trên đường phẳng.",
    "fueling_tip": "Buổi tập 60 phút: chỉ cần dùng nước lọc nguội, có thể bổ sung 200-300mg Sodium nếu thời tiết Hà Nội oi bức; không cần nạp thêm Carbs ngoài bữa ăn chính.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Muscular Endurance Bodyweight Circuit",
    "type": "Muscular Endurance",
    "duration_minutes": 55.0,
    "target_zone": "Zone 1",
    "target_hr_range": "115-140 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "description": "Process: Warm-up 10 min khớp và kích hoạt cơ mông → 10 reps Squat Jumps thân người thẳng, chuyển động 15s → 10 reps Split Jump Squats luân phiên chân, chuyển động 15s → 10 reps/chân Box Step-Ups trên bậc thềm ngang 75% gối, chuyển động 15s → 10 reps/chân Front Lunges bước dài có kiểm soát, chuyển động 15s → Nghỉ 60s giữa vòng, thực hiện tất cả 6 rounds liên tục → Cool-down 10 min thả lỏng bắp chân và gân kheo. Overall: Bài tập sức bền cơ bắp đặc hiệu bằng trọng lượng cơ thể tại chỗ mô phỏng tải trọng leo dốc cho vùng đùi và mông. Thiết kế dạng circuit liên tục để tạo áp lực mỏi cơ ngoại biên trong khi giữ nhịp tim hiếu khí. Reason: Do kế hoạch ngắn 8 tuần và không có dốc trong tuần, bài ME này là bắt buộc để gia cố khung gầm cơ bắp chuẩn bị cho 2100m D+. Benefit: Huấn luyện sợi cơ FTa chịu đựng ion H+ và mỏi mỏi cục bộ mà không gây stress tim mạch, ngăn ngừa sụp đổ cơ đùi trước khi xuống dốc. Warning: Giữ tư thế đầu gối thẳng hàng với mũi chân khi tiếp đất; nếu nhịp tim vọt lên Zone 3 hãy kéo dài thời gian nghỉ giữa các round để bảo đảm nguyên tắc rèn luyện cơ bắp không ép tim.",
    "fueling_tip": "Thời lượng 55 phút: uống 400-500ml nước điện giải giàu khoáng chất để chống co rút cơ, không cần bổ sung Carbs bổ sung.",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Easy Run Kèm Strides Đô Thị",
    "type": "Easy",
    "duration_minutes": 55.0,
    "target_zone": "Zone 2",
    "target_hr_range": "125-145 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 9.5,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Warm-up 10 min chạy Zone 1 nhịp nhàng → Chạy ổn định 35 min Zone 2 bằng phẳng thư giãn cơ thể → 5 x 20s Strides tăng tốc mượt mà đạt 90% nỗ lực trên đường thẳng, đi bộ thả lỏng 60s giữa mỗi rep → Cool-down 5 min đi bộ chậm. Overall: Bài chạy nền tảng hiếu khí nhẹ kết hợp các đoạn mở rộng sải chân nhằm duy trì độ linh hoạt của hệ thần kinh cơ. Giúp đôi chân rũ bỏ cảm giác nặng nề sau buổi ME hôm trước. Reason: Bổ sung thể tích chạy trong tuần đồng thời duy trì guồng chân nhanh mà không gây mệt mỏi hệ tim mạch. Benefit: Cải thiện hiệu suất sải bước (running economy), rèn luyện độ đàn hồi cơ gân mà không kích hoạt hệ thống yếm khí kéo dài. Warning: Các đoạn Strides chỉ tập trung vào dáng chạy đẹp và guồng chân thư giãn, không biến thành bài chạy rút sprint hết sức.",
    "fueling_tip": "Buổi tập 55 phút: dùng nước lọc thông thường, bù điện giải nhẹ nhàng nếu đổ mồ hôi nhiều.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Nghỉ Ngơi Tích Lũy Năng Lượng",
    "type": "Rest",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "target_hr_range": "51-115 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "description": "Process: Nghỉ ngơi hoàn toàn chuẩn bị cho khối lượng dốc cuối tuần → Ngủ đủ giấc và kéo giãn nhẹ nhàng cơ hông, bắp chuối 10 min trước khi đi ngủ. Overall: Ngày nghỉ định kỳ trước chuỗi ngày leo dốc cuối tuần nhằm nạp đầy bể dự trữ năng lượng. Tạo khoảng đệm 48 tiếng phục hồi sau bài ME thứ Tư. Reason: Tuân thủ quy tắc phục hồi và tạo sự tươi mới tối đa cho cơ bắp trước khi tiếp xúc với địa hình dốc lớn. Benefit: Phục hồi hoàn toàn kho dự trữ glycogen và tái tạo mô liên kết của đôi chân. Warning: Chú ý giấc ngủ và hạn chế rượu bia hay ăn đồ khó tiêu để cơ thể có trạng thái tối ưu vào sáng thứ Bảy.",
    "fueling_tip": "Tập trung nạp đủ nước và bữa ăn đủ dưỡng chất, bổ sung carbohydrate phức hợp và rau xanh.",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Chạy Trail Đồi Núi Kèm Hill Strides",
    "type": "Easy",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "target_hr_range": "125-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 15.6,
    "elevation_gain_m": 520.0,
    "grade_percent": 3.4,
    "description": "Process: Warm-up 15 min chạy nhẹ khởi động trên đường dốc thoai thoải Zone 1 → Chạy địa hình trail 60 min Zone 2 kiểm soát chặt chẽ nhịp tim dưới ngưỡng AeT → 6 x 15s Hill Strides trên dốc 10-12% với bước sải mạnh mẽ, đi bộ xuống dốc 2 min phục hồi hoàn toàn → Cool-down 6 min thả lỏng nhẹ nhàng. Overall: Buổi tập trail thứ Bảy giúp tích lũy độ cao tự nhiên kết hợp tăng cường sức mạnh bước chạy dốc. Nhịp tim giữ chủ đạo trong vùng hiếu khí dưới AeT. Reason: Tận dụng cơ hội ra núi cuối tuần để rèn luyện độ thăng bằng mắt cá và sức bền gân khớp trên địa hình không bằng phẳng. Benefit: Gia tăng sức bền chân trụ, cải thiện khả năng thích ứng của bàn chân với đá sỏi và tăng công suất cơ bắp khi đẩy người lên dốc. Warning: Cẩn thận khi đổ dốc kỹ thuật sau các đoạn dốc; giữ trọng tâm cân bằng và không sải bước quá dài gây quá tải khớp gối.",
    "fueling_tip": "Thời lượng 90 phút: nạp 30-45g Carbs kèm 500ml nước và 350-450mg Sodium mỗi giờ qua gel hoặc nước điện giải thể thao.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Leo Dốc Mô Phỏng Giải Đấu",
    "type": "Long Run",
    "duration_minutes": 150.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 26.0,
    "elevation_gain_m": 1050.0,
    "grade_percent": 4.4,
    "description": "Process: Warm-up 15 min đi bộ nhanh kết hợp chạy nhẹ Zone 1 → Chạy và power-hiking luân phiên 120 min trên địa hình trail dốc tích lũy độ cao, giữ HR tuyệt đối dưới AnT và phần lớn dưới AeT 146 bpm → Thực hành kỹ thuật thả dốc bước ngắn thả lỏng cơ đùi trong các đoạn dốc xuống → Cool-down 15 min đi bộ và vung tay thả lỏng toàn thân. Overall: Buổi chạy dài chủ chốt của tuần 2 nhằm xây dựng sức bền cơ bắp chuyên biệt cho tỷ lệ 43.8m D+/km của giải đấu. Đảm bảo phân bổ năng lượng đồng đều và tập trung vào kỹ thuật power-hiking. Reason: Cung cấp kích thích sinh lý lớn nhất trong tuần để thích nghi với địa hình đồi núi thực tế của Vietnam Urban-to-Trail 48K. Benefit: Nâng cao thể tích nhát bóp của tim, gia tăng sức chịu đựng của cơ tứ đầu đùi (quads) với tải trọng lệch tâm khi xuống dốc và tối ưu hóa khả năng hấp thu năng lượng khi vận động kéo dài. Warning: Đừng cố chạy trên các con dốc quá 12%, hãy chuyển sang đi bộ dốc nhịp nhàng ngay để tránh tụt đường huyết và quá tải hệ tim mạch sớm.",
    "fueling_tip": "Thời lượng 150 phút: thực hành chiến thuật Race Day với 60g Carbs mỗi giờ kết hợp 500-700ml nước chứa 500-600mg Sodium mỗi giờ, duy trì nhấp ngụm nhỏ cách nhau 15-20 phút.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>

## scheduler_fixture_vietnam_urban_recreational_treadmill

- Gemini+KB latency: **11.8s** (baseline: 20.9s)
- Tier attribution: **gemini**
- New: `{"workout_count": 14, "types": {"Rest": 4, "Easy": 8, "Long Run": 2}, "me_sessions": 0, "me_looks_like_circuit": null}`
- Ref: `{"workout_count": 9, "types": {"Easy": 3, "Long Run": 2, "Rest": 2, "Muscular Endurance": 1, "Strength": 1}, "me_sessions": 1, "me_looks_like_circuit": false}`
- Tier: **recreational** (expected recreational)
- Week-2 volume: **64.4 km** (expected 55-73)
- Context metrics v2: `{"prompt_identity": {"name": "plan_generation", "version": "6", "source": "langfuse", "sha256": "7a19da8c7e374c0247484ad22bc29703f5b88a3ed345899bec520b580ae36de7"}, "checks": {"arithmetic": true, "access": true, "intensity_accounting": true, "progression": true}, "unavailable_checks": [], "weeks": {"1": {"run_km": 54.3, "hike_km": 3.7, "aerobic_minutes": 385.0, "strength_minutes": 22.0, "passive_minutes": 0.0, "long_run_locomotion_time_share": 0.338, "long_run_distance_share": 0.321, "weekend_locomotion_time_share": 0.558}, "2": {"run_km": 59.7, "hike_km": 4.7, "aerobic_minutes": 425.0, "strength_minutes": 22.0, "passive_minutes": 0.0, "long_run_locomotion_time_share": 0.329, "long_run_distance_share": 0.315, "weekend_locomotion_time_share": 0.541}}, "block_engines": null, "internal_disclosure": false}`

<details><summary>Gemini+KB output</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Uống đủ nước trong ngày và duy trì các bữa ăn cân bằng giàu dinh dưỡng để chuẩn bị năng lượng cho tuần tập luyện.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Treadmill Easy Run và Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 50.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "pace_min_per_km": 5.75,
        "incline_pct": 1.0
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Barbell Back Squats",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "weights"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Dumbbell Step-Ups",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "weights",
            "box"
          ]
        }
      }
    ],
    "fueling_tip": "Buổi tập dưới 75 phút, chỉ cần nước lọc kèm 200-400mg sodium; không cần bổ sung carb ngoại sinh.",
    "duration_minutes": 62.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 8.7,
      "hike_km": 0.0,
      "aerobic_minutes": 50.0,
      "strength_minutes": 12.0,
      "passive_minutes": 0.0,
      "duration_minutes": 62.0,
      "estimated_indoor_ascent_m": 87.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 50.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "pace_min_per_km": 5.75,
          "incline_pct": 1.0
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Barbell Back Squats",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "weights"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Dumbbell Step-Ups",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "weights",
              "box"
            ]
          }
        }
      ],
      "description": "Run: 50 phút ở Zone 2, pace 5:45/km, Treadmill 1%. → Strength: 6 phút, Barbell Back Squats: 3 x 6, 120 s nghỉ giữa các set. → Strength: 6 phút, Dumbbell Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → D+ trong nhà (ước tính): 87 m."
    },
    "distance_km": 8.7,
    "description": "Run: 50 phút ở Zone 2, pace 5:45/km, Treadmill 1%. → Strength: 6 phút, Barbell Back Squats: 3 x 6, 120 s nghỉ giữa các set. → Strength: 6 phút, Dumbbell Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → D+ trong nhà (ước tính): 87 m.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "1",
    "treadmill_speed": "10.4",
    "elevation_gain_m": 87.0,
    "grade_percent": 1.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Easy Run ngoài trời",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 60.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.8
      }
    ],
    "fueling_tip": "Buổi tập dưới 75 phút, bổ sung 400-500ml nước lọc và điện giải nhẹ nếu thời tiết nóng ẩm.",
    "duration_minutes": 60.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 10.3,
      "hike_km": 0.0,
      "aerobic_minutes": 60.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 60.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 60.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.8
        }
      ],
      "description": "Run: 60 phút ở Zone 2, pace 5:48/km."
    },
    "distance_km": 10.3,
    "description": "Run: 60 phút ở Zone 2, pace 5:48/km.",
    "target_pace": "5:48 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Treadmill Incline và Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "role": "warmup",
        "pace_min_per_km": 5.8,
        "incline_pct": 1.0
      },
      {
        "kind": "hike",
        "duration_minutes": 35.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "pace_min_per_km": 9.5,
        "incline_pct": 12.0
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "treadmill",
        "role": "cooldown",
        "pace_min_per_km": 6.3,
        "incline_pct": 1.0
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Romanian Deadlift",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "weights"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 4.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Single-Leg Calf Raises",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      }
    ],
    "fueling_tip": "Buổi tập kéo dài khoảng 71 phút, dùng nước kèm 200-400mg sodium để bù mồ hôi trong phòng tập.",
    "duration_minutes": 70.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 4.2,
      "hike_km": 3.7,
      "aerobic_minutes": 60.0,
      "strength_minutes": 10.0,
      "passive_minutes": 0.0,
      "duration_minutes": 70.0,
      "estimated_indoor_ascent_m": 481.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "role": "warmup",
          "pace_min_per_km": 5.8,
          "incline_pct": 1.0
        },
        {
          "kind": "hike",
          "duration_minutes": 35.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "pace_min_per_km": 9.5,
          "incline_pct": 12.0
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "treadmill",
          "role": "cooldown",
          "pace_min_per_km": 6.3,
          "incline_pct": 1.0
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Romanian Deadlift",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "weights"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 4.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Single-Leg Calf Raises",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 2, pace 5:48/km, Treadmill 1%. → Hike: 35 phút ở Zone 2, pace 9:30/km, Treadmill 12%. → Cool-down: 10 phút ở Zone 1, pace 6:18/km, Treadmill 1%. → Strength: 6 phút, Romanian Deadlift: 3 x 6, 120 s nghỉ giữa các set. → Strength: 4 phút, Single-Leg Calf Raises: 3 x 12, 60 s nghỉ giữa các set. → D+ trong nhà (ước tính): 481 m."
    },
    "distance_km": 7.9,
    "description": "Warm-up: 15 phút ở Zone 2, pace 5:48/km, Treadmill 1%. → Hike: 35 phút ở Zone 2, pace 9:30/km, Treadmill 12%. → Cool-down: 10 phút ở Zone 1, pace 6:18/km, Treadmill 1%. → Strength: 6 phút, Romanian Deadlift: 3 x 6, 120 s nghỉ giữa các set. → Strength: 4 phút, Single-Leg Calf Raises: 3 x 12, 60 s nghỉ giữa các set. → D+ trong nhà (ước tính): 481 m.",
    "target_pace": "9:30 /km",
    "treadmill_incline": "1-12",
    "treadmill_speed": "6.3-10.3",
    "elevation_gain_m": 481.0,
    "grade_percent": 6.1,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Nghỉ ngơi hoàn toàn, bổ sung đủ nước và nạp tinh bột phức hợp để chuẩn bị cho hai ngày tập cuối tuần.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Aerobic Run và Dốc",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 85.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.8,
        "elevation_gain_m": 450
      }
    ],
    "fueling_tip": "Thời gian tập 85 phút: nạp 30-40g Carbs mỗi giờ cùng 400-500ml nước chứa 300-400mg Sodium.",
    "duration_minutes": 85.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 12.5,
      "hike_km": 0.0,
      "aerobic_minutes": 85.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 85.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 450.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 85.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.8,
          "elevation_gain_m": 450
        }
      ],
      "description": "Run: 85 phút ở Zone 2, pace 6:48/km, D+ 450 m (ước tính)."
    },
    "distance_km": 12.5,
    "description": "Run: 85 phút ở Zone 2, pace 6:48/km, D+ 450 m (ước tính).",
    "target_pace": "6:48 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 450.0,
    "grade_percent": 3.6,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Trail Long Run",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 130.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 7.0,
        "elevation_gain_m": 600
      }
    ],
    "fueling_tip": "Buổi tập kéo dài trên 2 tiếng: duy trì 45-60g Carbs mỗi giờ cùng 400-600ml nước chứa 400-500mg Sodium mỗi giờ.",
    "duration_minutes": 130.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 18.6,
      "hike_km": 0.0,
      "aerobic_minutes": 130.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 130.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 600.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 130.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 7.0,
          "elevation_gain_m": 600
        }
      ],
      "description": "Run: 130 phút ở Zone 2, pace 7:00/km, D+ 600 m (ước tính)."
    },
    "distance_km": 18.6,
    "description": "Run: 130 phút ở Zone 2, pace 7:00/km, D+ 600 m (ước tính).",
    "target_pace": "7:00 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 600.0,
    "grade_percent": 3.2,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Ưu tiên phục hồi cơ bắp với protein và đủ nước sau các bài chạy trail cuối tuần.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Treadmill Easy Run và Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 60.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "pace_min_per_km": 5.7,
        "incline_pct": 1.0
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Barbell Back Squats",
          "sets": 3,
          "reps": 5,
          "rest_seconds": 120.0,
          "equipment": [
            "weights"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Weighted Step-Ups",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "weights",
            "box"
          ]
        }
      }
    ],
    "fueling_tip": "Buổi tập dưới 75 phút, dùng nước lọc bổ sung thêm khoáng điện giải 200-400mg Sodium.",
    "duration_minutes": 72.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 10.5,
      "hike_km": 0.0,
      "aerobic_minutes": 60.0,
      "strength_minutes": 12.0,
      "passive_minutes": 0.0,
      "duration_minutes": 72.0,
      "estimated_indoor_ascent_m": 105.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 60.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "pace_min_per_km": 5.7,
          "incline_pct": 1.0
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Barbell Back Squats",
            "sets": 3,
            "reps": 5,
            "rest_seconds": 120.0,
            "equipment": [
              "weights"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Weighted Step-Ups",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "weights",
              "box"
            ]
          }
        }
      ],
      "description": "Run: 60 phút ở Zone 2, pace 5:42/km, Treadmill 1%. → Strength: 6 phút, Barbell Back Squats: 3 x 5, 120 s nghỉ giữa các set. → Strength: 6 phút, Weighted Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → D+ trong nhà (ước tính): 105 m."
    },
    "distance_km": 10.5,
    "description": "Run: 60 phút ở Zone 2, pace 5:42/km, Treadmill 1%. → Strength: 6 phút, Barbell Back Squats: 3 x 5, 120 s nghỉ giữa các set. → Strength: 6 phút, Weighted Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → D+ trong nhà (ước tính): 105 m.",
    "target_pace": "5:42 /km",
    "treadmill_incline": "1",
    "treadmill_speed": "10.5",
    "elevation_gain_m": 105.0,
    "grade_percent": 1.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Easy Run duy trì nền tảng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 65.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.75
      }
    ],
    "fueling_tip": "Thời lượng dưới 75 phút, uống 400-500ml nước lọc có điện giải nhẹ; không cần nạp năng lượng nhanh.",
    "duration_minutes": 65.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 11.3,
      "hike_km": 0.0,
      "aerobic_minutes": 65.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 65.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 65.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.75
        }
      ],
      "description": "Run: 65 phút ở Zone 2, pace 5:45/km."
    },
    "distance_km": 11.3,
    "description": "Run: 65 phút ở Zone 2, pace 5:45/km.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Treadmill Incline Hike và Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "role": "warmup",
        "pace_min_per_km": 5.8,
        "incline_pct": 1.0
      },
      {
        "kind": "hike",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "pace_min_per_km": 9.5,
        "incline_pct": 14.0
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "treadmill",
        "role": "cooldown",
        "pace_min_per_km": 6.3,
        "incline_pct": 1.0
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Romanian Deadlift",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "weights"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 4.0,
        "zone": null,
        "setting": "indoor",
        "exercise": {
          "name": "Eccentric Step-Downs",
          "sets": 3,
          "reps": 8,
          "rest_seconds": 60.0,
          "equipment": [
            "box"
          ]
        }
      }
    ],
    "fueling_tip": "Kéo dài 80 phút: nạp 30g Carbs từ gel hoặc nước uống thể thao cùng 400-500ml nước và 300-400mg Sodium.",
    "duration_minutes": 80.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 4.2,
      "hike_km": 4.7,
      "aerobic_minutes": 70.0,
      "strength_minutes": 10.0,
      "passive_minutes": 0.0,
      "duration_minutes": 80.0,
      "estimated_indoor_ascent_m": 698.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "role": "warmup",
          "pace_min_per_km": 5.8,
          "incline_pct": 1.0
        },
        {
          "kind": "hike",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "pace_min_per_km": 9.5,
          "incline_pct": 14.0
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "treadmill",
          "role": "cooldown",
          "pace_min_per_km": 6.3,
          "incline_pct": 1.0
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Romanian Deadlift",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "weights"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 4.0,
          "zone": null,
          "setting": "indoor",
          "exercise": {
            "name": "Eccentric Step-Downs",
            "sets": 3,
            "reps": 8,
            "rest_seconds": 60.0,
            "equipment": [
              "box"
            ]
          }
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 2, pace 5:48/km, Treadmill 1%. → Hike: 45 phút ở Zone 2, pace 9:30/km, Treadmill 14%. → Cool-down: 10 phút ở Zone 1, pace 6:18/km, Treadmill 1%. → Strength: 6 phút, Romanian Deadlift: 3 x 6, 120 s nghỉ giữa các set. → Strength: 4 phút, Eccentric Step-Downs: 3 x 8, 60 s nghỉ giữa các set. → D+ trong nhà (ước tính): 698 m."
    },
    "distance_km": 8.9,
    "description": "Warm-up: 15 phút ở Zone 2, pace 5:48/km, Treadmill 1%. → Hike: 45 phút ở Zone 2, pace 9:30/km, Treadmill 14%. → Cool-down: 10 phút ở Zone 1, pace 6:18/km, Treadmill 1%. → Strength: 6 phút, Romanian Deadlift: 3 x 6, 120 s nghỉ giữa các set. → Strength: 4 phút, Eccentric Step-Downs: 3 x 8, 60 s nghỉ giữa các set. → D+ trong nhà (ước tính): 698 m.",
    "target_pace": "9:30 /km",
    "treadmill_incline": "1-14",
    "treadmill_speed": "6.3-10.3",
    "elevation_gain_m": 698.0,
    "grade_percent": 7.8,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Nghỉ ngơi, ngủ đủ giấc và uống đều đặn từng ngụm nước trong ngày để sẵn sàng cho bài tập trail dài.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Aerobic Run và Kỹ thuật dốc",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 90.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.7,
        "elevation_gain_m": 500
      }
    ],
    "fueling_tip": "Buổi tập 90 phút: bổ sung 30-50g Carbs mỗi giờ kèm 400-600ml nước và 350-500mg Sodium/giờ.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 13.4,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 500.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 90.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.7,
          "elevation_gain_m": 500
        }
      ],
      "description": "Run: 90 phút ở Zone 2, pace 6:42/km, D+ 500 m (ước tính)."
    },
    "distance_km": 13.4,
    "description": "Run: 90 phút ở Zone 2, pace 6:42/km, D+ 500 m (ước tính).",
    "target_pace": "6:42 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 500.0,
    "grade_percent": 3.7,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Trail Long Run tích lũy độ dốc",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 140.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 6.9,
        "elevation_gain_m": 650
      }
    ],
    "fueling_tip": "Buổi tập trên 2 tiếng: nạp đều đặn 45-60g Carbs mỗi giờ, duy trì 500ml nước cùng 400-600mg Sodium mỗi giờ.",
    "duration_minutes": 140.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 20.3,
      "hike_km": 0.0,
      "aerobic_minutes": 140.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 140.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 650.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 140.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 6.9,
          "elevation_gain_m": 650
        }
      ],
      "description": "Run: 140 phút ở Zone 2, pace 6:54/km, D+ 650 m (ước tính)."
    },
    "distance_km": 20.3,
    "description": "Run: 140 phút ở Zone 2, pace 6:54/km, D+ 650 m (ước tính).",
    "target_pace": "6:54 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 650.0,
    "grade_percent": 3.2,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>
<details><summary>Captured baseline</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Easy Trail Run & Hill Strides",
    "type": "Easy",
    "duration_minutes": 75.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 13.0,
    "elevation_gain_m": 420.0,
    "grade_percent": 3.2,
    "treadmill_incline": "2-4",
    "treadmill_speed": "8.8-9.6",
    "description": "Process: Warm up 15 min chạy nhẹ nhàng trên địa hình trail thoai thoải @ Zone 1-2 → 50 min chạy ổn định duy trì nhịp tim dưới AeT @ Zone 2 (130-146 bpm) → 6 x 15s Hill Strides tăng tốc mượt mà trên dốc 8-10%, đi bộ thả lỏng 45s giữa các hiệp → Cool down 5 min đi bộ và thả lỏng bắp chân. Overall: Buổi chạy Trail đầu tiên của plan giúp kích hoạt lại phản xạ chân trên địa hình tự nhiên và làm quen với dốc. Cường độ hoàn toàn kiểm soát dưới ngưỡng hiếu khí AeT kết hợp các đoạn sải chân ngắn để kích hoạt thần kinh cơ. Reason: Khởi động chu kỳ tập luyện với kích thích chuyển động đặc thù trail sau tuần làm việc mà không tích lũy mệt mỏi hệ thống. Benefit: Tăng cường độ bền mao mạch, củng cố gân gót và dây chằng cổ chân trên nền đất không bằng phẳng. Warning: Kiểm soát chặt chẽ nhịp tim khi lên dốc, chủ động chuyển sang đi bộ nhanh nếu HR vượt quá 146 bpm.",
    "fueling_tip": "Buổi tập 75 phút cần 400-500ml nước mang theo; bổ sung 200-300mg sodium nếu thời tiết oi bức. Không bắt buộc nạp thêm carbs trong bài chạy này.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Khởi Động Núi",
    "type": "Long Run",
    "duration_minutes": 110.0,
    "target_zone": "Zone 2",
    "target_hr_range": "132-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 19.1,
    "elevation_gain_m": 720.0,
    "grade_percent": 3.8,
    "treadmill_incline": "3-5",
    "treadmill_speed": "8.5-9.2",
    "description": "Process: Warm up 10 min đi bộ nhanh và chạy bước nhỏ chân dốc @ Zone 1 → 90 min Long Run duy trì nhịp tim hiếu khí Zone 2, chuyển sang power-hiking chủ động trên các đoạn dốc >10% → Cool down 10 min đi bộ thả lỏng kết hợp xoay khớp hông. Overall: Bài Long Run mở đầu khối tập luyện giúp kích hoạt năng lực chuyển hóa chất béo và làm quen với nhịp điệu vận động bền bỉ trên địa hình đồi núi dốc. Reason: Tận dụng ngày cuối tuần để tích lũy độ cao D+ đặc thù mà các ngày trong tuần ở đô thị không thể đáp ứng. Benefit: Mở rộng thể tích tâm thất, phát triển mạng lưới ty thể trong sợi cơ bền và tăng sức chịu đựng của cơ tứ đầu đùi khi đổ dốc. Warning: Tránh ham chạy trên các con dốc gắt khiến nhịp tim vọt qua ngưỡng AnT (166 bpm), điều này sẽ phá hỏng bản chất của bài aerobic base.",
    "fueling_tip": "Thời lượng 110 phút: Nạp 30-45g carbs mỗi giờ (1 gói gel mỗi 40-45 phút), uống 500ml nước pha điện giải (khoảng 350mg sodium) đều đặn mỗi giờ.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Nghỉ Ngơi Tích Cực",
    "type": "Rest",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "target_hr_range": "Dưới 120 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Nghỉ ngơi trọn vẹn, không chạy bộ → 15 min kéo giãn nhẹ nhàng và Foam Rolling vào buổi tối. Overall: Ngày nghỉ hoàn toàn theo lịch cố định giúp cơ bắp và hệ thần kinh hồi phục sau khối lượng chạy trail cuối tuần. Reason: Đảm bảo thời gian tái tạo glycogen và thích nghi mô liên kết trước khi bước vào tuần tập trọn vẹn. Benefit: Giảm nồng độ cortisol, phòng tránh quá tải vi chấn thương gân cơ. Warning: Không thực hiện các hoạt động thể thao cường độ mạnh thay thế trong ngày hôm nay.",
    "fueling_tip": "Duy trì uống đủ 2-2.5 lít nước trong ngày, ưu tiên bữa ăn giàu đạm sạch và rau xanh để hỗ trợ tái tạo mô cơ.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Treadmill Muscular Endurance & Sức Mạnh Thần Kinh Cơ",
    "type": "Muscular Endurance",
    "duration_minutes": 65.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-146 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "treadmill_incline": "11-13",
    "treadmill_speed": "5.8",
    "description": "Process: Warm up 10 min chạy phẳng nhẹ nhàng trên treadmill @ 1% incline → 10 reps Split Jump Squats, 15s transition → 10 reps Squat Jumps, 15s transition → 10 reps/leg Box Step-Ups at 75% kneecap height, 15s transition → 10 reps/leg Front Lunges → Nghỉ 60s giữa các hiệp, thực hiện tổng cộng 4 rounds chuỗi bài trên → 20 min Power-hiking trên Treadmill ở độ dốc 12% @ tốc độ 5.8 kph duy trì nhịp tim Zone 2 → Cool down 5 min đi bộ phẳng thả lỏng chân. Overall: Buổi tập sức bền cơ bắp đặc thù kết hợp chuỗi circuit cơ học và leo dốc trên máy chạy tại phòng gym nhằm xây dựng nền tảng chịu mỏi cục bộ cho cơ đùi. Reason: Áp dụng quy tắc đường chạy ngắn dưới 10 tuần, đưa khối Muscular Endurance vào ngay giai đoạn đầu để thích nghi với độ dốc lớn của giải đấu 43.8 m D+/km. Benefit: Huấn luyện sợi cơ co giật nhanh FTa hoạt động bền bỉ trong môi trường hiếu khí mà không đẩy tim lên ngưỡng quá tải. Warning: Giữ form lưng thẳng và đầu gối thẳng trục khi thực hiện Box Step-Ups và Split Jumps, dừng ngay nếu khớp gối có dấu hiệu nhói đau.",
    "fueling_tip": "Thời lượng dưới 75 phút: Uống 400-600ml nước mát có bổ sung điện giải (200-300mg sodium) từng ngụm nhỏ giữa các hiệp nghỉ.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Phẳng Easy Aerobic Run",
    "type": "Easy",
    "duration_minutes": 60.0,
    "target_zone": "Zone 2",
    "target_hr_range": "128-142 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 10.4,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "treadmill_incline": "1-2",
    "treadmill_speed": "9.4-10.2",
    "description": "Process: Warm up 10 min chạy thật chậm thả lỏng @ Zone 1 → 45 min chạy ổn định trên đường bằng phẳng đô thị @ Zone 2 (128-142 bpm, Cadence 175-180 spm) → Cool down 5 min đi bộ và duỗi cơ tĩnh. Overall: Bài chạy nhẹ nhàng trên địa hình phẳng nội thành TP.HCM nhằm tích lũy thể tích hiếu khí đơn thuần. Reason: Tuân thủ điều kiện sinh hoạt đô thị ngày trong tuần phẳng, đồng thời xả mỏi cơ bắp sau bài tập sức bền cơ đùi ngày thứ Ba. Benefit: Gia tăng lưu lượng máu phục hồi vi mô, củng cố mật độ mao mạch và duy trì nền tảng chuyển hóa mỡ. Warning: Giữ nhịp thở đàm thoại êm ái xuyên suốt buổi chạy, tuyệt đối không đẩy tốc độ vào Zone 3 dù cảm giác chân rất nhẹ.",
    "fueling_tip": "Chạy dưới 75 phút: Uống 300-500ml nước lọc trước và sau buổi tập; không cần nạp thêm năng lượng dạng đường bột.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Treadmill Incline Steady Climbing & Bổ Trợ Sức Mạnh",
    "type": "Strength",
    "duration_minutes": 60.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-146 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "treadmill_incline": "9-11",
    "treadmill_speed": "6",
    "description": "Process: Warm up 10 min chạy phẳng nhẹ @ Zone 1 → 25 min Power-hiking leo dốc liên tục trên Treadmill incline 10% @ 6.0 kph giữ tim Zone 2 → Dumbbell Goblet Squats: 3x8 reps với tạ vừa, 90s rest → Romanian Deadlifts: 3x8 reps, 90s rest → Eccentric Calf Raises trên bậc thang: 3x12 reps mỗi chân, 60s rest → Cool down 5 min giãn cơ cẳng chân và hông. Overall: Buổi tập sức mạnh tổng hợp và leo dốc trên máy nhằm tăng cường độ bền gân kheo, khớp hông và chuỗi cơ sau. Reason: Tận dụng ngày có quyền sử dụng phòng gym theo lịch tuần để rèn luyện sức chịu đựng của hệ cơ xương khớp đối với độ dốc. Benefit: Tăng công suất phát lực của cơ mông, ổn định xương chậu và chống sụp cổ chân khi leo dốc dài. Warning: Tập trung siết chặt cơ bụng và giữ lưng thẳng trong bài Goblet Squat và Deadlift để tránh dồn áp lực vào thắt lưng dưới.",
    "fueling_tip": "Thời lượng 60 phút: Uống 500ml nước có pha khoáng chất nhẹ; nạp 20g đạm sau buổi tập để đẩy nhanh tốc độ tổng hợp protein cơ bắp.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Nghỉ Ngơi Tích Cực",
    "type": "Rest",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "target_hr_range": "Dưới 120 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Nghỉ ngơi toàn diện, không tập luyện thể thao cường độ cao → 10 min ngâm chân nước ấm hoặc kéo giãn cơ nhẹ trước khi ngủ. Overall: Ngày nghỉ cố định thứ hai trong tuần giúp cơ thể tích lũy năng lượng và hồi phục hoàn toàn cho khối lượng chạy núi cuối tuần. Reason: Đảm bảo vùng đệm 48 giờ giữa bài tập sức mạnh/ME với bài chạy dài chủ nhật nhằm bảo vệ gân khớp. Benefit: Tối đa hóa khả năng bù đắp thể chất (supercompensation), nạp đầy kho dự trữ glycogen. Warning: Ngủ đủ giấc tối thiểu 7-8 tiếng, hạn chế đứng hoặc đi bộ quá nhiều trong công việc hàng ngày.",
    "fueling_tip": "Ăn các bữa ăn cân bằng, bổ sung carbohydrate phức hợp và duy trì đủ lượng nước cần thiết cho cơ thể.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Easy Aerobic & Đổ Dốc Kỹ Thuật",
    "type": "Easy",
    "duration_minutes": 75.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 13.0,
    "elevation_gain_m": 500.0,
    "grade_percent": 3.8,
    "treadmill_incline": "3-5",
    "treadmill_speed": "8.5-9.2",
    "description": "Process: Warm up 15 min chạy nhẹ nhàng vào chân núi @ Zone 1-2 → 50 min chạy trail địa hình mấp mô luân phiên leo dốc vừa và đổ dốc kỹ thuật @ Zone 2 (130-146 bpm) → 6 x 12s Hill Bounds trên dốc tự nhiên 15%, đi bộ thả lỏng 2 min giữa các lần bứt tốc → Cool down 5 min đi bộ thả lỏng. Overall: Buổi chạy trail thứ Bảy giúp rèn luyện khả năng phối hợp thần kinh cơ khi tiếp đất trên địa hình gồ ghề và kích hoạt sợi cơ bùng nổ thông qua Hill Bounds. Reason: Xây dựng khả năng thích nghi chịu tải lệch tâm (eccentric loading) cho cơ tứ đầu đùi trên cung đường đồi núi thực tế. Benefit: Tăng độ vững cổ chân, cải thiện khả năng đọc địa hình khi đổ dốc và củng cố công suất sải chân leo dốc ngắn. Warning: Dừng ngay Hill Bounds nếu cảm thấy bước chân bị giảm lực hoặc kỹ thuật tiếp đất không còn kiểm soát vững vàng.",
    "fueling_tip": "Thời lượng 75 phút trên trail: Mang theo 500-600ml nước điện giải (300mg sodium), có thể nhai 1 viên kẹo năng lượng (chew) sau 45 phút chạy.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Leo Núi Đặc Thù",
    "type": "Long Run",
    "duration_minutes": 125.0,
    "target_zone": "Zone 2",
    "target_hr_range": "132-146 bpm",
    "target_pace": "6:00 - 5:31 /km",
    "distance_km": 21.7,
    "elevation_gain_m": 900.0,
    "grade_percent": 4.3,
    "treadmill_incline": "3.5-5.5",
    "treadmill_speed": "8.3-9",
    "description": "Process: Warm up 15 min chạy chậm khởi động @ Zone 1 → 95 min Long Run leo dốc bền bỉ @ Zone 2, chủ động đi bộ dốc cao (power-hiking sải dài) khi độ dốc vượt quá 10%, duy trì bước chân êm khi đổ dốc → Cool down 15 min đi bộ chậm và thả lỏng toàn thân. Overall: Bài chạy dài trọng điểm của tuần giúp nâng cao độ bền thể chất trên cung đường núi có độ cao D+ sát với đặc thù giải đấu. Reason: Phát triển dung lượng tim và sức bền cơ xương khớp thích ứng với tỷ lệ dốc 43.8 m D+/km của mục tiêu 48K. Benefit: Cải thiện hiệu suất oxy hóa chất béo ở tốc độ bền, gia tăng sức chịu đựng của cơ lưng và đùi trước khi vận động liên tục trên 2 giờ. Warning: Không để nhịp tim trôi (cardiac drift) vào Zone 4 ở nửa sau buổi tập; luôn hạ nhịp độ hoặc đi bộ chậm lại nếu nhịp tim tiến sát 150 bpm.",
    "fueling_tip": "Thời lượng 125 phút: Bổ sung 40-50g carbs mỗi giờ (dùng gel hoặc bột pha nước sau mỗi 35-40 phút), uống 500-700ml nước chứa 400-500mg sodium mỗi giờ.",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>

## scheduler_fixture_vietnam_urban_sub_elite_no_gym

- Gemini+KB latency: **20.2s** (baseline: 22.7s)
- Tier attribution: **gemini**
- New: `{"workout_count": 14, "types": {"Easy": 7, "Rest": 2, "Recovery": 2, "Long Run": 2, "Tempo": 1}, "me_sessions": 0, "me_looks_like_circuit": null}`
- Ref: `{"workout_count": 9, "types": {"Interval": 1, "Long Run": 2, "Recovery": 1, "Tempo": 1, "Rest": 1, "Muscular Endurance": 1, "Easy": 2}, "me_sessions": 1, "me_looks_like_circuit": false}`
- Tier: **sub_elite** (expected sub_elite)
- Week-2 volume: **115.0 km** (expected 92-119)
- Context metrics v2: `{"prompt_identity": {"name": "plan_generation", "version": "6", "source": "langfuse", "sha256": "7a19da8c7e374c0247484ad22bc29703f5b88a3ed345899bec520b580ae36de7"}, "checks": {"arithmetic": true, "access": true, "intensity_accounting": true, "progression": true}, "unavailable_checks": [], "weeks": {"1": {"run_km": 104.2, "hike_km": 4.2, "aerobic_minutes": 596.2, "strength_minutes": 17.0, "passive_minutes": 16.8, "long_run_locomotion_time_share": 0.335, "long_run_distance_share": 0.299, "weekend_locomotion_time_share": 0.497}, "2": {"run_km": 110.3, "hike_km": 4.7, "aerobic_minutes": 631.6, "strength_minutes": 20.0, "passive_minutes": 22.4, "long_run_locomotion_time_share": 0.34, "long_run_distance_share": 0.302, "weekend_locomotion_time_share": 0.501}}, "block_engines": null, "internal_disclosure": false}`

<details><summary>Gemini+KB output</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Easy Run và Bodyweight Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "warmup",
        "pace_min_per_km": 5.4
      },
      {
        "kind": "run",
        "duration_minutes": 55.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.95
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "flat_outdoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "flat_outdoor",
        "exercise": {
          "name": "Walking Lunges",
          "sets": 3,
          "reps": 10,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 5.0,
        "zone": null,
        "setting": "flat_outdoor",
        "exercise": {
          "name": "Single Leg Calf Raises",
          "sets": 3,
          "reps": 15,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "cooldown",
        "pace_min_per_km": 5.45
      }
    ],
    "rationale": "Duy trì chuyển động thân dưới chuẩn xác và dừng ngay nếu xuất hiện đau gối hoặc căng cứng gân gót.",
    "fueling_tip": "Buổi tập 97 phút: 30-40g Carbs mỗi giờ cùng 400-500ml nước chứa 300-400mg Sodium.",
    "duration_minutes": 97.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 15.7,
      "hike_km": 0.0,
      "aerobic_minutes": 80.0,
      "strength_minutes": 17.0,
      "passive_minutes": 0.0,
      "duration_minutes": 97.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "warmup",
          "pace_min_per_km": 5.4
        },
        {
          "kind": "run",
          "duration_minutes": 55.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.95
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "flat_outdoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "flat_outdoor",
          "exercise": {
            "name": "Walking Lunges",
            "sets": 3,
            "reps": 10,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 5.0,
          "zone": null,
          "setting": "flat_outdoor",
          "exercise": {
            "name": "Single Leg Calf Raises",
            "sets": 3,
            "reps": 15,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "cooldown",
          "pace_min_per_km": 5.45
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 55 phút ở Zone 2, pace 4:57/km. → Strength: 6 phút, Bodyweight Squats: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Walking Lunges: 3 x 10, 60 s nghỉ giữa các set. → Strength: 5 phút, Single Leg Calf Raises: 3 x 15, 45 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:27/km."
    },
    "distance_km": 15.7,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 55 phút ở Zone 2, pace 4:57/km. → Strength: 6 phút, Bodyweight Squats: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Walking Lunges: 3 x 10, 60 s nghỉ giữa các set. → Strength: 5 phút, Single Leg Calf Raises: 3 x 15, 45 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:27/km. Duy trì chuyển động thân dưới chuẩn xác và dừng ngay nếu xuất hiện đau gối hoặc căng cứng gân gót.",
    "target_pace": "4:57 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Easy Run duy trì Aerobic Base",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "warmup",
        "pace_min_per_km": 5.4
      },
      {
        "kind": "run",
        "duration_minutes": 60.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.95
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "cooldown",
        "pace_min_per_km": 5.45
      }
    ],
    "fueling_tip": "Buổi tập 85 phút: nạp 30g Carbs kết hợp 400-500ml nước cùng 300-400mg Sodium mỗi giờ.",
    "duration_minutes": 85.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 16.7,
      "hike_km": 0.0,
      "aerobic_minutes": 85.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 85.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "warmup",
          "pace_min_per_km": 5.4
        },
        {
          "kind": "run",
          "duration_minutes": 60.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.95
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "cooldown",
          "pace_min_per_km": 5.45
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 60 phút ở Zone 2, pace 4:57/km. → Cool-down: 10 phút ở Zone 1, pace 5:27/km."
    },
    "distance_km": 16.7,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 60 phút ở Zone 2, pace 4:57/km. → Cool-down: 10 phút ở Zone 1, pace 5:27/km.",
    "target_pace": "4:57 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Nghỉ ngơi hoàn toàn",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Uống đủ nước trong ngày và bổ sung dinh dưỡng cân bằng giàu protein để phục hồi cơ bắp.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Easy Run và Strides phẳng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "warmup",
        "pace_min_per_km": 5.4
      },
      {
        "kind": "run",
        "duration_minutes": 55.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.95
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      },
      {
        "kind": "run",
        "duration_minutes": 2.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.45
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      },
      {
        "kind": "run",
        "duration_minutes": 2.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.45
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      },
      {
        "kind": "run",
        "duration_minutes": 2.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.45
      },
      {
        "kind": "run",
        "duration_minutes": 1.0,
        "zone": "Zone 4",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.1
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "cooldown",
        "pace_min_per_km": 5.45
      }
    ],
    "rationale": "Chạy các đoạn Strides với kỹ thuật tiếp đất nhẹ nhàng và dừng lại nếu bước chạy có dấu hiệu gượng ép.",
    "fueling_tip": "Buổi tập 90 phút: sử dụng 30-45g Carbs cùng 500ml nước có 400mg Sodium.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 17.8,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "warmup",
          "pace_min_per_km": 5.4
        },
        {
          "kind": "run",
          "duration_minutes": 55.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.95
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        },
        {
          "kind": "run",
          "duration_minutes": 2.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.45
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        },
        {
          "kind": "run",
          "duration_minutes": 2.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.45
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        },
        {
          "kind": "run",
          "duration_minutes": 2.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.45
        },
        {
          "kind": "run",
          "duration_minutes": 1.0,
          "zone": "Zone 4",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.1
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "cooldown",
          "pace_min_per_km": 5.45
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 55 phút ở Zone 2, pace 4:57/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Run: 2 phút ở Zone 1, pace 5:27/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Run: 2 phút ở Zone 1, pace 5:27/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Run: 2 phút ở Zone 1, pace 5:27/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Cool-down: 10 phút ở Zone 1, pace 5:27/km."
    },
    "distance_km": 17.8,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 55 phút ở Zone 2, pace 4:57/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Run: 2 phút ở Zone 1, pace 5:27/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Run: 2 phút ở Zone 1, pace 5:27/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Run: 2 phút ở Zone 1, pace 5:27/km. → Run: 1 phút ở Zone 4, pace 4:06/km. → Cool-down: 10 phút ở Zone 1, pace 5:27/km. Chạy các đoạn Strides với kỹ thuật tiếp đất nhẹ nhàng và dừng lại nếu bước chạy có dấu hiệu gượng ép.",
    "target_pace": "4:57 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Recovery Run nhẹ nhàng",
    "type": "Recovery",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 45.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.35
      }
    ],
    "rationale": "Giữ nhịp tim hoàn toàn thoải mái dưới ngưỡng hiếu khí để tích lũy thể lực cho hai ngày cuối tuần.",
    "fueling_tip": "Buổi tập dưới 75 phút: dùng nước lọc kèm 200-400mg Sodium nếu thời tiết nóng ẩm; không cần bổ sung Carbs.",
    "duration_minutes": 45.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 8.4,
      "hike_km": 0.0,
      "aerobic_minutes": 45.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 45.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 45.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.35
        }
      ],
      "description": "Run: 45 phút ở Zone 1, pace 5:21/km."
    },
    "distance_km": 8.4,
    "description": "Run: 45 phút ở Zone 1, pace 5:21/km. Giữ nhịp tim hoàn toàn thoải mái dưới ngưỡng hiếu khí để tích lũy thể lực cho hai ngày cuối tuần.",
    "target_pace": "5:21 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Run Dốc và Hill Sprints",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "warmup",
        "pace_min_per_km": 5.4,
        "elevation_gain_m": 50
      },
      {
        "kind": "run",
        "duration_minutes": 65.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.6,
        "elevation_gain_m": 520
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "cooldown",
        "pace_min_per_km": 5.5,
        "elevation_gain_m": 40
      }
    ],
    "rationale": "Chấm dứt bài Hill Sprints ngay lập tức khi xuất hiện cảm giác hụt lực bộc phát.",
    "fueling_tip": "Buổi tập 113 phút: duy trì 45g Carbs mỗi giờ cùng 500ml nước và 400-500mg Sodium.",
    "duration_minutes": 113.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 17.4,
      "hike_km": 0.0,
      "aerobic_minutes": 96.2,
      "strength_minutes": 0.0,
      "passive_minutes": 16.8,
      "duration_minutes": 113.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 682.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "warmup",
          "pace_min_per_km": 5.4,
          "elevation_gain_m": 50
        },
        {
          "kind": "run",
          "duration_minutes": 65.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.6,
          "elevation_gain_m": 520
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "cooldown",
          "pace_min_per_km": 5.5,
          "elevation_gain_m": 40
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km, D+ 50 m (ước tính). → Run: 65 phút ở Zone 2, pace 5:36/km, D+ 520 m (ước tính). → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Cool-down: 15 phút ở Zone 1, pace 5:30/km, D+ 40 m (ước tính)."
    },
    "distance_km": 17.4,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km, D+ 50 m (ước tính). → Run: 65 phút ở Zone 2, pace 5:36/km, D+ 520 m (ước tính). → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Cool-down: 15 phút ở Zone 1, pace 5:30/km, D+ 40 m (ước tính). Chấm dứt bài Hill Sprints ngay lập tức khi xuất hiện cảm giác hụt lực bộc phát.",
    "target_pace": "5:36 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 682.0,
    "grade_percent": 3.9,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Trail Long Run và Power Hiking",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 20.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "warmup",
        "pace_min_per_km": 5.45,
        "elevation_gain_m": 60
      },
      {
        "kind": "run",
        "duration_minutes": 90.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.75,
        "elevation_gain_m": 500
      },
      {
        "kind": "hike",
        "duration_minutes": 40.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 9.5,
        "elevation_gain_m": 480
      },
      {
        "kind": "run",
        "duration_minutes": 40.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.65,
        "elevation_gain_m": 80
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "cooldown",
        "pace_min_per_km": 5.5,
        "elevation_gain_m": 20
      }
    ],
    "rationale": "Sử dụng kỹ thuật sải bước ngắn khi đổ dốc để hạn chế chấn động khớp gối.",
    "fueling_tip": "Buổi tập 200 phút: nạp 60-70g Carbs mỗi giờ kết hợp 600ml nước và 600-700mg Sodium, bắt đầu từ phút thứ 30.",
    "duration_minutes": 200.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 28.2,
      "hike_km": 4.2,
      "aerobic_minutes": 200.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 200.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 1140.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 20.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "warmup",
          "pace_min_per_km": 5.45,
          "elevation_gain_m": 60
        },
        {
          "kind": "run",
          "duration_minutes": 90.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.75,
          "elevation_gain_m": 500
        },
        {
          "kind": "hike",
          "duration_minutes": 40.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 9.5,
          "elevation_gain_m": 480
        },
        {
          "kind": "run",
          "duration_minutes": 40.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.65,
          "elevation_gain_m": 80
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "cooldown",
          "pace_min_per_km": 5.5,
          "elevation_gain_m": 20
        }
      ],
      "description": "Warm-up: 20 phút ở Zone 1, pace 5:27/km, D+ 60 m (ước tính). → Run: 90 phút ở Zone 2, pace 5:45/km, D+ 500 m (ước tính). → Hike: 40 phút ở Zone 2, pace 9:30/km, D+ 480 m (ước tính). → Run: 40 phút ở Zone 2, pace 5:39/km, D+ 80 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 5:30/km, D+ 20 m (ước tính)."
    },
    "distance_km": 32.4,
    "description": "Warm-up: 20 phút ở Zone 1, pace 5:27/km, D+ 60 m (ước tính). → Run: 90 phút ở Zone 2, pace 5:45/km, D+ 500 m (ước tính). → Hike: 40 phút ở Zone 2, pace 9:30/km, D+ 480 m (ước tính). → Run: 40 phút ở Zone 2, pace 5:39/km, D+ 80 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 5:30/km, D+ 20 m (ước tính). Sử dụng kỹ thuật sải bước ngắn khi đổ dốc để hạn chế chấn động khớp gối.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 1140.0,
    "grade_percent": 3.5,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Easy Run và Bodyweight Strength Bổ Trợ",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "warmup",
        "pace_min_per_km": 5.4
      },
      {
        "kind": "run",
        "duration_minutes": 60.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.95
      },
      {
        "kind": "strength",
        "duration_minutes": 7.0,
        "zone": null,
        "setting": "flat_outdoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 3,
          "reps": 15,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 7.0,
        "zone": null,
        "setting": "flat_outdoor",
        "exercise": {
          "name": "Walking Lunges",
          "sets": 3,
          "reps": 12,
          "rest_seconds": 60.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 6.0,
        "zone": null,
        "setting": "flat_outdoor",
        "exercise": {
          "name": "Single Leg Calf Raises",
          "sets": 3,
          "reps": 18,
          "rest_seconds": 45.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "cooldown",
        "pace_min_per_km": 5.45
      }
    ],
    "rationale": "Thực hiện động tác có kiểm soát tốc độ hạ người và giữ cột sống thẳng tự nhiên.",
    "fueling_tip": "Buổi tập 105 phút: nạp 35-45g Carbs mỗi giờ kết hợp 500ml nước và 350-450mg Sodium.",
    "duration_minutes": 105.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 16.7,
      "hike_km": 0.0,
      "aerobic_minutes": 85.0,
      "strength_minutes": 20.0,
      "passive_minutes": 0.0,
      "duration_minutes": 105.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "warmup",
          "pace_min_per_km": 5.4
        },
        {
          "kind": "run",
          "duration_minutes": 60.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.95
        },
        {
          "kind": "strength",
          "duration_minutes": 7.0,
          "zone": null,
          "setting": "flat_outdoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 3,
            "reps": 15,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 7.0,
          "zone": null,
          "setting": "flat_outdoor",
          "exercise": {
            "name": "Walking Lunges",
            "sets": 3,
            "reps": 12,
            "rest_seconds": 60.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 6.0,
          "zone": null,
          "setting": "flat_outdoor",
          "exercise": {
            "name": "Single Leg Calf Raises",
            "sets": 3,
            "reps": 18,
            "rest_seconds": 45.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "cooldown",
          "pace_min_per_km": 5.45
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 60 phút ở Zone 2, pace 4:57/km. → Strength: 7 phút, Bodyweight Squats: 3 x 15, 60 s nghỉ giữa các set. → Strength: 7 phút, Walking Lunges: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Single Leg Calf Raises: 3 x 18, 45 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:27/km."
    },
    "distance_km": 16.7,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 60 phút ở Zone 2, pace 4:57/km. → Strength: 7 phút, Bodyweight Squats: 3 x 15, 60 s nghỉ giữa các set. → Strength: 7 phút, Walking Lunges: 3 x 12, 60 s nghỉ giữa các set. → Strength: 6 phút, Single Leg Calf Raises: 3 x 18, 45 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:27/km. Thực hiện động tác có kiểm soát tốc độ hạ người và giữ cột sống thẳng tự nhiên.",
    "target_pace": "4:57 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Easy Run Tích Lũy Thể Lực",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "warmup",
        "pace_min_per_km": 5.4
      },
      {
        "kind": "run",
        "duration_minutes": 65.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.95
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "cooldown",
        "pace_min_per_km": 5.45
      }
    ],
    "fueling_tip": "Buổi tập 90 phút: dùng 30-40g Carbs mỗi giờ cùng 450-550ml nước chứa 350-450mg Sodium.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 17.7,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "warmup",
          "pace_min_per_km": 5.4
        },
        {
          "kind": "run",
          "duration_minutes": 65.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.95
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "cooldown",
          "pace_min_per_km": 5.45
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 65 phút ở Zone 2, pace 4:57/km. → Cool-down: 10 phút ở Zone 1, pace 5:27/km."
    },
    "distance_km": 17.7,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 65 phút ở Zone 2, pace 4:57/km. → Cool-down: 10 phút ở Zone 1, pace 5:27/km.",
    "target_pace": "4:57 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Nghỉ ngơi hoàn toàn",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "zone": null,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Tập trung bổ sung dinh dưỡng hồi phục, giữ lượng nước ổn định và ưu tiên giấc ngủ sâu.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "zone": null,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Easy Run với Sub-Threshold Lặp Lại",
    "type": "Tempo",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "warmup",
        "pace_min_per_km": 5.4
      },
      {
        "kind": "run",
        "duration_minutes": 30.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.95
      },
      {
        "kind": "run",
        "duration_minutes": 8.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.35
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.45
      },
      {
        "kind": "run",
        "duration_minutes": 8.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.35
      },
      {
        "kind": "run",
        "duration_minutes": 3.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.45
      },
      {
        "kind": "run",
        "duration_minutes": 8.0,
        "zone": "Zone 3",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.35
      },
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "role": "cooldown",
        "pace_min_per_km": 5.45
      }
    ],
    "rationale": "Duy trì nhịp thở ổn định dưới ngưỡng AnT và hạ nhịp độ nếu xuất hiện hiện tượng thở dốc.",
    "fueling_tip": "Buổi tập 90 phút: 40-50g Carbs mỗi giờ kèm 500-600ml nước có 400mg Sodium.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 18.2,
      "hike_km": 0.0,
      "aerobic_minutes": 90.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "warmup",
          "pace_min_per_km": 5.4
        },
        {
          "kind": "run",
          "duration_minutes": 30.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.95
        },
        {
          "kind": "run",
          "duration_minutes": 8.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.35
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.45
        },
        {
          "kind": "run",
          "duration_minutes": 8.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.35
        },
        {
          "kind": "run",
          "duration_minutes": 3.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.45
        },
        {
          "kind": "run",
          "duration_minutes": 8.0,
          "zone": "Zone 3",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.35
        },
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "role": "cooldown",
          "pace_min_per_km": 5.45
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 30 phút ở Zone 2, pace 4:57/km. → Run: 8 phút ở Zone 3, pace 4:21/km. → Run: 3 phút ở Zone 1, pace 5:27/km. → Run: 8 phút ở Zone 3, pace 4:21/km. → Run: 3 phút ở Zone 1, pace 5:27/km. → Run: 8 phút ở Zone 3, pace 4:21/km. → Cool-down: 15 phút ở Zone 1, pace 5:27/km."
    },
    "distance_km": 18.2,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Run: 30 phút ở Zone 2, pace 4:57/km. → Run: 8 phút ở Zone 3, pace 4:21/km. → Run: 3 phút ở Zone 1, pace 5:27/km. → Run: 8 phút ở Zone 3, pace 4:21/km. → Run: 3 phút ở Zone 1, pace 5:27/km. → Run: 8 phút ở Zone 3, pace 4:21/km. → Cool-down: 15 phút ở Zone 1, pace 5:27/km. Duy trì nhịp thở ổn định dưới ngưỡng AnT và hạ nhịp độ nếu xuất hiện hiện tượng thở dốc.",
    "target_pace": "4:57 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Recovery Run Thả Lỏng",
    "type": "Recovery",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 50.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.35
      }
    ],
    "rationale": "Chạy hoàn toàn chậm rãi để thả lỏng cơ xương khớp và chuẩn bị cho hai ngày leo dốc cuối tuần.",
    "fueling_tip": "Buổi tập dưới 75 phút: chỉ cần uống nước lọc mát bổ sung thêm chút chất điện giải.",
    "duration_minutes": 50.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 9.3,
      "hike_km": 0.0,
      "aerobic_minutes": 50.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 50.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 50.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.35
        }
      ],
      "description": "Run: 50 phút ở Zone 1, pace 5:21/km."
    },
    "distance_km": 9.3,
    "description": "Run: 50 phút ở Zone 1, pace 5:21/km. Chạy hoàn toàn chậm rãi để thả lỏng cơ xương khớp và chuẩn bị cho hai ngày leo dốc cuối tuần.",
    "target_pace": "5:21 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Dốc và Hill Bounding Tốc Độ",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "warmup",
        "pace_min_per_km": 5.4,
        "elevation_gain_m": 50
      },
      {
        "kind": "run",
        "duration_minutes": 70.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.6,
        "elevation_gain_m": 560
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "mountain",
        "pace_min_per_km": 3.8,
        "elevation_gain_m": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "zone": null,
        "setting": "mountain"
      },
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "cooldown",
        "pace_min_per_km": 5.5,
        "elevation_gain_m": 40
      }
    ],
    "rationale": "Dừng bài tập bứt tốc ngay khi công suất đẩy chân giảm sút nhằm bảo toàn thần kinh cơ.",
    "fueling_tip": "Buổi tập 124 phút: duy trì 45-50g Carbs mỗi giờ cùng 500-600ml nước chứa 450mg Sodium.",
    "duration_minutes": 124.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 18.4,
      "hike_km": 0.0,
      "aerobic_minutes": 101.6,
      "strength_minutes": 0.0,
      "passive_minutes": 22.4,
      "duration_minutes": 124.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 746.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "warmup",
          "pace_min_per_km": 5.4,
          "elevation_gain_m": 50
        },
        {
          "kind": "run",
          "duration_minutes": 70.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.6,
          "elevation_gain_m": 560
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "mountain",
          "pace_min_per_km": 3.8,
          "elevation_gain_m": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "zone": null,
          "setting": "mountain"
        },
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "cooldown",
          "pace_min_per_km": 5.5,
          "elevation_gain_m": 40
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km, D+ 50 m (ước tính). → Run: 70 phút ở Zone 2, pace 5:36/km, D+ 560 m (ước tính). → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Cool-down: 15 phút ở Zone 1, pace 5:30/km, D+ 40 m (ước tính)."
    },
    "distance_km": 18.4,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km, D+ 50 m (ước tính). → Run: 70 phút ở Zone 2, pace 5:36/km, D+ 560 m (ước tính). → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Run: 0.2 phút ở Zone 5, pace 3:48/km, D+ 12 m (ước tính). → Recovery: 2.8 phút. → Cool-down: 15 phút ở Zone 1, pace 5:30/km, D+ 40 m (ước tính). Dừng bài tập bứt tốc ngay khi công suất đẩy chân giảm sút nhằm bảo toàn thần kinh cơ.",
    "target_pace": "5:36 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 746.0,
    "grade_percent": 4.1,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Trail Long Run Mô Phỏng Độ Dốc Lớn",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 20.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "warmup",
        "pace_min_per_km": 5.45,
        "elevation_gain_m": 70
      },
      {
        "kind": "run",
        "duration_minutes": 95.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.75,
        "elevation_gain_m": 550
      },
      {
        "kind": "hike",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 9.5,
        "elevation_gain_m": 550
      },
      {
        "kind": "run",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.65,
        "elevation_gain_m": 90
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "role": "cooldown",
        "pace_min_per_km": 5.5,
        "elevation_gain_m": 20
      }
    ],
    "rationale": "Điều chỉnh nhịp bước ngắn khi leo dốc gắt và chủ động đi bộ để giữ nhịp tim trong ngưỡng an toàn.",
    "fueling_tip": "Buổi tập 215 phút: duy trì 60-80g Carbs mỗi giờ kết hợp 600-750ml nước và 600-750mg Sodium đều đặn.",
    "duration_minutes": 215.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 30.0,
      "hike_km": 4.7,
      "aerobic_minutes": 215.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 215.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 1280.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 20.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "warmup",
          "pace_min_per_km": 5.45,
          "elevation_gain_m": 70
        },
        {
          "kind": "run",
          "duration_minutes": 95.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.75,
          "elevation_gain_m": 550
        },
        {
          "kind": "hike",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 9.5,
          "elevation_gain_m": 550
        },
        {
          "kind": "run",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.65,
          "elevation_gain_m": 90
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "role": "cooldown",
          "pace_min_per_km": 5.5,
          "elevation_gain_m": 20
        }
      ],
      "description": "Warm-up: 20 phút ở Zone 1, pace 5:27/km, D+ 70 m (ước tính). → Run: 95 phút ở Zone 2, pace 5:45/km, D+ 550 m (ước tính). → Hike: 45 phút ở Zone 2, pace 9:30/km, D+ 550 m (ước tính). → Run: 45 phút ở Zone 2, pace 5:39/km, D+ 90 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 5:30/km, D+ 20 m (ước tính)."
    },
    "distance_km": 34.7,
    "description": "Warm-up: 20 phút ở Zone 1, pace 5:27/km, D+ 70 m (ước tính). → Run: 95 phút ở Zone 2, pace 5:45/km, D+ 550 m (ước tính). → Hike: 45 phút ở Zone 2, pace 9:30/km, D+ 550 m (ước tính). → Run: 45 phút ở Zone 2, pace 5:39/km, D+ 90 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 5:30/km, D+ 20 m (ước tính). Điều chỉnh nhịp bước ngắn khi leo dốc gắt và chủ động đi bộ để giữ nhịp tim trong ngưỡng an toàn.",
    "target_pace": "5:45 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 1280.0,
    "grade_percent": 3.7,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>
<details><summary>Captured baseline</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Build",
    "title": "Hill Sprints & Easy Aerobic Run",
    "type": "Interval",
    "duration_minutes": 80.0,
    "target_zone": "Zone 2",
    "target_hr_range": "135-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 16.1,
    "interval_reps": 8,
    "interval_rep_value": 12.0,
    "interval_rep_unit": "s",
    "elevation_gain_m": 260.0,
    "grade_percent": 1.7,
    "description": "Process: Khởi động 20 min Zone 1-2 trên đường bằng phẳng → 8 x 12s Hill Sprints dốc 12-15% với 3 min đi bộ thả lỏng hồi phục hoàn toàn giữa các rep → 45 min chạy tích lũy Zone 2 đường bằng nhấp nhô → Thả lỏng 5 min đi bộ. Overall: Buổi tập kết hợp kích hoạt thần kinh cơ bắp trên dốc tự nhiên cuối tuần và tích lũy thể tích hiếu khí. Đây là cơ hội tận dụng địa hình dốc ngoài Hà Nội để tối đa hóa tuyển dụng sợi cơ nhanh. Reason: Khởi động chu kỳ huấn luyện 8 tuần với kích thích neuromuscular mà không gây mỏi tim mạch hay tích tụ acid lactic toàn thân. Benefit: Tăng cường lực đẩy bàn chân, tuyển dụng sợi cơ FTa và chuẩn bị hệ gân cơ cho độ dốc lớn của giải đấu. Warning: Dừng ngay lập tức nếu cảm thấy căng cứng gân gót hoặc cơ bắp chân; các hiệp sprint phải thực hiện với độ dốc cao và nghỉ đủ 3 phút để nạp lại hoàn toàn ATP.",
    "fueling_tip": "Buổi tập trên 75 phút: chuẩn bị 500ml nước chứa 300mg sodium, nạp 30g carbs (1 gói gel) vào phút thứ 40 để duy trì đường huyết ổn định.",
    "treadmill_incline": "0",
    "treadmill_speed": "0"
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Build",
    "title": "Trail Long Run & Power Hiking Simulation",
    "type": "Long Run",
    "duration_minutes": 160.0,
    "target_zone": "Zone 2",
    "target_hr_range": "138-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 32.2,
    "elevation_gain_m": 1250.0,
    "grade_percent": 5.2,
    "description": "Process: Khởi động 15 min chạy nhẹ chân dốc Zone 1 → Chạy ổn định 130 min Zone 2 trên địa hình trail đồi núi kết hợp kỹ thuật power hiking bằng gậy ở các đoạn dốc trên 12% và kiểm soát nhịp tim dưới AeT → Thả lỏng 15 min đi bộ nhẹ nhàng chân dốc. Overall: Bài chạy dài trail chuyên biệt mô phỏng độ dốc gắt của giải đấu 76K tại khu vực núi ngoại thành. Tập trung giữ nhịp tim dưới AeT và rèn luyện kỹ thuật sải bước leo dốc bằng gậy. Reason: Tận dụng ngày chủ nhật tại địa hình núi để thích nghi hệ cơ xương khớp với độ dốc tích lũy lớn và kiểm tra khả năng nạp năng lượng liên tục. Benefit: Nâng cao dung tích hiếu khí vùng đồi núi, củng cố sức bền gân gối và cơ đùi trước trước áp lực co cơ lệch tâm khi đổ dốc. Warning: Giữ nhịp tim tuyệt đối dưới 154 bpm trên các đoạn leo dốc; chuyển ngay sang power hiking nếu nhịp tim chạm ngưỡng AnT.",
    "fueling_tip": "Thời lượng > 150 phút: nạp 60-70g carbs/giờ kết hợp 500-700ml nước hòa tan 500mg sodium mỗi giờ. Bắt đầu nạp gel hoặc bột năng lượng từ phút thứ 30 và duy trì đều đặn mỗi 30-40 phút.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Build",
    "title": "Easy Recovery Run Road",
    "type": "Recovery",
    "duration_minutes": 60.0,
    "target_zone": "Zone 1",
    "target_hr_range": "120-138 bpm",
    "target_pace": "5:47 - 5:10 /km",
    "distance_km": 10.9,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Khởi động 5 min đi bộ và xoay khớp nhẹ nhàng → Chạy liên tục 50 min Zone 1 trên đường nhựa bằng phẳng đô thị → Thả lỏng 5 min đi bộ và giãn cơ tĩnh. Overall: Bài chạy phục hồi hoàn toàn bằng phẳng tại Hà Nội nhằm thúc đẩy tuần hoàn máu sau khối lượng dốc lớn cuối tuần. Giữ nhịp độ cực kỳ thư giãn và thả lỏng toàn bộ cơ bắp. Reason: Xả mỏi cơ bắp và hỗ trợ đào thải chất chuyển hóa mà không gây thêm tải trọng chấn động lên gân khớp. Benefit: Tăng lưu lượng máu mao mạch tới các cơ chi dưới đang chịu tổn thương vi mô, đẩy nhanh quá trình tái tạo glycogen. Warning: Không chạy theo tốc độ của người khác; nếu chân cảm thấy nặng nề, chủ động giảm tốc độ về dải cuối Zone 1.",
    "fueling_tip": "Buổi tập < 75 phút ở cường độ Zone 1: chỉ cần 400-500ml nước lọc; không cần bổ sung carb ngoại sinh trong buổi tập.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Build",
    "title": "Sub-Threshold Tempo Intervals Road",
    "type": "Tempo",
    "duration_minutes": 75.0,
    "target_zone": "Zone 3",
    "target_hr_range": "158-168 bpm",
    "target_pace": "4:45 - 4:20 /km",
    "distance_km": 16.5,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Khởi động 15 min chạy nhẹ Zone 1-2 → 3 x 10 min chạy Zone 3 Sub-Threshold (HR 158-168 bpm, dưới AnT 171 bpm), 3 min chạy bộ thả lỏng Zone 1 giữa các hiệp → Thả lỏng 15 min chạy nhẹ Zone 1. Overall: Bài tập sức bền tốc độ trên đường bằng phẳng nội thành Hà Nội, nhắm vào việc nâng cao ngưỡng AnT mà không kích hoạt cortisol quá mức. Giữ cơ thể kiểm soát hoàn toàn nhịp thở. Reason: Tối ưu hóa chuyển hóa lactate dưới ngưỡng AnT theo triết lý Uphill Athlete, giúp cơ bắp sử dụng mỡ hiệu quả ở dải tốc độ cao. Benefit: Nâng cao vận tốc chạy ổn định, cải thiện khả năng tái hấp thu lactate của sợi cơ co giật chậm FTa. Warning: Tuyệt đối không đẩy nhịp tim vượt ngưỡng AnT (171 bpm) để tránh biến bài tập thành bài kỵ khí Zone 4 quá tải.",
    "fueling_tip": "Thời lượng 75 phút với phân đoạn chất lượng: uống 500ml nước điện giải (300mg sodium) và nạp 1 gói gel chứa 30g carbs ở phút thứ 35 trước khi bước vào hiệp biến tốc cuối cùng.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Build",
    "title": "Scheduled Rest Day",
    "type": "Rest",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "target_hr_range": "47-70 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Nghỉ ngơi hoàn toàn không vận động nặng → Giãn cơ nhẹ hoặc đi dạo thả lỏng thư giãn hệ thần kinh. Overall: Ngày nghỉ ngơi phục hồi theo lịch cố định trong tuần của vận động viên. Tạo điều kiện cho cơ bắp tái tổng hợp năng lượng và cân bằng nội tiết tố. Reason: Cung cấp thời gian nghỉ ngơi thiết yếu để hấp thụ khối lượng tập của các ngày trước và sẵn sàng cho buổi ME sáng thứ năm. Benefit: Hạ nồng độ cortisol huyết thanh, giảm viêm mô liên kết và bảo tồn sức bền thần kinh trung ương. Warning: Tránh đứng lâu hoặc làm việc nặng thể chất gây mỏi chân; đảm bảo ngủ đủ ít nhất 8 tiếng trong đêm.",
    "fueling_tip": "Ngày nghỉ hoàn toàn: tập trung vào chế độ ăn cân bằng dinh dưỡng, giàu protein chất lượng cao (1.6-1.8g/kg) và uống đủ 2-2.5 lít nước trong ngày.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Build",
    "title": "Bodyweight Muscular Endurance Circuit",
    "type": "Muscular Endurance",
    "duration_minutes": 50.0,
    "target_zone": "Zone 2",
    "target_hr_range": "130-150 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Khởi động 10 min khớp động và kích hoạt cơ mông → 10 reps Split Jump Squats, 15s transition → 10 reps Squat Jumps, 15s transition → 10 reps mỗi chân Box Step-Ups trên bậc thềm cao 75% đầu gối, 15s transition → 10 reps mỗi chân Front Lunges, 60s nghỉ giữa vòng (thực hiện liên tục 6 rounds) → Thả lỏng 5 min giãn cơ cẳng chân và đùi. Overall: Chuỗi bài tập Muscular Endurance thể trọng tại nhà không sử dụng tạ, nhắm vào việc xây dựng sức bền cơ học cục bộ cho đùi trước và mông. Cảm giác mỏi cơ ngoại vi sâu nhưng nhịp tim kiểm soát dưới AeT. Reason: Thay thế cho việc thiếu địa hình dốc trong tuần tại Hà Nội, xây dựng khung gầm cơ bắp chống sụp đổ khớp gối khi leo dốc. Benefit: Tăng mật độ ty thể và khả năng kháng mỏi cơ học của các sợi cơ co giật nhanh FTa trong điều kiện thiếu oxy cục bộ. Warning: Dừng tập hoặc chuyển sang động tác chậm nếu tư thế tiếp đất bị sụp sập khớp gối; giữ lưng thẳng và kiểm soát chuyển động khi tiếp đất.",
    "fueling_tip": "Buổi tập < 75 phút: nhấp từng ngụm nhỏ nước lọc pha khoáng nhẹ (khoảng 350-500ml); không cần bổ sung đường.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Build",
    "title": "Aerobic Base Run Urban Road",
    "type": "Easy",
    "duration_minutes": 70.0,
    "target_zone": "Zone 2",
    "target_hr_range": "138-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 14.1,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Khởi động 10 min chạy nhẹ Zone 1 → Chạy ổn định 55 min Zone 2 trên cung đường bằng phẳng đô thị → Thả lỏng 5 min đi bộ thư giãn. Overall: Buổi chạy nền tảng hiếu khí phẳng duy trì thể tích tuần và hỗ trợ lưu thông máu sau bài tập ME ngày thứ Năm. Giữ tốc độ mượt mà và sải chân ổn định. Reason: Duy trì tần suất kích thích hiếu khí mà không gây quá tải cơ học, chuẩn bị trạng thái sung mãn cho 2 buổi tập cuối tuần có dốc. Benefit: Tăng cường quá trình chuyển hóa lipid, củng cố dung tích mao mạch của cơ bắp vận động. Warning: Kiểm soát nhịp tim không vượt quá 154 bpm; nếu thời tiết oi bức tại Hà Nội làm nhịp tim trôi lên cao (cardiac drift), chủ động giảm pace.",
    "fueling_tip": "Thời lượng 70 phút: uống 400-500ml nước có bổ sung 250mg natri để bù lượng mồ hôi thất thoát do độ ẩm môi trường.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Build",
    "title": "Mountain Vert Accumulation & Strides",
    "type": "Easy",
    "duration_minutes": 105.0,
    "target_zone": "Zone 2",
    "target_hr_range": "138-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 21.1,
    "elevation_gain_m": 850.0,
    "grade_percent": 5.1,
    "description": "Process: Khởi động 15 min chạy phẳng chân núi Zone 1 → 80 min chạy liên tục Zone 2 trên đường trail đồi núi kết hợp leo dốc tự nhiên nhịp nhàng → 4 x 15s Strides sải chân dài trên đoạn đường phẳng chân dốc, 45s đi bộ hồi phục → Thả lỏng 6 min đi bộ hạ nhiệt. Overall: Buổi chạy trail tích lũy độ cao tại vùng núi ngoại ô, kết hợp các đoạn mở sải chân ngắn cuối bài để duy trì độ đàn hồi của cơ bắp. Giữ nhịp tim kiểm soát dưới AeT trên các đoạn dốc. Reason: Tích lũy khối lượng leo dốc cuối tuần đầu tiên của chu kỳ, kích hoạt chuỗi cơ sau và làm quen dần với độ dốc trung bình của cuộc thi. Benefit: Tăng cường độ thích ứng gân Achilles và cơ dép với độ dốc thực tế, cải thiện hiệu suất chuyển hóa cơ bắp. Warning: Chú ý quan sát mặt đường mòn tránh trượt ngã trên rễ cây hay đá dăm; giữ thân trên hơi hướng về phía trước khi leo dốc.",
    "fueling_tip": "Thời lượng 105 phút trên địa hình đồi núi: sử dụng 500-600ml nước/giờ chứa 400mg sodium, nạp 40-50g carbs/giờ bằng gel hoặc thanh năng lượng.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Build",
    "title": "Trail Long Run Mountain Specificity",
    "type": "Long Run",
    "duration_minutes": 175.0,
    "target_zone": "Zone 2",
    "target_hr_range": "138-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 35.2,
    "elevation_gain_m": 1350.0,
    "grade_percent": 5.3,
    "description": "Process: Khởi động 15 min đi bộ và chạy nhẹ Zone 1 → 145 min chạy dài Zone 2 địa hình trail núi dốc, áp dụng luân phiên chạy bước ngắn trên dốc vừa và power hiking bằng gậy trên dốc gắt (>15%), giữ nhịp tim ổn định 138-154 bpm → Thả lỏng 15 min đi bộ phẳng thả lỏng chân. Overall: Bài chạy dài trọng điểm của tuần trên địa hình núi mô phỏng địa hình giải đấu 76K. Trọng tâm là rèn luyện khả năng phân phối sức bền trên dốc lớn và rèn luyện đường tiêu hóa. Reason: Đây là buổi tập tích lũy độ dốc và khối lượng chính trong tuần nhằm mô phỏng đặc thù leo dốc kỹ thuật cao của cuộc thi mục tiêu. Benefit: Gia tăng sức bền cơ học cục bộ, thích nghi màng sợi cơ đùi trước trước lực co cơ lệch tâm khi đổ dốc liên tục, tối ưu dung tích chứa glycogen. Warning: Không bung sức chạy nhanh khi đổ dốc để bảo vệ khớp gối và cơ tứ đầu đùi; duy trì nhịp thở đều đặn và kiểm tra dây giày cẩn thận.",
    "fueling_tip": "Thời lượng 175 phút: nạp 60-80g carbs/giờ bắt đầu từ phút thứ 30. Kết hợp sử dụng 600-750ml nước có hòa tan 500-700mg sodium mỗi giờ để phòng ngừa chuột rút cơ bắp.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>

## scheduler_fixture_vietnam_urban_sub_elite_treadmill

- Gemini+KB latency: **19.1s** (baseline: 23.1s)
- Tier attribution: **gemini**
- New: `{"workout_count": 14, "types": {"Easy": 8, "Rest": 2, "Interval": 2, "Long Run": 2}, "me_sessions": 0, "me_looks_like_circuit": null}`
- Ref: `{"workout_count": 9, "types": {"Easy": 3, "Long Run": 2, "Recovery": 1, "Muscular Endurance": 1, "Rest": 1, "Tempo": 1}, "me_sessions": 1, "me_looks_like_circuit": false}`
- Tier: **sub_elite** (expected sub_elite)
- Week-2 volume: **103.1 km** (expected 92-119)
- Context metrics v2: `{"prompt_identity": {"name": "plan_generation", "version": "6", "source": "langfuse", "sha256": "7a19da8c7e374c0247484ad22bc29703f5b88a3ed345899bec520b580ae36de7"}, "checks": {"arithmetic": true, "access": true, "intensity_accounting": true, "progression": true}, "unavailable_checks": [], "weeks": {"1": {"run_km": 90.0, "hike_km": 8.2, "aerobic_minutes": 571.2, "strength_minutes": 20.0, "passive_minutes": 16.8, "long_run_locomotion_time_share": 0.315, "long_run_distance_share": 0.294, "weekend_locomotion_time_share": 0.508}, "2": {"run_km": 94.2, "hike_km": 8.9, "aerobic_minutes": 596.6, "strength_minutes": 20.0, "passive_minutes": 22.4, "long_run_locomotion_time_share": 0.31, "long_run_distance_share": 0.293, "weekend_locomotion_time_share": 0.511}}, "block_engines": null, "internal_disclosure": false}`

<details><summary>Gemini+KB output</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Easy Run mở đầu tuần",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 75.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.0
      }
    ],
    "fueling_tip": "Nước lọc kèm viên điện giải nhẹ (khoảng 200-300mg sodium) là đủ cho bài chạy 75 phút ở Zone 2.",
    "duration_minutes": 75.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 15.0,
      "hike_km": 0.0,
      "aerobic_minutes": 75.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 75.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 75.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.0
        }
      ],
      "description": "Run: 75 phút ở Zone 2, pace 5:00/km."
    },
    "distance_km": 15.0,
    "description": "Run: 75 phút ở Zone 2, pace 5:00/km.",
    "target_pace": "5:00 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Treadmill leo dốc và rèn sức mạnh",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.4,
        "role": "warmup"
      },
      {
        "kind": "hike",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "pace_min_per_km": 10.0,
        "incline_pct": 12
      },
      {
        "kind": "strength",
        "duration_minutes": 10.0,
        "setting": "indoor",
        "exercise": {
          "name": "Bodyweight Squats",
          "sets": 4,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "bodyweight"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 10.0,
        "setting": "indoor",
        "exercise": {
          "name": "Step-Ups",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "box"
          ]
        }
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.5,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Bổ sung 400-500ml nước chứa 300mg sodium trong suốt buổi tập máy và bổ trợ.",
    "duration_minutes": 90.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 4.6,
      "hike_km": 4.5,
      "aerobic_minutes": 70.0,
      "strength_minutes": 20.0,
      "passive_minutes": 0.0,
      "duration_minutes": 90.0,
      "estimated_indoor_ascent_m": 536.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.4,
          "role": "warmup"
        },
        {
          "kind": "hike",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "pace_min_per_km": 10.0,
          "incline_pct": 12
        },
        {
          "kind": "strength",
          "duration_minutes": 10.0,
          "setting": "indoor",
          "exercise": {
            "name": "Bodyweight Squats",
            "sets": 4,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "bodyweight"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 10.0,
          "setting": "indoor",
          "exercise": {
            "name": "Step-Ups",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "box"
            ]
          }
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.5,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Hike: 45 phút ở Zone 2, pace 10:00/km, Treadmill 12%. → Strength: 10 phút, Bodyweight Squats: 4 x 6, 120 s nghỉ giữa các set. → Strength: 10 phút, Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:30/km. → D+ trong nhà (ước tính): 536 m."
    },
    "distance_km": 9.1,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Hike: 45 phút ở Zone 2, pace 10:00/km, Treadmill 12%. → Strength: 10 phút, Bodyweight Squats: 4 x 6, 120 s nghỉ giữa các set. → Strength: 10 phút, Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:30/km. → D+ trong nhà (ước tính): 536 m.",
    "target_pace": "10:00 /km",
    "treadmill_incline": "12",
    "treadmill_speed": "6",
    "elevation_gain_m": 536.0,
    "grade_percent": 5.9,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Nghỉ ngơi phục hồi",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Ăn uống đủ chất với carbohydrate phức hợp và protein để chuẩn bị cho chuỗi ngày tiếp theo.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Treadmill Hill Sprints và Zone 2",
    "type": "Interval",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 20.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.8,
        "incline_pct": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.8,
        "incline_pct": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.8,
        "incline_pct": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.8,
        "incline_pct": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.8,
        "incline_pct": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.8,
        "incline_pct": 12
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.9
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.4,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Uống 400-500ml nước điện giải. Không cần nạp gel do tổng thời lượng dưới 95 phút và cường độ cao chỉ kéo dài từng đợt ngắn.",
    "duration_minutes": 93.0,
    "target_zone": "Zone 5",
    "prescription": {
      "run_km": 15.1,
      "hike_km": 0.0,
      "aerobic_minutes": 76.2,
      "strength_minutes": 0.0,
      "passive_minutes": 16.8,
      "duration_minutes": 93.0,
      "estimated_indoor_ascent_m": 38.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 20.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.8,
          "incline_pct": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.8,
          "incline_pct": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.8,
          "incline_pct": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.8,
          "incline_pct": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.8,
          "incline_pct": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.8,
          "incline_pct": 12
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.9
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.4,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 20 phút ở Zone 1, pace 5:18/km. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 45 phút ở Zone 2, pace 4:54/km. → Cool-down: 10 phút ở Zone 1, pace 5:24/km. → D+ trong nhà (ước tính): 38 m."
    },
    "distance_km": 15.1,
    "description": "Warm-up: 20 phút ở Zone 1, pace 5:18/km. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:48/km, Treadmill 12%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 45 phút ở Zone 2, pace 4:54/km. → Cool-down: 10 phút ở Zone 1, pace 5:24/km. → D+ trong nhà (ước tính): 38 m.",
    "target_pace": "3:48 /km",
    "treadmill_incline": "12",
    "treadmill_speed": "15.8",
    "elevation_gain_m": 38.0,
    "grade_percent": 0.3,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Easy Run thả lỏng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 60.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.3
      }
    ],
    "fueling_tip": "Uống nước theo nhu cầu khát, 200-300mg sodium nếu trời nóng ẩm tại TP.HCM.",
    "duration_minutes": 60.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 11.3,
      "hike_km": 0.0,
      "aerobic_minutes": 60.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 60.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 60.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.3
        }
      ],
      "description": "Run: 60 phút ở Zone 1, pace 5:18/km."
    },
    "distance_km": 11.3,
    "description": "Run: 60 phút ở Zone 1, pace 5:18/km.",
    "target_pace": "5:18 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Aerobic Run địa hình đồi dốc",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.0,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 85.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.8,
        "elevation_gain_m": 700
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.2,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Nạp 40-50g Carbs mỗi giờ cùng 500ml nước có 400mg sodium để duy trì thể lực trên dốc.",
    "duration_minutes": 110.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 18.8,
      "hike_km": 0.0,
      "aerobic_minutes": 110.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 110.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 700.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.0,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 85.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.8,
          "elevation_gain_m": 700
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.2,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 85 phút ở Zone 2, pace 5:48/km, D+ 700 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km."
    },
    "distance_km": 18.8,
    "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 85 phút ở Zone 2, pace 5:48/km, D+ 700 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km.",
    "target_pace": "5:48 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 700.0,
    "grade_percent": 3.7,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run leo núi tích lũy độ cao",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.0,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 120.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.7,
        "elevation_gain_m": 900
      },
      {
        "kind": "hike",
        "duration_minutes": 35.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 9.5,
        "elevation_gain_m": 250
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.2,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Với buổi tập trên 150 phút, nạp 60g Carbs mỗi giờ qua gel hoặc bột hòa tan, bổ sung 500-600ml nước và 500mg sodium mỗi giờ.",
    "duration_minutes": 180.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 25.2,
      "hike_km": 3.7,
      "aerobic_minutes": 180.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 180.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 1150.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.0,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 120.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.7,
          "elevation_gain_m": 900
        },
        {
          "kind": "hike",
          "duration_minutes": 35.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 9.5,
          "elevation_gain_m": 250
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.2,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 120 phút ở Zone 2, pace 5:42/km, D+ 900 m (ước tính). → Hike: 35 phút ở Zone 1, pace 9:30/km, D+ 250 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km."
    },
    "distance_km": 28.9,
    "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 120 phút ở Zone 2, pace 5:42/km, D+ 900 m (ước tính). → Hike: 35 phút ở Zone 1, pace 9:30/km, D+ 250 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km.",
    "target_pace": "5:42 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 1150.0,
    "grade_percent": 4.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Easy Run phục hồi Zone 1",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 70.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.3
      }
    ],
    "fueling_tip": "Uống 400ml nước lọc kèm chất điện giải cơ bản sau chạy để phục hồi bài cuối tuần.",
    "duration_minutes": 70.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 13.2,
      "hike_km": 0.0,
      "aerobic_minutes": 70.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 70.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 70.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.3
        }
      ],
      "description": "Run: 70 phút ở Zone 1, pace 5:18/km."
    },
    "distance_km": 13.2,
    "description": "Run: 70 phút ở Zone 1, pace 5:18/km.",
    "target_pace": "5:18 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Treadmill Incline và Gym Strength",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.4,
        "role": "warmup"
      },
      {
        "kind": "hike",
        "duration_minutes": 50.0,
        "zone": "Zone 2",
        "setting": "treadmill",
        "pace_min_per_km": 9.8,
        "incline_pct": 13
      },
      {
        "kind": "strength",
        "duration_minutes": 10.0,
        "setting": "indoor",
        "exercise": {
          "name": "Barbell Deadlifts",
          "sets": 4,
          "reps": 5,
          "rest_seconds": 150.0,
          "equipment": [
            "weights"
          ]
        }
      },
      {
        "kind": "strength",
        "duration_minutes": 10.0,
        "setting": "indoor",
        "exercise": {
          "name": "Weighted Step-Ups",
          "sets": 3,
          "reps": 6,
          "rest_seconds": 120.0,
          "equipment": [
            "box",
            "weights"
          ]
        }
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.5,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Bổ sung 400-500ml nước có 300-400mg sodium trong buổi tập để bù mồ hôi trong phòng gym.",
    "duration_minutes": 95.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 4.6,
      "hike_km": 5.1,
      "aerobic_minutes": 75.0,
      "strength_minutes": 20.0,
      "passive_minutes": 0.0,
      "duration_minutes": 95.0,
      "estimated_indoor_ascent_m": 658.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.4,
          "role": "warmup"
        },
        {
          "kind": "hike",
          "duration_minutes": 50.0,
          "zone": "Zone 2",
          "setting": "treadmill",
          "pace_min_per_km": 9.8,
          "incline_pct": 13
        },
        {
          "kind": "strength",
          "duration_minutes": 10.0,
          "setting": "indoor",
          "exercise": {
            "name": "Barbell Deadlifts",
            "sets": 4,
            "reps": 5,
            "rest_seconds": 150.0,
            "equipment": [
              "weights"
            ]
          }
        },
        {
          "kind": "strength",
          "duration_minutes": 10.0,
          "setting": "indoor",
          "exercise": {
            "name": "Weighted Step-Ups",
            "sets": 3,
            "reps": 6,
            "rest_seconds": 120.0,
            "equipment": [
              "box",
              "weights"
            ]
          }
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.5,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Hike: 50 phút ở Zone 2, pace 9:48/km, Treadmill 13%. → Strength: 10 phút, Barbell Deadlifts: 4 x 5, 150 s nghỉ giữa các set. → Strength: 10 phút, Weighted Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:30/km. → D+ trong nhà (ước tính): 658 m."
    },
    "distance_km": 9.7,
    "description": "Warm-up: 15 phút ở Zone 1, pace 5:24/km. → Hike: 50 phút ở Zone 2, pace 9:48/km, Treadmill 13%. → Strength: 10 phút, Barbell Deadlifts: 4 x 5, 150 s nghỉ giữa các set. → Strength: 10 phút, Weighted Step-Ups: 3 x 6, 120 s nghỉ giữa các set. → Cool-down: 10 phút ở Zone 1, pace 5:30/km. → D+ trong nhà (ước tính): 658 m.",
    "target_pace": "9:48 /km",
    "treadmill_incline": "13",
    "treadmill_speed": "6.1",
    "elevation_gain_m": 658.0,
    "grade_percent": 6.8,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Nghỉ ngơi hoàn toàn",
    "type": "Rest",
    "segments": [
      {
        "kind": "rest",
        "duration_minutes": 0.0,
        "setting": "indoor"
      }
    ],
    "fueling_tip": "Duy trì uống đủ nước và nạp đều đặn các bữa ăn giàu dưỡng chất để cơ thể tái tạo mô cơ.",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "prescription": {
      "run_km": 0.0,
      "hike_km": 0.0,
      "aerobic_minutes": 0.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 0.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "rest",
          "duration_minutes": 0.0,
          "setting": "indoor"
        }
      ],
      "description": "Nghỉ."
    },
    "distance_km": 0.0,
    "description": "Nghỉ.",
    "target_pace": "",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Treadmill Hill Sprints và Aerobic Run",
    "type": "Interval",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 20.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.3,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 0.2,
        "zone": "Zone 5",
        "setting": "treadmill",
        "pace_min_per_km": 3.7,
        "incline_pct": 14
      },
      {
        "kind": "recovery",
        "duration_minutes": 2.8,
        "setting": "treadmill"
      },
      {
        "kind": "run",
        "duration_minutes": 45.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 4.9
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.4,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Bổ sung 400-600ml nước với 300mg sodium. Nghỉ trọn vẹn giữa các lần sprint trên treadmill dốc.",
    "duration_minutes": 99.0,
    "target_zone": "Zone 5",
    "prescription": {
      "run_km": 15.2,
      "hike_km": 0.0,
      "aerobic_minutes": 76.6,
      "strength_minutes": 0.0,
      "passive_minutes": 22.4,
      "duration_minutes": 99.0,
      "estimated_indoor_ascent_m": 60.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 20.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.3,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 0.2,
          "zone": "Zone 5",
          "setting": "treadmill",
          "pace_min_per_km": 3.7,
          "incline_pct": 14
        },
        {
          "kind": "recovery",
          "duration_minutes": 2.8,
          "setting": "treadmill"
        },
        {
          "kind": "run",
          "duration_minutes": 45.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 4.9
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.4,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 20 phút ở Zone 1, pace 5:18/km. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 45 phút ở Zone 2, pace 4:54/km. → Cool-down: 10 phút ở Zone 1, pace 5:24/km. → D+ trong nhà (ước tính): 60 m."
    },
    "distance_km": 15.2,
    "description": "Warm-up: 20 phút ở Zone 1, pace 5:18/km. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 0.2 phút ở Zone 5, pace 3:42/km, Treadmill 14%. → Recovery: 2.8 phút, Treadmill 0%. → Run: 45 phút ở Zone 2, pace 4:54/km. → Cool-down: 10 phút ở Zone 1, pace 5:24/km. → D+ trong nhà (ước tính): 60 m.",
    "target_pace": "3:42 /km",
    "treadmill_incline": "14",
    "treadmill_speed": "16.2",
    "elevation_gain_m": 60.0,
    "grade_percent": 0.4,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Easy Run bằng phẳng",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 70.0,
        "zone": "Zone 2",
        "setting": "flat_outdoor",
        "pace_min_per_km": 5.0
      }
    ],
    "fueling_tip": "Nước lọc thông thường hoặc bổ sung nhẹ 200mg sodium nếu thời tiết oi bức.",
    "duration_minutes": 70.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 14.0,
      "hike_km": 0.0,
      "aerobic_minutes": 70.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 70.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 0.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 70.0,
          "zone": "Zone 2",
          "setting": "flat_outdoor",
          "pace_min_per_km": 5.0
        }
      ],
      "description": "Run: 70 phút ở Zone 2, pace 5:00/km."
    },
    "distance_km": 14.0,
    "description": "Run: 70 phút ở Zone 2, pace 5:00/km.",
    "target_pace": "5:00 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Aerobic Run tích lũy độ dốc",
    "type": "Easy",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.0,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 95.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.7,
        "elevation_gain_m": 800
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.2,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Nạp 40-50g Carbs mỗi giờ cùng 500ml nước pha 400-500mg sodium khi chạy dốc dài.",
    "duration_minutes": 120.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 20.8,
      "hike_km": 0.0,
      "aerobic_minutes": 120.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 120.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 800.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.0,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 95.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.7,
          "elevation_gain_m": 800
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.2,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 95 phút ở Zone 2, pace 5:42/km, D+ 800 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km."
    },
    "distance_km": 20.8,
    "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 95 phút ở Zone 2, pace 5:42/km, D+ 800 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km.",
    "target_pace": "5:42 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 800.0,
    "grade_percent": 3.8,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run kỹ thuật mô phỏng địa hình",
    "type": "Long Run",
    "segments": [
      {
        "kind": "run",
        "duration_minutes": 15.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.0,
        "role": "warmup"
      },
      {
        "kind": "run",
        "duration_minutes": 125.0,
        "zone": "Zone 2",
        "setting": "mountain",
        "pace_min_per_km": 5.6,
        "elevation_gain_m": 950
      },
      {
        "kind": "hike",
        "duration_minutes": 35.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 9.2,
        "elevation_gain_m": 300
      },
      {
        "kind": "run",
        "duration_minutes": 10.0,
        "zone": "Zone 1",
        "setting": "mountain",
        "pace_min_per_km": 6.2,
        "role": "cooldown"
      }
    ],
    "fueling_tip": "Thời lượng 185 phút: thực hành chiến thuật nạp dinh dưỡng thi đấu với 60-70g Carbs mỗi giờ, 600ml nước và 600mg sodium mỗi giờ.",
    "duration_minutes": 185.0,
    "target_zone": "Zone 2",
    "prescription": {
      "run_km": 26.4,
      "hike_km": 3.8,
      "aerobic_minutes": 185.0,
      "strength_minutes": 0.0,
      "passive_minutes": 0.0,
      "duration_minutes": 185.0,
      "estimated_indoor_ascent_m": 0.0,
      "estimated_outdoor_ascent_m": 1250.0,
      "segments": [
        {
          "kind": "run",
          "duration_minutes": 15.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.0,
          "role": "warmup"
        },
        {
          "kind": "run",
          "duration_minutes": 125.0,
          "zone": "Zone 2",
          "setting": "mountain",
          "pace_min_per_km": 5.6,
          "elevation_gain_m": 950
        },
        {
          "kind": "hike",
          "duration_minutes": 35.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 9.2,
          "elevation_gain_m": 300
        },
        {
          "kind": "run",
          "duration_minutes": 10.0,
          "zone": "Zone 1",
          "setting": "mountain",
          "pace_min_per_km": 6.2,
          "role": "cooldown"
        }
      ],
      "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 125 phút ở Zone 2, pace 5:36/km, D+ 950 m (ước tính). → Hike: 35 phút ở Zone 1, pace 9:12/km, D+ 300 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km."
    },
    "distance_km": 30.2,
    "description": "Warm-up: 15 phút ở Zone 1, pace 6:00/km. → Run: 125 phút ở Zone 2, pace 5:36/km, D+ 950 m (ước tính). → Hike: 35 phút ở Zone 1, pace 9:12/km, D+ 300 m (ước tính). → Cool-down: 10 phút ở Zone 1, pace 6:12/km.",
    "target_pace": "5:36 /km",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "elevation_gain_m": 1250.0,
    "grade_percent": 4.1,
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>
<details><summary>Captured baseline</summary>

```json
[
  {
    "week_number": 1,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Easy Run Địa Hình & Hill Strides",
    "type": "Easy",
    "duration_minutes": 80.0,
    "target_zone": "Zone 2",
    "target_hr_range": "140-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 16.1,
    "elevation_gain_m": 450.0,
    "grade_percent": 2.9,
    "description": "Process: Warm up 15 min chạy nhẹ Zone 1 trên trail bằng phẳng → Chạy liên tục 55 min Zone 2 kiểm soát nhịp tim dưới AeT 154 bpm qua các đoạn dốc thoai thoải → 6 x 15s Hill Strides dốc 8-10% tập trung guồng chân và đẩy hông, đi bộ thả dốc 45s giữa mỗi rep → Cool down 5 min thả lỏng nhẹ nhàng. Overall: Buổi chạy khai cuộc trên địa hình đồi núi thực tế nhằm làm quen lại với phản lực mặt đường trail và kích hoạt hệ thần kinh. Tải nạp ở mức nhẹ nhàng, tích lũy nền tảng hiếu khí mà không gây stress hệ cơ xương. Reason: Bắt đầu plan ngắn 8 tuần sau giai đoạn duy trì khối lượng 108 km/tuần, mở đầu chu kỳ chuyển tiếp địa hình cuối tuần. Benefit: Tăng cường tư thế vận động đặc thù trên đường mòn, cải thiện khả năng tuyển mộ sợi cơ nhanh mà không làm tăng nồng độ lactate. Warning: Kiểm soát chặt chẽ nhịp tim trên các đoạn dốc, chủ động chuyển sang đi bộ nhanh nếu HR tiệm cận 154 bpm.",
    "fueling_tip": "Buổi tập 80 phút: Chuẩn bị 500-600ml nước kèm 300mg sodium; bổ sung 1 gói gel năng lượng (khoảng 30g carbs) ở phút 45 để duy trì đường huyết ổn định.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 1,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Leo Dốc Kỹ Thuật & Power Hiking",
    "type": "Long Run",
    "duration_minutes": 150.0,
    "target_zone": "Zone 2",
    "target_hr_range": "135-152 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 30.2,
    "elevation_gain_m": 1400.0,
    "grade_percent": 4.8,
    "description": "Process: Khởi động khớp cổ chân và gối 10 min tại chân dốc → Chạy bền 130 min Zone 2 luân phiên: chạy thả lỏng trên đoạn bằng/dốc xuống nhẹ và chuyển sang power hiking nhịp nhàng dùng gậy trên các đoạn dốc >12% → Cool down 10 min đi bộ thả lỏng cơ bắp trên nền phẳng. Overall: Bài Long Run mở màn mô phỏng trực tiếp tỷ lệ dốc lớn của giải Synthetic 76K trên đường mòn tự nhiên. Trọng tâm là sự bền bỉ của cơ bắp chi dưới và kỹ thuật hiking tiết kiệm năng lượng. Reason: Tận dụng duy nhất hai ngày cuối tuần được tiếp cận núi dốc để xây dựng sức bền đặc thù và làm quen tải dốc thực tế. Benefit: Tăng sinh ty thể trong sợi cơ bền, phát triển khả năng chịu lực nén lệch tâm của cơ đùi trước khi đổ dốc. Warning: Giữ nhịp tim tuyệt đối dưới 154 bpm khi power hiking leo dốc; tiếp đất bước ngắn khi xuống dốc để bảo vệ khớp gối.",
    "fueling_tip": "Buổi tập 150 phút: Tiêu thụ 40-50g carbs mỗi giờ thông qua gel và điện giải; nạp 500-650ml nước/giờ chứa 400-500mg sodium để hạn chế chuột rút cơ bắp.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Monday",
    "phase": "Base",
    "title": "Recovery Run Đường Phẳng",
    "type": "Recovery",
    "duration_minutes": 50.0,
    "target_zone": "Zone 1",
    "target_hr_range": "120-138 bpm",
    "target_pace": "5:47 - 5:10 /km",
    "distance_km": 9.1,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: 5 min đi bộ tăng dần nhịp tim → 40 min chạy thả lỏng hoàn toàn Zone 1 trên đường nhựa phẳng đô thị → 5 min giãn cơ bắp chân và gân kheo. Overall: Bài chạy phục hồi chủ động cự ly ngắn giúp đào thải ứ trệ chuyển hóa sau khối lượng dốc lớn cuối tuần trước. Duy trì bước chạy êm và nhịp thở đàm thoại trôi chảy. Reason: Giảm thiểu chấn thương gân cơ sau bài Long Run 1400m D+, đưa lưu lượng máu tới nuôi dưỡng các mô liên kết mà không tạo áp lực tim mạch. Benefit: Thúc đẩy quá trình tái tạo glycogen và phục hồi sợi cơ mà không làm tăng hormone stress cortisol. Warning: Tuyệt đối không chạy vượt sang Zone 2 dù cảm giác chân rất khỏe; giữ guồng chân nhẹ nhàng.",
    "fueling_tip": "Buổi tập 50 phút Zone 1: Chỉ cần uống nước lọc mát từng ngụm nhỏ theo nhu cầu; bổ sung 200mg sodium sau buổi chạy nếu thời tiết nóng ẩm.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Tuesday",
    "phase": "Base",
    "title": "Treadmill ME Leo Dốc & Aerobic Base",
    "type": "Muscular Endurance",
    "duration_minutes": 70.0,
    "target_zone": "Zone 2",
    "target_hr_range": "135-150 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Warm up 10 min chạy phẳng trên treadmill pace 5:20/km nâng dần nhiệt độ cơ thể → 6 reps Treadmill Incline 12% ở vận tốc 5.2 km/h kéo dài 6 min, tập trung sải chân đẩy dốc bằng đùi trước và mông → 2 min đi bộ phẳng 4.0 km/h phục hồi giữa các rep → Cool down 12 min chạy chậm phẳng Zone 1 hạ nhiệt tim mạch. Overall: Buổi Muscular Endurance đầu tiên tại phòng gym trên máy chạy dốc chuyên dụng, phát triển khả năng chống mỏi cục bộ cho cơ đẩy. Cường độ tim mạch giữ chặt chẽ trong Zone 2 nhưng cơ đùi chịu kích thích kháng lực cao. Reason: Lịch trình trong tuần tại HCM phẳng, sử dụng cơ sở vật chất gym vào Thứ Ba để nạp độ dốc đặc thù giải đấu. Benefit: Tăng khả năng huy động sợi cơ trung gian FTa và sức chịu đựng acid cục bộ tại cơ tứ đầu đùi mà không gây kiệt sức tim mạch. Warning: Duy trì tư thế lưng thẳng, không tì đè hoặc bám tay vào thanh vịn treadmill để đảm bảo tải trọng dồn hoàn toàn lên cơ chân.",
    "fueling_tip": "Buổi tập 70 phút trong nhà: Bổ sung 500ml nước pha sẵn điện giải (300mg sodium) do mồ hôi thoát nhiều trong gym; không nhất thiết phải nạp thêm carbs.",
    "treadmill_incline": "11-13",
    "treadmill_speed": "5.2",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Wednesday",
    "phase": "Base",
    "title": "Nghỉ Ngơi Phục Hồi Hoàn Toàn",
    "type": "Rest",
    "duration_minutes": 0.0,
    "target_zone": "Zone 1",
    "target_hr_range": "Dưới 115 bpm",
    "target_pace": "",
    "distance_km": 0.0,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Nghỉ ngơi toàn diện → Giãn cơ nhẹ nhàng hoặc foam rolling bắp chuối và dải chậu chày 15 min tại nhà → Đi ngủ sớm đảm bảo giấc ngủ sâu tối thiểu 8 tiếng. Overall: Ngày nghỉ tĩnh theo đúng lịch trình cố định nhằm tạo khoảng trống sinh học cho cơ thể siêu bù trừ năng lượng. Không thực hiện các hoạt động thể lực gắng sức. Reason: Phục hồi cấu trúc cơ bắp sau kích thích ME dốc ngày Thứ Ba, chuẩn bị nền tảng thể lực cho buổi Tempo biến tốc ngày Thứ Năm. Benefit: Giảm căng thẳng thần kinh trung ương, hạ thấp nồng độ enzyme creatine kinase trong máu và tái cân bằng glycogen cơ. Warning: Tránh đứng lâu hoặc mang vác nặng; chú ý theo dõi nhịp tim khi nghỉ ngơi (Resting HR) vào buổi sáng.",
    "fueling_tip": "Duy trì chế độ dinh dưỡng cân bằng giàu đạm chất lượng cao và rau xanh; uống đủ 2-2.5 lít nước trong ngày để hỗ trợ trao đổi chất.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Thursday",
    "phase": "Base",
    "title": "Treadmill Tempo Dốc Sub-Threshold",
    "type": "Tempo",
    "duration_minutes": 75.0,
    "target_zone": "Zone 3",
    "target_hr_range": "155-168 bpm",
    "target_pace": "4:45 - 4:20 /km",
    "distance_km": 16.5,
    "elevation_gain_m": 600.0,
    "grade_percent": 5.0,
    "description": "Process: Warm up 15 min chạy phẳng Zone 2 pace 5:00/km → 3 x 10 min chạy dốc 8% trên treadmill pace 6:40/km (tương đương gắng sức Zone 3 phẳng 4:35/km, HR 158-165 bpm) → 3 min chạy chậm phẳng Zone 1 phục hồi giữa các hiệp → Cool down 12 min chạy chậm thả lỏng về Zone 1. Overall: Bài tập sức bền tốc độ trên độ dốc có kiểm soát, giữ nhịp tim ổn định hoàn toàn dưới ngưỡng AnT 171 bpm. Tối ưu hóa việc tiêu thụ lactate làm nhiên liệu cho cơ bắp đang hoạt động. Reason: Khai thác ngày có gym thứ hai trong tuần để duy trì ngưỡng kỵ khí và sức mạnh sải chân trên dốc. Benefit: Tăng tốc độ tối đa có thể duy trì khi leo dốc dài, nâng cao công suất hiếu khí cục bộ mà không tích tụ ion H+ quá mức. Warning: Không để nhịp tim vượt ngưỡng AnT 171 bpm ở những phút cuối mỗi rep; nếu tim vượt mức kiểm soát cần hạ nhẹ độ dốc hoặc tốc độ.",
    "fueling_tip": "Buổi tập 75 phút cường độ Zone 3: Uống 600ml nước điện giải (350mg sodium); dùng 1 gel năng lượng (30g carbs) trước hiệp dốc thứ 2 ở phút thứ 35.",
    "treadmill_incline": "7-9",
    "treadmill_speed": "9.3-10.2",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Friday",
    "phase": "Base",
    "title": "Easy Aerobic Run Đường Phẳng",
    "type": "Easy",
    "duration_minutes": 65.0,
    "target_zone": "Zone 2",
    "target_hr_range": "138-152 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 13.1,
    "elevation_gain_m": 0.0,
    "grade_percent": 0.0,
    "description": "Process: Warm up 10 min chạy nhẹ Zone 1 phẳng → Chạy liên tục duy trì 45 min Zone 2 kiểm soát nhịp tim ổn định quanh mốc 145 bpm → 5 x 20s Strides thả lỏng chân trên đường bằng phẳng với 40s đi bộ hồi phục → Cool down 5 min đi bộ và thả lỏng. Overall: Chạy nền tảng hiếu khí phẳng nội đô nhằm duy trì khối lượng hàng tuần trước khi bước vào chuỗi dốc lớn cuối tuần. Giữ cơ thể trong trạng thái hiếu khí thuần khiết. Reason: Tích lũy số km aerobic hàng tuần mà không phát sinh thêm tải trọng dốc hay làm căng thẳng khớp gối. Benefit: Tăng mật độ mao mạch quanh các sợi cơ xương, cải thiện tính kinh tế của dáng chạy đường bằng phẳng. Warning: Giữ bước chạy mượt mà, không bung sức ở các đoạn strides; ngưng bài tập nếu cảm thấy gân Achilles bị căng tức.",
    "fueling_tip": "Buổi tập 65 phút: Uống 400-500ml nước khoáng thường; không cần bổ sung carbs ngoài trong suốt quá trình chạy.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Saturday",
    "phase": "Base",
    "title": "Trail Hill Bounding & Aerobic Run",
    "type": "Easy",
    "duration_minutes": 85.0,
    "target_zone": "Zone 2",
    "target_hr_range": "140-154 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 17.1,
    "elevation_gain_m": 650.0,
    "grade_percent": 4.0,
    "description": "Process: Warm up 15 min chạy nhẹ Zone 1 trên trail → 6 x 10s Hill Bounding bật nhảy sải dài trên dốc 15% bộc phát lực tối đa, nghỉ đi bộ thả lỏng 3 min giữa mỗi rep → Chạy liên tục 45 min Zone 2 địa hình trail nhấp nhô giữ HR dưới 154 bpm → Cool down 7 min thả lỏng cơ bắp toàn thân. Overall: Buổi tập kết hợp kích hoạt thần kinh cơ thông qua hill bounding và tích lũy sức bền trên trail tự nhiên. Nhấn mạnh vào việc tuyển mộ sợi cơ nhanh trước khi chạy nền tảng. Reason: Thứ Bảy lên núi dốc, áp dụng phương pháp Uphill Athlete để phát huy lực đẩy mà không làm tim bị kiệt sức. Benefit: Cải thiện độ đàn hồi của gân gót và công suất đẩy của khớp hông, gia tăng độ linh hoạt khi xử lý địa hình gồ ghề. Warning: Dừng ngay các hiệp bounding nếu sải chân mất uy lực hoặc mất thăng bằng tiếp đất; tiếp đất bằng ức bàn chân có kiểm soát.",
    "fueling_tip": "Buổi tập 85 phút ngoài trời: Dùng 1 bình 500ml nước điện giải (300-400mg sodium) và 1 gói gel chứa 30g carbs ở phút thứ 40.",
    "treadmill_incline": "10-15",
    "treadmill_speed": "7.4-8.1",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  },
  {
    "week_number": 2,
    "day_of_week": "Sunday",
    "phase": "Base",
    "title": "Long Run Leo Dốc Kỹ Thuật & Xuống Dốc Eccentric",
    "type": "Long Run",
    "duration_minutes": 160.0,
    "target_zone": "Zone 2",
    "target_hr_range": "135-152 bpm",
    "target_pace": "5:10 - 4:45 /km",
    "distance_km": 32.2,
    "elevation_gain_m": 1550.0,
    "grade_percent": 5.1,
    "description": "Process: Khởi động xoay khớp 10 min tại chân núi → Chạy bền 140 min Zone 2 trên cung đường trail dốc kỹ thuật, thực hiện power hiking nhịp nhàng khi lên các con dốc gắt và duy trì guồng chân nhanh tiếp đất mềm mại khi đổ dốc → Cool down 10 min đi bộ thả lỏng hồi phục. Overall: Bài chạy dài trọng điểm của tuần trên núi cao nhằm mô phỏng tỷ lệ dốc khắt khe của Synthetic 76K. Rèn luyện sức chịu đựng co cơ lệch tâm (eccentric) của đùi trước khi đổ dốc liên tục. Reason: Hoàn thành khối lượng dốc lớn nhất trong tuần vào Chủ Nhật, tận dụng tối đa thời gian trên địa hình núi tự nhiên. Benefit: Xây dựng khả năng kháng mỏi cơ học cho đôi chân, hoàn thiện kỹ năng kiểm soát trọng tâm cơ thể và quản lý năng lượng khi vận động dài giờ. Warning: Không thả trôi tốc độ mất kiểm soát khi xuống dốc để tránh dồn phản lực phá hủy khớp gối và cơ tứ đầu đùi; tập trung cao độ vào từng bước chân tiếp xúc đá sỏi.",
    "fueling_tip": "Buổi tập 160 phút: Nạp 60-70g carbs mỗi giờ (kết hợp gel và bột năng lượng) cùng 600-750ml nước có chứa 500-700mg sodium/giờ; bắt đầu nạp đều đặn ngay từ phút thứ 30.",
    "treadmill_incline": "0",
    "treadmill_speed": "0",
    "interval_reps": null,
    "interval_rep_value": null,
    "interval_rep_unit": null
  }
]
```
</details>
