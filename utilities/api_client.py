import random
import string
from datetime import datetime

import requests

from config.config_reader import ConfigReader
from utilities.logger import get_logger

logger = get_logger(__name__)


class ApiClient:
    """
    Thin REST client against the KHUB backend the POS app talks to.

    Originally used only to look up data the POS UI itself never surfaces
    (e.g. the order number right after checkout). The test-data creation
    methods below (create_category/get_channels/create_product/
    create_customer) were ported from khub-web-tests'
    scripts/create_general_test_data_api.py — that script targets
    automation_preprod by default, a DIFFERENT tenant/catalog than the one
    this POS suite runs against, so these are new methods here rather than
    an import from that repo, pointed at this project's own `preprod`
    backend config instead.
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

    # ── Test-data creation (ported from khub-web-tests' create_general_test_data_api.py) ──

    # Real MSA/tobacco reporting category — id and `code` ("003293") confirmed
    # live against preprod. MSA product creation requires an existing category
    # whose `code` is a real MSA taxonomy code (a regulatory reporting value,
    # not something a test can invent), so this is deliberately NOT created
    # fresh per run like the plain category below - it's a fixed, shared,
    # pre-established category, matched by the existing Sale Order test's own
    # tobacco products.
    EXISTING_MSA_CATEGORY = {"id": 21, "code": "003293", "name": "Tobacco Derived Products"}

    def create_category(self, is_msa_compliant: bool = False) -> dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "AutoPOS_Tobacco_Cat" if is_msa_compliant else "AutoPOS_Cat"
        name = f"{prefix}_{ts}"
        resp = self.session.post(
            self.config["url"] + "/tenant/api/v1/catalog/categories",
            json={
                "name": name,
                "parent_id": None,
                "code": None,
                "is_msa_compliant": is_msa_compliant,
                "visible_on_ecom": False,
                "slug": "",
                "seo_metadata": {"description": "", "title": ""},
                "description": "",
                "image": None,
                "imagesUploadLoading": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        entity = data.get("entity") or data.get("data") or data
        category_id = entity.get("id")
        if not category_id:
            raise RuntimeError(f"Category created but ID not in response: {data}")
        logger.info(f"Created category '{name}' (id={category_id})")
        return {"id": category_id, "name": name}

    def get_channels(self) -> list[dict]:
        resp = self.session.get(
            self.config["url"] + "/tenant/api/v1/inventory/channel/list",
            params={"search_key": "", "page_size": -1},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        entities = data.get("entities") or data.get("data", {}).get("entities") or []
        if not entities:
            raise RuntimeError(f"No channels returned: {data}")
        entities.sort(key=lambda c: (not c.get("is_primary", False), c.get("id", 0)))
        return entities

    def create_product(
        self,
        category_id: int,
        channels: list[dict],
        is_msa_compliant: bool = False,
        price: float = 25.00,
        msa_category_code: str | None = None,
    ) -> dict:
        """Creates one product with `price`, in one channel's stock (in_hand=100
        per channel), ready to sell through the POS immediately.

        `msa_category_code` is required whenever `is_msa_compliant=True` -
        confirmed live against preprod that the category's own `is_msa_compliant`
        flag is NOT enough; the backend rejects the product with "MSA product
        creation not allowed when no MSA category is selected" unless this
        real MSA taxonomy code is also passed at the top level of the payload,
        matching `category_id`'s own `code`."""
        if is_msa_compliant and not msa_category_code:
            raise ValueError("msa_category_code is required when is_msa_compliant=True")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "AutoPOS_Tobacco_Prod" if is_msa_compliant else "AutoPOS_Prod"
        name = f"{prefix}_{ts}"
        upc = str(random.randint(1_000_000_000, 9_999_999_999))

        unit_price = {
            "base_cost": price * 0.6,
            "cost": price * 0.6,
            "margin": 10,
            "price": price,
            "lowest_selling_price": 0,
            "ecom_price": None,
            "upc": upc,
            "is_msa_upc": is_msa_compliant,
            "definition": 1,
            "unit": 1,
            "subUnitId": None,
            "unitType": "Piece",
            "subUnit": "Unit",
            "margin_type": 1,
            "unit_price_tiers": [{"tier_id": i, "price": 0, "placeholder": f"Tier {i}"} for i in range(1, 6)],
            "unit_name": "Piece",
            "msrp_price": 0,
        }

        def _channel_entry(ch: dict, test_val: int) -> dict:
            return {
                "channel_name": ch["name"],
                "channel_id": ch["id"],
                "in_hand": 100,
                "on_hold": 0,
                "damaged": 0,
                "min_qty": 0,
                "max_qty": 0,
                "sold_by_unit": 1,
                "bought_by_unit": 1,
                "autoCalculate": False,
                "unit_prices": [unit_price],
                "ps_allowed_qty": None,
                "test": test_val,
            }

        channel_info = [_channel_entry(ch, i + 1) for i, ch in enumerate(channels)]

        # Required by the API whenever is_msa_compliant is True (Master
        # Settlement Agreement / tobacco reporting fields).
        msa_attributes = {
            "category_id": category_id,
            "product_description": name[:50],
            "promotion_indicator": "N",
            "items_per_selling_unit": 1,
        } if is_msa_compliant else None

        payload = {
            "name": name,
            "brand_id": None,
            "slug": name,
            "auto_generate_sku": True,
            "auto_fetch_img": False,
            "is_tax_applicable": True,
            "back_order_portal": True,
            "back_order_ecom": False,
            "is_msa_compliant": is_msa_compliant,
            "description": "",
            "desc_alter_by_client": False,
            "upc": upc,
            "upc_2": "",
            "upc_3": "",
            "mlc": "",
            "bin": "",
            "piece_definition": 1,
            "piece_upc": upc,
            "pack_definition": "",
            "pack_upc": "",
            "case_definition": "",
            "case_upc": "",
            "pallet_definition": "",
            "pallet_upc": "",
            "autoCalculate": True,
            "zone": "",
            "aisle": "",
            "gtn": "",
            "weight_unit": 2,
            "imagesUploadLoading": False,
            "images": [],
            "images_seo": [],
            "video_type": 5,
            "main_category_id": category_id,
            "min_qty": "",
            "max_qty": "",
            "status": 1,
            "is_online": False,
            "is_hot_seller": False,
            "is_featured": False,
            "is_new_arrival": False,
            "attributes": [],
            "attribute_groups": [],
            "unit_of_measurement": 10,
            "channel_info": channel_info,
            "product_seo_meta_data": {"description": "", "title": ""},
            "other_upcs": [],
            "ecom_name": None,
            "cost": 0,
            "base_cost": 0,
            "margin": 0,
            "category_ids": [category_id],
            "supplier_ids": [],
            "tag_values": [],
            "manufacturer_ids": [],
        }
        if msa_category_code:
            payload["msa_category_code"] = msa_category_code
        if msa_attributes is not None:
            payload["msa_attributes"] = msa_attributes

        resp = self.session.post(
            self.config["url"] + "/tenant/api/v1/catalog/products",
            json=payload,
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Product '{name}' creation failed ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        entity = data.get("entity") or data.get("data") or data
        product_id = entity.get("id") or entity.get("product_id")
        logger.info(f"Created product '{name}' (id={product_id}, upc={upc}, price=${price})")
        return {"id": product_id, "name": name, "upc": upc, "price": price}

    def create_customer(self) -> dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"AutoPOS_Cust_{ts}"
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        email = f"autopos_{ts}_{suffix}@example.com"
        phone = f"+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        phone_digits = phone.replace("+", "").replace(" ", "").replace("(", "").replace(")", "").replace("-", "")

        payload = {
            "name": name,
            "no": None,
            "email": email,
            "alternate_email": None,
            "skip_shipping_billing": True,
            "tier_id": None,
            "phone_no": None,
            "business_no": None,
            "business_name": name,
            "business_city": None,
            "password": "Password@123",
            "business_state": None,
            "business_phone_no": phone,
            "whatsapp_no": phone_digits,
            "date_of_join": None,
            "balance_limit_check": False,
            "excluded_product_ids": [],
            "is_msa_compliant": True,
            "is_active": True,
            "customer_type": None,
            "dba_name": name,
            "address": None,
            "sale_agent": "",
            "business_tax_no": None,
            "business_tax_expiry_date": None,
            "allow_ecom": "N",
            "promotion_acceptance": "Y",
            "class_of_trades": "Retailer",
            "invoice_aging": 0,
            "custom_status": False,
            "note": None,
            "out_of_state": False,
            "is_exempt_from_tax": "N",
            "tax_ids": [],
            "all_taxes_applicable": True,
            "restricted_category_ids": [],
            "allowed_category_ids": [],
            "category_access_type": None,
            "restricted_product_ids": [],
            "sale_agent_id": None,
            "sale_agent_obj": {"key": None, "value": None, "label": "Select User"},
            "resale_certificate_expiry": None,
            "business_certificate_expiry": None,
            "tobacco_license_expiry": None,
            "state_id_license_expiry": None,
            "is_whatsapp_customer": False,
            "customer_shipping_details": {
                "name": name,
                "company_name": name,
                "telephone_num": phone,
                "address": "4545 Ludtano Ln",
                "country": "United States",
                "county": "BALTIMORE CITY",
                "city": "Aberdeen Proving Ground",
                "state": "MARYLAND",
                "zip_code": "21001",
                "shipping_no": None,
                "tax_jurisdiction": "MARYLAND",
                "is_billing_same": "Y",
            },
            "customer_billing_details": {
                "name": name,
                "company_name": name,
                "telephone_num": phone,
                "address": "4545 Ludtano Ln",
                "country": "United States",
                "county": "BALTIMORE CITY",
                "city": "Aberdeen Proving Ground",
                "state": "MARYLAND",
                "zip_code": "21001",
            },
            "resale_certificate_num": None,
            "resale_certificate": None,
            "business_certificate": None,
            "business_certificate_num": None,
            "state_id_license": None,
            "state_id_license_num": None,
            "tobacco_license": None,
            "tobacco_license_num": None,
            "county": "",
            "billing_email": None,
            "tax_expiry_date": None,
        }

        resp = self.session.post(
            self.config["url"] + "/tenant/api/v1/sale/customers",
            json=payload,
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Customer creation failed ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        entity = data.get("entity") or data.get("data") or data
        customer_id = entity.get("id") or entity.get("customer_id")
        logger.info(f"Created customer '{name}' (id={customer_id}, phone={phone})")
        return {"id": customer_id, "name": name, "phone": phone, "email": email}

    def create_msa_product_and_customer(self, price: float = 25.00) -> dict:
        """Creates one fresh age-restricted product (under the existing,
        pre-established MSA category - see EXISTING_MSA_CATEGORY) so the POS
        triggers age verification exactly like the existing Sale Order test's
        tobacco products, plus one fresh customer, all through the API. Used
        as Split Payment's test-data setup - a self-contained, disposable
        product+customer per run instead of the static UPCs in test_data.yaml."""
        category = self.EXISTING_MSA_CATEGORY
        channels = self.get_channels()
        product = self.create_product(
            category["id"], channels, is_msa_compliant=True, price=price,
            msa_category_code=category["code"],
        )
        customer = self.create_customer()
        return {"category": category, "product": product, "customer": customer}
