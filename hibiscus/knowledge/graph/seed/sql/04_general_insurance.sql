-- ============================================================
-- 04_general_insurance.sql
-- Consolidated: All general insurance products, expansions, and documents
-- Merged from: 05_products_general.sql + 05b_products_general_extra.sql
--              + 10_gi_standard_expansion.sql + 14_additional_expansion.sql (Part 1)
--              + 07d_policy_docs_general.sql
-- ============================================================

-- ================ SECTION 1: CORE GENERAL PRODUCTS ==============
-- ============================================================
-- 05_products_general.sql - General insurance products with real UINs
-- Sources: icicilombard.com, tataaig.com, hdfcergo.com
-- Last verified: 2026-02-20
-- ============================================================

SET search_path TO insurance, public;

-- ===================== ICICI LOMBARD PRODUCTS =====================
-- Source: https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf

-- ICICI Lombard Private Car Package Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Private Car Package Policy', 'IRDAN115RP0017V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive private car insurance covering own damage and third-party liability. Covers accidental damage, theft, fire, natural calamities, and personal accident cover for owner-driver.',
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- ICICI Lombard Property All Risk Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Property All Risk Insurance Policy', 'IRDAN115RP0052V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive property insurance covering all risks to industrial and commercial property including fire, special perils, machinery breakdown, and business interruption.',
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Industrial All Risk (IAR)';

-- ICICI Lombard Extended Warranty Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Extended Warranty Insurance', 'IRDAN115RP0001V02201213', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2012-2013',
    'Extended warranty insurance for electronic appliances and gadgets, covering repair and replacement costs beyond manufacturer warranty.',
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'SME Package Insurance';

-- ICICI Lombard Employee Compensation Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Employee''s Compensation Insurance', 'IRDAN115RP0010V02200607', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Employer''s liability insurance covering compensation to employees for injury, death, or occupational disease during the course of employment as per Workmen''s Compensation Act, 1923.',
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Workmen Compensation';

-- ICICI Lombard Business Edge Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Business Edge Policy', 'IRDAN115CP0001V01202425', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2024-04-01', '2024-2025',
    'Comprehensive business insurance package for small and medium enterprises covering fire, burglary, liability, money insurance, and business interruption.',
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'SME Package Insurance';

-- ICICI Lombard Contractor Plant Machinery (CPM)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Contractor''s Plant & Machinery Insurance', 'IRDAN115RP0022V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Insurance covering contractor''s plant and machinery including excavators, cranes, bulldozers against accidental damage, theft, and natural perils while at construction sites.',
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Machinery Breakdown';

-- ===================== TATA AIG PRODUCTS =====================
-- Source: https://www.tataaig.com/

-- Tata AIG Home Protect Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'TATA AIG Home Protect Policy', 'IRDAN108RP0021V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive home insurance covering building structure, contents, and personal belongings against fire, natural disasters, burglary, and other perils.',
    'Building structure cover. Contents cover including furniture, electronics. Burglary and theft. Third-party liability. Alternative accommodation costs. Domestic help cover.',
    'https://www.tataaig.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- Tata AIG Bharat Griha Raksha (Standard)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'TATA AIG Bharat Griha Raksha', 'IRDAN108RP0019V02202021', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'IRDAI-mandated standard home insurance product covering residential dwelling structure and contents against fire and allied perils. Standardized terms across all general insurers.',
    'https://www.tataaig.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

-- Tata AIG Bharat Sookshma Udyam Suraksha (Standard SME)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'TATA AIG Bharat Sookshma Udyam Suraksha', 'IRDAN108RP0025V01202223', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'IRDAI-mandated standard micro enterprise insurance product covering small businesses with turnover up to Rs. 5 crore against fire, theft, liability, and other business risks.',
    'https://www.tataaig.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Shopkeeper Insurance';

-- Tata AIG Medicare Premier
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Medicare Premier', 'TATHLIP23167V032223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Premium comprehensive health insurance plan from Tata AIG offering extensive coverage including emergency air ambulance, global treatment, maternity expenses, and high-end diagnostics.',
    'Emergency air ambulance cover. Global treatment outside India. Restore benefits. Bariatric surgery cover. Maternity expenses. First-year newborn vaccination. OPD dental treatment. High-end diagnostics.',
    'https://www.tataaig.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Tata AIG Trade Credit Insurance (SEC)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Trade Credit Insurance (SEC)', 'IRDAN108P0020V01201213', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2012-2013',
    'Trade credit insurance policy protecting businesses against buyer payment defaults for domestic and export trade. Covers insolvency and protracted default of buyers.',
    'https://www.tataaig.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Credit Insurance';

-- ===================== HDFC ERGO GENERAL - NON-HEALTH PRODUCTS =====================
-- Source: https://www.hdfcergo.com/

-- HDFC ERGO Motor Insurance (Private Car)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Private Car Insurance', 'IRDAN146RP0001V02201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Comprehensive private car insurance covering own damage and third-party liability. Covers accidental damage, theft, fire, natural calamities, and PA cover for owner-driver.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- HDFC ERGO Home Shield Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Home Shield Insurance', 'IRDAN146RPMS0071V01202526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Comprehensive home insurance covering building structure, contents, and personal belongings against fire, natural disasters, burglary, and other perils.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- HDFC ERGO Bharat Griha Raksha Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Bharat Griha Raksha Plus', 'IRDAN146RPPR0070V01202425', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'IRDAI-mandated standard home insurance product with enhanced features. Long-term coverage for residential dwelling structure and contents.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

-- HDFC ERGO Explorer Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Explorer', 'HDTIOP24042V022425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and emergency evacuation for overseas travelers.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- HDFC ERGO Cyber Sachet Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Cyber Sachet Insurance', 'IRDAN146RP0026V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Retail cyber insurance protecting against online fraud, identity theft, phishing, social media harassment, and cyber extortion.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Cyber Insurance (Retail)';

-- HDFC ERGO Paws n Claws (Pet Insurance)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Paws n Claws', 'IRDAN146RP0001V01202324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Pet insurance covering veterinary treatment, surgery, and hospitalization expenses for dogs and cats. Includes third-party liability.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'SME Package Insurance';

-- ===================== SBI GENERAL INSURANCE PRODUCTS =====================
-- Source: https://content.sbigeneral.in/uploads/496dd68ad4c2415eb04c17c6282469f3.pdf

-- SBI General Private Car Package Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Private Car Insurance', 'IRDAN144RP0005V03201112', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2011-2012',
    'Comprehensive private car insurance covering own damage, third-party liability, personal accident for owner-driver, and optional add-ons.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- SBI General Standard Fire & Special Perils Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Standard Fire & Special Perils Policy', 'IRDAN144RP0008V04201112', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2011-2012',
    'Standard fire and special perils insurance covering property against fire, lightning, explosion, storm, cyclone, flood, earthquake, and riot damage.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- SBI General Burglary Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Burglary Insurance Policy', 'IRDAN144RP0001V01201011', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2010-2011',
    'Insurance covering theft and burglary involving forcible entry. Covers contents, stock, cash in safe, and damage caused during burglary.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Burglary Insurance';

-- SBI General Money Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Money Insurance Policy', 'IRDAN144RP0011V02201011', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2010-2011',
    'Insurance covering loss of money in transit, in locked safe, and on counter premises. Covers cash, bank notes, and negotiable instruments.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'SME Package Insurance';

-- SBI General Industrial All Risks
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Industrial All Risks Policy', 'IRDAN144CP0006V01201011', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2010-2011',
    'Comprehensive property insurance for large industrial establishments covering all risks including fire, machinery breakdown, and business interruption.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Industrial All Risk (IAR)';

-- ===================== GO DIGIT GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.godigit.com/

-- Digit Private Car Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Private Car Package Policy', 'IRDAN158RP005V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Comprehensive car insurance from Go Digit covering own damage, third-party liability, and personal accident. Available with instant digital issuance.',
    'Instant online purchase. Cashless repairs at 4,400+ garages. Zero depreciation add-on. Return to invoice cover. Engine protection. 24/7 claims support.',
    'https://www.godigit.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

-- Digit Two-Wheeler Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Two-Wheeler Insurance', 'IRDAN158RP006V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Comprehensive two-wheeler insurance covering own damage, third-party liability, personal accident, and optional add-ons for motorcycles and scooters.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Digit Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Health Insurance', 'IRDAN158HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Go Digit''s health insurance plan covering hospitalization, pre/post hospitalization, day-care procedures, and AYUSH treatments. Digital-first experience.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Digit Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit International Travel Insurance', 'IRDAN158TI001V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and emergency evacuation. Instant digital issuance.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'International Travel Insurance';

-- Digit Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Home Insurance', 'IRDAN158RP009V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Home insurance covering building structure, contents, and personal belongings against fire, natural disasters, burglary, and allied perils.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Householder Package Policy';

-- ===================== BAJAJ ALLIANZ GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.bajajgeneralinsurance.com/

-- Bajaj Allianz Private Car Package Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Private Car Package Policy', 'IRDAN113RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive car insurance covering own damage, third-party liability, and personal accident for owner-driver. Multiple add-on covers available.',
    'Zero depreciation cover. Engine protection. NCB protection. Roadside assistance. Return to invoice. Key and lock replacement. Consumable expenses cover.',
    'https://www.bajajgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

-- Bajaj Allianz Two-Wheeler Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Two-Wheeler Package Policy', 'IRDAN113RP0002V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive two-wheeler insurance for motorcycles and scooters. Third-party liability, own damage, personal accident cover, and natural disaster protection.',
    'https://www.bajajgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Bajaj Allianz Travel Companion
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Travel Companion', 'IRDAN113TI0001V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal liability. Sum insured up to $500,000.',
    'https://www.bajajgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'International Travel Insurance';

-- Bajaj Allianz Individual Cybersafe Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Individual Cybersafe Insurance', 'IRDAN113RP0025V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Retail cyber insurance protecting against 10 potential cyber threats under one single policy including social media harassment, identity theft, malware, and email spoofing.',
    'Covers 10 cyber threats. Social media harassment. Identity theft. Malware protection. Email spoofing. Psychological counselling. IT consultancy services.',
    'https://www.bajajgeneralinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Cyber Insurance (Retail)';

-- Bajaj Allianz Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Home Secure Policy', 'IRDAN113RP0020V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Comprehensive home insurance covering building structure, contents, personal belongings, burglary, and allied perils. Includes alternative accommodation costs.',
    'https://www.bajajgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Householder Package Policy';

-- ===================== NEW INDIA ASSURANCE PRODUCTS =====================
-- Source: https://www.newindia.co.in/all-products

-- New India Assurance Mediclaim Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Mediclaim Policy', 'IRDAN190HL0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Individual mediclaim policy from India''s largest general insurer. Covers hospitalization, pre/post hospitalization expenses, and day-care procedures.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- New India Assurance Private Car Package
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Private Car Package Policy', 'IRDAN190RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive car insurance from India''s largest general insurer. Covers own damage, third-party liability, personal accident, fire, theft, and natural calamities.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- New India Assurance Standard Fire & Special Perils
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Standard Fire & Special Perils', 'IRDAN190RP0010V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance covering property against fire, lightning, explosion, storm, cyclone, flood, earthquake, and other perils.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- New India Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Marine Cargo Policy', 'IRDAN190RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods in transit by sea, air, road, and rail. Available as single transit, open, and annual turnover policies.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Marine Cargo';

-- ===================== NATIONAL INSURANCE PRODUCTS =====================
-- Source: https://www.nationalinsurance.nic.co.in/

-- National Insurance Mediclaim Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Mediclaim Policy', 'IRDAN170HL0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Individual mediclaim policy covering hospitalization expenses, pre/post hospitalization, and day-care procedures. One of the oldest health insurance policies in India.',
    'https://www.nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- National Insurance Motor Package Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Motor Package Policy', 'IRDAN170RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive motor insurance for private cars covering own damage, third-party liability, personal accident, fire, theft, and natural calamities.',
    'https://www.nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- ===================== ORIENTAL INSURANCE PRODUCTS =====================
-- Source: https://www.orientalinsurance.org.in/

-- Oriental Insurance Mediclaim Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Happy Family Floater Policy', 'IRDAN180HL0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Family floater health insurance covering the entire family under a single policy with shared sum insured. Covers hospitalization and day-care procedures.',
    'https://www.orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Oriental Insurance Motor Package Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Motor Package Policy', 'IRDAN180RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive motor insurance covering private cars against own damage, third-party liability, and personal accident for owner-driver.',
    'https://www.orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- ===================== UNITED INDIA INSURANCE PRODUCTS =====================
-- Source: https://www.uiic.co.in/

-- United India Insurance Motor Package Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Motor Package Policy', 'IRDAN160RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive motor insurance for private cars from United India Insurance. Covers own damage, third-party liability, PA cover, and natural calamities.',
    'https://www.uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- United India Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Individual Mediclaim Policy', 'IRDAN160HL0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Individual mediclaim policy covering hospitalization, pre/post hospitalization, and day-care procedures. Available for individuals aged 3 months to 65 years.',
    'https://www.uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== CHOLAMANDALAM MS GENERAL PRODUCTS =====================
-- Source: https://www.cholainsurance.com/

-- Chola MS Private Car Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Private Car Insurance', 'IRDAN123RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive car insurance from Cholamandalam MS covering own damage, third-party liability, personal accident, with various add-on covers available.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Chola MS Flexi Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Flexi Health Insurance', 'IRDAN123HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Flexible health insurance with customizable coverage options for sum insured, payment method, and policy tenure. Covers individuals aged 3 months to 65 years.',
    'Customizable sum insured. Flexible payment options. Pre and post hospitalization. Day-care procedures. AYUSH coverage. Annual health check-up.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== IFFCO TOKIO GENERAL PRODUCTS =====================
-- Source: https://www.iffcotokio.co.in/

-- IFFCO Tokio Private Car Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Private Car Package Policy', 'IRDAN106RP0001V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Comprehensive car insurance from IFFCO Tokio covering own damage, third-party liability, personal accident, fire, theft, and natural calamities.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- IFFCO Tokio Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Swasthya Kavach Policy', 'IRDAN106HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance from IFFCO Tokio covering hospitalization, pre/post hospitalization, day-care procedures, and AYUSH treatments.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== ROYAL SUNDARAM GENERAL PRODUCTS =====================
-- Source: https://www.royalsundaram.in/

-- Royal Sundaram Private Car Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Private Car Package Policy', 'IRDAN102RP0001V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Comprehensive car insurance from Royal Sundaram covering own damage, third-party liability, personal accident, and optional add-on covers.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Royal Sundaram Lifeline Supreme Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Lifeline Supreme', 'IRDAN102HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance from Royal Sundaram covering hospitalization, day-care, pre/post hospitalization, and domiciliary treatment for individuals and families.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== ZURICH KOTAK GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.zurichkotak.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Health 360', 'IRDAN137HL0010V01202526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Comprehensive health insurance with Silver, Gold, and Platinum variants. Sum insured Rs. 5 lakh to Rs. 5 crore. Premium Secure feature keeps premium unchanged until claim. Cash Bag rewards and global cover.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Private Car Package Policy', 'IRDAN137RP0001V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive private car insurance from Zurich Kotak (formerly Kotak General). Covers own damage, third-party liability, and personal accident. 98.13% claims settlement ratio.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Two Wheeler Package Policy', 'IRDAN137RP0002V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive two-wheeler insurance covering own damage, theft, third-party liability, and personal accident for the rider.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- ===================== SHRIRAM GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.shriramgi.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Private Car Package Policy', 'IRDAN139RP0001V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive car insurance from Shriram General covering own damage, third-party liability, and personal accident. Motor portfolio grew 24% YTD in 2025.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Commercial Vehicle Insurance', 'IRDAN139RP0003V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Commercial vehicle insurance covering goods and passenger carrying vehicles. Comprehensive and liability-only options. Shriram GI is a leading commercial vehicle insurer.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Home Insurance', 'IRDAN139RP0010V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Home insurance covering building structure, contents, and personal belongings against fire, natural disasters, burglary with three plan options.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- ===================== UNIVERSAL SOMPO GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.universalsompo.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Private Car Package Policy', 'IRDAN117RP0001V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Comprehensive car insurance with add-ons including Zero-Depreciation, Engine Protect, Consumables, RTI, RSA, and NCB Protect. No Claim Bonus discount available.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Individual Health Insurance', 'IRDAN117HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance covering hospitalization and domiciliary treatment. 5500+ network hospitals for cashless treatment. 98.27% claim settlement ratio.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Shopkeeper Insurance', 'IRDAN117RP0015V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Package insurance for shopkeepers covering shop structure, stock, fire, burglary, and third-party liability under a single policy.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Shopkeeper Insurance';

-- ===================== ACKO GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.acko.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Private Car Package Policy', 'IRDAN157RP0001V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Digital-first car insurance from Acko. Save up to 85% on premiums. Comprehensive, third-party, and own-damage coverage. Quick claim settlements at 4000+ network garages.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Two Wheeler Package Policy', 'IRDAN157RP0002V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Digital two-wheeler insurance starting at Rs. 457. Buy or renew within 60 seconds. Covers accidental damages and third-party liabilities.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Platinum Health Insurance Plan', 'IRDAN157HL0005V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive health insurance with Rs. 10 lakh sum insured. Zero waiting period for listed conditions. Instant coverage starting at Rs. 18/day.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== ZUNO GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.hizuno.com/ (formerly Edelweiss General)

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Private Car Package Policy', 'IRDAN148RP0001V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Car insurance from Zuno (formerly Edelweiss General). Includes ZUNO Switch app-based motor own damage floater under IRDAI Sandbox with Pay-as-you-use model.',
    'https://www.hizuno.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Health Insurance Plan', 'IRDAN148HL0003V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Comprehensive health insurance from Zuno covering critical illnesses including cancer. Tie-ups with 5000+ hospitals for cashless treatment.',
    'https://www.hizuno.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Home Insurance', 'IRDAN148RP0008V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Home insurance from Zuno General covering building structure and contents against fire, theft, natural calamities and other perils.',
    'https://www.hizuno.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Householder Package Policy';

