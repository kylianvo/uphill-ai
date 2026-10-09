from services.gear_catalog import MIN_ENTRIES, filter_catalog, surface_of


def _chunk(name, terrain=None, brand="Hoka"):
    payload = {"brand": brand}
    if terrain is not None:
        payload["terrain"] = terrain
    return {"title": name, "payload": payload}


def test_surface_of_reads_the_terrain_text():
    assert surface_of({"terrain": ["Road", "treadmill"]}) == "road"
    assert surface_of({"terrain": ["Technical trail", "Mud"]}) == "trail"
    assert surface_of({"terrain": ["Gravel", "Road-to-trail"]}) == "both"
    assert surface_of({"terrain": "Smoother singletrack"}) == "trail"
    assert surface_of({}) == "unknown"


def _catalog():
    road = [_chunk(f"road{i}", ["Road"]) for i in range(20)]
    trail = [_chunk(f"trail{i}", ["Technical trail"]) for i in range(15)]
    both = [_chunk(f"both{i}", ["Road-to-trail"]) for i in range(5)]
    unknown = [_chunk("mystery")]
    return road + trail + both + unknown


def test_road_request_drops_trail_only_shoes():
    names = {c["title"] for c in filter_catalog(_catalog(), "road", None)}
    assert "trail0" not in names
    assert {"road0", "both0", "mystery"} <= names
    assert len(names) == 26


def test_mixed_or_missing_surface_keeps_everything():
    assert len(filter_catalog(_catalog(), "mixed", None)) == 41
    assert len(filter_catalog(_catalog(), None, None)) == 41


def test_brand_filter_applies_only_when_enough_entries_match():
    catalog = _catalog() + [_chunk(f"sal{i}", ["Technical trail"], brand="Salomon") for i in range(6)]
    salomon = filter_catalog(catalog, "trail", "Salomon")
    assert {c["payload"]["brand"] for c in salomon} == {"Salomon"}

    few = _catalog() + [_chunk("nb1", ["Technical trail"], brand="New Balance")]
    kept = filter_catalog(few, "trail", "New Balance")
    assert len(kept) > 1  # one match is too few: the prompt's "no match" rule needs the rest


def test_too_small_a_result_falls_back_to_the_full_catalog():
    small = [_chunk(f"road{i}", ["Road"]) for i in range(5)] + [_chunk(f"trail{i}", ["Trail"]) for i in range(20)]
    assert len(filter_catalog(small, "road", None)) == len(small)
    assert MIN_ENTRIES == 12
