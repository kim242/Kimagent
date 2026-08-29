"""Données de démonstration : une boutique Chariow fictive mais réaliste.

Utilisées par `kimagent run --demo` pour tester tout le pipeline sans
connexion à Chariow. La structure est identique à celle renvoyée par
`fetch_store_data` (source: "chariow-mcp" → ici "demo").
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

STORE = {
    "id": "sto_demo001",
    "name": "FormationPro Digital",
    "url": "https://formationpro.chariow.store",
    "currency": "EUR",
    "country": "FR",
    "status": "active",
    "settings": {
        "vat_enabled": True,
        "receipts_enabled": True,
        "customer_portal": True,
        "affiliate_program": True,
        "affiliate_commission_rate": 0.20,
    },
    "sales_summary": {
        "total_sales": 1248,
        "total_revenue": {"value": 48230.50, "currency": "EUR"},
        "total_customers": 892,
        "avg_order_value": {"value": 38.65, "currency": "EUR"},
        "last_30_days_revenue": {"value": 6812.00, "currency": "EUR"},
        "last_30_days_sales": 214,
    },
}

PRODUCTS = [
    {
        "id": "prd_form_video",
        "name": "Formation Vidéo — Marketing Digital de A à Z",
        "slug": "formation-marketing-digital",
        "type": "course",
        "status": "published",
        "price": {"value": 149.00, "currency": "EUR"},
        "category": "Formation",
        "sales_count": 312,
        "revenue": {"value": 40218.00, "currency": "EUR"},
        "rating": 4.8,
        "faqs": 6,
        "chapters": 24,
    },
    {
        "id": "prd_notion",
        "name": "Pack 50 Templates Notion pour Créateurs",
        "slug": "templates-notion-createurs",
        "type": "downloadable",
        "status": "published",
        "price": {"value": 29.00, "currency": "EUR"},
        "category": "Templates",
        "sales_count": 587,
        "revenue": {"value": 17023.00, "currency": "EUR"},
        "rating": 4.6,
    },
    {
        "id": "prd_licence",
        "name": "Licence Logiciel — Outil d'Automatisation Pro",
        "slug": "licence-automatisation-pro",
        "type": "license",
        "status": "published",
        "price": {"value": 99.00, "currency": "EUR"},
        "category": "Logiciel",
        "sales_count": 189,
        "revenue": {"value": 18711.00, "currency": "EUR"},
        "rating": 4.5,
        "licenses_issued": 189,
        "licenses_active": 142,
    },
    {
        "id": "prd_ebook",
        "name": "Ebook — 100 Idées de Contenus Rentables",
        "slug": "ebook-100-idees-contenus",
        "type": "downloadable",
        "status": "published",
        "price": {"value": 12.00, "currency": "EUR"},
        "category": "Ebook",
        "sales_count": 1024,
        "revenue": {"value": 12288.00, "currency": "EUR"},
        "rating": 4.4,
    },
    {
        "id": "prd_coaching",
        "name": "Coaching 1:1 — Accompagnement Lancement Produit",
        "slug": "coaching-lancement-produit",
        "type": "coaching",
        "status": "published",
        "price": {"value": 350.00, "currency": "EUR"},
        "category": "Coaching",
        "sales_count": 41,
        "revenue": {"value": 14350.00, "currency": "EUR"},
        "rating": 5.0,
        "sessions_weekly": 8,
    },
    {
        "id": "prd_bundle",
        "name": "Bundle Créateur Complet (Formation + Templates + Ebook)",
        "slug": "bundle-createur-complet",
        "type": "bundle",
        "status": "published",
        "price": {"value": 169.00, "currency": "EUR"},
        "category": "Bundle",
        "sales_count": 87,
        "revenue": {"value": 14703.00, "currency": "EUR"},
        "rating": 4.9,
    },
    {
        "id": "prd_brouillon",
        "name": "Masterclass — Vendre avec l'IA",
        "slug": "masterclass-vendre-ia",
        "type": "course",
        "status": "draft",
        "price": {"value": 79.00, "currency": "EUR"},
        "category": "Formation",
        "sales_count": 0,
        "revenue": {"value": 0.00, "currency": "EUR"},
    },
]

CUSTOMERS = [
    {
        "id": "cus_0001",
        "name": "Marie Dupont",
        "email": "marie.dupont@example.com",
        "country": "FR",
        "total_spent": {"value": 476.00, "currency": "EUR"},
        "orders_count": 7,
        "last_order": "2026-08-20",
        "is_affiliate": True,
    },
    {
        "id": "cus_0002",
        "name": "Thomas Ngoy",
        "email": "thomas.ngoy@example.com",
        "country": "CD",
        "total_spent": {"value": 149.00, "currency": "EUR"},
        "orders_count": 1,
        "last_order": "2026-08-18",
    },
    {
        "id": "cus_0003",
        "name": "Awa Kone",
        "email": "awa.kone@example.com",
        "country": "CI",
        "total_spent": {"value": 610.00, "currency": "EUR"},
        "orders_count": 9,
        "last_order": "2026-08-25",
        "is_affiliate": True,
    },
    {
        "id": "cus_0004",
        "name": "Jean-Marc Lefèvre",
        "email": "jm.lefevre@example.com",
        "country": "FR",
        "total_spent": {"value": 58.00, "currency": "EUR"},
        "orders_count": 2,
        "last_order": "2026-07-02",
    },
    {
        "id": "cus_0005",
        "name": "Sarah Benali",
        "email": "sarah.benali@example.com",
        "country": "MA",
        "total_spent": {"value": 308.00, "currency": "EUR"},
        "orders_count": 4,
        "last_order": "2026-08-28",
    },
]

_SALES_BASE = [
    (149.00, "prd_form_video", "Formation Vidéo — Marketing Digital de A à Z", "completed"),
    (29.00, "prd_notion", "Pack 50 Templates Notion pour Créateurs", "completed"),
    (12.00, "prd_ebook", "Ebook — 100 Idées de Contenus Rentables", "completed"),
    (99.00, "prd_licence", "Licence Logiciel — Outil d'Automatisation Pro", "completed"),
    (350.00, "prd_coaching", "Coaching 1:1 — Accompagnement Lancement Produit", "completed"),
    (169.00, "prd_bundle", "Bundle Créateur Complet", "completed"),
    (29.00, "prd_notion", "Pack 50 Templates Notion pour Créateurs", "abandoned"),
]


def _generate_sales(days: int = 45) -> list[dict]:
    """Génère des ventes plausibles sur les derniers jours."""
    import random

    random.seed(42)
    sales: list[dict] = []
    today = datetime.now(timezone.utc)
    for i in range(1, days + 1):
        day = today - timedelta(days=i)
        n = random.choices([0, 1, 2, 3, 4, 5], weights=[15, 25, 25, 18, 10, 7])[0]
        for _ in range(n):
            price, pid, pname, status = random.choice(_SALES_BASE)
            sales.append(
                {
                    "id": f"sal_demo{i:04d}{len(sales):03d}",
                    "product_id": pid,
                    "product_name": pname,
                    "amount": {"value": price, "currency": "EUR"},
                    "status": status,
                    "created_at": (day + timedelta(hours=random.randint(8, 22))).isoformat(
                        timespec="minutes"
                    ),
                    "customer_email": random.choice(
                        ["marie.dupont@example.com", "thomas.ngoy@example.com",
                         "awa.kone@example.com", "sarah.benali@example.com", "client@example.com"]
                    ),
                    "payment_method": random.choice(["card", "card", "paypal", "mobile_money"]),
                }
            )
    sales.sort(key=lambda s: s["created_at"], reverse=True)
    return sales


DISCOUNTS = [
    {
        "id": "dsc_001",
        "code": "BIENVENUE10",
        "name": "Bienvenue -10%",
        "type": "percentage",
        "value": 10,
        "status": "active",
        "usage_count": 143,
        "usage_limit": 500,
        "expires_at": "2026-12-31",
    },
    {
        "id": "dsc_002",
        "code": "ETE20",
        "name": "Promo Été -20%",
        "type": "percentage",
        "value": 20,
        "status": "expired",
        "usage_count": 512,
        "usage_limit": 1000,
        "expires_at": "2026-08-31",
    },
    {
        "id": "dsc_003",
        "code": "AFFILIE",
        "name": "Remise affiliés",
        "type": "percentage",
        "value": 15,
        "status": "active",
        "usage_count": 67,
        "usage_limit": None,
        "expires_at": None,
    },
]

LICENSES = [
    {
        "id": "lic_001",
        "key": "ABC-123-XYZ-789",
        "product_id": "prd_licence",
        "status": "active",
        "customer_email": "awa.kone@example.com",
        "activations": 2,
        "max_activations": 3,
        "expires_at": "2027-01-15",
    },
    {
        "id": "lic_002",
        "key": "DEF-456-UVW-012",
        "product_id": "prd_licence",
        "status": "active",
        "customer_email": "marie.dupont@example.com",
        "activations": 3,
        "max_activations": 3,
        "expires_at": "2026-11-30",
    },
    {
        "id": "lic_003",
        "key": "GHI-789-RST-345",
        "product_id": "prd_licence",
        "status": "expired",
        "customer_email": "client@example.com",
        "activations": 1,
        "max_activations": 3,
        "expires_at": "2026-06-01",
    },
]

PULSES = [
    {"id": "pls_001", "event": "sale.completed", "url": "https://app.example.com/webhook", "status": "active"},
    {"id": "pls_002", "event": "license.activated", "url": "https://app.example.com/license", "status": "active"},
]

ANALYTICS = {
    "get_store_analytics": {
        "period": "last_30_days",
        "visits": 8432,
        "unique_visitors": 6211,
        "sales": 214,
        "conversion_rate": 2.54,
        "revenue": {"value": 6812.00, "currency": "EUR"},
    },
    "get_sales_analytics": {
        "period": "last_30_days",
        "revenue": {"value": 6812.00, "currency": "EUR"},
        "sales_count": 214,
        "avg_order_value": {"value": 31.83, "currency": "EUR"},
        "refunds": {"value": 186.00, "currency": "EUR"},
        "top_products": [
            {"product": "Pack 50 Templates Notion pour Créateurs", "sales": 96, "revenue": 2784.00},
            {"product": "Ebook — 100 Idées de Contenus Rentables", "sales": 71, "revenue": 852.00},
            {"product": "Formation Vidéo — Marketing Digital de A à Z", "sales": 29, "revenue": 4321.00},
        ],
    },
    "get_customer_analytics": {
        "period": "last_30_days",
        "new_customers": 162,
        "returning_customers": 52,
        "top_countries": [{"country": "France", "customers": 94}, {"country": "Côte d'Ivoire", "customers": 31}, {"country": "RD Congo", "customers": 22}, {"country": "Maroc", "customers": 15}],
        "top_customers": [
            {"name": "Awa Kone", "spent": 610.00, "orders": 9},
            {"name": "Marie Dupont", "spent": 476.00, "orders": 7},
        ],
    },
    "get_visits_analytics": {
        "period": "last_30_days",
        "sources": [{"source": "Instagram", "visits": 3140}, {"source": "Google", "visits": 2410}, {"source": "Direct", "visits": 1290}, {"source": "Affiliés", "visits": 980}, {"source": "TikTok", "visits": 612}],
        "devices": [{"device": "mobile", "visits": 5230}, {"device": "desktop", "visits": 2980}, {"device": "tablet", "visits": 222}],
    },
    "get_conversion_rate_analytics": {
        "period": "last_30_days",
        "overall": 2.54,
        "by_device": [{"device": "desktop", "conversion_rate": 3.4}, {"device": "mobile", "conversion_rate": 2.1}],
        "by_product": [
            {"product": "Ebook — 100 Idées de Contenus Rentables", "conversion_rate": 6.8},
            {"product": "Pack 50 Templates Notion pour Créateurs", "conversion_rate": 4.2},
            {"product": "Coaching 1:1", "conversion_rate": 1.9},
            {"product": "Formation Vidéo", "conversion_rate": 1.2},
        ],
    },
}


def get_demo_data() -> dict:
    """Retourne un jeu de données complet identique à fetch_store_data()."""
    return {
        "meta": {
            "source": "demo",
            "mcp_url": "https://mcp.chariow.com/public (mode démo)",
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tool_errors": {},
        },
        "tools": {
            "get_store": STORE,
            "list_products": {"data": PRODUCTS, "pagination": {"has_more": False}},
            "list_customers": {"data": CUSTOMERS, "pagination": {"has_more": False}},
            "list_sales": {"data": _generate_sales(), "pagination": {"has_more": False}},
            "list_discounts": {"data": DISCOUNTS, "pagination": {"has_more": False}},
            "list_licenses": {"data": LICENSES, "pagination": {"has_more": False}},
            "list_pulses": {"data": PULSES, "pagination": {"has_more": False}},
            "get_store_analytics": ANALYTICS["get_store_analytics"],
            "get_sales_analytics": ANALYTICS["get_sales_analytics"],
            "get_customer_analytics": ANALYTICS["get_customer_analytics"],
            "get_visits_analytics": ANALYTICS["get_visits_analytics"],
            "get_conversion_rate_analytics": ANALYTICS["get_conversion_rate_analytics"],
        },
    }