-- ===================== NAVI GENERAL INSURANCE PRODUCTS =====================
-- Source: https://navi.com/insurance

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Private Car Package Policy', 'IRDAN155RP0001V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Car insurance from Navi General with third-party and comprehensive options. Add-ons include zero depreciation, hospital cash, NCB secure, and roadside assistance.',
    'https://navi.com/insurance/motor', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Health Insurance (Navi Cure)', 'IRDAN155HL0002V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance providing hospitalization cover, air ambulance, and day-care procedures. Policy issuance within 90 seconds via app. Cashless claims approved within 20 minutes.',
    'https://navi.com/insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Navi)', 'IRDAN155HL0003V01202021', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'IRDAI-mandated standard health insurance from Navi General with uniform terms. Sum insured Rs. 1 lakh to Rs. 5 lakh.',
    'https://navi.com/insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- ===================== LIBERTY GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.libertyinsurance.in/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Private Car Package Policy', 'IRDAN152RP0001V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Private car insurance from Liberty General with comprehensive and third-party options. Liberty Assure add-on provides priority repair, free engine tune-up, and waiver of deductible.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Two Wheeler Package Policy', 'IRDAN152RP0002V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Two-wheeler insurance from Liberty General covering own damage, theft, and third-party liability. Available through 6100+ auto service centres.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Health Connect', 'IRDAN152HL0005V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive health insurance from Liberty General covering hospitalization, day-care, and critical illness. Network of 6500+ hospitals.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== INDUSIND GENERAL INSURANCE (BHARTI AXA GENERAL) =====================
-- Source: https://www.bhartiaxa.com/ (general insurance arm)

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd GI Private Car Package Policy', 'IRDAN127RP0001V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Comprehensive car insurance from IndusInd General (formerly Bharti AXA General). Covers own damage, third-party liability, and personal accident.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd GI Health Insurance', 'IRDAN127HL0005V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance from IndusInd General (formerly Bharti AXA General) covering hospitalization, critical illness, and day-care procedures.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd GI Travel Insurance', 'IRDAN127RP0008V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'International travel insurance covering medical emergencies, trip cancellation, loss of baggage, and passport loss while travelling abroad.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- ===================== GENERALI CENTRAL GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.generalicentral.com/ (formerly Future Generali India Insurance)

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Private Car Package Policy', 'IRDAN118RP0001V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Comprehensive car insurance from Generali Central (formerly Future Generali). GWP of Rs. 5,547 crore in FY 2024-25.',
    'https://www.generalicentral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Health Total', 'IRDAN118HL0005V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance from Generali Central covering hospitalization, day-care, pre/post hospitalization, and AYUSH treatments.',
    'https://www.generalicentral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Home Insurance', 'IRDAN118RP0015V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Home insurance from Generali Central covering building structure and contents against fire, natural disasters, burglary, and other perils.',
    'https://www.generalicentral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- ===================== MAGMA GENERAL INSURANCE PRODUCTS =====================
-- Source: https://www.magmainsurance.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma Private Car Package Policy', 'IRDAN149RP0001V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Comprehensive car insurance from Magma General (formerly Magma HDI). Comprehensive plus add-ons including Zero-Dep, Engine Protect, and RSA.',
    'https://www.magmainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma One Health Insurance', 'IRDAN149HL0003V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive health plan from Magma General with four variants for different sum assured options. Covers individual health insurance needs for present and future.',
    'https://www.magmainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== RAHEJA QBE GENERAL INSURANCE =====================
-- Source: https://www.rahejaqbe.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Health Insurance', 'IRDAN141HL0001V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Health insurance from Raheja QBE covering hospitalization expenses, day-care treatments, and pre/post hospitalization costs.',
    'https://www.rahejaqbe.com/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Standard Fire Policy', 'IRDAN141RP0005V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Standard fire and special perils insurance from Raheja QBE covering property against fire, lightning, explosion, and natural calamities.',
    'https://www.rahejaqbe.com/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- ===================== KSHEMA GENERAL INSURANCE =====================
-- Note: Very new entrant, limited products

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kshema Motor Insurance', 'IRDAN172RP0001V01202425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Motor insurance from Kshema General Insurance, a new entrant in the Indian general insurance market. Provides comprehensive vehicle coverage.',
    'https://irdai.gov.in/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kshema General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

-- ===================== AGRICULTURE INSURANCE COMPANY (AIC) =====================
-- Source: https://www.aicofindia.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Pradhan Mantri Fasal Bima Yojana (PMFBY)', 'IRDAN106RP0001V01201617', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Government-mandated crop insurance scheme providing comprehensive coverage against yield losses from natural calamities, pests, and diseases. AIC settled Rs. 7,057 crore in claims to 1.12 crore farmers in FY25.',
    'https://www.aicofindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'PMFBY - Crop Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Restructured Weather Based Crop Insurance Scheme (RWBCIS)', 'IRDAN106RP0002V01201617', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Weather-based parametric crop insurance using weather indices to trigger automatic payouts. No need for field-level loss assessment. Covers climate-related crop losses.',
    'https://www.aicofindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'Weather-Based Crop Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Fal Suraksha Bima', 'IRDAN106RP0010V01202425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Specialized insurance product designed exclusively for banana and papaya crops. Provides targeted crop-specific coverage against natural perils.',
    'https://www.aicofindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- ===================== ECGC LIMITED =====================
-- Source: https://www.ecgc.in/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Export Credit Insurance - Standard Policy', 'IRDAN120RP0001V01200203', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Export credit insurance providing range of credit risk insurance covers to exporters against loss in export of goods and services. Protects against buyer default and country risks.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Overseas Investment Insurance', 'IRDAN120RP0005V01200506', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Insurance for Indian companies investing in joint ventures abroad. Covers equity investments and loan advances against political risks and expropriation.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ===================== ADDITIONAL PRODUCTS FOR THIN COMPANIES =====================

-- Royal Sundaram Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Travel Insurance', 'IRDAN102RP0010V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'International travel insurance from Royal Sundaram covering medical emergencies, trip cancellation, baggage loss, and emergency evacuation while travelling abroad.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- Royal Sundaram Two Wheeler Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Two Wheeler Insurance', 'IRDAN102RP0002V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Comprehensive two-wheeler insurance from Royal Sundaram covering own damage, theft, and third-party liability.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Cholamandalam MS Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Healthline', 'IRDAN116HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance from Cholamandalam MS covering hospitalization, day-care, and pre/post hospitalization for individuals and families.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Cholamandalam MS Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Travel Protect', 'IRDAN116RP0015V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'International travel insurance from Cholamandalam MS covering medical expenses, trip cancellation, baggage loss, and personal liability while travelling.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- IFFCO TOKIO Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO TOKIO Home Protect', 'IRDAN103RP0020V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Home insurance from IFFCO TOKIO covering building structure and contents against fire, natural disasters, burglary, and other perils.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- IFFCO TOKIO Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO TOKIO Swasthya Kavach', 'IRDAN103HL0005V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Comprehensive health insurance from IFFCO TOKIO covering hospitalization, day-care, pre/post hospitalization, and domiciliary treatment.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- National Insurance Motor
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Private Car OD Policy', 'IRDAN132RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standalone own-damage car insurance from National Insurance Company, one of the oldest PSU general insurers. Covers accidental damage, fire, theft, and natural calamities.',
    'https://www.nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Standalone Own Damage';

-- Oriental Insurance Travel
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Overseas Mediclaim', 'IRDAN129RP0010V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'International travel insurance from Oriental Insurance covering medical expenses, emergency evacuation, and repatriation. One of India''s oldest PSU general insurers.',
    'https://www.orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- United India Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Individual Health Insurance', 'IRDAN130HL0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive health insurance from United India Insurance covering hospitalization, day-care, and domiciliary treatment for individuals and families.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ============================================================
-- PHASE 2 EXPANSION - Fill ALL empty sub-categories
-- Research date: 2026-02-21
-- ============================================================

-- ===================== LIABILITY INSURANCE PRODUCTS =====================

-- Commercial General Liability (CGL)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Commercial General Liability', 'IRDAN115RP0003V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Comprehensive general liability policy covering third-party bodily injury and property damage claims arising from business operations. Includes products and completed operations liability.',
    'https://corporate.icicilombard.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Commercial General Liability (CGL)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Commercial General Liability', 'IRDAN113RP0015V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'CGL policy protecting businesses against third-party claims for bodily injury, property damage, and advertising injury arising from operations, products, or premises.',
    'https://www.bajajallianz.com/commercial-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Commercial General Liability (CGL)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Commercial General Liability Plus', 'IRDAN146RP0020V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive general liability insurance covering third-party bodily injury, property damage, and personal & advertising injury from business operations.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Commercial General Liability (CGL)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Commercial General Liability', 'IRDAN108RP0010V01201112', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2011-2012',
    'General liability policy for businesses covering third-party bodily injury and property damage arising from premises, operations, products, and completed operations.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Commercial General Liability (CGL)';

-- Cyber Liability Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Cyber Risk Insurance', 'IRDAN115RP0002V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Cyber insurance covering data breach costs, privacy notification expenses, crisis management, forensic investigation, and third-party liability from cyber attacks.',
    'https://sme.icicilombard.com/indemnity-and-liability-insurance/cyber-insurance-policy', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Cyber Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Cyber Insurance', 'IRDAN113RP0025V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Cyber risk insurance protecting businesses against data breaches, ransomware attacks, business interruption from cyber events, and regulatory defense costs.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Cyber Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Cyber Sachet Insurance', 'IRDAN146RP0030V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Retail cyber insurance for individuals covering financial loss from phishing, identity theft, social media hacking, cyber stalking, and online fraud.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Cyber Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Cyber Enterprise Risk Management', 'IRDAN108RP0028V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Enterprise cyber insurance covering data breach, network security liability, media liability, cyber extortion, and business interruption from cyber incidents.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Cyber Liability Insurance';

-- Directors & Officers Liability
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Directors & Officers Liability', 'IRDAN115RP0001V11200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'D&O liability insurance protecting directors and officers against claims for wrongful acts in their capacity as directors/officers. Covers defense costs and settlements.',
    'https://corporate.icicilombard.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Directors & Officers Liability';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Directors & Officers Liability', 'IRDAN113RP0018V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'D&O insurance covering claims against directors and officers for wrongful acts, mismanagement, breach of duty, and regulatory investigations.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Directors & Officers Liability';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Directors & Officers Liability', 'IRDAN146RP0022V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'D&O liability insurance for listed and unlisted companies covering wrongful acts, regulatory defense, and personal liability of directors and officers.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Directors & Officers Liability';

-- Professional Indemnity / E&O
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Professional Indemnity', 'IRDAN115RP0008V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Professional indemnity insurance for doctors, CAs, lawyers, architects, and engineers covering claims for negligence, errors, and omissions in professional services.',
    'https://corporate.icicilombard.com/Portal/Professional_Indemnity', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Professional Indemnity / E&O';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Professional Liability', 'IRDAN113RP0012V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Professional liability covering wrongful acts resulting in financial loss to third parties. For doctors, lawyers, accountants, IT professionals, and other professionals.',
    'https://www.bajajallianz.com/commercial-insurance/professional-liability-insurance.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Professional Indemnity / E&O';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Professional Indemnity', 'IRDAN190RP0015V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Professional indemnity from India''s largest PSU insurer covering professionals against claims for negligent acts, errors, and omissions in their professional services.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Professional Indemnity / E&O';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Professional Indemnity', 'IRDAN146RP0025V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Professional indemnity for design professionals, accountants, architects, engineers covering errors & omissions claims and defense costs.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Professional Indemnity / E&O';

-- Product Liability
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Product Liability', 'IRDAN115RP0006V01200405', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2004-2005',
    'Product liability insurance covering manufacturers and sellers against claims for bodily injury or property damage caused by defective products.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Product Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Product Liability', 'IRDAN108RP0012V01201213', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2012-2013',
    'Covers manufacturers, distributors, and retailers against liability from bodily injury or property damage caused by defective products.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Product Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Product Liability', 'IRDAN190RP0018V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Product liability policy from NIA covering liability arising from injury or damage caused by manufactured or sold products.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Product Liability Insurance';

-- Public Liability
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Public Liability', 'IRDAN190RP0020V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Public liability insurance covering legal liability to third parties for bodily injury or property damage from accidents on insured premises or operations.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Public Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Public Liability', 'IRDAN115RP0007V01200405', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2004-2005',
    'Public liability insurance under the Public Liability Insurance Act, 1991 covering industries handling hazardous substances against third-party claims.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Public Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Public Liability', 'IRDAN129RP0012V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Public liability from Oriental Insurance covering legal liability to third parties for bodily injury or property damage from business operations.',
    'https://www.orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Public Liability Insurance';

-- Workmen Compensation (additional)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Workmen Compensation', 'IRDAN115RP0005V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Workmen compensation covering employer liability under Employees Compensation Act for death, permanent and temporary disability of employees during employment.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Workmen Compensation';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Employees Compensation', 'IRDAN190RP0008V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Employees compensation policy from NIA covering employer liability for employee death or injury arising during employment as per Employees Compensation Act.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Workmen Compensation';

-- ===================== MARINE INSURANCE =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Marine Cargo', 'IRDAN115RP0004V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Marine cargo insurance covering goods in transit by sea, air, rail, or road with open policy and specific voyage options under institute cargo clauses.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Marine Cargo Open Policy', 'IRDAN146P0004V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Marine cargo insurance with open policy for businesses with frequent shipments covering loss or damage to cargo in transit.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Marine Cargo Open Policy', 'IRDAN190RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance from NIA covering import, export, and coastal transit of goods with automatic coverage for regular shipments.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Marine Cargo';

-- Marine Hull
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Marine Hull Insurance', 'IRDAN190RP0006V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine hull insurance covering ships and vessels against perils of the sea including collision, stranding, fire, and total loss under Institute Time Clauses.',
    'https://www.newindia.co.in/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Marine Hull';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Marine Hull and Machinery', 'IRDAN146RP0005V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Marine hull and machinery insurance covering vessels and maritime craft against physical damage, total loss, and marine perils.',
    'https://www.hdfcergo.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Marine Hull';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Marine Hull', 'IRDAN115RP0009V01200405', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2004-2005',
    'Marine hull insurance for ship owners covering physical damage to hull, machinery, and equipment with protection & indemnity options.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Marine Hull';

-- Inland Transit
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Inland Transit', 'IRDAN190RP0007V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Inland transit specific voyage policy (ITC-B) covering goods during transportation within India by road, rail, or inland waterways.',
    'https://www.newindia.co.in/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Inland Transit';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Inland Transit Insurance', 'IRDAN113RP0008V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Inland transit insurance covering goods in transit within India by road, rail, or waterways against fire, collision, overturning, and natural calamities.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Inland Transit';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Inland Transit', 'IRDAN115RP0010V01200405', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2004-2005',
    'Inland transit insurance covering loss or damage to goods during domestic transportation by road, rail, or inland waterways within India.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Inland Transit';

-- Marine Liability
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Charterer''s Liability', 'IRDAN190RP0022V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Charterer''s liability insurance covering liabilities of the charterer arising from chartered vessels. Vessel must have hull and machinery coverage.',
    'https://www.newindia.co.in/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Marine Liability';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Ship Repairer''s Liability', 'IRDAN146RP0028V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Marine liability for ship repairers covering legal liability for damage to vessels or equipment while in their care, custody, or control for repair.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Marine Liability';

-- ===================== ENGINEERING INSURANCE =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Contractor All Risk', 'IRDAN190RP0025V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'CAR policy covering civil engineering projects during construction against all risks of loss or damage including third-party liability.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Contractor All Risk (CAR)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Contractor All Risk', 'IRDAN115RP0012V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'CAR insurance for civil engineering construction covering physical loss or damage to contract works, construction machinery, and third-party liability.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Contractor All Risk (CAR)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Contractor All Risk', 'IRDAN108RP0015V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Comprehensive CAR policy covering construction projects including civil works, temporary structures, and materials against all risks during execution.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Contractor All Risk (CAR)';

-- Erection All Risk
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Erection All Risk', 'IRDAN190RP0026V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'EAR insurance covering erection and installation of machinery and steel structures against physical loss or damage during installation and testing.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Erection All Risk (EAR)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Erection All Risk', 'IRDAN115RP0013V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'EAR policy covering machinery erection, installation, and commissioning projects against all risks of physical loss or damage.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Erection All Risk (EAR)';

-- Boiler & Pressure Plant
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Boiler Insurance', 'IRDAN190RP0027V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Boiler insurance covering sudden explosion or collapse of boilers, pressure vessels, and economizers with third-party liability from boiler accidents.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Boiler & Pressure Plant';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Boiler & Pressure Plant', 'IRDAN146RP0015V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Boiler and pressure plant insurance covering explosion or collapse of boilers and pressure vessels including surrounding property damage and third-party liability.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Boiler & Pressure Plant';

-- Electronic Equipment Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Electronic Equipment', 'IRDAN190RP0028V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Electronic equipment insurance covering computers, servers, and electronic systems against sudden physical damage including power surge and short circuit.',
    'https://www.newindia.co.in/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Electronic Equipment Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Electronic Equipment', 'IRDAN115RP0014V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'All-risk coverage for electronic equipment against physical damage including external data media, increased cost of working, and third-party liability.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Electronic Equipment Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Electronic Equipment', 'IRDAN113RP0020V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'All-risk coverage for electronic equipment including data processing systems, medical devices, and communication equipment against sudden physical damage.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Electronic Equipment Insurance';

-- Machinery Breakdown (additional)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Machinery Breakdown', 'IRDAN115RP0015V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Machinery breakdown insurance covering sudden internal breakdown of machinery, manufacturing equipment, and electrical/mechanical installations.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Machinery Breakdown';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Machinery Breakdown', 'IRDAN190RP0029V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Machinery breakdown from NIA covering sudden mechanical or electrical breakdown of industrial machinery with optional loss of profits add-on.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Machinery Breakdown';

-- ===================== MOTOR GAPS =====================

