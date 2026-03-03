"""
Insurance Provider Information Service
Provides detailed information about insurance companies in India
"""

# Comprehensive database of insurance companies in India
INSURANCE_PROVIDERS = {
    "ACKO": {
        "fullName": "ACKO General Insurance Limited",
        "type": "General Insurance",
        "founded": "2016",
        "headquarters": "Mumbai, Maharashtra",
        "about": "ACKO is a digital-first general insurance company that offers motor, health, and travel insurance. Known for its paperless claims process and instant policy issuance, ACKO provides affordable insurance solutions through its mobile app and website.",
        "claimSettlementRatio": "98.50%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-266-2256",
            "email": "support@acko.com",
            "whatsapp": "+91-9666-800-800",
            "website": "https://www.acko.com",
            "claimEmail": "claims@acko.com"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance"],
        "networkSize": "14,300+ Network Hospitals, 10,000+ Garages",
        "irda": "IRDAI Registration No: 157"
    },

    "NIVA BUPA": {
        "fullName": "Niva Bupa Health Insurance Company Limited",
        "type": "Health Insurance",
        "founded": "2008",
        "headquarters": "New Delhi",
        "about": "Niva Bupa (formerly Max Bupa) is one of India's leading standalone health insurance companies. It offers comprehensive health insurance products covering individuals, families, and corporate groups with extensive network hospitals and cashless claim facilities.",
        "claimSettlementRatio": "96.30%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-266-4242",
            "email": "care@nivabupa.com",
            "website": "https://www.nivabupa.com",
            "claimEmail": "claims@nivabupa.com"
        },
        "specialties": ["Health Insurance", "Critical Illness", "Personal Accident"],
        "networkSize": "10,000+ Network Hospitals",
        "irda": "IRDAI Registration No: 133"
    },

    "ICICI LOMBARD": {
        "fullName": "ICICI Lombard General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2001",
        "headquarters": "Mumbai, Maharashtra",
        "about": "ICICI Lombard is one of India's leading private general insurance companies offering comprehensive insurance solutions including motor, health, home, travel, and commercial insurance. Known for excellent customer service and quick claim settlements.",
        "claimSettlementRatio": "96.49%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1860-266-7766",
            "email": "customersupport@icicilombard.com",
            "website": "https://www.icicilombard.com",
            "claimEmail": "claims@icicilombard.com"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Home Insurance"],
        "networkSize": "7,200+ Network Hospitals, 5,000+ Garages",
        "irda": "IRDAI Registration No: 115"
    },

    "HDFC ERGO": {
        "fullName": "HDFC ERGO General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2002",
        "headquarters": "Mumbai, Maharashtra",
        "about": "HDFC ERGO is a joint venture between HDFC Ltd and ERGO International AG. It offers a wide range of general insurance products including motor, health, travel, home, and commercial insurance with innovative solutions and strong claim support.",
        "claimSettlementRatio": "99.33%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-2700-700",
            "email": "customerservice@hdfcergo.com",
            "website": "https://www.hdfcergo.com",
            "claimEmail": "claims@hdfcergo.com"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Home Insurance"],
        "networkSize": "14,300+ Network Hospitals, 6,500+ Garages",
        "irda": "IRDAI Registration No: 146"
    },

    "BAJAJ ALLIANZ": {
        "fullName": "Bajaj Allianz General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2001",
        "headquarters": "Pune, Maharashtra",
        "about": "Bajaj Allianz is a joint venture between Bajaj Finserv and Allianz SE. It provides comprehensive general insurance solutions including motor, health, travel, home, and commercial insurance with pan-India presence and strong claim settlement track record.",
        "claimSettlementRatio": "93.06%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-209-5858",
            "email": "bagichelp@bajajallianz.co.in",
            "website": "https://www.bajajallianz.com",
            "claimEmail": "claims@bajajallianz.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Home Insurance"],
        "networkSize": "10,000+ Network Hospitals, 4,000+ Garages",
        "irda": "IRDAI Registration No: 113"
    },

    "TATA AIG": {
        "fullName": "Tata AIG General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2001",
        "headquarters": "Mumbai, Maharashtra",
        "about": "Tata AIG is a joint venture between Tata Sons and American International Group (AIG). It offers a comprehensive range of general insurance products with a focus on innovation, customer service, and quick claim settlements.",
        "claimSettlementRatio": "87.08%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-266-7780",
            "email": "customer.care@tataaig.com",
            "website": "https://www.tataaig.com",
            "claimEmail": "general.claims@tataaig.com"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Commercial Insurance"],
        "networkSize": "7,200+ Network Hospitals, 7,500+ Garages",
        "irda": "IRDAI Registration No: 108"
    },

    "SBI GENERAL": {
        "fullName": "SBI General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2009",
        "headquarters": "Mumbai, Maharashtra",
        "about": "SBI General Insurance is a joint venture between State Bank of India and Insurance Australia Group. It offers various general insurance products leveraging SBI's extensive branch network across India.",
        "claimSettlementRatio": "92.78%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-22-1111",
            "email": "customer.care@sbigeneral.in",
            "website": "https://www.sbigeneral.in",
            "claimEmail": "claims@sbigeneral.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Home Insurance", "Travel Insurance"],
        "networkSize": "9,500+ Network Hospitals, 7,200+ Garages",
        "irda": "IRDAI Registration No: 144"
    },

    "RELIANCE GENERAL": {
        "fullName": "Reliance General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2000",
        "headquarters": "Mumbai, Maharashtra",
        "about": "Reliance General Insurance offers a wide range of general insurance products including motor, health, travel, home, and commercial insurance. Part of the Reliance Group, it provides pan-India service with strong financial backing.",
        "claimSettlementRatio": "95.51%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-3009",
            "email": "customer.support@relianceada.com",
            "website": "https://www.reliancegeneral.co.in",
            "claimEmail": "claims@reliancegeneral.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Home Insurance"],
        "networkSize": "9,100+ Network Hospitals, 8,500+ Garages",
        "irda": "IRDAI Registration No: 103"
    },

    "NEW INDIA ASSURANCE": {
        "fullName": "The New India Assurance Company Limited",
        "type": "General Insurance",
        "founded": "1919",
        "headquarters": "Mumbai, Maharashtra",
        "about": "New India Assurance is India's oldest and largest general insurance company. It offers comprehensive insurance solutions across all segments with unmatched experience and pan-India presence through extensive branch network.",
        "claimSettlementRatio": "92.31%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-209-1415",
            "email": "customer.relations@newindia.co.in",
            "website": "https://www.newindia.co.in",
            "claimEmail": "claims@newindia.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Commercial Insurance", "Marine Insurance"],
        "networkSize": "10,000+ Network Hospitals, 3,000+ Garages",
        "irda": "IRDAI Registration No: 105"
    },

    "ORIENTAL INSURANCE": {
        "fullName": "The Oriental Insurance Company Limited",
        "type": "General Insurance",
        "founded": "1947",
        "headquarters": "New Delhi",
        "about": "Oriental Insurance is one of India's leading public sector general insurance companies. It provides comprehensive insurance coverage across various segments with strong government backing and extensive service network.",
        "claimSettlementRatio": "90.45%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-118-485",
            "email": "customercare@orientalinsurance.co.in",
            "website": "https://www.orientalinsurance.org.in",
            "claimEmail": "claims@orientalinsurance.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Commercial Insurance"],
        "networkSize": "9,000+ Network Hospitals, 3,100+ Garages",
        "irda": "IRDAI Registration No: 107"
    },

    "UNITED INDIA": {
        "fullName": "United India Insurance Company Limited",
        "type": "General Insurance",
        "founded": "1938",
        "headquarters": "Chennai, Tamil Nadu",
        "about": "United India Insurance is a public sector general insurance company offering a wide range of insurance products. With decades of experience and government backing, it provides reliable insurance solutions across India.",
        "claimSettlementRatio": "89.72%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-425-8881",
            "email": "customercare@uiic.co.in",
            "website": "https://www.uiic.co.in",
            "claimEmail": "claims@uiic.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Commercial Insurance"],
        "networkSize": "8,000+ Network Hospitals, 3,100+ Garages",
        "irda": "IRDAI Registration No: 106"
    },

    "DIGIT INSURANCE": {
        "fullName": "Go Digit General Insurance Limited",
        "type": "General Insurance",
        "founded": "2017",
        "headquarters": "Pune, Maharashtra",
        "about": "Digit Insurance is a digital-first insurance company offering paperless, hassle-free insurance solutions. Known for its quick claim settlements and innovative products, Digit focuses on motor, health, and travel insurance.",
        "claimSettlementRatio": "97.18%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-258-4242",
            "email": "support@godigit.com",
            "website": "https://www.godigit.com",
            "claimEmail": "claims@godigit.com"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance"],
        "networkSize": "16,000+ Network Hospitals, 9,500+ Garages",
        "irda": "IRDAI Registration No: 158"
    },

    "CARE HEALTH": {
        "fullName": "Care Health Insurance Limited",
        "type": "Health Insurance",
        "founded": "2012",
        "headquarters": "New Delhi",
        "about": "Care Health Insurance (formerly Religare Health Insurance) is a standalone health insurance company offering comprehensive health insurance solutions. It focuses on innovative health products and extensive hospital network.",
        "claimSettlementRatio": "94.17%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-102-4488",
            "email": "customer.relations@careinsurance.com",
            "website": "https://www.careinsurance.com",
            "claimEmail": "claims@careinsurance.com"
        },
        "specialties": ["Health Insurance", "Critical Illness", "Personal Accident"],
        "networkSize": "18,500+ Network Hospitals",
        "irda": "IRDAI Registration No: 148"
    },

    "STAR HEALTH": {
        "fullName": "Star Health and Allied Insurance Company Limited",
        "type": "Health Insurance",
        "founded": "2006",
        "headquarters": "Chennai, Tamil Nadu",
        "about": "Star Health is India's first standalone health insurance company and the largest in terms of retail health insurance. It offers comprehensive health insurance products with the largest network of hospitals and excellent claim settlement record.",
        "claimSettlementRatio": "90.37%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-425-2255",
            "email": "customercare@starhealth.in",
            "website": "https://www.starhealth.in",
            "claimEmail": "claims@starhealth.in"
        },
        "specialties": ["Health Insurance", "Critical Illness", "Diabetes Cover", "Cardiac Cover"],
        "networkSize": "14,000+ Network Hospitals",
        "irda": "IRDAI Registration No: 129"
    },

    "NATIONAL INSURANCE": {
        "fullName": "National Insurance Company Limited",
        "type": "General Insurance",
        "founded": "1906",
        "headquarters": "Kolkata, West Bengal",
        "about": "National Insurance is one of India's oldest and largest public sector general insurance companies. It offers comprehensive insurance solutions across all segments with extensive branch network and strong government backing.",
        "claimSettlementRatio": "91.28%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-200-7710",
            "email": "customercare@nic.co.in",
            "website": "https://www.nationalinsurance.nic.co.in",
            "claimEmail": "claims@nic.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Commercial Insurance"],
        "networkSize": "9,500+ Network Hospitals, 3,100+ Garages",
        "irda": "IRDAI Registration No: 104"
    },

    "FUTURE GENERALI": {
        "fullName": "Future Generali India Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2007",
        "headquarters": "Mumbai, Maharashtra",
        "about": "Future Generali is a joint venture between Future Group and Generali Group. It offers a wide range of general insurance products with focus on customer-centric solutions and innovative coverage options.",
        "claimSettlementRatio": "88.96%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-220-233",
            "email": "fgcare@futuregenerali.in",
            "website": "https://general.futuregenerali.in",
            "claimEmail": "claims@futuregenerali.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Home Insurance"],
        "networkSize": "9,700+ Network Hospitals, 4,000+ Garages",
        "irda": "IRDAI Registration No: 132"
    },

    "IFFCO TOKIO": {
        "fullName": "IFFCO-Tokio General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2000",
        "headquarters": "Gurugram, Haryana",
        "about": "IFFCO-Tokio is a joint venture between Indian Farmers Fertiliser Cooperative (IFFCO) and Tokio Marine Group. It offers comprehensive general insurance products with strong rural and urban reach.",
        "claimSettlementRatio": "94.00%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-103-5499",
            "email": "support@iffcotokio.co.in",
            "website": "https://www.iffcotokio.co.in",
            "claimEmail": "claims@iffcotokio.co.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Crop Insurance", "Travel Insurance"],
        "networkSize": "8,500+ Network Hospitals, 6,500+ Garages",
        "irda": "IRDAI Registration No: 106"
    },

    "CHOLAMANDALAM": {
        "fullName": "Cholamandalam MS General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2001",
        "headquarters": "Chennai, Tamil Nadu",
        "about": "Cholamandalam MS is a joint venture between the Murugappa Group and Mitsui Sumitomo Insurance. It offers a range of general insurance products with strong presence in motor and health insurance.",
        "claimSettlementRatio": "91.00%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-200-5544",
            "email": "customercare@cholams.murugappa.com",
            "website": "https://www.cholainsurance.com",
            "claimEmail": "claims@cholams.murugappa.com"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance"],
        "networkSize": "8,000+ Network Hospitals, 6,000+ Garages",
        "irda": "IRDAI Registration No: 123"
    },

    "ROYAL SUNDARAM": {
        "fullName": "Royal Sundaram General Insurance Company Limited",
        "type": "General Insurance",
        "founded": "2001",
        "headquarters": "Chennai, Tamil Nadu",
        "about": "Royal Sundaram is a private general insurance company offering motor, health, travel and home insurance products with emphasis on digital services and customer experience.",
        "claimSettlementRatio": "89.00%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-568-9999",
            "email": "customerservice@royalsundaram.in",
            "website": "https://www.royalsundaram.in",
            "claimEmail": "claims@royalsundaram.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance", "Home Insurance"],
        "networkSize": "7,200+ Network Hospitals, 5,500+ Garages",
        "irda": "IRDAI Registration No: 102"
    },

    "LIBERTY GENERAL": {
        "fullName": "Liberty General Insurance Limited",
        "type": "General Insurance",
        "founded": "2013",
        "headquarters": "Mumbai, Maharashtra",
        "about": "Liberty General Insurance offers motor, health, and travel insurance products with focus on digital-first customer experience and quick claim settlements.",
        "claimSettlementRatio": "86.00%",
        "claimSettlementYear": "2022-23",
        "customerSupport": {
            "phone": "1800-266-5844",
            "email": "customer.care@libertyinsurance.in",
            "website": "https://www.libertyinsurance.in",
            "claimEmail": "claims@libertyinsurance.in"
        },
        "specialties": ["Motor Insurance", "Health Insurance", "Travel Insurance"],
        "networkSize": "5,500+ Network Hospitals, 4,500+ Garages",
        "irda": "IRDAI Registration No: 150"
    }
}


