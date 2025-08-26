import os

try:
    import tomllib as toml  
except ModuleNotFoundError:
    import tomli as toml    

REQUIRED = {"host", "port", "user", "password", "from", "use_tls"}

def test_smtp_section_and_keys():
    path = os.path.join(".streamlit", "secrets.toml")
    assert os.path.exists(path), "secrets.toml not found in .streamlit/"
    with open(path, "rb") as f:
        data = toml.load(f)
    assert "smtp" in data, "[smtp] section missing"
    assert REQUIRED.issubset(data["smtp"].keys()), "Missing keys in [smtp]"