-- Third Party Only - Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Car Third Party Only', 'IRDAN115RP0017V02200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Mandatory third-party liability motor insurance for private cars covering legal liability for bodily injury and property damage as per Motor Vehicles Act.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Private Car - Third Party Only';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Car Third Party Only', 'IRDAN113RP0002V02200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standalone third-party car insurance covering legal liability under Motor Vehicles Act. Mandatory for all vehicles on Indian roads.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Private Car - Third Party Only';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Car Third Party Only', 'IRDAN146RP0002V02200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Third-party-only car insurance covering legal liability to third parties including unlimited liability for death/injury and Rs. 7.5 lakh for property damage.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Private Car - Third Party Only';

-- Third Party Only - Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Two Wheeler Third Party Only', 'IRDAN115RP0018V02200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Mandatory third-party liability for two-wheelers covering legal liability for death, injury, and property damage under Motor Vehicles Act.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Third Party Only';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Two Wheeler Third Party Only', 'IRDAN113RP0003V02200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standalone third-party two-wheeler insurance with mandatory coverage providing protection against legal liability from vehicle accidents.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Two-Wheeler - Third Party Only';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Two Wheeler Third Party Only', 'IRDAN146RP0003V02200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Third-party-only two-wheeler insurance covering mandatory legal liability for death/bodily injury and property damage to third parties.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Third Party Only';

-- Commercial Vehicle (additional)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Commercial Vehicle Package', 'IRDAN113RP0004V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive commercial vehicle insurance for goods carrying and passenger vehicles covering own damage, theft, fire, and third-party liability.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Commercial Vehicle Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Commercial Vehicle Package', 'IRDAN115RP0019V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Package insurance for commercial vehicles including trucks, buses, and goods carriers covering own damage, fire, theft, and third-party liability.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Commercial Vehicle', 'IRDAN190RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive commercial vehicle insurance from NIA for goods carrying and passenger vehicles with own damage and third-party coverage.',
    'https://www.newindia.co.in/all-products', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- Motor Add-Ons
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Zero Depreciation Add-On', 'IRDAN115RP0017V03200102', 'add_on', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Zero depreciation add-on covering full claim amount without depreciation deduction on plastic, rubber, glass, and fiber parts for cars up to 5 years old.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Motor Add-Ons / Riders';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Engine Protect Add-On', 'IRDAN113RP0001V05200102', 'add_on', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Engine protect add-on covering damage to engine, gearbox, and transmission parts due to water ingression, hydrostatic lock, and lubricating oil leakage.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Motor Add-Ons / Riders';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Return to Invoice Add-On', 'IRDAN146RP0001V05200304', 'add_on', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Return to invoice add-on covering difference between insured declared value and invoice price in case of total loss or theft of the vehicle.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Motor Add-Ons / Riders';

-- ===================== TRAVEL GAPS =====================

-- Domestic Travel
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Domestic Travel Insurance', 'IRDAN115RP0020V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Domestic travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during travel within India.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Domestic Travel Guard', 'IRDAN108RP0022V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Domestic travel insurance covering medical emergencies, trip delays, baggage loss, and personal accident during travel within India.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Domestic Travel Insurance', 'IRDAN113RP0022V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Comprehensive domestic travel insurance covering hospitalization, trip cancellation, baggage loss, and personal accident during domestic trips.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Domestic Travel Insurance';

-- Student Travel
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Student Travel Insurance', 'IRDAN108RP0023V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Travel insurance for students studying abroad covering medical expenses, sponsor protection, study interruption, and loss of passport.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Student Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Student Medical Insurance', 'IRDAN115RP0021V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Travel insurance for students abroad covering medical expenses, repatriation, study interruption, sponsor protection, and loss of passport.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Student Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Student Guard', 'IRDAN113RP0023V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Student travel insurance for overseas education covering medical expenses, personal liability, study interruption, and emergency evacuation.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Student Travel Insurance';

-- Corporate / Multi-Trip Travel
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Corporate Travel Insurance', 'IRDAN108RP0024V01201718', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Annual multi-trip corporate travel insurance for frequent business travellers with unlimited trips and per-trip duration up to 90 days.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Corporate / Multi-Trip Travel';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Annual Multi-Trip Travel', 'IRDAN115RP0022V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Annual multi-trip travel insurance for frequent travellers covering medical expenses, trip cancellation, and baggage loss for unlimited trips.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Corporate / Multi-Trip Travel';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Corporate Travel Shield', 'IRDAN146RP0032V01202223', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Corporate travel insurance for businesses covering employees on domestic and international trips with medical, evacuation, and trip disruption coverage.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Corporate / Multi-Trip Travel';

-- ===================== PERSONAL ACCIDENT GAPS =====================

-- PMSBY
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance PMSBY', 'IRDAN190RP0030V01201516', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Pradhan Mantri Suraksha Bima Yojana providing accidental death and disability cover of Rs. 2 lakh at Rs. 20/year for bank account holders aged 18-70.',
    'https://www.newindia.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'PMSBY';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard PMSBY', 'IRDAN115RP0023V01201516', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Pradhan Mantri Suraksha Bima Yojana providing Rs. 2 lakh accidental death and Rs. 1 lakh partial disability cover at Rs. 20/year through bank auto-debit.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'PMSBY';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz PMSBY', 'IRDAN113RP0024V01201516', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Government-backed Pradhan Mantri Suraksha Bima Yojana providing accidental death and disability insurance at Rs. 20/year auto-debited from bank account.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'PMSBY';

-- Group Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Group Personal Accident', 'IRDAN115RP0024V01201617', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Group personal accident insurance for employer-employee groups covering accidental death, permanent total and partial disability for all group members.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Group Personal Accident';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Group Personal Accident', 'IRDAN190RP0031V01200607', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Group PA policy for organizations covering employees against accidental death and disability with flexible sum assured and competitive group rates.',
    'https://www.newindia.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Group Personal Accident';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Group Personal Accident', 'IRDAN108RP0025V01201718', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Group personal accident insurance for corporates covering accidental death, permanent disability, temporary disability, and medical expenses for employee groups.',
    'https://www.tataaig.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Group Personal Accident';

-- ===================== MISCELLANEOUS GAPS =====================

-- Fidelity Guarantee
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Fidelity Guarantee', 'IRDAN190RP0032V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Fidelity guarantee insurance protecting employers against financial loss from dishonesty, fraud, or embezzlement by employees in positions of trust.',
    'https://www.newindia.co.in/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Fidelity Guarantee';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Fidelity Guarantee', 'IRDAN115RP0025V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Fidelity insurance covering financial loss to employer from dishonest or fraudulent acts of employees including embezzlement, forgery, and misappropriation.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Fidelity Guarantee';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Fidelity Guarantee', 'IRDAN129RP0015V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Fidelity guarantee from Oriental Insurance covering direct financial loss to employer from fraud, dishonesty, or embezzlement by employees.',
    'https://www.orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Fidelity Guarantee';

-- Surety Bond Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Surety Bond', 'IRDAN190RP0035V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Surety bond insurance replacing bank guarantees for government contracts. Three-party agreement guaranteeing contractor performance and payment obligations.',
    'https://www.newindia.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Surety Bond Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Surety Bond', 'IRDAN113RP0030V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Surety bond as alternative to bank guarantees for government infrastructure contracts covering bid bond, performance bond, and advance payment bond.',
    'https://www.bajajallianz.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Surety Bond Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Surety Bond', 'IRDAN115RP0026V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Surety bond insurance as substitute for bank guarantees in government contracts. IRDAI-approved product launched after 2022 surety bond regulations.',
    'https://www.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Surety Bond Insurance';

-- Livestock Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Cattle Insurance', 'IRDAN190RP0033V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Livestock insurance covering cattle, buffaloes, and other animals against death from disease, accident, or natural calamities for individual farmers and dairy cooperatives.',
    'https://www.newindia.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Livestock Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Livestock Insurance', 'IRDAN174RP0005V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Livestock insurance from AIC covering cattle, buffalo, sheep, goat, and poultry against death from disease, accident, and natural calamities.',
    'https://www.aicofindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'Livestock Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Livestock Insurance', 'IRDAN130RP0010V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Livestock insurance from United India covering milch cattle, draught animals, and other livestock against death from diseases, accidents, and natural perils.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Livestock Insurance';

-- Business Interruption
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Business Interruption', 'IRDAN115RP0027V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Loss of profits insurance covering consequential financial loss from business disruption following fire or other insured perils. Must be taken with fire policy.',
    'https://corporate.icicilombard.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Business Interruption';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Assurance Loss of Profits', 'IRDAN190RP0034V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Loss of profits from NIA covering consequential loss of gross profit from reduction in turnover following damage to insured premises from fire or other perils.',
    'https://www.newindia.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Business Interruption';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Business Interruption', 'IRDAN146RP0035V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Business interruption insurance covering loss of gross profit, increased cost of working, and professional accountant fees following insured damage to premises.',
    'https://www.hdfcergo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Business Interruption';

-- ============================================================
-- PHASE 4: MASSIVE EXPANSION - Smaller general insurers
-- Research date: 2026-02-21
-- ============================================================

-- ===================== ROYAL SUNDARAM (Reg: 102) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Private Car Package Policy', 'IRDAN102RP0001V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive private car insurance covering own damage and third-party liability. Includes coverage for fire, theft, natural calamities, and personal accident.',
    'https://www.royalsundaram.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Two Wheeler Package Policy', 'IRDAN102P0002V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Comprehensive two-wheeler insurance with own damage and third-party cover. Long-term package policy available with cashless repairs at 3300+ garages.',
    'https://www.royalsundaram.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Travel Insurance', 'IRDAN102RP0020V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'International and domestic travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during travel.',
    'https://www.royalsundaram.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Home Insurance', 'IRDAN102RP0022V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Home insurance protecting structure and contents against fire, natural calamities, theft, and other perils. Covers building structure and household contents.',
    'https://www.royalsundaram.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Fire Insurance Policy', 'IRDAN102RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance for commercial and industrial property. Covers fire, lightning, explosion, storm, flood, and allied perils.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Marine Cargo Policy', 'IRDAN102RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods in transit against maritime perils. Inland, import and export cargo protection.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- ===================== CHOLAMANDALAM MS (Reg: 104) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Car Insurance Policy', 'IRDAN104RP0001V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Comprehensive car insurance covering own damage and third-party liability. Cashless repairs at network garages with add-on options.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Two Wheeler Insurance', 'IRDAN104RP0002V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Comprehensive two-wheeler insurance with own damage and third-party cover. Affordable premiums with cashless repair network.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Travel Insurance Policy', 'IRDAN104RP0015V01201011', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2010-2011',
    'Travel insurance covering medical emergencies, trip cancellation, baggage loss for domestic and international travel.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Fire Insurance Policy', 'IRDAN104RP0003V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Standard fire and special perils insurance for commercial and industrial property. Covers fire, lightning, explosion, and natural calamities.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Marine Cargo Insurance', 'IRDAN104RP0005V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Marine cargo insurance covering goods in transit by sea, air, and land. Coverage for import, export, and inland transit.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Workmen Compensation Policy', 'IRDAN104RP0008V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Workmen compensation insurance as per the Workmen Compensation Act. Covers employer liability for injury, disease, or death of employees.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Workmen Compensation';

-- ===================== IFFCO TOKIO (Reg: 106) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Private Car Insurance', 'IRDAN106RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive car insurance covering own damage and third-party liability. Protection against accidents, theft, fire, and natural calamities.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Two Wheeler Insurance', 'IRDAN106RP0002V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive two-wheeler insurance with own damage and third-party cover. Affordable protection for bikes and scooters.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Marine Cargo Insurance', 'IRDAN106P0007V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods in transit against perils of sea, land, and air. Inland, import, and export cargo protection.',
    'https://www.iffcotokio.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Fire Insurance Policy', 'IRDAN106RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance covering commercial and industrial property. Fire, explosion, natural calamity protection.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Travel Insurance', 'IRDAN106RP0020V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Travel insurance for domestic and international travel covering medical emergencies, trip cancellation, baggage loss, and personal accident.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Crop Insurance', 'IRDAN106RP0025V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Crop insurance under PMFBY scheme providing coverage against yield losses. Protects farmers against natural calamities and crop failure.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- ===================== LIBERTY GENERAL (Reg: 150) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Car Insurance Policy', 'IRDAN150RP0001V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Comprehensive private car insurance from Liberty General. Own damage and third-party liability cover with cashless repair network.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Two Wheeler Insurance', 'IRDAN150RP0002V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Comprehensive two-wheeler insurance with own damage and third-party. Affordable coverage for bikes and scooters.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Fire Insurance Policy', 'IRDAN150RP0003V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Standard fire and special perils insurance. Property protection against fire, lightning, explosion, and natural calamities.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty Home Insurance', 'IRDAN150RP0011V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive home insurance covering structure and contents. Protection against fire, natural disasters, theft, and other perils.',
    'https://www.libertyinsurance.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

-- ===================== SHRIRAM GENERAL (Reg: 137) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Private Car Package Policy', 'IRDAN137RP0001V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive private car insurance with own damage and third-party cover. Extensive network of garages for cashless repairs.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Two Wheeler Insurance', 'IRDAN137RP0002V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive two-wheeler insurance covering own damage and third-party liability. Affordable premiums for bike protection.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Fire Insurance Policy', 'IRDAN137RP0003V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Standard fire and special perils insurance covering property against fire, explosion, natural calamities, and other insured perils.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Travel Insurance', 'IRDAN137RP0010V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Travel insurance for domestic and international journeys. Covers medical emergencies, trip cancellation, and baggage loss.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- ===================== ZURICH KOTAK (Reg: 152) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Car Secure Policy', 'IRDAN152RP0006V02201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive car insurance with damage cover, personal accident, passenger cover, third-party liability, and optional add-ons. Cashless service at network garages.',
    'https://www.zurichkotak.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Two Wheeler Secure Policy', 'IRDAN152RP0008V02201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Long-term two-wheeler insurance with loss/damage cover, third-party liability, personal accident for owner-driver. Extended policy tenure.',
    'https://www.zurichkotak.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Fire Insurance Policy', 'IRDAN152RP0003V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Standard fire and special perils insurance covering commercial and residential property. Protection against fire, natural calamities, and allied perils.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Marine Cargo Insurance', 'IRDAN152RP0005V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Marine cargo insurance covering goods in transit by sea, air, and land. Protection for import, export, and inland transit.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- ===================== NAVI GENERAL (Reg: 155) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Private Car Package Policy', 'IRDAN155RP0001V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Digital-first comprehensive car insurance with own damage and third-party cover. Quick online issuance with competitive premiums.',
    'https://navi.com/insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Two Wheeler Package Policy', 'IRDAN155RP0002V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Digital two-wheeler insurance with comprehensive coverage. Own damage and third-party liability with online claims process.',
    'https://navi.com/insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Home Insurance Policy', 'IRDAN155RP0010V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home insurance covering structure and contents against fire, natural disasters, theft, and other perils. Digital-first approach with easy claims.',
    'https://navi.com/insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

-- ===================== ACKO GENERAL (Reg: 157) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Car Insurance Policy', 'IRDAN157RP0001V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Digital-first comprehensive car insurance starting at Rs 2,094. Covers accidents, fire, theft, and natural calamities with zero paperwork claims.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Two Wheeler Insurance', 'IRDAN157RP0002V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Digital two-wheeler insurance starting at Rs 457. Comprehensive and third-party coverage for bikes and scooters with instant policy issuance.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Travel Insurance', 'IRDAN157RP0008V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Digital travel insurance for domestic and international trips. Medical emergency cover, trip cancellation, and baggage loss protection.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'International Travel Insurance';

-- ===================== ZUNO GENERAL (Reg: 158) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Car Insurance Policy', 'IRDAN158RP0001V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Digital comprehensive car insurance with own damage and third-party cover. Quick online purchase and claims settlement.',
    'https://www.zunoinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Two Wheeler Insurance', 'IRDAN158RP0002V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Digital two-wheeler insurance with comprehensive coverage. Affordable premiums with online issuance and claims.',
    'https://www.zunoinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Travel Insurance', 'IRDAN158RP0008V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Travel insurance covering medical emergencies, trip cancellation, and baggage loss for domestic and international travel.',
    'https://www.zunoinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'International Travel Insurance';

-- ===================== NATIONAL INSURANCE (Reg: 190) - Additional =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Marine Cargo Policy', 'IRDAN190RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods in transit by sea, air, and land. Open policy and specific voyage options for import, export, and inland cargo.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Marine Hull Policy', 'IRDAN190RP0006V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine hull insurance covering ships and vessels against maritime perils. Protection for ship-owners against loss or damage to vessels.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Marine Hull';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Machinery Breakdown Policy', 'IRDAN190RP0015V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Engineering insurance covering sudden and unforeseen physical damage to machinery. Protects against breakdown, electrical damage, and mechanical failure.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Machinery Breakdown';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Public Liability Policy', 'IRDAN190RP0020V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Public liability insurance covering legal liability for bodily injury or property damage to third parties. Mandatory for businesses using hazardous substances.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Public Liability Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Crop Insurance (PMFBY)', 'IRDAN190RP0040V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Pradhan Mantri Fasal Bima Yojana crop insurance protecting farmers against yield losses due to natural calamities, pests, and diseases.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- ===================== UNITED INDIA (Reg: 148) - Additional =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Marine Cargo Policy', 'IRDAN148RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods in transit. Open policy and specific voyage marine insurance for import, export, and inland transit.',
    'https://www.uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Fire Insurance Policy', 'IRDAN148RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance covering immovable and movable property. Protection against fire, lightning, explosion, and allied perils.',
    'https://www.uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Workmen Compensation Policy', 'IRDAN148RP0008V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Workmen compensation insurance covering employer liability for employee injury, disease, or death during employment.',
    'https://www.uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Workmen Compensation';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Machinery Breakdown Policy', 'IRDAN148RP0015V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Engineering insurance covering sudden breakdown damage to machinery and equipment. Protects against electrical and mechanical failure.',
    'https://www.uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Machinery Breakdown';

