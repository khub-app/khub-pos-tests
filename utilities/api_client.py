import requests

from config.config_reader import ConfigReader
from utilities.logger import get_logger

logger = get_logger(__name__)


class ApiClient:
    """
    Thin REST client against the KHUB backend the POS app talks to.

    Used only to look up data the POS UI itself never surfaces (e.g. the
    order number right after checkout) — NOT for creating test data. Test
    data (products/customers) is generated separately via khub-web-tests'
    scripts/create_general_test_data_api.py, run with --env=preprod (not
    automation_preprod — that's a different tenant's catalog).
    """

    def __init__(self, backend_name: str = "preprod"):
        self.config = ConfigReader().get_backend_api(backend_name)
        self.session = requests.Session()
        self._login()

    def _login(self):
        resp = self.session.post(
            self.config["url"] + "/tenant/api/v1/core/user/authenticate",
            json={"username": self.config["username"], "password": self.config["password"]},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        token = (
            data.get("access_token")
            or data.get("token")
            or data.get("entity", {}).get("access_token")
            or data.get("data", {}).get("access_token")
        )
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
        })
        logger.info(f"Authenticated against backend API as '{self.config['username']}'")

    def get_latest_guest_order_number(self) -> str:
        """Returns the `no` (e.g. "SO-260710-21437") of the most recent
        Guest Customer order — reliable immediately after our own checkout
        since `only_guest=1` narrows out the tenant's other named-customer
        activity, and we're calling this within seconds of our own order."""
        resp = self.session.get(
            self.config["url"] + "/tenant/api/v1/sale/order/list2",
            params={"page": 1, "page_size": 1, "only_guest": 1},
            timeout=30,
        )
        resp.raise_for_status()
        entities = resp.json().get("entities") or []
        if not entities:
            raise RuntimeError("No guest orders returned from /sale/order/list2")
        order_no = entities[0]["no"]
        logger.info(f"Latest guest order number: {order_no}")
        return order_no
