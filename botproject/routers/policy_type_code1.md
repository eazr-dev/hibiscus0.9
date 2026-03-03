def identify_policy_type_deepseek(text: str) -> str:
    """Identify policy type from document content using weighted keyword scoring.

    Uses a 2-phase approach:
      Phase 1 – Definitive keyword check: terms that ONLY appear in a specific
                policy type (e.g. "chassis no" is exclusively motor). A single
                match short-circuits to that type.
      Phase 2 – Weighted scoring across all types. Every keyword carries a
                weight (1-3). All types are scored simultaneously and the
                highest total wins. No early-return bias.

    Designed for the Indian insurance market – covers all major insurers
    (ICICI Lombard, HDFC ERGO, Bajaj Allianz, Tata AIG, New India, SBI General,
    Acko, Digit, Kotak, Iffco Tokio, Reliance, Royal Sundaram, Cholamandalam,
    National, Oriental, United India, etc.), policy structures, and IRDAI
    regulatory terminology.

    Handles cross-sell contamination (motor PDFs often include health/life ads).

    Supported types: health, motor, life, travel, home, pa, unknown
    """
    import logging as _log
    import re as _re
    _logger = _log.getLogger(__name__)
    text_lower = text.lower()
    # Normalize: collapse multiple whitespace, remove soft hyphens / zero-width
    # chars that break keyword matching for OCR-extracted text
    text_lower = _re.sub(r'[\u00ad\u200b\u200c\u200d\ufeff]', '', text_lower)
    text_lower = _re.sub(r'\s+', ' ', text_lower)

    _logger.info(">>> V2 WEIGHTED TYPE DETECTION RUNNING (not old priority-based) <<<")

    # ================================================================
    # PHASE 1 – DEFINITIVE KEYWORDS (single match → immediate return)
    # These terms exist ONLY in one policy type, never in cross-sell ads.
    # ================================================================

    # --- Motor definitive: terms exclusive to motor insurance ---
    motor_definitive = [
        # Policy structure sections
        'own damage premium', 'own damage policy period',
        'basic od premium', 'total own damage premium',
        'third party premium', 'total liability premium',
        'liability policy period',
        'section - i own damage', 'section - ii liability',
        'section i own damage', 'section ii liability',
        'section­i own damage', 'section­ii liability',
        # Vehicle identification
        'insured declared value', 'idv of vehicle', 'total idv',
        'chassis no', 'engine no',
        # Regulatory / Certificate of Insurance
        'motor vehicle act', 'motor vehicles act',
        'central motor vehicle rules', 'central motor vehicle',
        'form 51 of the central motor',
        'certificate of insurance and policy schedule',
        # Motor-only clauses
        'drivers clause', 'limitations as to use',
        'pa cover for owner driver', 'pa cover to owner driver',
        'compulsory pa cover for owner driver',
        'pa cover to unnamed passengers',
        'legal liability to paid driver',
        # Motor product names (Indian market)
        'auto secure', 'motor package policy',
        'private car package', 'two wheeler package',
        'commercial vehicle package',
        'standalone own damage', 'standalone od',
        # IMT endorsements (motor-only IRDAI endorsements)
        'imt 16', 'imt 22', 'imt 28', 'imt 07',
        'imt endorsement',
        # Motor add-on identifiers
        'engine secure', 'tyre secure', 'tyre protect',
        'return to invoice', 'depreciation reimbursement',
        'consumables expenses', 'consumable cover',
        'key replacement', 'key protect',
        'rim protect', 'windshield cover',
        'ncb protect', 'ncb protector',
        # Vehicle details table headers
        'cc/kw', 'mfg. year', 'mfg year',
        'rto location', 'rto code',
    ]
    motor_matches = [kw for kw in motor_definitive if kw in text_lower]
    if motor_matches:
        _logger.info(f">>> MOTOR DETECTED via Phase 1 definitive keywords: {motor_matches[:5]} <<<")
        return "motor"

    # --- Travel definitive: MUST be checked BEFORE health ---
    # Travel policies (especially from health insurers like Care Health) contain
    # many health keywords (hospitalization, cashless, pre-existing) that would
    # trigger health detection. Travel-exclusive terms must short-circuit first.
    travel_definitive = [
        # Product names (Indian market travel products)
        'explore asia', 'explore europe', 'explore worldwide',
        'travel guard', 'travel companion',
        'asia guard', 'asia guard gold', 'asiaguard',
        'travel protect', 'travel shield', 'travel secure',
        'travel infinity', 'travel elite', 'travel easy',
        'travel smart', 'star travel protect',
        'optima secure travel', 'travel max',
        # Travel-exclusive coverage terms
        'repatriation of mortal remains', 'loss of passport',
        'loss of checked-in baggage', 'checked-in baggage',
        'trip cancellation', 'trip interruption', 'trip delay',
        'trip curtailment',
        'baggage delay', 'baggage loss',
        'flight delay', 'hijack cover', 'hijack distress',
        'personal liability overseas', 'overseas medical',
        'country of travel', 'destination country',
        'schengen',
        'overseas mediclaim', 'overseas travel insurance',
        'loss of travel documents',
        'compassionate visit', 'sponsor protection',
        # Passport / travel document references
        'passport number', 'passport no',
        # Medical evacuation with repatriation (travel-exclusive combo)
        'medical evacuation and repatriation',
        # NOTE: 'geographical scope' and 'emergency medical evacuation' removed
        # from definitive — they appear in health policies as "Not Applicable"
        # fields. Kept in Phase 2 weighted scoring instead.
        # Currency-based sum insured (travel policies use foreign currency)
        'sum insured in usd', 'sum insured (usd)', 'sum insured (in usd)',
        'sum insured in eur', 'sum insured (eur)',
    ]
    travel_matches = [kw for kw in travel_definitive if kw in text_lower]
    if travel_matches:
        _logger.info(f">>> TRAVEL DETECTED via Phase 1 definitive keywords: {travel_matches[:5]} <<<")
        return "travel"

    # --- PA (Personal Accident) definitive: checked BEFORE health ---
    # PA/Guard plans from health insurers contain health keywords but are
    # fundamentally accident-only products with different scoring needs.
    pa_definitive = [
        'personal accident', 'personal accident cover',
        'personal guard', 'global personal guard',
        'accidental death benefit', 'accidental death and disablement',
        'accidental death',  # shorter form – PDF may say "Accidental Death 100% of SI"
        'permanent total disablement', 'permanent partial disablement',
        'permanent total disability benefit',
        'permanent partial disability benefit',
        'permanent total disability', 'permanent partial disability',
        'temporary total disablement', 'temporary total disability',
        'pa owner driver', 'group personal accident',
        'group care 360',  # EAZR company PA product
        'capital sum insured',  # PA-specific term for sum insured
    ]
    pa_matches = [kw for kw in pa_definitive if kw in text_lower]
    if len(pa_matches) >= 2:
        # PA-only keywords: if ANY of these match, it's definitely a PA policy
        # regardless of any health keywords (e.g. "cashless facility" in PA certs).
        pa_only_keywords = [
            'group care 360', 'personal guard', 'global personal guard',
            'group personal accident', 'pa owner driver',
        ]
        has_pa_only = any(kw in text_lower for kw in pa_only_keywords)

        if has_pa_only:
            _logger.info(f">>> PA DETECTED via PA-only keyword + definitive: {pa_matches[:5]} <<<")
            return "pa"

        # Anti-pattern: health policies with accident riders also match PA keywords.
        # If MULTIPLE strong health indicators are present, do NOT classify as PA.
        # Require >= 3 health anti-pattern matches to override PA (single matches
        # like "cashless facility" can appear in PA certificates too).
        health_anti_patterns = [
            'family floater', 'cashless hospitalization', 'cashless treatment',
            'pre-hospitalization', 'post-hospitalization',
            'domiciliary hospitalization', 'day care procedure',
            'hospitalization expenses', 'room rent', 'icu charges',
            'mediclaim', 'medicare', 'sum insured restoration',
            'restore benefit', 'cumulative bonus', 'network hospital',
        ]
        health_anti_matches = [kw for kw in health_anti_patterns if kw in text_lower]
        if len(health_anti_matches) >= 3:
            _logger.info(
                f">>> PA keywords found ({pa_matches[:5]}) but SKIPPED — "
                f"strong health signal ({len(health_anti_matches)} anti-patterns): "
                f"{health_anti_matches[:5]}. Falling through to health check. <<<"
            )
        else:
            _logger.info(f">>> PA DETECTED via Phase 1 definitive keywords: {pa_matches[:5]} <<<")
            return "pa"

    # --- Health definitive: terms exclusive to health insurance ---
    health_definitive = [
        'cashless hospitalization', 'cashless treatment',
        'cashless facility', 'network hospital',
        'pre-hospitalization', 'post-hospitalization',
        'domiciliary hospitalization', 'day care procedure',
        'family floater', 'sum insured restoration',
        'restore benefit', 'room rent limit',
        'icu charges', 'cumulative bonus',
        'mediclaim',
    ]
    if any(kw in text_lower for kw in health_definitive):
        return "health"

    # --- Life definitive ---
    life_definitive = [
        'sum assured', 'life assured', 'death benefit',
        'maturity benefit', 'surrender value',
        'mortality charge', 'fund value',
    ]
    if any(kw in text_lower for kw in life_definitive):
        return "life"

    # ================================================================
    # PHASE 2 – WEIGHTED SCORING (all types scored, highest wins)
    # Weight 3 = strong indicator, 2 = moderate, 1 = weak / shared term
    # ================================================================

    def _calc(kw_weights: dict, txt: str) -> int:
        return sum(w for kw, w in kw_weights.items() if kw in txt)

    # --- Motor keywords (comprehensive Indian market) ---
    motor_kw = {
        # Core motor terms
        'idv': 3, 'own damage': 3, 'third party liability': 3,
        'zero depreciation': 3, 'nil depreciation': 3,
        'vehicle insurance': 3, 'motor insurance': 3,
        'car insurance': 3, 'bike insurance': 3,
        'package policy': 2, 'comprehensive policy': 2,
        'third party only': 3, 'tp only': 3,
        'motor vehicle': 2,
        # Vehicle identification
        'chassis number': 3, 'engine number': 3,
        'registration number': 2, 'registration no': 2,
        'vehicle make': 2, 'vehicle model': 2,
        'make/model': 2, 'body type': 2, 'fuel type': 2,
        'cubic capacity': 2, 'manufacturing year': 2,
        'seating capacity': 2, 'geographical area': 2,
        'hypothecation': 2, 'hire purchase': 2,
        # Motor-specific add-ons
        'roadside assistance': 1, 'road side assistance': 1,
        'personal accident cover for owner': 2,
        'unnamed passengers': 2,
        'electrical accessories': 1, 'non-electrical accessories': 1,
        'bi-fuel': 1, 'cng kit': 1, 'lpg kit': 1,
        'loss of personal belongings': 1,
        'emergency transport': 1, 'hotel expenses': 1,
        # Premium structure
        'od premium': 2, 'tp premium': 2,
        'voluntary deductible': 2, 'compulsory deductible': 2,
        'imposed excess': 2,
        'no claim bonus': 1,  # shared with health, lower weight
        # Vehicle types
        'private car': 2, 'two wheeler': 2, 'four wheeler': 2,
        'commercial vehicle': 2, 'goods carrying': 2,
        'passenger carrying': 2, 'three wheeler': 2,
        'electric vehicle': 1,
        # Regulatory
        'certificate of insurance': 2,
    }

    # --- Health keywords (refined – removed motor-ambiguous terms) ---
    health_kw = {
        'hospitalization': 3,
        'room rent': 3, 'sub-limit': 2,
        'pre-existing disease': 3, 'waiting period': 2,
        'copay': 2, 'co-pay': 2,
        'daycare': 2, 'ambulance cover': 2,
        'health checkup': 2, 'ayush': 2,
        'organ donor': 2, 'maternity benefit': 2,
        'floater': 2,
        'health insurer': 2,
        # Lower weight – appear in motor cross-sell ads
        'medical expenses': 1,
        'health insurance': 1,
        # 'deductible' REMOVED – appears in motor policies too
    }

    # --- Life keywords ---
    life_kw = {
        'life insurance': 3, 'term insurance': 3, 'endowment': 3,
        'whole life': 3, 'life cover': 3,
        'ulip': 3, 'term plan': 3,
        'money back': 2, 'annuity': 2, 'pension plan': 2,
    }

    # --- Travel keywords (expanded for Indian travel insurance market) ---
    travel_kw = {
        'travel insurance': 3, 'trip insurance': 3,
        'overseas travel': 3, 'international travel': 3,
        'flight delay': 3, 'baggage loss': 3,
        'trip cancellation': 3, 'medical evacuation': 3,
        'passport loss': 2, 'loss of passport': 3,
        'repatriation': 3, 'baggage delay': 3,
        'trip delay': 3, 'trip interruption': 3,
        'trip curtailment': 3,
        'country of travel': 3, 'destination country': 3,
        'geographical scope': 2, 'schengen': 3,
        'checked-in baggage': 3, 'hijack': 2,
        'overseas medical': 2, 'personal liability overseas': 3,
        'explore asia': 3, 'explore europe': 3,
        'asia guard': 3, 'travel guard': 3,
        'compassionate visit': 3, 'loss of travel documents': 3,
        'sponsor protection': 2,
    }

    # --- PA (Personal Accident) keywords ---
    pa_kw = {
        'personal accident': 3, 'personal accident cover': 3,
        'accidental death': 3, 'accidental death benefit': 3,
        'permanent total disability': 3, 'permanent partial disability': 3,
        'permanent total disablement': 3, 'permanent partial disablement': 3,
        'temporary total disability': 3, 'temporary total disablement': 3,
        'capital sum insured': 2,
        'group personal accident': 3,
        'accidental death and disablement': 3,
        'personal guard': 3, 'global personal guard': 3,
        'pa cover': 2, 'pa insurance': 2,
        'disability schedule': 2, 'disablement schedule': 2,
        'scale of compensation': 2,
        'loss of limbs': 2, 'loss of sight': 2,
        'weekly benefit': 1, 'weekly compensation': 1,
    }

    # --- Home keywords ---
    home_kw = {
        'home insurance': 3, 'fire insurance': 3,
        'property insurance': 3, 'householder': 3,
        'building insurance': 3, 'contents insurance': 3,
        'burglary': 3, 'natural calamity': 2,
    }

    scores = {
        'motor': _calc(motor_kw, text_lower),
        'health': _calc(health_kw, text_lower),
        'life': _calc(life_kw, text_lower),
        'travel': _calc(travel_kw, text_lower),
        'home': _calc(home_kw, text_lower),
        'pa': _calc(pa_kw, text_lower),
    }

    max_type = max(scores, key=scores.get)
    if scores[max_type] == 0:
        return "unknown"

    return max_type


