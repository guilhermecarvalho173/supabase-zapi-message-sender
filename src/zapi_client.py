import requests


class ZApiError(requests.exceptions.HTTPError):
    def __init__(self, message: str, response: requests.Response) -> None:
        super().__init__(message, response=response)


class ZApiClient:
    def __init__(self, instance_id: str, token: str, client_token: str | None = None) -> None:
        self.base_url = f"https://api.z-api.io/instances/{instance_id}/token/{token}"
        self.headers = {"Content-Type": "application/json"}

        if client_token:
            self.headers["Client-Token"] = client_token

    def send_text(self, phone: str, message: str) -> dict:
        response = requests.post(
            f"{self.base_url}/send-text",
            json={"phone": phone, "message": message},
            headers=self.headers,
            timeout=30,
        )

        try:
            data = response.json()
        except ValueError:
            data = {"raw_response": response.text}

        if response.status_code >= 400:
            raise ZApiError(f"Erro HTTP {response.status_code} retornado pela Z-API: {data}", response)

        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"Erro retornado pela Z-API: {data}")

        return data