def get_insurance_provider_info(provider_name: str) -> dict:
    """
    Get detailed information about an insurance provider.

    Uses multi-level matching: direct → alias mapping → difflib fuzzy.
    """
    if not provider_name:
        return None

    provider_name_upper = provider_name.upper().strip()

    # Direct match
    if provider_name_upper in INSURANCE_PROVIDERS:
        return INSURANCE_PROVIDERS[provider_name_upper]

    # Alias mapping — sorted by key length (longest first) to avoid partial match issues
    provider_mapping = {
        "ACKO GENERAL INSURANCE": "ACKO",
        "ACKO GENERAL": "ACKO",
        "MAX BUPA": "NIVA BUPA",
        "NIVA BUPA": "NIVA BUPA",
        "ICICI LOMBARD": "ICICI LOMBARD",
        "HDFC ERGO": "HDFC ERGO",
        "BAJAJ ALLIANZ": "BAJAJ ALLIANZ",
        "TATA AIG": "TATA AIG",
        "SBI GENERAL": "SBI GENERAL",
        "RELIANCE GENERAL": "RELIANCE GENERAL",
        "NEW INDIA ASSURANCE": "NEW INDIA ASSURANCE",
        "NEW INDIA": "NEW INDIA ASSURANCE",
        "ORIENTAL INSURANCE": "ORIENTAL INSURANCE",
        "UNITED INDIA": "UNITED INDIA",
        "GO DIGIT": "DIGIT INSURANCE",
        "DIGIT INSURANCE": "DIGIT INSURANCE",
        "CARE HEALTH": "CARE HEALTH",
        "RELIGARE HEALTH": "CARE HEALTH",
        "STAR HEALTH": "STAR HEALTH",
        "NATIONAL INSURANCE": "NATIONAL INSURANCE",
        "FUTURE GENERALI": "FUTURE GENERALI",
        "IFFCO TOKIO": "IFFCO TOKIO",
        "IFFCO-TOKIO": "IFFCO TOKIO",
        "CHOLAMANDALAM": "CHOLAMANDALAM",
        "CHOLA MS": "CHOLAMANDALAM",
        "ROYAL SUNDARAM": "ROYAL SUNDARAM",
        "LIBERTY GENERAL": "LIBERTY GENERAL",
        # Short-form aliases
        "NIVA": "NIVA BUPA",
        "ICICI": "ICICI LOMBARD",
        "HDFC": "HDFC ERGO",
        "BAJAJ": "BAJAJ ALLIANZ",
        "TATA": "TATA AIG",
        "SBI": "SBI GENERAL",
        "RELIANCE": "RELIANCE GENERAL",
        "ORIENTAL": "ORIENTAL INSURANCE",
        "DIGIT": "DIGIT INSURANCE",
        "CARE": "CARE HEALTH",
        "RELIGARE": "CARE HEALTH",
        "STAR": "STAR HEALTH",
        "NATIONAL": "NATIONAL INSURANCE",
        "FUTURE": "FUTURE GENERALI",
        "GENERALI": "FUTURE GENERALI",
        "LIBERTY": "LIBERTY GENERAL",
    }

    for key in sorted(provider_mapping.keys(), key=len, reverse=True):
        if key in provider_name_upper:
            return INSURANCE_PROVIDERS.get(provider_mapping[key])

    # Fuzzy match using difflib as last resort
    try:
        from difflib import get_close_matches
        all_names = list(INSURANCE_PROVIDERS.keys())
        matches = get_close_matches(provider_name_upper, all_names, n=1, cutoff=0.6)
        if matches:
            return INSURANCE_PROVIDERS[matches[0]]
    except Exception:
        pass

    # Default/unknown provider info
    return {
        "fullName": provider_name,
        "type": "Insurance Company",
        "founded": "N/A",
        "headquarters": "India",
        "about": f"{provider_name} is an insurance company operating in India.",
        "claimSettlementRatio": "N/A",
        "claimSettlementYear": "N/A",
        "customerSupport": {
            "phone": "N/A",
            "email": "N/A",
            "website": "N/A",
            "claimEmail": "N/A"
        },
        "specialties": [],
        "networkSize": "N/A",
        "irda": "N/A"
    }
