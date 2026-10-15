from urllib.request import urlopen

if __name__ == "__main__":
    with urlopen("http://127.0.0.1:8080/health", timeout=3) as response:
        assert response.status == 200