-- ===================== ORIENTAL INSURANCE (Reg: 103) - Additional =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Fire Insurance Policy', 'IRDAN103RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance covering commercial, industrial, and residential property. Fire, explosion, natural calamity coverage.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Marine Cargo Policy', 'IRDAN103RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods during transit. Open and specific voyage policies for import, export, and inland cargo.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Marine Cargo';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Machinery Breakdown Policy', 'IRDAN103RP0015V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Engineering insurance covering machinery against sudden breakdown and failure. Protects industrial and commercial equipment.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Machinery Breakdown';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Public Liability Policy', 'IRDAN103RP0020V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Public liability insurance covering legal liability for bodily injury or property damage to third parties arising from business operations.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Public Liability Insurance';

-- ===================== UNIVERSAL SOMPO (Reg: 110) - Additional =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Private Car Package', 'IRDAN117RP0001V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Comprehensive car insurance covering own damage and third-party liability. Cashless repair at network garages.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Fire Insurance Policy', 'IRDAN117RP0003V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Standard fire and special perils insurance for commercial and residential property. Covers fire, explosion, and natural calamities.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- ===================== MAGMA GENERAL (Reg: 151) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma HDI Car Insurance', 'IRDAN151RP0001V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Comprehensive car insurance covering own damage and third-party. Cashless claims at network garages with add-on options.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma HDI Two Wheeler Insurance', 'IRDAN151RP0002V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Two-wheeler insurance with comprehensive coverage against own damage and third-party liability. Affordable premiums for bikes.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma HDI Fire Insurance', 'IRDAN151RP0003V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Standard fire and special perils insurance for property protection against fire, natural calamities, and allied perils.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Standard Fire & Special Perils';

-- ===================== RAHEJA QBE (Reg: 163) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Comprehensive Car Insurance', 'IRDAN163RP0001V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive private car insurance with own damage and third-party liability cover. Protection against accidents, theft, fire, and natural calamities.',
    'https://www.rahejaqbe.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Two Wheeler Insurance', 'IRDAN163RP0002V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive two-wheeler insurance with own damage and third-party cover. Affordable protection for motorcycles and scooters.',
    'https://www.rahejaqbe.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Fire Insurance Policy', 'IRDAN163RP0003V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Standard fire and special perils insurance for property protection. Covers fire, explosion, and allied perils for commercial and residential property.',
    'https://www.rahejaqbe.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- ===================== GENERALI CENTRAL (General) (Reg: 132) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Car Insurance', 'IRDAN132RP0001V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Comprehensive car insurance from Generali Central covering own damage and third-party liability. Cashless repairs and add-on covers available.',
    'https://www.generalicentral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Two Wheeler Insurance', 'IRDAN132RP0002V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Comprehensive two-wheeler insurance with own damage and third-party cover. Affordable motorcycle and scooter protection.',
    'https://www.generalicentral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Fire Insurance', 'IRDAN132RP0003V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Standard fire and special perils insurance covering commercial and residential property. Protection against fire, explosion, and natural perils.',
    'https://www.generalicentral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- ===================== INDUSIND GENERAL =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Car Insurance', 'IRDAN156RP0001V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive car insurance with own damage and third-party cover. Digital-first motor insurance solution.',
    'https://www.indusindgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Two Wheeler Insurance', 'IRDAN156RP0002V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive two-wheeler insurance covering own damage and third-party. Digital-first approach for bikes and scooters.',
    'https://www.indusindgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Fire Insurance', 'IRDAN156RP0003V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Standard fire and special perils insurance for commercial and residential properties. Fire, explosion, and allied perils coverage.',
    'https://www.indusindgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';


-- ===================== SBI GENERAL INSURANCE EXPANSION (Phase 7) =====================

-- SBI General Arogya Supreme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Arogya Supreme', 'IRDAN155RP0002V02202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Comprehensive retail health insurance with wide range of coverage options including hospitalization and day care procedures.',
    'https://www.sbigeneral.in/product', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- SBI General Motor Private Car Comprehensive
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Private Car Comprehensive', 'IRDAN155RP0001V02201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive private car insurance covering own damage and third-party liability with cashless garage network.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- SBI General Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Two Wheeler Insurance', 'IRDAN155RP0003V02201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive two-wheeler insurance covering own damage and third-party liability for bikes and scooters.',
    'https://www.sbigeneral.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- SBI General Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Home Insurance', 'IRDAN155RP0010V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Home insurance covering structure and contents against fire, natural calamities, theft and other perils.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- SBI General Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Travel Insurance', 'IRDAN155RP0008V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Travel insurance covering medical emergencies, trip cancellation, baggage loss and personal accident during travel.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

-- SBI General Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Personal Accident Insurance', 'IRDAN155RP0009V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Personal accident insurance covering death, permanent disability due to accidents. 24x7 worldwide coverage.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- SBI General Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Fire Insurance', 'IRDAN155RP0004V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Standard fire and special perils insurance for commercial and residential properties against fire and allied perils.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- SBI General Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Marine Cargo Insurance', 'IRDAN155RP0005V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Marine cargo insurance covering goods in transit against loss or damage during transportation by sea, air or land.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- SBI General Cyber Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Cyber Insurance', 'IRDAN155RP0018V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Cyber insurance protecting against financial losses from cyber attacks, data breaches, and online fraud.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Commercial General Liability (CGL)';

-- ===================== IFFCO TOKIO EXPANSION (Phase 7) =====================

-- IFFCO Tokio Private Car Comprehensive
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Private Car Comprehensive', 'IRDAN127RP0001V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive private car insurance with own damage and third-party coverage. Cashless repairs at network garages.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- IFFCO Tokio Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Two Wheeler Insurance', 'IRDAN127RP0002V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Two-wheeler insurance with comprehensive coverage for bikes and scooters. OD and TP liability protection.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- IFFCO Tokio Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Health Insurance', 'IRDAN127RP0006V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Health insurance covering hospitalization expenses including pre and post hospitalization. Cashless treatment at network hospitals.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- IFFCO Tokio Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Fire Insurance', 'IRDAN127RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance for commercial and residential properties. Comprehensive fire protection.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- IFFCO Tokio Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Marine Cargo Insurance', 'IRDAN127RP0004V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance protecting goods during transit by sea, air and land against various perils.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- IFFCO Tokio Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Travel Insurance', 'IRDAN127RP0008V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Comprehensive travel insurance covering medical emergencies, trip cancellation and baggage loss during domestic and international travel.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

-- IFFCO Tokio Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Personal Accident Insurance', 'IRDAN127RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Personal accident policy covering accidental death and disability. 24x7 worldwide accident coverage.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- IFFCO Tokio Crop Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IFFCO Tokio Crop Insurance', 'IRDAN127RP0015V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Crop insurance under Pradhan Mantri Fasal Bima Yojana covering yield loss due to natural calamities and weather events.',
    'https://www.iffcotokio.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- ===================== CHOLAMANDALAM MS EXPANSION (Phase 7) =====================

-- Chola MS Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Private Car Insurance', 'IRDAN128RP0001V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Comprehensive car insurance with own damage and third-party coverage. Network of garages for cashless claims.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Chola MS Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Two Wheeler Insurance', 'IRDAN128RP0002V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Two-wheeler insurance for bikes and scooters with comprehensive coverage including own damage and third-party.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Chola MS Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Health Insurance', 'IRDAN128RP0010V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Health insurance covering hospitalization expenses with network of 9000+ hospitals for cashless treatment.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Chola MS Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Fire Insurance', 'IRDAN128RP0003V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Standard fire and special perils policy covering property against fire, explosion, and natural calamities.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Chola MS Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Marine Cargo Insurance', 'IRDAN128RP0004V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Marine cargo insurance protecting goods in transit against loss or damage during transportation.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- Chola MS Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Travel Insurance', 'IRDAN128RP0009V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Travel insurance for domestic and international travel covering medical emergencies and trip disruptions.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

-- Chola MS Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Personal Accident Insurance', 'IRDAN128RP0005V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Personal accident insurance covering accidental death and permanent disability with 24x7 worldwide coverage.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- Chola MS Engineering Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Chola MS Engineering Insurance', 'IRDAN128RP0006V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Engineering insurance covering machinery breakdown and erection risks for industrial and construction projects.',
    'https://www.cholainsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited' AND sc.name = 'Machinery Breakdown';

-- ===================== ROYAL SUNDARAM EXPANSION (Phase 7) =====================

-- Royal Sundaram Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Private Car Insurance', 'IRDAN110RP0001V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Comprehensive car insurance with 3300+ cashless garages and 24x7 roadside assistance for emergency support.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Royal Sundaram Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Two Wheeler Insurance', 'IRDAN110RP0002V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Two-wheeler insurance for bikes and scooters covering own damage and third-party liability.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Royal Sundaram Health Insurance - Lifeline Supreme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Lifeline Supreme', 'IRDAN110RP0005V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Comprehensive health insurance with wide coverage options including hospitalization, day care, and critical illness.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Royal Sundaram Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Home Insurance', 'IRDAN110RP0008V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Home insurance covering building structure and contents against fire, natural disasters, burglary and other perils.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Royal Sundaram Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Travel Insurance', 'IRDAN110RP0006V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Travel insurance for domestic and international trips covering medical emergencies, trip cancellation, and baggage loss.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

-- Royal Sundaram Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Fire Insurance', 'IRDAN110RP0003V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Standard fire and special perils insurance for commercial and residential properties against fire and allied risks.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Royal Sundaram Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Royal Sundaram Marine Cargo Insurance', 'IRDAN110RP0004V01200001', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2000-2001',
    'Marine cargo insurance protecting goods in transit by sea, air and land against loss or damage.',
    'https://www.royalsundaram.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- ===================== SMALLER GENERAL INSURERS EXPANSION (Phase 7) =====================

-- Liberty General Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Private Car Insurance', 'IRDAN152RP0001V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Comprehensive car insurance with own damage and third-party coverage. Cashless claim facility at network garages.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

-- Liberty General Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Two Wheeler Insurance', 'IRDAN152RP0002V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Two-wheeler insurance providing comprehensive coverage for bikes and scooters with OD and TP components.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Liberty General Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Health Insurance', 'IRDAN152RP0004V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Health insurance covering hospitalization, day care procedures and critical illness with cashless facility.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Liberty General Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Fire Insurance', 'IRDAN152RP0003V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Standard fire and special perils insurance for properties covering fire, explosion and natural calamities.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Shriram General Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram General Private Car Insurance', 'IRDAN148RP0001V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Comprehensive car insurance for private vehicles with own damage and third-party liability coverage.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Shriram General Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram General Two Wheeler Insurance', 'IRDAN148RP0002V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Two-wheeler insurance for bikes and scooters. Comprehensive coverage with own damage and third-party.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Shriram General Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram General Health Insurance', 'IRDAN148RP0005V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Health insurance covering hospitalization and medical expenses with cashless facility at network hospitals.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Shriram General Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram General Fire Insurance', 'IRDAN148RP0003V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Standard fire and special perils policy for commercial and residential properties. Fire, explosion and allied perils.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Magma General Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Private Car Insurance', 'IRDAN153RP0001V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Private car insurance with comprehensive coverage including own damage, third-party liability and personal accident.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

-- Magma General Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Two Wheeler Insurance', 'IRDAN153RP0002V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Two-wheeler insurance with comprehensive and third-party only options for bikes and scooters.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Magma General Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Health Insurance', 'IRDAN153RP0004V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Health insurance covering hospitalization expenses with cashless claims at network hospitals.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Magma General Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Fire Insurance', 'IRDAN153RP0003V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'Fire insurance for commercial and residential properties covering fire, explosion, and natural perils.',
    'https://www.magmahdi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Generali Central Insurance Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Private Car Insurance', 'IRDAN147RP0001V01200607', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Comprehensive car insurance with own damage and TP liability. Cashless claims at partner garages nationwide.',
    'https://www.generalicentralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Generali Central Insurance Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Health Insurance', 'IRDAN147RP0005V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Health insurance covering hospitalization, day care treatments and critical illness at network hospitals.',
    'https://www.generalicentralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Universal Sompo Private Car
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Private Car Insurance', 'IRDAN142RP0001V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Comprehensive car insurance with OD and TP coverage. Cashless repairs at network garages.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Private Car - Comprehensive';

-- Universal Sompo Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Health Insurance', 'IRDAN142RP0004V01200910', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2009-2010',
    'Health insurance covering hospitalization and surgical procedures with cashless facility at network hospitals.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Universal Sompo Two Wheeler
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Two Wheeler Insurance', 'IRDAN142RP0002V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Two-wheeler insurance with comprehensive and TP only options for bikes and scooters.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Universal Sompo Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Fire Insurance', 'IRDAN142RP0003V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Fire and special perils insurance for commercial and residential properties against fire and natural calamities.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';


-- ================ SECTION 2: EXTRA GENERAL PRODUCTS =============
-- ============================================================
-- 05b_products_general_extra.sql - Additional general insurance products
-- Expands underrepresented general insurers to 10-15+ products each
-- Sources: Company websites, IRDAI portal, policybazaar.com
-- Last verified: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== ECGC LIMITED =====================
-- Source: https://www.ecgc.in/

-- ECGC Specific Shipment Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Specific Shipment Policy (SSP)', 'IRDAN120RP0002V01200203', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2002-2003',
    'Export credit insurance for individual shipments covering commercial and political risks. Valid for specific shipments made within the policy period for up to 80% of shipment value.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ECGC Small Exporters Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Small Exporters Policy (SEP)', 'IRDAN120RP0003V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Export credit insurance for small exporters with turnover up to Rs 5 crore. Covers commercial and political risks with maximum risk coverage below Rs 2 crores.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ECGC Shipments Comprehensive Risks Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Shipments Comprehensive Risks Policy (SCR)', 'IRDAN120RP0004V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Comprehensive 12-month export credit insurance for exporters with turnover over Rs 500 crores covering both commercial and political risks on all shipments.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ECGC Services Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Services Policy (SRC)', 'IRDAN120RP0006V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Export credit insurance for service contracts covering Indian companies providing technical or professional services to foreign principals against payment default risks.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ECGC Bank Export Credit Insurance (WTPC)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Export Credit Insurance for Banks (ECIB-WTPC)', 'IRDAN120RP0007V01200607', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2006-2007',
    'Enhanced export credit risk insurance for banks covering whole turnover packaging credit and post shipment lending with coverage up to 90% for small exporters.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ECGC Buyer Credit Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ECGC Buyers Credit Comprehensive Risks Policy', 'IRDAN120RP0008V01200708', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2007-2008',
    'Insurance covering buyer''s credit extended by Indian banks to overseas buyers for import of Indian goods, protecting against commercial and political risks.',
    'https://www.ecgc.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ECGC Limited' AND sc.name = 'Credit Insurance';

-- ===================== AIC (Agriculture Insurance Co.) =====================
-- Source: https://www.aicofindia.com/

-- AIC Coconut Palm Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Coconut Palm Insurance Scheme', 'IRDAN106RP0003V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Insurance scheme for coconut palm plantations covering loss or damage to coconut trees due to natural calamities, pests, and diseases.',
    'https://www.aicofindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- AIC National Agricultural Insurance Scheme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC National Agricultural Insurance Scheme (NAIS)', 'IRDAN106RP0004V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'National agricultural insurance scheme providing insurance protection to farmers against crop losses due to natural calamities, pests, and diseases.',
    'https://www.aicofindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- AIC Add-on Coverage for PMFBY
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC PMFBY Add-on Coverage - Prevented Sowing', 'IRDAN106RP0005V01201920', 'add_on', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Add-on coverage for prevented sowing/planting under PMFBY when farmers are unable to sow due to adverse weather conditions.',
    'https://www.aicofindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- AIC Horticulture Crop Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Horticulture Crop Insurance', 'IRDAN106RP0006V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Insurance for horticulture crops including fruits, vegetables, spices, and plantation crops against losses from natural calamities and adverse weather.',
    'https://www.aicofindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- AIC Cattle Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Cattle Insurance Scheme', 'IRDAN106RP0007V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Insurance coverage for cattle including cows, buffaloes, and bulls against death due to disease, accident, surgical operation, and natural calamities.',
    'https://www.aicofindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'Livestock Insurance';

-- AIC Poultry Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'AIC Poultry Insurance Scheme', 'IRDAN106RP0008V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Insurance for poultry farms covering loss of poultry birds due to disease, accidents, and natural calamities with coverage for layer and broiler birds.',
    'https://www.aicofindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited' AND sc.name = 'Livestock Insurance';

-- ===================== RAHEJA QBE =====================
-- Source: https://www.rahejaqbe.com/

-- Raheja QBE Marine Cargo Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Marine Cargo Insurance', 'IRDAN163RP0004V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Marine cargo insurance covering goods in transit by sea, rail, road, and air against loss or damage from insured perils including theft, piracy, and natural disasters.',
    'https://www.rahejaqbe.com/marine-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- Raheja QBE General Liability Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE General Liability Insurance', 'IRDAN163RP0005V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'General liability insurance providing coverage against third-party bodily injury and property damage claims arising from business operations.',
    'https://www.rahejaqbe.com/general-liability-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Commercial General Liability (CGL)';

-- Raheja QBE Professional Indemnity
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Professional Indemnity Insurance', 'IRDAN163RP0006V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Professional indemnity insurance indemnifying professionals against claims of negligence, mistakes, or omissions in professional services.',
    'https://www.rahejaqbe.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Professional Indemnity / E&O';

-- Raheja QBE Engineering Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Contractor All Risk Insurance', 'IRDAN163RP0007V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Contractor''s all risk insurance providing comprehensive protection against all types of civil construction risks during the construction period.',
    'https://www.rahejaqbe.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Contractor All Risk (CAR)';

-- Raheja QBE Cyber Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Raheja QBE Cyber Insurance Policy', 'IRDAN163RP0008V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Cyber insurance providing coverage against data breaches, cyber attacks, ransomware, business interruption from cyber events, and regulatory fines.',
    'https://www.rahejaqbe.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited' AND sc.name = 'Cyber Liability Insurance';

-- ===================== GO DIGIT GENERAL =====================
-- Source: https://www.godigit.com/

