from scripts import validate_v1_front_door


def test_current_v1_front_door_is_consistent() -> None:
    assert validate_v1_front_door.validate() == []