def fetch_policy_from_db_deepseek(uin: str, policy_type: str):
    """Fetch policy data and document_link from database based on UIN and policy type"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # PostgreSQL Database Configuration
        DB_CONFIG = {
            "host": os.getenv("TYPEORM_HOST", "eazr.ca3p8fstvky1.ap-south-1.rds.amazonaws.com"),
            "user": os.getenv("TYPEORM_USERNAME", "postgres"),
            "password": os.getenv("TYPEORM_PASSWORD", "xpt7Wt9layPaEEfxinwU"),
            "database": os.getenv("TYPEORM_DATABASE", "insurance_data"),
            "port": int(os.getenv("TYPEORM_PORT", "5432"))
        }

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Determine table name based on policy type
        table_map = {
            "health": "health_ins_masterdata",
            "life": "life_ins_masterdata",
            "non_life": "non_life_ins_masterdata"
        }

        table_name = table_map.get(policy_type)
        if not table_name:
            logger.warning(f"Unknown policy type: {policy_type}")
            return None

        # Query to fetch policy data including document_link (using exact column name "UIN")
        query = f'SELECT * FROM {table_name} WHERE "UIN" = %s LIMIT 1'
        cursor.execute(query, (uin,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            logger.info(f"Found policy in {table_name} with UIN: {uin}")
            result_dict = dict(result)

            # Check if document_link exists
            if 'document_link' in result_dict and result_dict['document_link']:
                logger.info(f"Document link found: {result_dict['document_link']}")
            else:
                logger.warning("No document_link found in database record")

            return result_dict
        else:
            logger.warning(f"No policy found in {table_name} with UIN: {uin}")
            return None

    except Exception as e:
        logger.error(f"Error fetching policy from database: {str(e)}")
        return None


def download_pdf_from_url_deepseek(url: str):
    """Download PDF from given URL and return as BytesIO"""
    try:
        import requests
        from io import BytesIO

        logger.info(f"Downloading PDF from URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        pdf_buffer = BytesIO(response.content)
        logger.info(f"Successfully downloaded PDF from URL")
        return pdf_buffer
    except Exception as e:
        logger.error(f"Error downloading PDF from URL: {str(e)}")
        return None


def extract_text_from_pdf_buffer_deepseek(pdf_buffer) -> str:
    """Extract text from PDF buffer"""
    try:
        import PyPDF2
        import pdfplumber
        from io import BytesIO

        extracted_text = ""

        # Try PyPDF2 first
        pdf_reader = PyPDF2.PdfReader(pdf_buffer)
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"

        # If PyPDF2 fails, try pdfplumber
        if not extracted_text.strip():
            pdf_buffer.seek(0)
            with pdfplumber.open(pdf_buffer) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() + "\n"

        logger.info(f"Extracted {len(extracted_text)} characters from PDF")
        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""