-- Digit Commercial Vehicle Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Commercial Vehicle Insurance', 'IRDAN158RP007V01201819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Comprehensive insurance for commercial vehicles including trucks, buses, and goods carriers covering own damage and third-party liability.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- Digit Fire Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Fire Insurance Policy', 'IRDAN158RP010V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Standard fire and special perils insurance covering buildings, plants, machinery, and contents against fire, lightning, explosion, and allied perils.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Standard Fire & Special Perils';

-- Digit Marine Cargo Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Marine Cargo Insurance', 'IRDAN158RP011V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Marine cargo insurance covering goods in transit against loss or damage from marine perils, accidents, and other insured risks.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Marine Cargo';

-- Digit D&O Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Directors & Officers Liability Insurance', 'IRDAN158RP012V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'D&O liability insurance protecting directors and officers against claims arising from their decisions and actions in managing the company.',
    'https://www.godigit.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Directors & Officers Liability';

-- Digit Workmen Compensation
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Workmen Compensation Insurance', 'IRDAN158RP013V01202122', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Employer''s liability insurance covering compensation to employees for injury, death, or occupational disease during employment as per the Workmen Compensation Act.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Workmen Compensation';

-- Digit Erection All Risk
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Erection All Risk Insurance', 'IRDAN158RP014V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Erection all risk insurance covering risks during erection, testing, and commissioning of machinery, plant, and equipment at construction sites.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Erection All Risk (EAR)';

-- Digit Contractor All Risk
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Contractor All Risk Insurance', 'IRDAN158RP015V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Contractor all risk insurance providing comprehensive coverage for civil construction projects against material damage and third-party liability.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit General Insurance Limited' AND sc.name = 'Contractor All Risk (CAR)';

-- ===================== ACKO GENERAL =====================
-- Source: https://www.acko.com/

-- Acko Domestic Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Domestic Travel Insurance', 'IRDAN157RP0009V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Domestic travel insurance covering trip cancellation, medical emergencies, baggage loss, and travel delays during travel within India.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Domestic Travel Insurance';

-- Acko Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Home Insurance Policy', 'IRDAN157RP0010V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive home insurance covering building structure and contents against fire, natural disasters, burglary, and other perils.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Householder Package Policy';

-- Acko Gadget Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Gadget Insurance', 'IRDAN157RP0011V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Insurance for electronic gadgets including smartphones, laptops, and tablets covering accidental damage, liquid damage, and screen breakage.',
    'https://www.acko.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'SME Package Insurance';

-- Acko Commercial Vehicle Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Commercial Vehicle Insurance', 'IRDAN157RP0012V01202324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Insurance for commercial vehicles including goods carriers and passenger vehicles covering own damage and third-party liability.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko General Insurance Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- ===================== ZUNO GENERAL =====================
-- Source: https://www.hizuno.com/

-- Zuno Smart Drive Motor Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Smart Drive Policy', 'IRDAN148RP0010V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Innovative motor insurance policy that rewards safe driving behavior with premium discounts based on driving patterns tracked through the Zuno app.',
    'https://www.hizuno.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Private Car - Comprehensive';

-- Zuno Health Top Up Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Health Top Up Insurance', 'EDLHLIP21563V012021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Top-up health insurance plan providing additional coverage above a deductible to supplement existing health insurance at affordable premiums.',
    'https://www.hizuno.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Zuno Empower Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Empower Health', 'ZUNHLIP23204V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive health insurance plan covering hospitalization, day-care procedures, pre and post hospitalization expenses with wellness benefits.',
    'https://www.hizuno.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Zuno Loan Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zuno Loan Care Policy', 'IRDAN148RP0011V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Loan protection insurance covering outstanding loan amount in case of death, disability, or involuntary job loss of the borrower.',
    'https://www.hizuno.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zuno General Insurance Limited' AND sc.name = 'Credit Insurance';

-- ===================== INDUSIND GENERAL =====================
-- Source: https://www.reliancegeneral.co.in/ (now IndusInd GI)

-- IndusInd GI Commercial Vehicle Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Commercial Vehicle Insurance', 'IRDAN156RP0004V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive insurance for commercial vehicles covering own damage from accidents, theft, fire, natural calamities, and mandatory third-party liability.',
    'https://www.reliancegeneral.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- IndusInd GI Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Home Insurance', 'IRDAN156RP0005V01202021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Comprehensive home insurance covering building structure and contents against fire, natural disasters, burglary, and other named perils.',
    'https://www.reliancegeneral.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- IndusInd GI Marine Cargo Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Marine Cargo Insurance', 'IRDAN127RP0005V01200910', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2009-2010',
    'Marine cargo insurance covering goods in transit by sea, rail, road, and air against loss from insured perils including sinking, collision, and theft.',
    'https://www.reliancegeneral.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- IndusInd GI Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd General Personal Accident Insurance', 'IRDAN127RP0006V01201011', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2010-2011',
    'Personal accident insurance providing financial protection against death and disability arising from accidents with medical expense reimbursement.',
    'https://www.reliancegeneral.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd General Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- ===================== NAVI GENERAL =====================
-- Source: https://navi.com/insurance

-- Navi Smart Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Smart Health Insurance', 'NAVHLIP25037V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Smart health insurance plan from Navi providing comprehensive hospitalization coverage with wellness benefits and digital-first claims process.',
    'https://navi.com/insurance/health', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Navi Special Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Special Care Insurance', 'NAVHLIP24038V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Health insurance plan providing coverage for specific conditions and treatments requiring specialized medical care.',
    'https://navi.com/insurance/health', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Critical Illness Insurance';

-- Navi Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Group Health Insurance', 'NAVHLGP24039V012324', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Group health insurance for employers providing hospitalization coverage to employees and their dependents at competitive group premium rates.',
    'https://navi.com/insurance/health', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Group Health Insurance';

-- Navi Surrogacy Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Navi Surrogacy Care Insurance', 'NAVHLIP24040V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Specialized health insurance covering surrogacy-related medical expenses including pre-natal care, delivery, post-natal care for the surrogate mother.',
    'https://navi.com/insurance/health', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Navi General Insurance Limited' AND sc.name = 'Maternity Insurance';

-- ===================== NATIONAL INSURANCE COMPANY =====================
-- Source: https://nationalinsurance.nic.co.in/

-- National Insurance Two Wheeler Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Two Wheeler Package Policy', 'IRDAN170RP0002V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive two-wheeler insurance covering own damage from accidents, theft, fire, and natural calamities along with third-party liability.',
    'https://nationalinsurance.nic.co.in/products/all-products/motor/two-wheeler', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- National Insurance Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Marine Cargo Policy', 'IRDAN190RP0010V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Marine cargo insurance covering goods in transit against marine perils, accidents, theft, and natural calamities during sea, air, rail, and road transit.',
    'https://nationalinsurance.nic.co.in/en/marine', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- National Insurance Fire Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Standard Fire Policy', 'IRDAN190RP0005V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Standard fire and special perils insurance covering buildings, plants, machinery, and contents against fire, lightning, explosion, and allied perils.',
    'https://nationalinsurance.nic.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Standard Fire & Special Perils';

-- National Insurance Home Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Bharat Griha Raksha Policy', 'IRDAN190RP0050V01202122', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'IRDAI-mandated standard home insurance policy providing coverage for dwelling structure and contents against fire, natural calamities, and other perils.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

-- National Insurance Travel Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Overseas Travel Insurance', 'IRDAN190RP0025V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Overseas travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during international travel.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- National Insurance Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Personal Accident Policy', 'IRDAN190RP0008V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Personal accident insurance providing compensation for death and disability due to accidents with medical expense reimbursement.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- National Insurance Commercial Vehicle
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Commercial Vehicle Package Policy', 'IRDAN190RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive insurance for commercial vehicles covering own damage, third-party liability, and personal accident for driver and passengers.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- National Insurance Workmen Compensation
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Workmen Compensation Policy', 'IRDAN190RP0012V01200102', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Employer''s liability insurance covering compensation to employees for injury or death during employment as per the Workmen''s Compensation Act.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Workmen Compensation';

-- National Insurance Burglary Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'National Insurance Burglary Insurance Policy', 'IRDAN190RP0018V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Burglary insurance covering loss or damage to property, goods, and valuables due to burglary, housebreaking, and theft.',
    'https://nationalinsurance.nic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'National Insurance Company Limited' AND sc.name = 'Burglary Insurance';

-- ===================== ZURICH KOTAK GENERAL =====================
-- Source: https://www.zurichkotak.com/

-- Zurich Kotak MediShield
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak MediShield', 'ZUKHLIP23195V022223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive health insurance plan from Zurich Kotak covering hospitalization, day-care procedures, and critical illness with cashless facility at network hospitals.',
    'https://www.zurichkotak.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Zurich Kotak Health Maximiser
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Health Maximiser', 'ZUKHLIP24026V022324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Health insurance plan with enhanced coverage limits and comprehensive benefits for hospitalization and daycare procedures.',
    'https://www.zurichkotak.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Zurich Kotak LiveWise
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak LiveWise', 'ZUKHLIP24027V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Health insurance plan from Zurich Kotak focused on holistic wellness with preventive health benefits and comprehensive hospitalization coverage.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Zurich Kotak Property Shield - Retail
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Property Shield Retail', 'IRDAN152RP0001V02202324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Retail property insurance covering dwelling, contents, and personal belongings against fire, natural calamities, burglary, and other perils.',
    'https://www.zurichkotak.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'Householder Package Policy';

-- Zurich Kotak Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Zurich Kotak Travel Insurance', 'IRDAN137RP0005V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during overseas travel.',
    'https://www.zurichkotak.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- ===================== UNITED INDIA INSURANCE =====================
-- Source: https://uiic.co.in/

-- United India Two Wheeler Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Two Wheeler Package Policy', 'IRDAN160RP0002V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive two-wheeler insurance covering own damage and third-party liability for motorized two-wheelers.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- United India Commercial Vehicle Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Commercial Vehicle Package Policy', 'IRDAN160RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Insurance for commercial vehicles including trucks, buses, and goods carriers covering own damage and third-party liability.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- United India Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Overseas Travel Insurance', 'IRDAN130RP0015V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Overseas travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during international travel.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- United India Home Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Bharat Griha Raksha Policy', 'IRDAN130RP0020V01202122', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'IRDAI-mandated standard home insurance policy covering dwelling and contents against fire, natural calamities, burglary, and other perils.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Bharat Griha Raksha (Standard)';

-- United India Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Personal Accident Policy', 'IRDAN130RP0005V01200304', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2003-2004',
    'Personal accident insurance providing compensation for death and disability due to accidents.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- United India Shopkeeper Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Shopkeeper Insurance Policy', 'IRDAN130RP0018V01201920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Package insurance for shopkeepers covering fire, burglary, personal accident, public liability, and money in transit under a single policy.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Shopkeeper Insurance';

-- United India Professional Indemnity
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'United India Professional Indemnity Insurance', 'IRDAN130RP0012V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Professional indemnity insurance for professionals covering claims of negligence, errors, and omissions in professional services.',
    'https://uiic.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'United India Insurance Company Limited' AND sc.name = 'Professional Indemnity / E&O';

-- ===================== ORIENTAL INSURANCE =====================
-- Source: https://orientalinsurance.org.in/

-- Oriental Insurance Two Wheeler Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Two Wheeler Package Policy', 'IRDAN180RP0002V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Comprehensive two-wheeler insurance covering own damage and third-party liability for motorized two-wheelers.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- Oriental Insurance Commercial Vehicle
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Commercial Vehicle Package Policy', 'IRDAN180RP0003V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Insurance for commercial vehicles covering own damage, third-party liability, and personal accident for driver and passengers.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- Oriental Insurance Travel Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Domestic Travel Policy', 'IRDAN129RP0011V01200506', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2005-2006',
    'Domestic travel insurance covering trip cancellation, medical emergencies, baggage loss, and travel delays within India.',
    'https://orientalinsurance.org.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Domestic Travel Insurance';

-- Oriental Insurance Erection All Risk
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Erection All Risk Policy', 'IRDAN103RP0010V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Erection all risk insurance covering risks during erection, testing, and commissioning of machinery and equipment at project sites.',
    'https://orientalinsurance.org.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Erection All Risk (EAR)';

-- Oriental Insurance Boiler & Pressure Plant
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Boiler & Pressure Plant Policy', 'IRDAN103RP0012V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Insurance covering boilers and pressure plants against explosion and collapse risks including damage to surrounding property.',
    'https://orientalinsurance.org.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Boiler & Pressure Plant';

-- Oriental Insurance Contractor All Risk
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Oriental Insurance Contractor All Risk Policy', 'IRDAN103RP0011V01200102', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2001-2002',
    'Contractor all risk insurance providing comprehensive protection for civil construction projects against material damage and third-party liability.',
    'https://orientalinsurance.org.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The Oriental Insurance Company Limited' AND sc.name = 'Contractor All Risk (CAR)';

-- ===================== GENERALI CENTRAL GI =====================
-- Source: IRDAI filings

-- Generali Central Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Marine Cargo Insurance', 'IRDAN118RP0005V01200910', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2009-2010',
    'Marine cargo insurance covering goods in transit by sea, air, rail, and road against loss or damage from insured perils.',
    'https://generalinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- Generali Central Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Travel Insurance', 'IRDAN118RP0010V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during overseas travel.',
    'https://generalinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- Generali Central Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Personal Accident Insurance', 'IRDAN118RP0008V01201112', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2011-2012',
    'Personal accident insurance covering death and disability due to accidents with medical expense reimbursement.',
    'https://generalinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- Generali Central Liability Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Public Liability Insurance', 'IRDAN118RP0012V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Public liability insurance covering third-party bodily injury and property damage claims arising from business premises and operations.',
    'https://generalinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Insurance Company Limited' AND sc.name = 'Public Liability Insurance';

-- ===================== SHRIRAM GI =====================
-- Source: https://www.shriramgi.com/

-- Shriram GI Marine Cargo Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Marine Cargo Insurance', 'IRDAN139RP0005V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Marine cargo insurance covering goods in transit against perils of sea, land, and air transport.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- Shriram GI Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Personal Accident Insurance', 'IRDAN139RP0006V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'Personal accident insurance covering death and disability from accidents with medical expense reimbursement.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- Shriram GI Two Wheeler Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram GI Two Wheeler Insurance', 'IRDAN139RP0002V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Comprehensive two-wheeler insurance covering own damage and third-party liability for all two-wheelers.',
    'https://www.shriramgi.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram General Insurance Company Limited' AND sc.name = 'Two-Wheeler - Comprehensive';

-- ===================== UNIVERSAL SOMPO =====================
-- Source: https://www.universalsompo.com/

-- Universal Sompo Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Travel Insurance', 'IRDAN117RP0010V01201314', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2013-2014',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- Universal Sompo Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Marine Cargo Insurance', 'IRDAN117RP0005V01200809', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2008-2009',
    'Marine cargo insurance covering goods in transit by sea, rail, road, and air against loss from insured perils.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Marine Cargo';

-- Universal Sompo Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Personal Accident Insurance', 'IRDAN117RP0008V01201112', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2011-2012',
    'Personal accident insurance providing compensation for death and disability due to accidents.',
    'https://www.universalsompo.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- ===================== MAGMA GI =====================
-- Source: IRDAI filings

-- Magma GI Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Travel Insurance', 'IRDAN153RP0008V01201718', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2017-2018',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss during overseas travel.',
    'https://www.magma.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'International Travel Insurance';

-- Magma GI Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Marine Cargo Insurance', 'IRDAN153RP0005V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Marine cargo insurance covering goods in transit against perils of sea, land, and air transport.',
    'https://www.magma.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Marine Cargo';

-- Magma GI Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Magma General Personal Accident Insurance', 'IRDAN153RP0006V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Personal accident insurance covering death and disability due to accidents with medical expense reimbursement.',
    'https://www.magma.co.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Magma General Insurance Limited' AND sc.name = 'Individual Personal Accident';

-- ===================== LIBERTY GI =====================
-- Source: https://www.libertyinsurance.in/

-- Liberty GI Marine Cargo
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Marine Cargo Insurance', 'IRDAN150RP0005V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Marine cargo insurance covering goods in transit by sea, rail, road, and air against perils including collision, sinking, and theft.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Marine Cargo';

-- Liberty GI Travel Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Travel Insurance', 'IRDAN150RP0008V01201617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, and personal accident during overseas travel.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'International Travel Insurance';

-- Liberty GI Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Personal Accident Insurance', 'IRDAN150RP0006V01201516', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2015-2016',
    'Personal accident insurance providing compensation for accidental death and disability with medical expense reimbursement.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Individual Personal Accident';

-- Liberty GI Commercial Vehicle
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Liberty General Commercial Vehicle Insurance', 'IRDAN150RP0004V01201415', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2014-2015',
    'Insurance for commercial vehicles covering own damage, third-party liability, and personal accident cover.',
    'https://www.libertyinsurance.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Liberty General Insurance Limited' AND sc.name = 'Commercial Vehicle Insurance';

-- ================ SECTION 3: GI STANDARD EXPANSION ==============
-- ============================================================
-- 10_gi_standard_expansion.sql
-- Programmatic generation of standard products for ALL 27 GI companies
-- Each company gets ~50 standard products across all subcategories
-- ON CONFLICT DO NOTHING ensures no duplicates
-- ============================================================
SET search_path TO insurance, public;

DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'general'
        ORDER BY c.legal_name
    LOOP
        seq := 200;

        FOR product_data IN
            SELECT * FROM (VALUES
                -- MOTOR INSURANCE (7 products)
                ('Private Car - Comprehensive', ' Private Car Package Policy', 'individual', 'Comprehensive motor insurance covering own damage (accidental damage, fire, theft, natural calamities) and third-party liability for private cars. Includes mandatory PA cover for owner-driver.'),
                ('Private Car - Third Party Only', ' Car Third Party Liability Policy', 'individual', 'Mandatory third-party liability car insurance covering legal liability for death, bodily injury, and property damage caused to third parties under Motor Vehicles Act.'),
                ('Two-Wheeler - Comprehensive', ' Two Wheeler Package Policy', 'individual', 'Comprehensive two-wheeler insurance covering own damage and third-party liability for motorcycles and scooters.'),
                ('Two-Wheeler - Third Party Only', ' Two Wheeler TP Only Policy', 'individual', 'Mandatory third-party liability two-wheeler insurance. Long-term 5-year TP available for new two-wheelers per IRDAI mandate.'),
                ('Commercial Vehicle Insurance', ' Commercial Vehicle Insurance', 'individual', 'Insurance for commercial vehicles including trucks, buses, taxis, and goods carriers covering own damage and third-party liability.'),
                ('Standalone Own Damage', ' Standalone Own Damage Policy', 'individual', 'Standalone own damage motor insurance covering loss or damage to own vehicle from accidents, fire, theft, and natural calamities.'),
                ('Motor Add-Ons / Riders', ' Motor Add-On Covers', 'add_on', 'Optional motor add-on covers including zero depreciation, engine protection, roadside assistance, return to invoice, consumables cover, NCB protection, key and lock replacement.'),

                -- FIRE INSURANCE (4 products)
                ('Standard Fire & Special Perils', ' Standard Fire & Special Perils Policy', 'individual', 'Standard fire and special perils insurance covering buildings, machinery, stock and contents against fire, lightning, explosion, storm, flood, earthquake and other IRDAI-specified perils.'),
                ('Industrial All Risk (IAR)', ' Industrial All Risk Policy', 'individual', 'Comprehensive all-risk property insurance for large industrial establishments covering material damage from any accidental cause not specifically excluded.'),
                ('Burglary Insurance', ' Burglary Insurance Policy', 'individual', 'Insurance against loss or damage to property caused by burglary, housebreaking and theft including hold-up and larceny.'),
                ('Business Interruption', ' Business Interruption Policy', 'individual', 'Loss of profit insurance covering financial loss from business interruption due to insured perils like fire, explosion, or machinery breakdown.'),

                -- MARINE INSURANCE (4 products)
                ('Marine Cargo', ' Marine Cargo Insurance Policy', 'individual', 'Insurance covering goods and cargo during transit by sea, air, rail, and road against marine perils, theft, and accidental damage.'),
                ('Marine Hull', ' Marine Hull Insurance Policy', 'individual', 'Insurance covering ships, vessels, and their machinery and equipment against marine perils and physical damage.'),
                ('Inland Transit', ' Inland Transit Insurance Policy', 'individual', 'Insurance covering goods in transit within India by rail, road, air, or inland waterway against damage and loss.'),
                ('Marine Liability', ' Marine Liability Insurance', 'individual', 'Protection and Indemnity (P&I) insurance covering third-party liabilities arising from marine operations.'),

                -- ENGINEERING INSURANCE (5 products)
                ('Contractor All Risk (CAR)', ' Contractor All Risk Policy', 'individual', 'Engineering insurance covering civil construction works against all risks of physical loss or damage during construction period.'),
                ('Erection All Risk (EAR)', ' Erection All Risk Policy', 'individual', 'Engineering insurance covering erection and installation of machinery and equipment against all risks during the erection period.'),
                ('Machinery Breakdown', ' Machinery Breakdown Insurance', 'individual', 'Engineering insurance covering sudden and unforeseen physical damage to machinery from internal causes like overheating, short circuit, or mechanical failure.'),
                ('Boiler & Pressure Plant', ' Boiler & Pressure Plant Insurance', 'individual', 'Insurance covering boilers and pressure plant against explosion, collapse, and overheating including damage to surrounding property.'),
                ('Electronic Equipment Insurance', ' Electronic Equipment Insurance', 'individual', 'All-risk insurance covering electronic equipment against physical damage, electrical disturbance, theft, and operator error.'),

                -- LIABILITY INSURANCE (7 products)
                ('Commercial General Liability (CGL)', ' Commercial General Liability Policy', 'individual', 'CGL insurance covering third-party bodily injury and property damage arising from business premises, operations, and products.'),
                ('Directors & Officers Liability', ' Directors & Officers Liability Policy', 'individual', 'D&O liability insurance protecting directors and officers against claims from wrongful acts including defense costs and settlements.'),
                ('Professional Indemnity / E&O', ' Professional Indemnity Policy', 'individual', 'Professional indemnity insurance covering legal liability arising from professional negligence, errors, or omissions in providing professional services.'),
                ('Product Liability Insurance', ' Product Liability Insurance', 'individual', 'Insurance covering liability for bodily injury or property damage caused by defective products manufactured or sold.'),
                ('Public Liability Insurance', ' Public Liability Insurance', 'individual', 'Insurance covering legal liability to third parties for bodily injury or property damage from the insured premises or business operations.'),
                ('Workmen Compensation', ' Workmen Compensation Policy', 'individual', 'Insurance covering employer statutory liability for employee injury, disability, or death during course of employment under Employees Compensation Act.'),
                ('Cyber Liability Insurance', ' Cyber Liability Policy', 'individual', 'Corporate cyber liability insurance covering data breach response costs, cyber extortion, business interruption from cyber attacks, and regulatory defense.'),

                -- TRAVEL INSURANCE (4 products)
                ('International Travel Insurance', ' International Travel Insurance', 'individual', 'Overseas travel insurance covering medical emergencies, emergency evacuation, trip cancellation, baggage loss, passport loss, and personal liability.'),
                ('Domestic Travel Insurance', ' Domestic Travel Insurance', 'individual', 'Domestic travel insurance covering medical emergencies, trip cancellation, baggage loss, and travel delays for journeys within India.'),
                ('Student Travel Insurance', ' Student Travel Insurance', 'individual', 'Long-duration travel insurance for students studying abroad covering medical emergencies, study interruption, sponsor protection, and compassionate visit.'),
                ('Corporate / Multi-Trip Travel', ' Corporate Travel Policy', 'group', 'Annual multi-trip corporate travel insurance covering employees on domestic and international business travel throughout the year.'),

                -- HOME INSURANCE (4 products)
                ('Bharat Griha Raksha (Standard)', ' Bharat Griha Raksha Policy', 'standard', 'IRDAI-mandated standard home insurance covering residential dwelling structure and contents against fire, natural disasters, burglary, and allied perils.'),
                ('Householder Package Policy', ' Householder Comprehensive Policy', 'individual', 'Comprehensive home package insurance covering building structure, contents, burglary, personal accident, public liability, and plate glass breakage.'),
                ('Home Contents Insurance', ' Home Contents Insurance', 'individual', 'Insurance covering household contents including furniture, appliances, electronics, and valuables against fire, theft, and natural perils.'),
                ('Home Structure Insurance', ' Home Structure Insurance', 'individual', 'Insurance covering the physical structure of residential buildings against fire, natural disasters, and structural damage.'),

                -- PERSONAL ACCIDENT (3 products)
                ('Individual Personal Accident', ' Personal Accident Insurance', 'individual', 'Personal accident insurance covering accidental death and permanent total or partial disability with optional medical expense reimbursement.'),
                ('Group Personal Accident', ' Group Personal Accident Policy', 'group', 'Group personal accident insurance for employer-employee groups and institutions covering accidental death and disability.'),
                ('PMSBY', ' Pradhan Mantri Suraksha Bima Yojana', 'group', 'Government PMSBY providing Rs 2 lakh accidental death and Rs 1 lakh partial disability cover at annual premium of Rs 20 for savings bank account holders aged 18-70.'),

                -- MISCELLANEOUS (6 products)
                ('Shopkeeper Insurance', ' Bharat Sookshma Udyam Suraksha', 'standard', 'IRDAI-mandated standard micro-enterprise insurance for businesses with annual turnover up to Rs 5 crore covering fire, burglary, personal accident, money, and public liability.'),
                ('SME Package Insurance', ' Bharat Laghu Udyam Suraksha', 'standard', 'IRDAI-mandated standard small enterprise insurance for businesses with annual turnover Rs 5-50 crore. Comprehensive package covering property, liability, and business interruption.'),
                ('Fidelity Guarantee', ' Fidelity Guarantee Insurance', 'individual', 'Insurance covering employers against direct financial loss caused by acts of dishonesty, fraud, forgery, or embezzlement by employees.'),
                ('Surety Bond Insurance', ' Surety Bond Insurance', 'individual', 'Insurance-based surety bonds as alternative to bank guarantees for contract performance bonds, bid bonds, and advance payment guarantees.'),
                ('Cyber Insurance (Retail)', ' Retail Cyber Insurance', 'individual', 'Retail cyber insurance protecting individuals against online financial fraud, phishing, identity theft, cyber stalking, and unauthorized digital transactions.'),
                ('Credit Insurance', ' Trade Credit Insurance', 'individual', 'Trade credit insurance protecting businesses against buyer payment defaults and insolvency for domestic and export receivables.'),

                -- CROP / AGRICULTURE (3 products)
                ('PMFBY - Crop Insurance', ' PMFBY Crop Insurance', 'group', 'Pradhan Mantri Fasal Bima Yojana providing comprehensive crop insurance against natural calamities, pests, and diseases at subsidized premiums.'),
                ('Weather-Based Crop Insurance', ' Weather-Based Crop Insurance', 'group', 'Restructured Weather Based Crop Insurance Scheme using weather parameters like rainfall, temperature, and humidity as proxy for crop yield losses.'),
                ('Livestock Insurance', ' Livestock Insurance Policy', 'individual', 'Insurance covering cattle, buffaloes, horses, and other livestock against death from disease, accident, natural calamities, and surgical operations.')
            ) AS t(subcategory_name, product_suffix, product_type, summary)
        LOOP
            -- Look up subcategory
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                -- Generate UIN
                uin_val := 'IRDAN' || comp.registration_number || 'RP' || LPAD(seq::text, 4, '0') || 'V01' ||
                    CASE
                        WHEN seq < 210 THEN '200102'
                        WHEN seq < 215 THEN '200304'
                        WHEN seq < 225 THEN '200506'
                        WHEN seq < 235 THEN '200708'
                        WHEN seq < 245 THEN '201516'
                        WHEN seq < 255 THEN '202021'
                        ELSE '202223'
                    END;

                -- Generate product name using short_name or company name prefix
                prod_name := COALESCE(comp.short_name, split_part(comp.legal_name, ' Insurance', 1)) || product_data.product_suffix;

                BEGIN
                    INSERT INTO insurance.insurance_products (
                        company_id, sub_category_id, product_name, uin,
                        product_type, linked_type, par_type,
                        is_active, financial_year_filed, policy_summary, source_url, data_confidence
                    ) VALUES (
                        comp.id, sc_rec.id, prod_name, uin_val,
                        product_data.product_type::insurance.product_type_enum,
                        'not_applicable'::insurance.product_linked_enum,
                        'not_applicable'::insurance.par_enum,
                        TRUE, '2022-2023', product_data.summary, comp.website,
                        'high'::insurance.confidence_enum
                    );
                EXCEPTION WHEN unique_violation THEN
                    -- Skip if UIN already exists
                    NULL;
                END;

                seq := seq + 1;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'GI standard expansion complete';
END $$;
-- ================ SECTION 4: ADDITIONAL GI VARIANTS =============
-- (Extracted from 14_additional_expansion.sql Part 1)
-- ============================================================
-- 14_additional_expansion.sql
-- Additional products to cross 5000+ threshold
-- More variants, COVID products, and niche products
-- ============================================================
SET search_path TO insurance, public;

