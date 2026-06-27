from scripts.validate_m5d_frontend_publication_request import validate

def test_m5d_request_is_request_only():
    assert validate()==[]