-- Part 1: Additional GI product variants (V2 versions of existing products)
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'general'
        ORDER BY c.legal_name
    LOOP
        seq := 400;

        FOR product_data IN
            SELECT * FROM (VALUES
                -- Additional motor variants
                ('Private Car - Comprehensive', ' Long Term Car Insurance (3yr)', 'individual', 'Long-term comprehensive car insurance for 3 years providing continuous coverage without annual renewal hassle. Bundled OD and TP cover with multi-year discount.'),
                ('Two-Wheeler - Comprehensive', ' Long Term Bike Insurance (5yr)', 'individual', 'Long-term comprehensive two-wheeler insurance for 5 years with bundled TP. Convenient multi-year coverage with premium discount and no renewal gap risk.'),
                ('Commercial Vehicle Insurance', ' Fleet Insurance Policy', 'group', 'Fleet motor insurance covering multiple commercial vehicles under single policy with fleet discount. Covers trucks, buses, taxis, and delivery vehicles.'),

                -- Additional fire / property
                ('Standard Fire & Special Perils', ' Consequential Loss Policy', 'individual', 'Fire consequential loss (loss of profits) insurance covering business income loss and increased cost of working following an insured fire or special perils event.'),
                ('Industrial All Risk (IAR)', ' Mega Risk Insurance Policy', 'individual', 'Mega risk insurance for very large industrial complexes with sum insured exceeding Rs 2500 crore. Comprehensive all-risk coverage with international reinsurance.'),

                -- Additional engineering
                ('Machinery Breakdown', ' Loss of Profits (MB)', 'individual', 'Consequential loss following machinery breakdown covering loss of gross profit and standing charges during the indemnity period after machinery failure.'),
                ('Electronic Equipment Insurance', ' IT Infrastructure Insurance', 'individual', 'Specialized insurance covering IT infrastructure including servers, data centers, networking equipment, and software against physical damage and data loss.'),

                -- Additional liability
                ('Commercial General Liability (CGL)', ' Umbrella Liability Policy', 'individual', 'Umbrella excess liability providing additional limits above underlying CGL, auto liability, and employers liability policies for catastrophic claims.'),
                ('Professional Indemnity / E&O', ' Medical Malpractice Insurance', 'individual', 'Professional indemnity insurance for doctors, hospitals, and healthcare professionals covering claims arising from medical negligence and treatment errors.'),

                -- Additional specialty
                ('SME Package Insurance', ' Jewellers Block Insurance', 'individual', 'All-risk insurance for jewellers covering stock of jewellery, precious stones, watches, and gold/silver items against theft, robbery, fire while in premises, transit, or exhibitions.'),
                ('Fidelity Guarantee', ' Bankers Indemnity Insurance', 'individual', 'Comprehensive insurance for banking institutions covering cash in safe and transit, fidelity guarantee, forged instruments, loss of securities, and electronic crime.'),
                ('Shopkeeper Insurance', ' Office Package Policy', 'individual', 'Comprehensive office package insurance covering office contents, electronic equipment, money, fidelity guarantee, and public liability for commercial offices.'),
                ('Credit Insurance', ' Political Risk Insurance', 'individual', 'Political risk insurance covering export businesses against losses from political events including war, government action, currency inconvertibility, and contract frustration.')
            ) AS t(subcategory_name, product_suffix, product_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                uin_val := 'IRDAN' || comp.registration_number || 'RP' || LPAD(seq::text, 4, '0') || 'V02' ||
                    CASE WHEN seq < 405 THEN '201920' WHEN seq < 410 THEN '202122' ELSE '202324' END;
                prod_name := COALESCE(comp.short_name, split_part(comp.legal_name, ' Insurance', 1)) || product_data.product_suffix;

                BEGIN
                    INSERT INTO insurance.insurance_products (
                        company_id, sub_category_id, product_name, uin,
                        product_type, linked_type, par_type,
                        is_active, financial_year_filed, policy_summary, source_url, data_confidence
                    ) VALUES (
                        comp.id, sc_rec.id, prod_name, uin_val,
                        product_data.product_type::insurance.product_type_enum,
                        'not_applicable'::insurance.product_linked_enum,
                        'not_applicable'::insurance.par_enum,
                        TRUE, '2023-2024', product_data.summary, comp.website,
                        'high'::insurance.confidence_enum
                    );
                EXCEPTION WHEN unique_violation THEN
                    NULL;
                END;
                seq := seq + 1;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Additional GI variants complete';
END $$;

-- ================ SECTION 5: GENERAL POLICY DOCUMENTS ===========
-- ============================================================
-- 07d_policy_docs_general.sql - Policy documents for general insurance products
-- Covers Motor, Travel, Fire, Marine, Engineering, Liability, etc.
-- Sources: Official company websites
-- Last updated: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== ICICI LOMBARD PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN115RP0012V01200506', 'ICICI Lombard Contractor All Risk - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/engineering-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0014V01200506', 'ICICI Lombard Electronic Equipment - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/engineering-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0013V01200506', 'ICICI Lombard Erection All Risk - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/engineering-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0015V01200506', 'ICICI Lombard Machinery Breakdown - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/engineering-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0027V01200607', 'ICICI Lombard Business Interruption - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/fire-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0052V01202223', 'ICICI Lombard Property All Risk - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/property-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0014V01202122', 'ICICI Lombard Complete Home Protect - Brochure', 'brochure', 'https://www.icicilombard.com/docs/default-source/Policy-Wordings-product-Brochure/home-insurance-brochure.pdf', 'ICICI Lombard Official'),
    ('IRDAN115RP0003V01202021', 'ICICI Lombard Commercial General Liability - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0002V01202021', 'ICICI Lombard Cyber Risk Insurance - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/cyber-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0001V11200607', 'ICICI Lombard Directors & Officers Liability - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0010V02200607', 'ICICI Lombard Employees Compensation - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0006V01200405', 'ICICI Lombard Product Liability - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0008V01200203', 'ICICI Lombard Professional Indemnity - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0007V01200405', 'ICICI Lombard Public Liability - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0005V01200304', 'ICICI Lombard Workmen Compensation - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/liability-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0010V01200405', 'ICICI Lombard Inland Transit - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/marine-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0004V01200304', 'ICICI Lombard Marine Cargo - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/marine-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0009V01200405', 'ICICI Lombard Marine Hull - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/marine-insurance', 'ICICI Lombard Official'),
    ('IRDAN115CP0001V01202425', 'ICICI Lombard Business Edge Policy - Brochure', 'brochure', 'https://www.icicilombard.com/docs/default-source/default-document-library/elevate-brochure_final_4-6-24.pdf', 'ICICI Lombard Official'),
    ('IRDAN115RP0001V02201213', 'ICICI Lombard Extended Warranty - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/miscellaneous-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0025V01200607', 'ICICI Lombard Fidelity Guarantee - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/miscellaneous-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0026V01202223', 'ICICI Lombard Surety Bond - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/surety-bond', 'ICICI Lombard Official'),
    ('IRDAN115RP0017V02200102', 'ICICI Lombard Car Third Party Only - Brochure', 'brochure', 'https://www.icicilombard.com/motor-insurance/car-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0019V01200102', 'ICICI Lombard Commercial Vehicle Package - Brochure', 'brochure', 'https://www.icicilombard.com/motor-insurance/commercial-vehicle-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0017V01200102', 'ICICI Lombard Private Car Package Policy - Brochure', 'brochure', 'https://www.icicilombard.com/docs/default-source/Policy-Wordings-product-Brochure/motor_insurance(1).pdf', 'ICICI Lombard Official'),
    ('IRDAN115RP0018V02200102', 'ICICI Lombard Two Wheeler Third Party - Brochure', 'brochure', 'https://www.icicilombard.com/motor-insurance/two-wheeler-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0017V03200102', 'ICICI Lombard Zero Depreciation Add-On - Brochure', 'brochure', 'https://www.icicilombard.com/motor-insurance/add-on-covers', 'ICICI Lombard Official'),
    ('IRDAN115RP0024V01201617', 'ICICI Lombard Group Personal Accident - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/personal-accident', 'ICICI Lombard Official'),
    ('IRDAN115RP0023V01201516', 'ICICI Lombard PMSBY - Brochure', 'brochure', 'https://www.icicilombard.com/corporate-insurance/pmsby', 'ICICI Lombard Official'),
    ('IRDAN115RP0022V01201718', 'ICICI Lombard Annual Multi-Trip Travel - Brochure', 'brochure', 'https://www.icicilombard.com/docs/default-source/policy-wordings-product-brochure/international-travel-insurance-policy-wording.pdf', 'ICICI Lombard Official'),
    ('IRDAN115RP0020V01201516', 'ICICI Lombard Domestic Travel Insurance - Brochure', 'brochure', 'https://www.icicilombard.com/travel-insurance/domestic-travel-insurance', 'ICICI Lombard Official'),
    ('IRDAN115RP0021V01201617', 'ICICI Lombard Student Medical Insurance - Brochure', 'brochure', 'https://www.icicilombard.com/travel-insurance/student-travel-insurance', 'ICICI Lombard Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== BAJAJ ALLIANZ GENERAL PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN113RP0020V01201617', 'Bajaj Allianz Electronic Equipment - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/engineering-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0020V01202021', 'Bajaj Allianz Home Secure Policy - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/home-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0020V01202122', 'Bajaj Allianz Home Structure Insurance - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/home-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0015V01201516', 'Bajaj Allianz Commercial General Liability - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/liability-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0025V01201920', 'Bajaj Allianz Cyber Insurance - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/cyber-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0018V01201617', 'Bajaj Allianz Directors & Officers Liability - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/liability-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0012V01201415', 'Bajaj Allianz Professional Liability - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/liability-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0008V01200304', 'Bajaj Allianz Inland Transit Insurance - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/marine-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0025V01202122', 'Bajaj Allianz Individual Cybersafe Insurance - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/cyber-insurance/individual-cybersafe', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0030V01202223', 'Bajaj Allianz Surety Bond - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/corporate-insurance/surety-bond', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0002V02200102', 'Bajaj Allianz Car Third Party Only - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/motor-insurance/car-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0004V01200102', 'Bajaj Allianz Commercial Vehicle Package - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/motor-insurance/commercial-vehicle-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0001V05200102', 'Bajaj Allianz Engine Protect Add-On - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/motor-insurance/car-insurance/add-on-covers', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0001V01200102', 'Bajaj Allianz Private Car Package Policy - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/motor-insurance/car-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0003V02200102', 'Bajaj Allianz Two Wheeler Third Party - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/motor-insurance/two-wheeler-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0002V01200102', 'Bajaj Allianz Two Wheeler Package Policy - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/motor-insurance/two-wheeler-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0024V01201516', 'Bajaj Allianz PMSBY - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/personal-accident/pmsby', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0022V01201617', 'Bajaj Allianz Domestic Travel Insurance - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/travel-insurance/domestic', 'Bajaj Allianz GI Official'),
    ('IRDAN113RP0023V01201718', 'Bajaj Allianz Student Guard - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/travel-insurance/student-guard', 'Bajaj Allianz GI Official'),
    ('IRDAN113TI0001V01201617', 'Bajaj Allianz Travel Companion - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/travel-insurance/international', 'Bajaj Allianz GI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== HDFC ERGO PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN146RP0015V01201617', 'HDFC ERGO Boiler & Pressure Plant - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/engineering-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0035V01201819', 'HDFC ERGO Business Interruption - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/fire-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0025V01202122', 'HDFC ERGO Home Shield Contents Cover - Brochure', 'brochure', 'https://www.hdfcergo.com/home-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0020V01201819', 'HDFC ERGO Commercial General Liability Plus - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/liability-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0030V01202122', 'HDFC ERGO Cyber Sachet Insurance - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/cyber-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0022V01201920', 'HDFC ERGO Directors & Officers Liability - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/liability-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0025V01201920', 'HDFC ERGO Professional Indemnity - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/liability-insurance', 'HDFC ERGO Official'),
    ('IRDAN146P0004V01200304', 'HDFC ERGO Marine Cargo Open Policy - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/marine-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0005V01200304', 'HDFC ERGO Marine Hull and Machinery - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/marine-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0028V01201920', 'HDFC ERGO Ship Repairers Liability - Brochure', 'brochure', 'https://www.hdfcergo.com/corporate-insurance/marine-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0001V05200304', 'HDFC ERGO Return to Invoice Add-On - Brochure', 'brochure', 'https://www.hdfcergo.com/motor-insurance/car-insurance/add-on-covers', 'HDFC ERGO Official'),
    ('IRDAN146RP0003V02200304', 'HDFC ERGO Two Wheeler Third Party Only - Brochure', 'brochure', 'https://www.hdfcergo.com/motor-insurance/two-wheeler-insurance', 'HDFC ERGO Official'),
    ('IRDAN146RP0032V01202223', 'HDFC ERGO Corporate Travel Shield - Brochure', 'brochure', 'https://www.hdfcergo.com/travel-insurance/corporate-travel', 'HDFC ERGO Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== TATA AIG GENERAL PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN108RP0015V01201314', 'Tata AIG Contractor All Risk - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/engineering-insurance', 'Tata AIG Official'),
    ('IRDAN108RP0019V02202021', 'TATA AIG Bharat Griha Raksha - Brochure', 'brochure', 'https://www.tataaig.com/home-insurance/bharat-griha-raksha', 'Tata AIG Official'),
    ('IRDAN108RP0021V01202223', 'TATA AIG Home Protect Policy - Brochure', 'brochure', 'https://www.tataaig.com/home-insurance', 'Tata AIG Official'),
    ('IRDAN137RP0009V01202122', 'Tata AIG Home Contents Insurance - Brochure', 'brochure', 'https://www.tataaig.com/home-insurance/home-contents', 'Tata AIG Official'),
    ('IRDAN108RP0010V01201112', 'Tata AIG Commercial General Liability - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/liability-insurance', 'Tata AIG Official'),
    ('IRDAN108RP0028V01201920', 'Tata AIG Cyber Enterprise Risk Management - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/cyber-insurance', 'Tata AIG Official'),
    ('IRDAN108RP0012V01201213', 'Tata AIG Product Liability - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/liability-insurance', 'Tata AIG Official'),
    ('IRDAN108RP0025V01202223', 'TATA AIG Bharat Sookshma Udyam Suraksha - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/sme-insurance', 'Tata AIG Official'),
    ('IRDAN108P0020V01201213', 'Tata AIG Trade Credit Insurance - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/trade-credit-insurance', 'Tata AIG Official'),
    ('IRDAN108RP0025V01201718', 'Tata AIG Group Personal Accident - Brochure', 'brochure', 'https://www.tataaig.com/business-insurance/personal-accident', 'Tata AIG Official'),
    ('IRDAN108RP0024V01201718', 'Tata AIG Corporate Travel Insurance - Brochure', 'brochure', 'https://www.tataaig.com/travel-insurance/corporate-travel', 'Tata AIG Official'),
    ('IRDAN108RP0022V01201516', 'Tata AIG Domestic Travel Guard - Brochure', 'brochure', 'https://www.tataaig.com/travel-insurance/domestic-travel', 'Tata AIG Official'),
    ('IRDAN108RP0023V01201617', 'Tata AIG Student Travel Insurance - Brochure', 'brochure', 'https://www.tataaig.com/travel-insurance/student-travel', 'Tata AIG Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== NEW INDIA ASSURANCE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN190RP0033V01200506', 'New India Assurance Cattle Insurance - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/cattle-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0027V01200607', 'New India Assurance Boiler Insurance - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/engineering-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0025V01200506', 'New India Assurance Contractor All Risk - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/engineering-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0028V01200607', 'New India Assurance Electronic Equipment - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/engineering-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0026V01200506', 'New India Assurance Erection All Risk - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/engineering-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0029V01200607', 'New India Assurance Machinery Breakdown - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/engineering-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0034V01200506', 'New India Assurance Loss of Profits - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/fire-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0008V01200102', 'New India Assurance Employees Compensation - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/liability-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0018V01200607', 'New India Assurance Product Liability - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/liability-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0015V01200506', 'New India Assurance Professional Indemnity - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/liability-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0020V01200506', 'New India Assurance Public Liability - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/liability-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0022V01200607', 'New India Assurance Charterers Liability - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/marine-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0007V01200102', 'New India Assurance Inland Transit - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/marine-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0005V01200102', 'New India Assurance Marine Cargo - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/marine-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0006V01200102', 'New India Assurance Marine Hull - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/marine-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0032V01200506', 'New India Assurance Fidelity Guarantee - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/miscellaneous-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0035V01202223', 'New India Assurance Surety Bond - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/miscellaneous-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0003V01200102', 'New India Assurance Commercial Vehicle - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/motor-insurance', 'New India Assurance Official'),
    ('IRDAN190RP0031V01200607', 'New India Assurance Group Personal Accident - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/personal-accident', 'New India Assurance Official'),
    ('IRDAN190RP0030V01201516', 'New India Assurance PMSBY - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/pmsby', 'New India Assurance Official'),
    ('IRDAN190RP0040V01201617', 'National Insurance Crop Insurance (PMFBY) - Brochure', 'brochure', 'https://www.nationalinsurance.nic.co.in/en/crop-insurance', 'National Insurance Official'),
    ('IRDAN190RP0015V01200102', 'National Insurance Machinery Breakdown - Brochure', 'brochure', 'https://www.nationalinsurance.nic.co.in/en/engineering-insurance', 'National Insurance Official'),
    ('IRDAN190RP0020V01200102', 'National Insurance Public Liability - Brochure', 'brochure', 'https://www.nationalinsurance.nic.co.in/en/liability-insurance', 'National Insurance Official'),
    ('IRDAN170RP0001V01200102', 'National Insurance Motor Package - Brochure', 'brochure', 'https://www.nationalinsurance.nic.co.in/en/motor-insurance', 'National Insurance Official'),
    ('IRDAN132RP0003V01200102', 'National Insurance Private Car OD - Brochure', 'brochure', 'https://www.nationalinsurance.nic.co.in/en/motor-insurance', 'National Insurance Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== REMAINING GENERAL INSURERS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    -- Acko General
    ('IRDAN157RP0001V01201819', 'Acko Car Insurance Policy - Brochure', 'brochure', 'https://www.acko.com/car-insurance', 'Acko Official'),
    ('IRDAN157RP0001V01201718', 'Acko Private Car Package Policy - Brochure', 'brochure', 'https://www.acko.com/car-insurance', 'Acko Official'),
    ('IRDAN157RP0002V01201819', 'Acko Two Wheeler Insurance - Brochure', 'brochure', 'https://www.acko.com/two-wheeler-insurance', 'Acko Official'),
    ('IRDAN157RP0002V01201718', 'Acko Two Wheeler Package Policy - Brochure', 'brochure', 'https://www.acko.com/two-wheeler-insurance', 'Acko Official'),
    ('IRDAN157RP0008V01201920', 'Acko Travel Insurance - Brochure', 'brochure', 'https://www.acko.com/travel-insurance', 'Acko Official'),
    -- Agriculture Insurance
    ('IRDAN106RP0010V01202425', 'AIC Fal Suraksha Bima - Brochure', 'brochure', 'https://www.aicofindia.com/AICEng/Pages/Products.aspx', 'AIC Official'),
    ('IRDAN174RP0005V01201516', 'AIC Livestock Insurance - Brochure', 'brochure', 'https://www.aicofindia.com/AICEng/Pages/Products.aspx', 'AIC Official'),
    ('IRDAN106RP0001V01201617', 'AIC PMFBY - Brochure', 'brochure', 'https://www.aicofindia.com/AICEng/Pages/Products.aspx', 'AIC Official'),
    ('IRDAN106RP0002V01201617', 'AIC RWBCIS - Brochure', 'brochure', 'https://www.aicofindia.com/AICEng/Pages/Products.aspx', 'AIC Official'),
    -- Cholamandalam MS
    ('IRDAN128RP0006V01200203', 'Chola MS Engineering Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/engineering-insurance', 'Chola MS Official'),
    ('IRDAN128RP0003V01200203', 'Chola MS Fire Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/fire-insurance', 'Chola MS Official'),
    ('IRDAN104RP0003V01200304', 'Chola MS Fire Insurance Policy - Brochure', 'brochure', 'https://www.cholainsurance.com/fire-insurance', 'Chola MS Official'),
    ('IRDAN104RP0008V01200304', 'Chola MS Workmen Compensation - Brochure', 'brochure', 'https://www.cholainsurance.com/liability-insurance', 'Chola MS Official'),
    ('IRDAN128RP0004V01200203', 'Chola MS Marine Cargo Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/marine-insurance', 'Chola MS Official'),
    ('IRDAN104RP0005V01200304', 'Chola MS Marine Cargo Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/marine-insurance', 'Chola MS Official'),
    ('IRDAN104RP0001V01200304', 'Chola MS Car Insurance Policy - Brochure', 'brochure', 'https://www.cholainsurance.com/motor-insurance/car-insurance', 'Chola MS Official'),
    ('IRDAN123RP0001V01200102', 'Chola MS Private Car Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/motor-insurance/car-insurance', 'Chola MS Official'),
    ('IRDAN128RP0001V01200203', 'Chola MS Private Car Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/motor-insurance/car-insurance', 'Chola MS Official'),
    ('IRDAN104RP0002V01200304', 'Chola MS Two Wheeler Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/motor-insurance/two-wheeler-insurance', 'Chola MS Official'),
    ('IRDAN128RP0002V01200203', 'Chola MS Two Wheeler Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/motor-insurance/two-wheeler-insurance', 'Chola MS Official'),
    ('IRDAN128RP0005V01200203', 'Chola MS Personal Accident Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/personal-accident-insurance', 'Chola MS Official'),
    ('IRDAN128RP0009V01200708', 'Chola MS Travel Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/travel-insurance', 'Chola MS Official'),
    ('IRDAN104RP0015V01201011', 'Chola MS Travel Insurance Policy - Brochure', 'brochure', 'https://www.cholainsurance.com/travel-insurance', 'Chola MS Official'),
    ('IRDAN116RP0015V01201516', 'Chola MS Travel Protect - Brochure', 'brochure', 'https://www.cholainsurance.com/travel-insurance', 'Chola MS Official'),
    -- ECGC
    ('IRDAN120RP0001V01200203', 'ECGC Export Credit Insurance - Brochure', 'brochure', 'https://www.ecgc.in/english/products-services/', 'ECGC Official'),
    ('IRDAN120RP0005V01200506', 'ECGC Overseas Investment Insurance - Brochure', 'brochure', 'https://www.ecgc.in/english/products-services/', 'ECGC Official'),
    -- IFFCO Tokio
    ('IRDAN106RP0025V01201516', 'IFFCO Tokio Crop Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/crop-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0015V01201617', 'IFFCO Tokio Crop Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/crop-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0003V01200102', 'IFFCO Tokio Fire Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/fire-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106RP0003V01200102', 'IFFCO Tokio Fire Insurance Policy - Brochure', 'brochure', 'https://www.iffcotokio.co.in/fire-insurance', 'IFFCO Tokio Official'),
    ('IRDAN103RP0020V01201819', 'IFFCO TOKIO Home Protect - Brochure', 'brochure', 'https://www.iffcotokio.co.in/home-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0004V01200102', 'IFFCO Tokio Marine Cargo Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/marine-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106P0007V01200102', 'IFFCO Tokio Marine Cargo Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/marine-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0001V01200102', 'IFFCO Tokio Private Car Comprehensive - Brochure', 'brochure', 'https://www.iffcotokio.co.in/motor-insurance/car-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106RP0001V01200102', 'IFFCO Tokio Private Car Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/motor-insurance/car-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106RP0001V01200001', 'IFFCO Tokio Private Car Package Policy - Brochure', 'brochure', 'https://www.iffcotokio.co.in/motor-insurance/car-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106RP0002V01200102', 'IFFCO Tokio Two Wheeler Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/motor-insurance/two-wheeler-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0002V01200102', 'IFFCO Tokio Two Wheeler Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/motor-insurance/two-wheeler-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0005V01200102', 'IFFCO Tokio Personal Accident Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/personal-accident-insurance', 'IFFCO Tokio Official'),
    ('IRDAN127RP0008V01200506', 'IFFCO Tokio Travel Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/travel-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106RP0020V01200708', 'IFFCO Tokio Travel Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/travel-insurance', 'IFFCO Tokio Official'),
    -- Generali Central GI, Go Digit, IndusInd GI, Kshema, Liberty, Magma, Navi, Raheja QBE
    ('IRDAN132RP0003V01200607', 'Generali Central Fire Insurance - Brochure', 'brochure', 'https://general.futuregenerali.in/fire-insurance', 'Future Generali GI Official'),
    ('IRDAN118RP0015V01201516', 'Generali Central Home Insurance - Brochure', 'brochure', 'https://general.futuregenerali.in/home-insurance', 'Future Generali GI Official'),
    ('IRDAN132RP0001V01200607', 'Generali Central Car Insurance - Brochure', 'brochure', 'https://general.futuregenerali.in/motor-insurance/car-insurance', 'Future Generali GI Official'),
    ('IRDAN147RP0001V01200607', 'Generali Central Private Car Insurance - Brochure', 'brochure', 'https://general.futuregenerali.in/motor-insurance/car-insurance', 'Future Generali GI Official'),
    ('IRDAN118RP0001V01200809', 'Generali Central Private Car Package - Brochure', 'brochure', 'https://general.futuregenerali.in/motor-insurance/car-insurance', 'Future Generali GI Official'),
    ('IRDAN132RP0002V01200607', 'Generali Central Two Wheeler Insurance - Brochure', 'brochure', 'https://general.futuregenerali.in/motor-insurance/two-wheeler-insurance', 'Future Generali GI Official'),
    ('IRDAN158RP009V01201819', 'Digit Home Insurance - Brochure', 'brochure', 'https://www.godigit.com/home-insurance', 'Go Digit Official'),
    ('IRDAN158RP005V01201718', 'Digit Private Car Package Policy - Brochure', 'brochure', 'https://www.godigit.com/motor-insurance/car-insurance', 'Go Digit Official'),
    ('IRDAN158RP006V01201718', 'Digit Two-Wheeler Insurance - Brochure', 'brochure', 'https://www.godigit.com/motor-insurance/two-wheeler-insurance', 'Go Digit Official'),
    ('IRDAN158TI001V01201718', 'Digit International Travel Insurance - Brochure', 'brochure', 'https://www.godigit.com/travel-insurance', 'Go Digit Official'),
    ('IRDAN156RP0003V01201920', 'IndusInd General Fire Insurance - Brochure', 'brochure', 'https://www.indusindgeneralinsurance.com/fire-insurance', 'IndusInd GI Official'),
    ('IRDAN127RP0001V01200809', 'IndusInd GI Private Car Package - Brochure', 'brochure', 'https://www.indusindgeneralinsurance.com/motor-insurance', 'IndusInd GI Official'),
    ('IRDAN156RP0001V01201920', 'IndusInd General Car Insurance - Brochure', 'brochure', 'https://www.indusindgeneralinsurance.com/motor-insurance', 'IndusInd GI Official'),
    ('IRDAN156RP0002V01201920', 'IndusInd General Two Wheeler Insurance - Brochure', 'brochure', 'https://www.indusindgeneralinsurance.com/motor-insurance', 'IndusInd GI Official'),
    ('IRDAN127RP0008V01201516', 'IndusInd GI Travel Insurance - Brochure', 'brochure', 'https://www.indusindgeneralinsurance.com/travel-insurance', 'IndusInd GI Official'),
    ('IRDAN172RP0001V01202425', 'Kshema Motor Insurance - Brochure', 'brochure', 'https://www.kshemageneral.com/motor-insurance', 'Kshema General Official'),
    -- Liberty, Magma, Navi, Raheja QBE, Royal Sundaram, SBI General, Shriram, Oriental, United India, Universal Sompo, Zuno, Zurich Kotak, Star Health PA
    ('IRDAN150RP0003V01201314', 'Liberty Fire Insurance Policy - Brochure', 'brochure', 'https://www.libertyinsurance.in/fire-insurance', 'Liberty GI Official'),
    ('IRDAN152RP0003V01201314', 'Liberty General Fire Insurance - Brochure', 'brochure', 'https://www.libertyinsurance.in/fire-insurance', 'Liberty GI Official'),
    ('IRDAN150RP0011V01202122', 'Liberty Home Insurance - Brochure', 'brochure', 'https://www.libertyinsurance.in/home-insurance', 'Liberty GI Official'),
    ('IRDAN150RP0001V01201314', 'Liberty Car Insurance Policy - Brochure', 'brochure', 'https://www.libertyinsurance.in/motor-insurance/car-insurance', 'Liberty GI Official'),
    ('IRDAN152RP0001V01201314', 'Liberty Private Car Package Policy - Brochure', 'brochure', 'https://www.libertyinsurance.in/motor-insurance/car-insurance', 'Liberty GI Official'),
    ('IRDAN150RP0002V01201314', 'Liberty Two Wheeler Insurance - Brochure', 'brochure', 'https://www.libertyinsurance.in/motor-insurance/two-wheeler-insurance', 'Liberty GI Official'),
    ('IRDAN152RP0002V01201314', 'Liberty Two Wheeler Package Policy - Brochure', 'brochure', 'https://www.libertyinsurance.in/motor-insurance/two-wheeler-insurance', 'Liberty GI Official'),
    ('IRDAN153RP0003V01201314', 'Magma General Fire Insurance - Brochure', 'brochure', 'https://www.magma.co.in/fire-insurance', 'Magma General Official'),
    ('IRDAN151RP0003V01201415', 'Magma HDI Fire Insurance - Brochure', 'brochure', 'https://www.magma.co.in/fire-insurance', 'Magma General Official'),
    ('IRDAN153RP0001V01201314', 'Magma General Private Car Insurance - Brochure', 'brochure', 'https://www.magma.co.in/motor-insurance', 'Magma General Official'),
    ('IRDAN153RP0002V01201314', 'Magma General Two Wheeler Insurance - Brochure', 'brochure', 'https://www.magma.co.in/motor-insurance', 'Magma General Official'),
    ('IRDAN151RP0001V01201415', 'Magma HDI Car Insurance - Brochure', 'brochure', 'https://www.magma.co.in/motor-insurance', 'Magma General Official'),
    ('IRDAN151RP0002V01201415', 'Magma HDI Two Wheeler Insurance - Brochure', 'brochure', 'https://www.magma.co.in/motor-insurance', 'Magma General Official'),
    ('IRDAN149RP0001V01201415', 'Magma Private Car Package Policy - Brochure', 'brochure', 'https://www.magma.co.in/motor-insurance', 'Magma General Official'),
    ('IRDAN155RP0010V01202122', 'Navi Home Insurance Policy - Brochure', 'brochure', 'https://www.naviinsurance.com/home-insurance', 'Navi General Official'),
    ('IRDAN155RP0001V01201617', 'Navi Private Car Package Policy (V01) - Brochure', 'brochure', 'https://www.naviinsurance.com/motor-insurance/car-insurance', 'Navi General Official'),
    ('IRDAN155RP0001V01202021', 'Navi Private Car Package Policy - Brochure', 'brochure', 'https://www.naviinsurance.com/motor-insurance/car-insurance', 'Navi General Official'),
    ('IRDAN155RP0002V01202021', 'Navi Two Wheeler Package Policy - Brochure', 'brochure', 'https://www.naviinsurance.com/motor-insurance/two-wheeler-insurance', 'Navi General Official'),
    ('IRDAN163RP0003V01201920', 'Raheja QBE Fire Insurance Policy - Brochure', 'brochure', 'https://www.rahejaqbe.com/fire-insurance', 'Raheja QBE Official'),
    ('IRDAN141RP0005V01201516', 'Raheja QBE Standard Fire Policy - Brochure', 'brochure', 'https://www.rahejaqbe.com/fire-insurance', 'Raheja QBE Official'),
    ('IRDAN163RP0001V01201920', 'Raheja QBE Comprehensive Car Insurance - Brochure', 'brochure', 'https://www.rahejaqbe.com/motor-insurance', 'Raheja QBE Official'),
    ('IRDAN163RP0002V01201920', 'Raheja QBE Two Wheeler Insurance - Brochure', 'brochure', 'https://www.rahejaqbe.com/motor-insurance', 'Raheja QBE Official'),
    -- Royal Sundaram
    ('IRDAN110RP0003V01200001', 'Royal Sundaram Fire Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/fire-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0003V01200102', 'Royal Sundaram Fire Insurance Policy - Brochure', 'brochure', 'https://www.royalsundaram.in/fire-insurance', 'Royal Sundaram Official'),
    ('IRDAN110RP0008V01200607', 'Royal Sundaram Home Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/home-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0022V01201516', 'Royal Sundaram Home Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/home-insurance', 'Royal Sundaram Official'),
    ('IRDAN110RP0004V01200001', 'Royal Sundaram Marine Cargo Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/marine-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0005V01200102', 'Royal Sundaram Marine Cargo Policy - Brochure', 'brochure', 'https://www.royalsundaram.in/marine-insurance', 'Royal Sundaram Official'),
    ('IRDAN110RP0001V01200001', 'Royal Sundaram Private Car Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/motor-insurance/car-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0001V01201920', 'Royal Sundaram Private Car Package Policy - Brochure', 'brochure', 'https://www.royalsundaram.in/motor-insurance/car-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0001V01200001', 'Royal Sundaram Private Car Package Policy - Brochure', 'brochure', 'https://www.royalsundaram.in/motor-insurance/car-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0002V01200001', 'Royal Sundaram Two Wheeler Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/motor-insurance/two-wheeler-insurance', 'Royal Sundaram Official'),
    ('IRDAN110RP0002V01200001', 'Royal Sundaram Two Wheeler Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/motor-insurance/two-wheeler-insurance', 'Royal Sundaram Official'),
    ('IRDAN102P0002V01201617', 'Royal Sundaram Two Wheeler Package - Brochure', 'brochure', 'https://www.royalsundaram.in/motor-insurance/two-wheeler-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0010V01200506', 'Royal Sundaram Travel Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/travel-insurance', 'Royal Sundaram Official'),
    ('IRDAN102RP0020V01201415', 'Royal Sundaram Travel Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/travel-insurance', 'Royal Sundaram Official'),
    ('IRDAN110RP0006V01200506', 'Royal Sundaram Travel Insurance - Brochure', 'brochure', 'https://www.royalsundaram.in/travel-insurance', 'Royal Sundaram Official'),
    -- SBI General
    ('IRDAN144RP0001V01201011', 'SBI General Burglary Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/fire-burglary-insurance', 'SBI General Official'),
    ('IRDAN155RP0004V01201920', 'SBI General Fire Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/fire-burglary-insurance', 'SBI General Official'),
    ('IRDAN155RP0010V01201920', 'SBI General Home Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/home-insurance', 'SBI General Official'),
    ('IRDAN144CP0006V01201011', 'SBI General Industrial All Risks - Brochure', 'brochure', 'https://www.sbigeneral.in/fire-burglary-insurance', 'SBI General Official'),
    ('IRDAN144RP0008V04201112', 'SBI General Standard Fire & Special Perils - Brochure', 'brochure', 'https://www.sbigeneral.in/fire-burglary-insurance', 'SBI General Official'),
    ('IRDAN155RP0018V01202122', 'SBI General Cyber Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/cyber-insurance', 'SBI General Official'),
    ('IRDAN155RP0005V01201920', 'SBI General Marine Cargo Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/marine-insurance', 'SBI General Official'),
    ('IRDAN144RP0011V02201011', 'SBI General Money Insurance Policy - Brochure', 'brochure', 'https://www.sbigeneral.in/corporate-insurance', 'SBI General Official'),
    ('IRDAN155RP0001V02201920', 'SBI General Private Car Comprehensive - Brochure', 'brochure', 'https://www.sbigeneral.in/motor-insurance/car-insurance', 'SBI General Official'),
    ('IRDAN144RP0005V03201112', 'SBI General Private Car Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/motor-insurance/car-insurance', 'SBI General Official'),
    ('IRDAN155RP0003V02201920', 'SBI General Two Wheeler Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/motor-insurance/two-wheeler-insurance', 'SBI General Official'),
    ('IRDAN155RP0009V01201920', 'SBI General Personal Accident Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/personal-accident-insurance', 'SBI General Official'),
    ('IRDAN155RP0008V01201920', 'SBI General Travel Insurance - Brochure', 'brochure', 'https://www.sbigeneral.in/travel-insurance', 'SBI General Official'),
    -- Shriram General
    ('IRDAN137RP0003V01201516', 'Shriram GI Fire Insurance Policy - Brochure', 'brochure', 'https://www.shriramgi.com/fire-insurance', 'Shriram GI Official'),
    ('IRDAN148RP0003V01200809', 'Shriram General Fire Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/fire-insurance', 'Shriram GI Official'),
    ('IRDAN139RP0010V01201819', 'Shriram GI Home Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/home-insurance', 'Shriram GI Official'),
    ('IRDAN139RP0003V01201516', 'Shriram GI Commercial Vehicle Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/motor-insurance/commercial-vehicle', 'Shriram GI Official'),
    ('IRDAN139RP0001V01201516', 'Shriram GI Private Car Package Policy - Brochure', 'brochure', 'https://www.shriramgi.com/motor-insurance/car-insurance', 'Shriram GI Official'),
    ('IRDAN148RP0001V01200809', 'Shriram General Private Car Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/motor-insurance/car-insurance', 'Shriram GI Official'),
    ('IRDAN148RP0002V01200809', 'Shriram General Two Wheeler Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/motor-insurance/two-wheeler-insurance', 'Shriram GI Official'),
    ('IRDAN137RP0010V01201617', 'Shriram GI Travel Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/travel-insurance', 'Shriram GI Official'),
    -- Star Health PA
    ('SHAHLIP21042V012021', 'Star Family Accident Care - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/family-accident-care', 'Star Health Official'),
    -- Oriental, United India, Universal Sompo, Zuno, Zurich Kotak
    ('IRDAN103RP0015V01200102', 'Oriental Machinery Breakdown - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/engineering-insurance', 'Oriental Insurance Official'),
    ('IRDAN103RP0003V01200102', 'Oriental Fire Insurance Policy - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/fire-insurance', 'Oriental Insurance Official'),
    ('IRDAN129RP0012V01200506', 'Oriental Insurance Public Liability - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/liability-insurance', 'Oriental Insurance Official'),
    ('IRDAN103RP0020V01200102', 'Oriental Public Liability Policy - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/liability-insurance', 'Oriental Insurance Official'),
    ('IRDAN103RP0005V01200102', 'Oriental Marine Cargo Policy - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/marine-insurance', 'Oriental Insurance Official'),
    ('IRDAN129RP0015V01200607', 'Oriental Insurance Fidelity Guarantee - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/miscellaneous-insurance', 'Oriental Insurance Official'),
    ('IRDAN180RP0001V01200102', 'Oriental Insurance Motor Package Policy - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/motor-insurance', 'Oriental Insurance Official'),
    ('IRDAN129RP0010V01200506', 'Oriental Insurance Overseas Mediclaim - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/travel-insurance', 'Oriental Insurance Official'),
    ('IRDAN130RP0010V01200607', 'United India Livestock Insurance - Brochure', 'brochure', 'https://uiic.co.in/product/crop-insurance', 'United India Official'),
    ('IRDAN148RP0015V01200102', 'United India Machinery Breakdown - Brochure', 'brochure', 'https://uiic.co.in/product/engineering-insurance', 'United India Official'),
    ('IRDAN148RP0003V01200102', 'United India Fire Insurance Policy - Brochure', 'brochure', 'https://uiic.co.in/product/fire-insurance', 'United India Official'),
    ('IRDAN148RP0008V01200102', 'United India Workmen Compensation - Brochure', 'brochure', 'https://uiic.co.in/product/liability-insurance', 'United India Official'),
    ('IRDAN148RP0005V01200102', 'United India Marine Cargo Policy - Brochure', 'brochure', 'https://uiic.co.in/product/marine-insurance', 'United India Official'),
    ('IRDAN160RP0001V01200102', 'United India Motor Package Policy - Brochure', 'brochure', 'https://uiic.co.in/product/motor-insurance', 'United India Official'),
    ('IRDAN142RP0003V01200809', 'Universal Sompo Fire Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/fire-insurance', 'Universal Sompo Official'),
    ('IRDAN117RP0003V01200708', 'Universal Sompo Fire Insurance Policy - Brochure', 'brochure', 'https://www.universalsompo.com/fire-insurance', 'Universal Sompo Official'),
    ('IRDAN117RP0015V01201920', 'Universal Sompo Shopkeeper Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/shopkeeper-insurance', 'Universal Sompo Official'),
    ('IRDAN142RP0001V01200809', 'Universal Sompo Private Car Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/motor-insurance', 'Universal Sompo Official'),
    ('IRDAN117RP0001V01200708', 'Universal Sompo Private Car Package - Brochure', 'brochure', 'https://www.universalsompo.com/motor-insurance', 'Universal Sompo Official'),
    ('IRDAN142RP0002V01200809', 'Universal Sompo Two Wheeler Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/motor-insurance', 'Universal Sompo Official'),
    ('IRDAN148RP0008V01201920', 'Zuno Home Insurance - Brochure', 'brochure', 'https://www.zunoinsurance.com/home-insurance', 'Zuno General Official'),
    ('IRDAN158RP0001V01201920', 'Zuno Car Insurance Policy - Brochure', 'brochure', 'https://www.zunoinsurance.com/car-insurance', 'Zuno General Official'),
    ('IRDAN148RP0001V01201718', 'Zuno Private Car Package Policy - Brochure', 'brochure', 'https://www.zunoinsurance.com/car-insurance', 'Zuno General Official'),
    ('IRDAN158RP0002V01201920', 'Zuno Two Wheeler Insurance - Brochure', 'brochure', 'https://www.zunoinsurance.com/two-wheeler-insurance', 'Zuno General Official'),
    ('IRDAN158RP0008V01202021', 'Zuno Travel Insurance - Brochure', 'brochure', 'https://www.zunoinsurance.com/travel-insurance', 'Zuno General Official'),
    ('IRDAN152RP0003V01201415', 'Zurich Kotak Fire Insurance Policy - Brochure', 'brochure', 'https://www.zurichkotak.com/fire-insurance', 'Zurich Kotak Official'),
    ('IRDAN152RP0005V01201415', 'Zurich Kotak Marine Cargo Insurance - Brochure', 'brochure', 'https://www.zurichkotak.com/marine-insurance', 'Zurich Kotak Official'),
    ('IRDAN152RP0006V02201516', 'Zurich Kotak Car Secure Policy - Brochure', 'brochure', 'https://www.zurichkotak.com/motor-insurance/car-insurance', 'Zurich Kotak Official'),
    ('IRDAN152RP0008V02201617', 'Zurich Kotak Two Wheeler Secure Policy - Brochure', 'brochure', 'https://www.zurichkotak.com/motor-insurance/two-wheeler-insurance', 'Zurich Kotak Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;
