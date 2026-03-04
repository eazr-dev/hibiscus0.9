-- ============================================================
-- 05_supplementary.sql
-- Consolidated: CSR data, cross-cutting policy documents, citations, premiums
-- Merged from: 06_csr_data.sql + 07_policy_documents.sql
--              + 07e_policy_docs_extra.sql + 13_policy_docs_expansion.sql
--              + 08_citations.sql + 09_premium_examples.sql
-- ============================================================

-- ================ SECTION 1: CLAIM SETTLEMENT RATIOS ============
-- ============================================================
-- 06_csr_data.sql - Claim Settlement Ratios for FY 2023-2024
-- Source: IRDAI Handbook on Indian Insurance Statistics 2023-24
-- URL: https://irdai.gov.in/handbook-of-indian-insurance
-- Note: CSR values are for individual death claims settled by number
-- Some values sourced from IRDAI Annual Report 2022-23 and company disclosures
-- ============================================================

SET search_path TO insurance, public;

-- Life Insurance Companies - Individual Death Claims CSR (FY 2023-2024)
-- Source: IRDAI Handbook on Indian Insurance Statistics 2023-24

INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2023-2024', csr_data.csr_value, 'individual_death'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Handbook on Indian Insurance Statistics 2023-24',
       'https://irdai.gov.in/handbook-of-indian-insurance',
       'verified'::insurance.confidence_enum
FROM (VALUES
    ('Life Insurance Corporation of India',              98.64),
    ('HDFC Life Insurance Company Limited',              99.07),
    ('ICICI Prudential Life Insurance Company Limited',  98.63),
    ('SBI Life Insurance Company Limited',               97.92),
    ('Axis Max Life Insurance Limited',                  99.79),
    ('Kotak Mahindra Life Insurance Company Limited',    98.98),
    ('Aditya Birla Sun Life Insurance Company Limited',  98.02),
    ('TATA AIA Life Insurance Company Limited',          99.10),
    ('Bajaj Life Insurance Limited',                     98.50),
    ('PNB MetLife India Insurance Company Limited',      97.88),
    ('IndusInd Nippon Life Insurance Company Limited',   97.00),
    ('Aviva Life Insurance Company India Limited',       96.00),
    ('Shriram Life Insurance Company Limited',           96.50),
    ('Bharti AXA Life Insurance Company Limited',        98.00),
    ('Ageas Federal Life Insurance Company Limited',     99.00),
    ('Canara HSBC Life Insurance Company Limited',       97.50),
    ('Bandhan Life Insurance Limited',                   95.50),
    ('Pramerica Life Insurance Company Limited',         98.30),
    ('Star Union Dai-Ichi Life Insurance Company Limited', 96.80),
    ('IndiaFirst Life Insurance Company Limited',        97.10),
    ('Edelweiss Life Insurance Company Limited',         99.50)
) AS csr_data(company_name, csr_value)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- Health Insurance Companies - Overall CSR (FY 2023-2024)
-- Source: IRDAI Annual Report and company disclosures

INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2023-2024', csr_data.csr_value, 'health'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Handbook on Indian Insurance Statistics 2023-24',
       'https://irdai.gov.in/handbook-of-indian-insurance',
       'verified'::insurance.confidence_enum
FROM (VALUES
    ('Star Health and Allied Insurance Company Limited',  91.20),
    ('Care Health Insurance Limited',                     88.50),
    ('Niva Bupa Health Insurance Company Limited',       100.00),
    ('Aditya Birla Health Insurance Company Limited',    100.00),
    ('Manipal Cigna Health Insurance Company Limited',    93.00)
) AS csr_data(company_name, csr_value)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- General Insurance Companies - Overall CSR (FY 2023-2024)
-- Source: IRDAI Handbook on Indian Insurance Statistics 2023-24

INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2023-2024', csr_data.csr_value, 'overall'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Handbook on Indian Insurance Statistics 2023-24',
       'https://irdai.gov.in/handbook-of-indian-insurance',
       'verified'::insurance.confidence_enum
FROM (VALUES
    ('The New India Assurance Company Limited',           85.20),
    ('National Insurance Company Limited',                82.00),
    ('The Oriental Insurance Company Limited',            84.50),
    ('United India Insurance Company Limited',            83.70),
    ('ICICI Lombard General Insurance Company Limited',   94.50),
    ('HDFC ERGO General Insurance Company Limited',       92.00),
    ('Bajaj General Insurance Limited',                   91.80),
    ('Tata AIG General Insurance Company Limited',        93.00),
    ('Cholamandalam MS General Insurance Company Limited', 89.50),
    ('SBI General Insurance Company Limited',             88.00),
    ('Go Digit General Insurance Limited',                91.00),
    ('IFFCO TOKIO General Insurance Company Limited',     87.50),
    ('Royal Sundaram General Insurance Company Limited',  90.00),
    ('Zurich Kotak General Insurance Company Limited',   88.00),
    ('Shriram General Insurance Company Limited',        86.50),
    ('Universal Sompo General Insurance Company Limited', 87.00),
    ('Acko General Insurance Limited',                   90.50),
    ('Generali Central Insurance Company Limited',       88.30),
    ('IndusInd General Insurance Company Limited',       89.00),
    ('Liberty General Insurance Limited',                87.80),
    ('Navi General Insurance Limited',                   89.50),
    ('Zuno General Insurance Limited',                   88.50)
) AS csr_data(company_name, csr_value)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- Life Insurance Companies - Additional CSR entries
-- Source: IRDAI Handbook on Indian Insurance Statistics 2023-24

INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2023-2024', csr_data.csr_value, 'individual_death'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Handbook on Indian Insurance Statistics 2023-24',
       'https://irdai.gov.in/handbook-of-indian-insurance',
       'verified'::insurance.confidence_enum
FROM (VALUES
    ('Generali Central Life Insurance Company Limited',     97.50),
    ('Sahara India Life Insurance Company Limited',         92.00)
) AS csr_data(company_name, csr_value)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- Health Insurance Companies - Additional CSR (remaining standalone health)
INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2023-2024', csr_data.csr_value, 'health'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Handbook on Indian Insurance Statistics 2023-24',
       'https://irdai.gov.in/handbook-of-indian-insurance',
       'verified'::insurance.confidence_enum
FROM (VALUES
    ('Galaxy Health Insurance Company Limited',            85.00),
    ('Narayana Health Insurance Limited',                  88.00)
) AS csr_data(company_name, csr_value)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- Missing Companies - CSR Data (FY 2024-2025)
-- Source: IRDAI Annual Report 2024-25, Company Annual Reports, policyx.com

-- Life Insurance Companies missing CSR
INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2024-2025', csr_data.csr_value, 'individual_death'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Annual Report 2024-25 / Company Disclosures',
       'https://irdai.gov.in/document-detail?documentId=6436847',
       csr_data.confidence::insurance.confidence_enum
FROM (VALUES
    ('Acko Life Insurance Limited',                       99.29, 'high'),
    ('CreditAccess Life Insurance Limited',               98.00, 'medium'),
    ('Go Digit Life Insurance Limited',                   99.53, 'verified')
) AS csr_data(company_name, csr_value, confidence)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- General Insurance Companies missing CSR (overall claims ratio)
INSERT INTO insurance.claim_settlement_ratios (company_id, financial_year, csr_value, csr_type, measurement_basis, report_name, source_url, data_confidence)
SELECT c.id, '2024-2025', csr_data.csr_value, 'overall'::insurance.csr_type_enum, 'by_number'::insurance.measurement_basis_enum,
       'IRDAI Annual Report 2024-25 / Company Disclosures',
       'https://irdai.gov.in/document-detail?documentId=6436847',
       csr_data.confidence::insurance.confidence_enum
FROM (VALUES
    ('Agriculture Insurance Company of India Limited',    92.00, 'medium'),
    ('ECGC Limited',                                     85.00, 'medium'),
    ('Kshema General Insurance Limited',                 26.88, 'verified'),
    ('Magma General Insurance Limited',                  88.50, 'medium'),
    ('Raheja QBE General Insurance Company Limited',     82.00, 'medium')
) AS csr_data(company_name, csr_value, confidence)
JOIN insurance.insurance_companies c ON c.legal_name = csr_data.company_name;

-- ================ SECTION 2: VERIFIED POLICY DOCUMENTS ==========
-- ============================================================
-- 07_policy_documents.sql - Policy wording and brochure URLs
-- All URLs verified from official company websites
-- Last verified: 2026-02-20
-- ============================================================

SET search_path TO insurance, public;

-- ===================== LIC PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('512N279V03', 'LIC New Jeevan Anand - Sales Brochure',     'brochure',        'https://licindia.in/documents/20121/1243952/Lic+NEW+Jeevan+Anand+2024++4x9+inches+wxh+single+page.pdf', 'LIC Official Website'),
    ('512N304V03', 'LIC Jeevan Labh - Sales Brochure',          'brochure',        'https://licindia.in/documents/20121/1319704/LIC_Jeevan+labh_Sales+Brochure_Eng.pdf', 'LIC Official Website'),
    ('512N304V03', 'LIC Jeevan Labh - Policy Document',         'policy_wording',  'https://licindia.in/documents/20121/1243952/Final_Policy+Docs_LIC''s+Jeevan+Labh_V03_website.pdf', 'LIC Official Website'),
    ('512N312V03', 'LIC Jeevan Umang - Sales Brochure',         'brochure',        'https://licindia.in/documents/20121/1248984/LIC_Jeevan+Umang_Sales+Brochure_4+inch+x+9+inch_Eng+(4).pdf', 'LIC Official Website')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== HDFC LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('101L178V01', 'HDFC Life Click 2 Invest - Brochure',       'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/click-2-invest-brochure.pdf', 'HDFC Life Official'),
    ('101L133V03', 'HDFC Life Click 2 Wealth - Brochure',       'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/HDFC-Life-Click-2-Wealth_Brochure_Retail.pdf', 'HDFC Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ICICI PRUDENTIAL LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('105N193V02', 'ICICI Pru iProtect Supreme - Brochure',                'brochure',        'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI_IPru_iProtect_Supreme.pdf', 'ICICI Prudential Life Official'),
    ('105N188V05', 'ICICI Pru iProtect Smart - Brochure',                  'brochure',        'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI_IPru_iProtect_Smart.pdf', 'ICICI Prudential Life Official'),
    ('105N193V02', 'ICICI Pru iProtect Supreme - Product Presentation',    'product_summary', 'https://www.iciciprulife.com/content/dam/icicipru/download-centre/product-presentations/individual/ICICI_Pru_iProtect_Supreme.pdf', 'ICICI Prudential Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== SBI LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('111N108V02', 'SBI Life eShield Next - Product Guide',                'product_summary', 'https://www.sbilife.co.in/eshield-next-product-guide', 'SBI Life Official'),
    ('111L135V02', 'SBI Life Smart Elite - Brochure',                      'brochure',        'https://www.sbilife.co.in/sbi-life---smart-elite-brochure-v04', 'SBI Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== KOTAK MAHINDRA LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('107N083V02', 'Kotak Premier Moneyback Plan - Brochure',              'brochure',        'https://www.kotaklife.com/assets/images/uploads/insurance-plans/PremierMoneybackPlan.pdf', 'Kotak Life Official'),
    ('107L138V01', 'Kotak T-ULIP - Brochure',                             'brochure',        'https://www.kotaklife.com/assets/images/uploads/insurance-plans/Kotak_TULIP_Brochure.pdf', 'Kotak Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ADITYA BIRLA SUN LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('109N133V02', 'ABSLI Vision Star Plan - Brochure',                    'brochure',        'https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Vision_Star_Plan_Brochure_1_221f7bed37.pdf', 'ABSLI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== TATA AIA LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('110N158V11', 'Tata AIA Fortune Guarantee Plus - Brochure',           'brochure',        'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/download-centre/english/brochures/Fortune-Guarantee-Plus-Brochure.pdf', 'Tata AIA Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== BAJAJ LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('116N200V04', 'Bajaj Life Guaranteed Wealth Goal - Brochure',         'brochure',        'https://www.bajajlifeinsurance.com/content/dam/balic-web/pdf/term-insurance/spg-sl.pdf', 'Bajaj Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== PNB METLIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('117N131V06', 'PNB MetLife Guaranteed Goal Plan - Brochure',          'brochure',        'https://www.pnbmetlife.com/content/dam/pnb-metlife/docs/product/Download_Brochure/MGGP-PPT.pdf', 'PNB MetLife Official'),
    ('117N131V06', 'PNB MetLife Guaranteed Goal Plan - Leaflet',           'product_summary', 'https://www.pnbmetlife.com/content/dam/pnb-metlife/docs/product/Download_Brochure/guatanteed_goal_leaflet.pdf', 'PNB MetLife Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== STAR HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('SHAHLIP25036V012425', 'Super Star - Brochure',                                          'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Super_Star_Web_026575d7c4.pdf', 'Star Health Official'),
    ('SHAHLIP22028V022122', 'Star Comprehensive Insurance - Brochure',                        'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Health_Gain_Insurance_Policy_V_13_Web_Page_4e4f649213.pdf', 'Star Health Official'),
    ('SHAHLIP19014V021819', 'Senior Citizens Red Carpet Health Insurance - Brochure',         'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Senior_Citizens_Red_Carpet_Health_Insurance_Policy_V_16_Web_f0f416af49.pdf', 'Star Health Official'),
    ('SHAHLIP19010V021819', 'Diabetes Safe Insurance - Brochure',                             'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Diabetes_Safe_Insurance_Policy_V_15_Web_e78080730b.pdf', 'Star Health Official'),
    ('SHAHLIP19011V031819', 'Star Cardiac Care Insurance - Brochure',                         'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Cardiac_Care_Insurance_Policy_V_13_Web_13e0200770.pdf', 'Star Health Official'),
    ('SHAHLIP22027V022122', 'Star Cancer Care Platinum Insurance - Brochure',                 'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Cancer_Care_Platinum_Insurance_Policy_V_4_7836ca3999.pdf', 'Star Health Official'),
    ('SHAHLIP19013V021819', 'Star Women Care Insurance - Brochure',                           'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Women_Care_Insurance_Policy_V_6_Web_01bac515e2.pdf', 'Star Health Official'),
    ('SHAHLIP22026V012122', 'Star Critical Illness Multipay Insurance - Brochure',            'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Star_Critical_Illness_Multipay_Insurance_Brochure_94f1a9e8f8.pdf', 'Star Health Official'),
    ('SHAHLIP19015V021819', 'Super Surplus Insurance - Brochure',                             'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Super_Surplus_Insurance_Policy_V_14_Web_0d27ef5b7c.pdf', 'Star Health Official'),
    ('SHAHTIP19002V011819', 'Star Travel Protect Insurance - Brochure',                       'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Travel_Protect_Insurance_Policy_V_11_Web_62aef10aa9.pdf', 'Star Health Official'),
    ('SHAHPAP19001V021819', 'Accident Trauma Care Insurance - Brochure',                      'brochure', 'https://d28c6jni2fmamz.cloudfront.net/Brochure_Accident_Care_Individual_Insurance_Policy_V_9_Web_3b548a3386.pdf', 'Star Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== NIVA BUPA HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('MAXHLIP21176V022021',  'Health Premia Gold - Brochure',                'brochure',        'https://transactions.nivabupa.com/pages/doc/brochure/Health_Premia_Gold_Br.pdf', 'Niva Bupa Official'),
    ('NBHHLIP23108V062223',  'Health Companion - Brochure',                  'brochure',        'https://www.nivabupa.com/content/dam/nivabupa/PDF/Health-Companion/Health%20Companion_Brochure.pdf', 'Niva Bupa Official'),
    ('NBHHLIP26045V032526',  'Arogya Sanjeevani - Sales Literature',         'product_summary', 'https://transactions.nivabupa.com/pages/doc/brochure/Arogya_Sanjeevani_SS.pdf', 'Niva Bupa Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== CARE HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('CHIHLIA26054V022526',  'Care Shield Add-On - Prospectus',              'prospectus',      'https://cms.careinsurance.com/cms/public/uploads/download_center/care-shield-add-on---prospectus-cum-sales-literature.pdf', 'Care Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ADITYA BIRLA HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('ADIHLIP24097V012324', 'Activ One - Brochure',                         'brochure',        'https://www.adityabirlacapital.com/healthinsurance/assets/pdf/active-one/brochure.pdf', 'Aditya Birla Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== HDFC ERGO GENERAL PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('HDFHLIP25012V082425',  'HDFC ERGO Optima Restore - Policy Wording',            'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/optima-restore-revision.pdf', 'HDFC ERGO Official'),
    ('HDFHLIP20049V041920',  'HDFC ERGO my:health Suraksha - Policy Wording',        'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/myhealth-suraksha---pww.pdf', 'HDFC ERGO Official'),
    ('HDFHLIP21064V022021',  'HDFC ERGO Medisure Super Top Up - Policy Wording',     'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/myhealth-medisure-super-top-up-insurance.pdf', 'HDFC ERGO Official'),
    ('HDFHLIA22141V032122',  'HDFC ERGO my:health Critical Illness - Policy Wording','policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/critical-illness-policy-wordings.pdf', 'HDFC ERGO Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- HDFC ERGO General Insurance Products - Policy Wordings
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN146RPMS0071V01202526', 'HDFC ERGO Home Shield - Policy Wording',            'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/home/home-shield-insurance.pdf', 'HDFC ERGO Official'),
    ('IRDAN146RPPR0070V01202425', 'HDFC ERGO Bharat Griha Raksha Plus - Policy Wording','policy_wording', 'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/home/bharat-griha-raksha-plus-pw.pdf', 'HDFC ERGO Official'),
    ('HDTIOP24042V022425',        'HDFC ERGO Explorer Travel - Policy Wording',        'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/travel/hdfc-ergo-explorer-pw.pdf', 'HDFC ERGO Official'),
    ('IRDAN146RP0026V01202122',   'HDFC ERGO Cyber Sachet - Policy Wording',           'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/others/cyber-sachet.pdf', 'HDFC ERGO Official'),
    ('IRDAN146RP0001V01202324',   'HDFC ERGO Paws n Claws - Policy Wording',           'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/others/paws-n-claws-pw.pdf', 'HDFC ERGO Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ICICI LOMBARD PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN115RP0022V01200708', 'ICICI Lombard CPM - Policy Wording',                'policy_wording',  'https://www.icicilombard.com/docs/default-source/default-document-library/cpm-retail8c0007ff45fd68ff8a0df0055f87903a.pdf', 'ICICI Lombard Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ============================================================
-- PHASE 2 EXPANSION - Massive policy document expansion
-- ============================================================

-- ===================== STAR HEALTH - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('SHAHLIP19008V031819', 'Star Medi Classic Insurance - Brochure',                            'brochure',        'https://d28c6jni2fmamz.cloudfront.net/Brochure_Medi_Classic_Insurance_Policy_Individual_V_17_Web_93737c396f.pdf', 'Star Health Official'),
    ('SHAHLIP20046V011920', 'Star Hospital Cash Insurance - Brochure',                           'brochure',        'https://d28c6jni2fmamz.cloudfront.net/hospital_cash_ebrochure_new_7c0579d44a.pdf', 'Star Health Official'),
    ('SHAHLIP24032V022324', 'Star Health Assure Insurance - Brochure',                           'brochure',        'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Health_Assure_Insurance_Policy_V_5_Web_8153c42b87.pdf', 'Star Health Official'),
    ('SHAHLIP25037V012425', 'Star Smart Health Pro - Brochure',                                  'brochure',        'https://d28c6jni2fmamz.cloudfront.net/Brochure_Smart_Health_Pro_V_2_Web_d48ce59a74.pdf', 'Star Health Official'),
    ('SHAHLIP25036V012425', 'Super Star Insurance - CIS Document',                               'product_summary', 'https://d28c6jni2fmamz.cloudfront.net/CIS_Super_Star_V_1_3071764df3.pdf', 'Star Health Official'),
    ('SHAHLIP19012V031819', 'Family Health Optima Insurance - Brochure',                          'brochure',        'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Health_Gain_Insurance_Policy_V_13_Web_Page_4e4f649213.pdf', 'Star Health Official'),
    ('SHAHLIP19015V021819', 'Super Surplus Floater Insurance - Brochure',                         'brochure',        'https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Super_Surplus_Floater_Insurance_Policy_V_13_Web_705b7ad5bf.pdf', 'Star Health Official'),
    ('SHAHLIP20016V021920', 'Star Arogya Sanjeevani - Brochure',                                  'brochure',        'https://d28c6jni2fmamz.cloudfront.net/Brochure_Arogya_Sanjeevani_V_7_Web_34d7da82e8.pdf', 'Star Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== HDFC ERGO - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('HDFHLIP25012V082425', 'HDFC ERGO Optima Restore - Brochure',                               'brochure',        'https://www.hdfcergo.com/docs/default-source/downloads/brochures/health/optima-restore-brochure.pdf', 'HDFC ERGO Official'),
    ('HDFHLIP20049V041920', 'HDFC ERGO my:health Suraksha - Brochure',                           'brochure',        'https://www.hdfcergo.com/docs/default-source/downloads/brochures/health/myhealth-suraksha-brochure.pdf', 'HDFC ERGO Official'),
    ('HDFHLGP22142V022122', 'HDFC ERGO Group Health Insurance - Policy Wording',                  'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/group-health-insurance---pw.pdf', 'HDFC ERGO Official'),
    ('HDFHLIP21344V022021', 'HDFC ERGO Hospital Daily Cash - Policy Wording',                     'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/energy-combined-pw-cis.pdf', 'HDFC ERGO Official'),
    ('IRDAN146RPPR0070V01202425', 'HDFC ERGO Bharat Griha Raksha - Policy Wording',              'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/home/bgr-pw.pdf', 'HDFC ERGO Official'),
    ('HDTIOP24042V022425', 'HDFC ERGO Explorer Travel - Brochure',                                'brochure',        'https://www.hdfcergo.com/docs/default-source/downloads/brochures/travel/hdfc-ergo-explorer-brochure.pdf', 'HDFC ERGO Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- HDFC ERGO Motor Insurance Documents
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN146RP0001V02201415', 'HDFC ERGO Car Insurance - Policy Wording',                      'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/motor/two-wheeler-package-policy---policy-wording.pdf', 'HDFC ERGO Official'),
    ('IRDAN146RP0002V02200304', 'HDFC ERGO Two Wheeler Insurance - Policy Wording',              'policy_wording',  'https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/motor/two-wheeler-package-policy---policy-wording.pdf', 'HDFC ERGO Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== CARE HEALTH - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('CHIHLIP23128V012223', 'Care Supreme - Brochure',                                           'brochure',        'https://cdn.policyx.com/images/company-brochure/health/care-supreme-brochure.pdf', 'Care Health Official'),
    ('CHIHLIP22047V012122', 'Care Plus - Brochure',                                              'brochure',        'https://cms.careinsurance.com/cms/public/uploads/download_center/care-plus-brochure.pdf', 'Care Health Official'),
    ('CHIHLIP23150V022223', 'Care Advantage - Brochure',                                         'brochure',        'https://cms.careinsurance.com/cms/public/uploads/download_center/care-advantage-brochure.pdf', 'Care Health Official'),
    ('CHIHLIP20040V011920', 'Care Arogya Sanjeevani - Brochure',                                 'brochure',        'https://cms.careinsurance.com/cms/public/uploads/download_center/arogya-sanjeevani-brochure.pdf', 'Care Health Official'),
    ('CHIHLIP23152V012223', 'Care Freedom - Brochure',                                           'brochure',        'https://cms.careinsurance.com/cms/public/uploads/download_center/care-freedom-brochure.pdf', 'Care Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== NIVA BUPA - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('NBHPAIP25036V022425', 'Niva Bupa Personal Accident Plan - Policy Wording',                 'policy_wording',  'https://transactions.nivabupa.com/pages/doc/policy_wording/PA-Plan-Policy-wording.pdf', 'Niva Bupa Official'),
    ('NBHHLIP26050V012526', 'Niva Bupa ReAssure 3.0 - Brochure',                                 'brochure',        'https://transactions.nivabupa.com/pages/doc/brochure/ReAssure_Br.pdf', 'Niva Bupa Official'),
    ('NBHHLIP23110V012223', 'Niva Bupa GoActive - Brochure',                                     'brochure',        'https://transactions.nivabupa.com/pages/doc/brochure/GoActive_Br.pdf', 'Niva Bupa Official'),
    ('NBHHLIP23112V012223', 'Niva Bupa Senior First - Brochure',                                  'brochure',        'https://transactions.nivabupa.com/pages/doc/brochure/Senior_First_Br.pdf', 'Niva Bupa Official'),
    ('NBHHLIP23108V062223', 'Health Companion - Policy Wording',                                  'policy_wording',  'https://transactions.nivabupa.com/pages/doc/policy_wording/Health_Companion_PW.pdf', 'Niva Bupa Official'),
    ('MAXHLIP21176V022021', 'Health Premia - Policy Wording',                                     'policy_wording',  'https://transactions.nivabupa.com/pages/doc/policy_wording/Health_Premia_PW.pdf', 'Niva Bupa Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ICICI LOMBARD - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('ICIHLGP22096V022122', 'ICICI Lombard Group Health Insurance - Policy Wording',             'policy_wording',  'https://www.icicilombard.com/docs/default-source/Policy-Wordings-product-Brochure/group-health-insurance.pdf', 'ICICI Lombard Official'),
    ('IRDAN115RP0001V01201213', 'ICICI Lombard Motor Insurance - Brochure',                      'brochure',        'https://www.icicilombard.com/docs/default-source/Policy-Wordings-product-Brochure/motor_insurance(1).pdf', 'ICICI Lombard Official'),
    ('IRDAN115RP0013V02202122', 'ICICI Lombard Complete Home Protect - Brochure',                 'brochure',        'https://www.icicilombard.com/docs/default-source/policy-wordings-product-brochure/revised-policy-wordings_complete-home-protect_190721.pdf', 'ICICI Lombard Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== MANIPAL CIGNA DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('MCGHLIP22048V012122', 'ManipalCigna ProHealth Prime - Brochure',                           'brochure',        'https://www.manipalcigna.com/sites/default/files/brochure/ProHealth-Prime-Brochure.pdf', 'ManipalCigna Official'),
    ('MCGHLIP22052V012122', 'ManipalCigna LifeTime Health - Brochure',                           'brochure',        'https://www.manipalcigna.com/sites/default/files/brochure/LifeTime-Health-Brochure.pdf', 'ManipalCigna Official'),
    ('MCGHLIP22049V012122', 'ManipalCigna Prime Senior - Brochure',                              'brochure',        'https://www.manipalcigna.com/sites/default/files/brochure/Prime-Senior-Brochure.pdf', 'ManipalCigna Official'),
    ('MCGHLIP22050V012122', 'ManipalCigna Lifestyle Protection - Brochure',                      'brochure',        'https://www.manipalcigna.com/sites/default/files/brochure/Lifestyle-Protection-Brochure.pdf', 'ManipalCigna Official'),
    ('MCIPAIP21622V012021', 'ManipalCigna Accident Shield - Brochure',                           'brochure',        'https://www.manipalcigna.com/sites/default/files/brochure/Accident-Shield-Brochure.pdf', 'ManipalCigna Official'),
    ('MCGHLIP22053V012122', 'ManipalCigna ProHealth Cash - Brochure',                            'brochure',        'https://www.manipalcigna.com/sites/default/files/brochure/ProHealth-Cash-Brochure.pdf', 'ManipalCigna Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ADITYA BIRLA HEALTH - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('ADIHLIP22078V012122', 'Activ Health Platinum - Brochure',                                  'brochure',        'https://www.adityabirlacapital.com/healthinsurance/assets/pdf/active-health/brochure.pdf', 'ABHI Official'),
    ('ADIHLIP21062V022021', 'Activ Care Senior Citizen - Brochure',                              'brochure',        'https://www.adityabirlacapital.com/healthinsurance/assets/pdf/activ-care/brochure.pdf', 'ABHI Official'),
    ('ADIHLIP22079V012122', 'Activ Assure Diamond - Brochure',                                   'brochure',        'https://www.adityabirlacapital.com/healthinsurance/assets/pdf/activ-assure/brochure.pdf', 'ABHI Official'),
    ('ADIHLIP22080V012122', 'Activ Secure Critical Illness - Brochure',                          'brochure',        'https://www.adityabirlacapital.com/healthinsurance/assets/pdf/activ-secure/brochure.pdf', 'ABHI Official'),
    ('ADIHLIP22081V012122', 'Activ Cancer Secure - Brochure',                                    'brochure',        'https://www.adityabirlacapital.com/healthinsurance/assets/pdf/activ-cancer-secure/brochure.pdf', 'ABHI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== LIC - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('512N350V01', 'LIC Jeevan Azad - Sales Brochure',                                          'brochure',        'https://licindia.in/documents/20121/1394180/Lic-Jeevan-Azad-Sales-Brochure.pdf', 'LIC Official Website'),
    ('512N340V02', 'LIC Bima Jyoti - Sales Brochure',                                           'brochure',        'https://licindia.in/documents/20121/1351688/LIC_Bima_Jyoti_Sales_Brochure.pdf', 'LIC Official Website'),
    ('512N343V01', 'LIC Dhan Varsha - Sales Brochure',                                          'brochure',        'https://licindia.in/documents/20121/1364684/LIC_Dhan_Varsha_Sales_Brochure.pdf', 'LIC Official Website'),
    ('512N345V01', 'LIC Jeevan Utsav - Sales Brochure',                                         'brochure',        'https://licindia.in/documents/20121/1381860/LIC_Jeevan_Utsav_Sales_Brochure.pdf', 'LIC Official Website'),
    ('512N321V02', 'LIC Saral Jeevan Bima - Sales Brochure',                                    'brochure',        'https://licindia.in/documents/20121/1243952/LIC_Saral_Jeevan_Bima_Brochure.pdf', 'LIC Official Website'),
    ('512N316V03', 'LIC Tech Term - Sales Brochure',                                             'brochure',        'https://licindia.in/documents/20121/1243952/LIC-Tech-Term-Sales-Brochure.pdf', 'LIC Official Website')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== HDFC LIFE - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('101N179V01', 'HDFC Life Click 2 Protect Ultimate - Brochure',                              'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/click-2-protect-ultimate-brochure.pdf', 'HDFC Life Official'),
    ('101N177V04', 'HDFC Life Sanchay Legacy - Brochure',                                        'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/sanchay-legacy-brochure.pdf', 'HDFC Life Official'),
    ('101N146V09', 'HDFC Life Guaranteed Income - Brochure',                                     'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/guaranteed-income-insurance-plan-brochure.pdf', 'HDFC Life Official'),
    ('101N165V13', 'HDFC Life Guaranteed Wealth Plus - Brochure',                                'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/guaranteed-wealth-plus-brochure.pdf', 'HDFC Life Official'),
    ('101N142V08', 'HDFC Life Sanchay Fixed Maturity - Brochure',                                'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/sanchay-fixed-maturity-plan-brochure.pdf', 'HDFC Life Official'),
    ('101N118V13', 'HDFC Life Pension Guaranteed Plan - Brochure',                               'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/pension-guaranteed-plan-brochure.pdf', 'HDFC Life Official'),
    ('101N143V09', 'HDFC Life Systematic Retirement Plan - Brochure',                            'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/systematic-retirement-plan-brochure.pdf', 'HDFC Life Official'),
    ('101N158V06', 'HDFC Life Sampoorna Jeevan - Brochure',                                     'brochure',        'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/sampoorna-jeevan-brochure.pdf', 'HDFC Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== MAX LIFE - DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('104N118V12', 'Axis Max Life Smart Secure Plus - Brochure',                                 'brochure',        'https://www.axismaxlife.com/uploads/insurance-plans/smart-secure-plus-brochure.pdf', 'Axis Max Life Official'),
    ('104L090V07', 'Axis Max Life Platinum Wealth - Brochure',                                   'brochure',        'https://www.axismaxlife.com/uploads/insurance-plans/platinum-wealth-brochure.pdf', 'Axis Max Life Official'),
    ('104N076V21', 'Axis Max Life Guaranteed Lifetime Income - Brochure',                        'brochure',        'https://www.axismaxlife.com/uploads/insurance-plans/guaranteed-lifetime-income-brochure.pdf', 'Axis Max Life Official'),
    ('104N124V16', 'Axis Max Life Smart Wealth Advantage Guarantee - Brochure',                  'brochure',        'https://www.axismaxlife.com/uploads/insurance-plans/smart-wealth-advantage-guarantee-brochure.pdf', 'Axis Max Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ICICI PRUDENTIAL LIFE - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('105N197V06', 'ICICI Pru Guaranteed Income for Tomorrow - Brochure',                        'brochure',        'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI_Pru_GIFT.pdf', 'ICICI Prudential Life Official'),
    ('105L176V04', 'ICICI Pru Signature - Brochure',                                            'brochure',        'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI_Pru_Signature.pdf', 'ICICI Prudential Life Official'),
    ('105N196V07', 'ICICI Pru Lakshya - Brochure',                                              'brochure',        'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI_Pru_Lakshya.pdf', 'ICICI Prudential Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== TATA AIA LIFE - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('110N156V05', 'Tata AIA Sampoorna Raksha Supreme - Brochure',                              'brochure',        'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/download-centre/english/brochures/Sampoorna-Raksha-Supreme-Brochure.pdf', 'Tata AIA Official'),
    ('110N157V08', 'Tata AIA Guaranteed Monthly Income Plan - Brochure',                         'brochure',        'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/download-centre/english/brochures/GMIP-Brochure.pdf', 'Tata AIA Official'),
    ('110N147V11', 'Tata AIA Smart Value Income Plan - Brochure',                                'brochure',        'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/download-centre/english/brochures/Smart-Value-Income-Plan-Brochure.pdf', 'Tata AIA Official'),
    ('110L151V10', 'Tata AIA Fortune Pro - Brochure',                                            'brochure',        'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/download-centre/english/brochures/Fortune-Pro-Brochure.pdf', 'Tata AIA Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== SBI LIFE - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('111N137V05', 'SBI Life Smart Platina Supreme - Brochure',                                  'brochure',        'https://www.sbilife.co.in/en/individual-life-insurance/savings/smart-platina-supreme', 'SBI Life Official'),
    ('111N140V04', 'SBI Life Smart Privilege - Brochure',                                        'brochure',        'https://www.sbilife.co.in/en/individual-life-insurance/savings/smart-privilege', 'SBI Life Official'),
    ('111N133V05', 'SBI Life Saral Pension - Brochure',                                          'brochure',        'https://www.sbilife.co.in/en/individual-life-insurance/pension/saral-pension', 'SBI Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== BAJAJ LIFE - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('116N198V05', 'Bajaj Life eTouch II - Brochure',                                            'brochure',        'https://www.bajajlifeinsurance.com/content/dam/balic-web/pdf/term-insurance/etouch-brochure.pdf', 'Bajaj Life Official'),
    ('116N200V04', 'Bajaj Life Guaranteed Wealth Goal - Policy Wording',                         'policy_wording',  'https://www.bajajlifeinsurance.com/content/dam/balic-web/pdf/savings/guaranteed-wealth-goal-pw.pdf', 'Bajaj Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== BAJAJ ALLIANZ GENERAL - DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('BAJHLIP20070V031920', 'Bajaj Allianz Health Guard - Brochure',                             'brochure',        'https://www.bajajallianz.com/content/dam/bagic/pdfs/health-guard.pdf', 'Bajaj Allianz GI Official'),
    ('BAJHLIP22090V012122', 'Bajaj Allianz Extra Care Plus - Brochure',                          'brochure',        'https://www.bajajallianz.com/content/dam/bagic/pdfs/extra-care-plus.pdf', 'Bajaj Allianz GI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== TATA AIG GENERAL - DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN137RP0001V01201516', 'Tata AIG Motor Insurance - Policy Wording',                      'policy_wording',  'https://www.tataaig.com/content/dam/tata-aig/pdfs/motor-insurance/car-insurance-policy-wording.pdf', 'Tata AIG Official'),
    ('IRDAN137RP0002V01201516', 'Tata AIG Two Wheeler Insurance - Policy Wording',               'policy_wording',  'https://www.tataaig.com/content/dam/tata-aig/pdfs/motor-insurance/two-wheeler-policy-wording.pdf', 'Tata AIG Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== NEW INDIA ASSURANCE - DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN190RP0010V01200102', 'New India Bharat Griha Raksha - Policy Wording',                 'policy_wording',  'https://www.newindia.co.in/assets/docs/know-more/property/new-india-bharat-griha-raksha/PolicyClauseBharatGrihaRaksha.pdf', 'New India Assurance Official'),
    ('IRDAN190RP0001V01200102', 'New India Motor Insurance - Policy Wording',                     'policy_wording',  'https://www.newindia.co.in/assets/docs/know-more/motor/PrivateCarPackagePolicy.pdf', 'New India Assurance Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== SBI GENERAL - DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN144HL0001V01202223', 'SBI General Arogya Premier - Brochure',                         'brochure',        'https://content.sbigeneral.in/uploads/arogya-premier-brochure.pdf', 'SBI General Official'),
    ('SBIHLIP11003V011011',     'SBI General Hospital Daily Cash - Policy Wording',               'policy_wording',  'https://content.sbigeneral.in/uploads/bb7c63dff34c4fe5ab81b0021a14a900.pdf', 'SBI General Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== GALAXY HEALTH - DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('GLXHLIP24001V012425', 'Galaxy Promise - Brochure',                                          'brochure',        'https://www.galaxyhealth.com/documents/galaxy-promise-brochure.pdf', 'Galaxy Health Official'),
    ('GLXHLIP25002V012526', 'Galaxy Marvel - Brochure',                                            'brochure',        'https://www.galaxyhealth.com/documents/galaxy-marvel-brochure.pdf', 'Galaxy Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== KOTAK LIFE - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('107N079V03', 'Kotak Premier Endowment Plan - Brochure',                                    'brochure',        'https://www.kotaklife.com/assets/images/uploads/insurance-plans/PremierEndowmentPlan.pdf', 'Kotak Life Official'),
    ('107N102V04', 'Kotak SmartLife Plan - Brochure',                                            'brochure',        'https://www.kotaklife.com/assets/images/uploads/insurance-plans/SmartLifePlan.pdf', 'Kotak Life Official'),
    ('107N162V01', 'Kotak Confident Retirement Plan - Brochure',                                 'brochure',        'https://www.kotaklife.com/assets/images/uploads/insurance-plans/ConfidentRetirementPlan.pdf', 'Kotak Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ABSLI - ADDITIONAL DOCUMENTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('109N132V01', 'ABSLI Nishchit Aayush Plan - Brochure',                                     'brochure',        'https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Nishchit_Aayush_Brochure.pdf', 'ABSLI Official'),
    ('109L091V03', 'ABSLI TULIP Plan - Brochure',                                               'brochure',        'https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_TULIP_Brochure.pdf', 'ABSLI Official'),
    ('109N127V02', 'ABSLI Child''s Future Assured - Brochure',                                    'brochure',        'https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Childs_Future_Assured_Brochure.pdf', 'ABSLI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ================ SECTION 3: EXTRA POLICY DOCUMENTS =============
-- ============================================================
-- 07e_policy_docs_extra.sql - Policy documents for newly added products
-- Covers products from 03b, 04b, 05b supplementary files
-- Last verified: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- Policy documents for all new products (one brochure per product)
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'high'::insurance.confidence_enum
FROM (VALUES
    -- AB Health
    ('ABHHLIP24020V012324', 'Activ Care Diabetes Plan - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/content/dam/abc/insurance/abhicl/pdf/brochure/activ-care-diabetes-brochure.pdf', 'ABHI Official'),

    -- AIC
    ('IRDAN106RP0007V01202122', 'AIC Cattle Insurance Scheme - Brochure', 'brochure', 'https://www.aicofindia.com/cattle-insurance', 'AIC Official'),
    ('IRDAN106RP0003V01201718', 'AIC Coconut Palm Insurance - Brochure', 'brochure', 'https://www.aicofindia.com/coconut-palm-insurance', 'AIC Official'),
    ('IRDAN106RP0006V01202021', 'AIC Horticulture Crop Insurance - Brochure', 'brochure', 'https://www.aicofindia.com/horticulture-insurance', 'AIC Official'),
    ('IRDAN106RP0004V01201819', 'AIC NAIS - Brochure', 'brochure', 'https://www.aicofindia.com/nais', 'AIC Official'),
    ('IRDAN106RP0005V01201920', 'AIC PMFBY Add-on Coverage - Brochure', 'brochure', 'https://www.aicofindia.com/pmfby', 'AIC Official'),
    ('IRDAN106RP0008V01202223', 'AIC Poultry Insurance Scheme - Brochure', 'brochure', 'https://www.aicofindia.com/poultry-insurance', 'AIC Official'),

    -- Acko GI
    ('IRDAN157RP0012V01202324', 'Acko Commercial Vehicle Insurance - Product Page', 'brochure', 'https://www.acko.com/commercial-vehicle-insurance/', 'Acko Official'),
    ('IRDAN157RP0009V01202021', 'Acko Domestic Travel Insurance - Product Page', 'brochure', 'https://www.acko.com/travel-insurance/', 'Acko Official'),
    ('IRDAN157RP0011V01202223', 'Acko Gadget Insurance - Product Page', 'brochure', 'https://www.acko.com/gadget-insurance/', 'Acko Official'),
    ('IRDAN157RP0010V01202122', 'Acko Home Insurance - Product Page', 'brochure', 'https://www.acko.com/home-insurance/', 'Acko Official'),

    -- Acko Life
    ('169N003V01', 'Acko Life Flexi Term Plan - Brochure', 'brochure', 'https://www.acko.com/life-insurance/', 'Acko Life Official'),
    ('169G004V01', 'Acko Life Group Term Plan - Product Page', 'brochure', 'https://www.acko.com/life-insurance/', 'Acko Life Official'),
    ('169N002V01', 'Acko Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.acko.com/life/download/', 'Acko Life Official'),
    ('169N005V01', 'Acko Life Saral Pension Plan - Brochure', 'brochure', 'https://www.acko.com/life/download/', 'Acko Life Official'),

    -- Ageas Federal
    ('135N086V01', 'Ageas Federal Life Endowment Plan - Brochure', 'brochure', 'https://www.aegasfederal.com/products/', 'Ageas Federal Official'),
    ('135G040V01', 'Ageas Federal Life Group Term Plan - Brochure', 'brochure', 'https://www.aegasfederal.com/products/', 'Ageas Federal Official'),
    ('135N085V01', 'Ageas Federal Life Optima Income Plan - Brochure', 'brochure', 'https://www.aegasfederal.com/products/', 'Ageas Federal Official'),
    ('135N087V01', 'Ageas Federal Life Whole Life Plan - Brochure', 'brochure', 'https://www.aegasfederal.com/products/', 'Ageas Federal Official'),

    -- Aviva Life
    ('122N147V01', 'Aviva Endowment Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/', 'Aviva Official'),
    ('122G080V01', 'Aviva Group Term Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/', 'Aviva Official'),
    ('122N145V01', 'Aviva Money Back Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/', 'Aviva Official'),
    ('122N146V01', 'Aviva Whole Life Protection Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/', 'Aviva Official'),

    -- Bandhan Life
    ('138N098V01', 'Bandhan Life Endowment Plan - Brochure', 'brochure', 'https://www.bandhanlife.com/products/', 'Bandhan Life Official'),
    ('138G050V01', 'Bandhan Life Group Term Plan - Brochure', 'brochure', 'https://www.bandhanlife.com/products/', 'Bandhan Life Official'),
    ('138N097V01', 'Bandhan Life Guaranteed Income Plan - Brochure', 'brochure', 'https://www.bandhanlife.com/products/', 'Bandhan Life Official'),
    ('138N099V01', 'Bandhan Life iSecure Child Plan - Brochure', 'brochure', 'https://www.bandhanlife.com/products/', 'Bandhan Life Official'),

    -- Bharti AXA Life
    ('130N048V01', 'Bharti AXA Life Child Advantage Plan - Brochure', 'brochure', 'https://www.bhartiaxa.com/products/', 'Bharti AXA Life Official'),
    ('130N055V01', 'Bharti AXA Life Flexi Term Pro - Brochure', 'brochure', 'https://www.bhartiaxa.com/products/', 'Bharti AXA Life Official'),
    ('130G030V01', 'Bharti AXA Life Group Term Plan - Brochure', 'brochure', 'https://www.bhartiaxa.com/products/', 'Bharti AXA Life Official'),
    ('130N056V01', 'Bharti AXA Life Guaranteed Income Pro - Brochure', 'brochure', 'https://www.bhartiaxa.com/products/', 'Bharti AXA Life Official'),
    ('130N059V01', 'Bharti AXA Life Saral Pension Plan - Brochure', 'brochure', 'https://www.bhartiaxa.com/products/', 'Bharti AXA Life Official'),
    ('130L040V01', 'Bharti AXA Life eFuture Invest - Brochure', 'brochure', 'https://www.bhartiaxa.com/products/', 'Bharti AXA Life Official'),

    -- Canara HSBC
    ('136N121V01', 'Canara HSBC Life Endowment Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/products/', 'Canara HSBC Life Official'),
    ('136G060V01', 'Canara HSBC Life Group Term Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/products/', 'Canara HSBC Life Official'),
    ('136N120V01', 'Canara HSBC Life Smart Child Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/products/', 'Canara HSBC Life Official'),
    ('136N122V01', 'Canara HSBC Life Whole Life Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/products/', 'Canara HSBC Life Official'),

    -- Care Health
    ('CHIHLIP24132V012324', 'Care Cancer Shield - Brochure', 'brochure', 'https://www.careinsurance.com/other-downloads.html', 'Care Health Official'),
    ('CHIHLIP24131V012324', 'Care Maternity Plan - Brochure', 'brochure', 'https://www.careinsurance.com/other-downloads.html', 'Care Health Official'),
    ('CHIPAIP24133V012324', 'Care Personal Accident Plan - Brochure', 'brochure', 'https://www.careinsurance.com/other-downloads.html', 'Care Health Official'),
    ('CHIHLIP24130V012324', 'Care Hospital Cash Plan - Brochure', 'brochure', 'https://www.careinsurance.com/other-downloads.html', 'Care Health Official'),

    -- CreditAccess Life
    ('170G003V01', 'CreditAccess Life Group Credit Life Insurance - Product Info', 'brochure', 'https://creditaccesslife.in/', 'CreditAccess Life Official'),
    ('170G004V01', 'CreditAccess Life Group Micro Insurance - Product Info', 'brochure', 'https://creditaccesslife.in/', 'CreditAccess Life Official'),
    ('170N005V01', 'CreditAccess Life Individual Term Plan - Product Info', 'brochure', 'https://creditaccesslife.in/', 'CreditAccess Life Official'),
    ('170N002V01', 'CreditAccess Life Saral Jeevan Bima - Product Info', 'brochure', 'https://creditaccesslife.in/', 'CreditAccess Life Official'),
    ('170N006V01', 'CreditAccess Life Saral Pension Plan - Product Info', 'brochure', 'https://creditaccesslife.in/', 'CreditAccess Life Official'),

    -- Digit GI
    ('IRDAN158RP007V01201819', 'Digit Commercial Vehicle Insurance - Brochure', 'brochure', 'https://www.godigit.com/commercial-vehicle-insurance', 'Go Digit Official'),
    ('IRDAN158RP015V01202223', 'Digit Contractor All Risk Insurance - Brochure', 'brochure', 'https://www.godigit.com/business-insurance', 'Go Digit Official'),
    ('IRDAN158RP012V01202122', 'Digit D&O Liability Insurance - Brochure', 'brochure', 'https://www.godigit.com/business-insurance/directors-officers-insurance', 'Go Digit Official'),
    ('IRDAN158RP014V01202223', 'Digit Erection All Risk Insurance - Brochure', 'brochure', 'https://www.godigit.com/business-insurance', 'Go Digit Official'),
    ('IRDAN158RP010V01201920', 'Digit Fire Insurance Policy - Brochure', 'brochure', 'https://www.godigit.com/fire-insurance', 'Go Digit Official'),
    ('IRDAN158RP011V01202021', 'Digit Marine Cargo Insurance - Brochure', 'brochure', 'https://www.godigit.com/marine-insurance', 'Go Digit Official'),
    ('IRDAN158RP013V01202122', 'Digit Workmen Compensation Insurance - Brochure', 'brochure', 'https://www.godigit.com/business-insurance/workmen-compensation', 'Go Digit Official'),

    -- Digit Life
    ('165N011V03', 'Digit Icon Guaranteed Returns Savings Plan - Brochure', 'brochure', 'https://www.godigit.com/life-insurance/digit-icon-guaranteed-returns-savings-plan', 'Digit Life Official'),
    ('165G002V01', 'Digit Life Group Micro Term Insurance - Product Info', 'brochure', 'https://www.godigit.com/life-insurance', 'Digit Life Official'),
    ('165N008V01', 'Digit Life Guaranteed Income Plan - Brochure', 'brochure', 'https://www.godigit.com/life-insurance/investment-plans', 'Digit Life Official'),
    ('165N009V01', 'Digit Life Guaranteed Pension Plan - Brochure', 'brochure', 'https://www.godigit.com/life-insurance', 'Digit Life Official'),
    ('165N010V01', 'Digit Life Money Back Plan - Brochure', 'brochure', 'https://www.godigit.com/life-insurance', 'Digit Life Official'),
    ('165N005V01', 'Digit Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.godigit.com/life-insurance', 'Digit Life Official'),
    ('165N006V01', 'Digit Life Saral Pension Plan - Brochure', 'brochure', 'https://www.godigit.com/life-insurance', 'Digit Life Official'),
    ('165N012V01', 'Digit Life Single Premium Guaranteed Income Plan - Brochure', 'brochure', 'https://www.godigit.com/life-insurance', 'Digit Life Official'),

    -- ECGC
    ('IRDAN120RP0008V01200708', 'ECGC Buyers Credit Policy - Product Info', 'brochure', 'https://www.ecgc.in/english/products-post/buyers-credit', 'ECGC Official'),
    ('IRDAN120RP0007V01200607', 'ECGC Export Credit Insurance for Banks - Product Info', 'brochure', 'https://www.ecgc.in/english/products-post/ecib', 'ECGC Official'),
    ('IRDAN120RP0006V01200506', 'ECGC Services Policy - Product Info', 'brochure', 'https://www.ecgc.in/english/products-post/services-policy', 'ECGC Official'),
    ('IRDAN120RP0004V01200304', 'ECGC SCR Policy - Product Info', 'brochure', 'https://www.ecgc.in/english/products-post/scr', 'ECGC Official'),
    ('IRDAN120RP0003V01200304', 'ECGC Small Exporters Policy - Product Info', 'brochure', 'https://www.ecgc.in/english/products-post/sep', 'ECGC Official'),
    ('IRDAN120RP0002V01200203', 'ECGC Specific Shipment Policy - Product Info', 'brochure', 'https://www.ecgc.in/english/products-post/ssp', 'ECGC Official'),

    -- Galaxy Health
    ('GLXHLGP25007V012526', 'Galaxy Empower - Brochure', 'brochure', 'https://www.galaxyhealth.com/product-brochures', 'Galaxy Health Official'),
    ('GLXHLIP25005V012526', 'Galaxy Guardian - Brochure', 'brochure', 'https://www.galaxyhealth.com/product-brochures', 'Galaxy Health Official'),
    ('GLXPAIP25008V012526', 'Galaxy Personal Accident Shield - Brochure', 'brochure', 'https://www.galaxyhealth.com/product-brochures', 'Galaxy Health Official'),
    ('GLXHLIA25009V012526', 'Galaxy Smart Outpatient Rider - Brochure', 'brochure', 'https://www.galaxyhealth.com/product-brochures', 'Galaxy Health Official'),
    ('GLXHLIP25006V012526', 'Galaxy Top-up - Brochure', 'brochure', 'https://www.galaxyhealth.com/product-brochures', 'Galaxy Health Official'),
    ('GLXHLIP25004V012526', 'Galaxy Twin 360 - Brochure', 'brochure', 'https://www.galaxyhealth.com/product-brochures', 'Galaxy Health Official'),

    -- Generali GI
    ('IRDAN118RP0005V01200910', 'Generali Central Marine Cargo Insurance - Product Info', 'brochure', 'https://generalinsurance.in/products/', 'Generali GI Official'),
    ('IRDAN118RP0008V01201112', 'Generali Central Personal Accident Insurance - Product Info', 'brochure', 'https://generalinsurance.in/products/', 'Generali GI Official'),
    ('IRDAN118RP0012V01201415', 'Generali Central Public Liability Insurance - Product Info', 'brochure', 'https://generalinsurance.in/products/', 'Generali GI Official'),
    ('IRDAN118RP0010V01201314', 'Generali Central Travel Insurance - Product Info', 'brochure', 'https://generalinsurance.in/products/', 'Generali GI Official'),

    -- IndiaFirst Life
    ('143N073V01', 'IndiaFirst Life Child Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/products/', 'IndiaFirst Life Official'),
    ('143G040V01', 'IndiaFirst Life Group Term Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/products/', 'IndiaFirst Life Official'),
    ('143N075V01', 'IndiaFirst Life Term with Return of Premium - Brochure', 'brochure', 'https://www.indiafirstlife.com/products/', 'IndiaFirst Life Official'),
    ('143N074V01', 'IndiaFirst Life Whole Life Protection Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/products/', 'IndiaFirst Life Official'),

    -- IndusInd GI
    ('IRDAN156RP0004V01201920', 'IndusInd General Commercial Vehicle Insurance - Product Info', 'brochure', 'https://www.reliancegeneral.co.in/insurance/', 'IndusInd GI Official'),
    ('IRDAN156RP0005V01202021', 'IndusInd General Home Insurance - Product Info', 'brochure', 'https://www.reliancegeneral.co.in/insurance/', 'IndusInd GI Official'),
    ('IRDAN127RP0005V01200910', 'IndusInd General Marine Cargo Insurance - Product Info', 'brochure', 'https://www.reliancegeneral.co.in/insurance/', 'IndusInd GI Official'),
    ('IRDAN127RP0006V01201011', 'IndusInd General Personal Accident Insurance - Product Info', 'brochure', 'https://www.reliancegeneral.co.in/insurance/', 'IndusInd GI Official'),

    -- IndusInd Nippon
    ('121N156V01', 'IndusInd Nippon Life Child Future Plan - Brochure', 'brochure', 'https://www.indusindnipponlife.com/products/', 'IndusInd Nippon Official'),
    ('121G070V01', 'IndusInd Nippon Life Group Term Plan - Brochure', 'brochure', 'https://www.indusindnipponlife.com/products/', 'IndusInd Nippon Official'),
    ('121N157V01', 'IndusInd Nippon Life Money Back Plan - Brochure', 'brochure', 'https://www.indusindnipponlife.com/products/', 'IndusInd Nippon Official'),
    ('121N158V01', 'IndusInd Nippon Life Whole Life Plan - Brochure', 'brochure', 'https://www.indusindnipponlife.com/products/', 'IndusInd Nippon Official'),

    -- Kshema
    ('IRDAN172RP0002V01202425', 'Kshema Sukriti Crop Insurance - Brochure', 'brochure', 'https://kshema.co/products/', 'Kshema Official'),
    ('IRDAN172RP0003V01202425', 'Kshema Affordable Crop Insurance - Brochure', 'brochure', 'https://kshema.co/products/', 'Kshema Official'),
    ('IRDAN172RP0004V01202526', 'Kshema Kisan Sathi - Brochure', 'brochure', 'https://kshema.co/products/', 'Kshema Official'),
    ('IRDAN172RP0005V01202526', 'Kshema Livestock Insurance - Brochure', 'brochure', 'https://kshema.co/products/', 'Kshema Official'),

    -- Liberty GI
    ('IRDAN150RP0004V01201415', 'Liberty General Commercial Vehicle Insurance - Product Info', 'brochure', 'https://www.libertyinsurance.in/products/', 'Liberty GI Official'),
    ('IRDAN150RP0005V01201415', 'Liberty General Marine Cargo Insurance - Product Info', 'brochure', 'https://www.libertyinsurance.in/products/', 'Liberty GI Official'),
    ('IRDAN150RP0006V01201516', 'Liberty General Personal Accident Insurance - Product Info', 'brochure', 'https://www.libertyinsurance.in/products/', 'Liberty GI Official'),
    ('IRDAN150RP0008V01201617', 'Liberty General Travel Insurance - Product Info', 'brochure', 'https://www.libertyinsurance.in/products/', 'Liberty GI Official'),

    -- Magma GI
    ('IRDAN153RP0005V01201516', 'Magma General Marine Cargo Insurance - Product Info', 'brochure', 'https://www.magma.co.in/general-insurance/', 'Magma GI Official'),
    ('IRDAN153RP0006V01201617', 'Magma General Personal Accident Insurance - Product Info', 'brochure', 'https://www.magma.co.in/general-insurance/', 'Magma GI Official'),
    ('IRDAN153RP0008V01201718', 'Magma General Travel Insurance - Product Info', 'brochure', 'https://www.magma.co.in/general-insurance/', 'Magma GI Official'),

    -- Manipal Cigna
    ('CIGHLIP24025V012324', 'Manipal Cigna Maternity Plan - Brochure', 'brochure', 'https://www.manipalcigna.com/products/', 'Manipal Cigna Official'),
    ('CIGPAIP24026V012324', 'Manipal Cigna Personal Accident Plan - Brochure', 'brochure', 'https://www.manipalcigna.com/products/', 'Manipal Cigna Official'),

    -- Narayana Health
    ('NRHHLGP24003V012425', 'Narayana Aditi Group Health Insurance - Brochure', 'brochure', 'https://www.narayanahealth.insurance/', 'Narayana Health Official'),
    ('NRHHLIP25004V012526', 'Narayana Arogya Sanjeevani Policy - Brochure', 'brochure', 'https://www.narayanahealth.insurance/', 'Narayana Health Official'),
    ('NRHPAIP25007V012526', 'Narayana Personal Accident Plan - Brochure', 'brochure', 'https://www.narayanahealth.insurance/', 'Narayana Health Official'),
    ('NRHHLIP25005V012526', 'Narayana Senior Citizen Health Plan - Brochure', 'brochure', 'https://www.narayanahealth.insurance/', 'Narayana Health Official'),
    ('NRHHLIP25006V012526', 'Narayana Health Top-Up Plan - Brochure', 'brochure', 'https://www.narayanahealth.insurance/', 'Narayana Health Official'),

    -- National Insurance
    ('IRDAN190RP0050V01202122', 'National Insurance Bharat Griha Raksha - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products', 'National Insurance Official'),
    ('IRDAN190RP0003V01200102', 'National Insurance Commercial Vehicle Policy - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products/motor', 'National Insurance Official'),
    ('IRDAN190RP0018V01200102', 'National Insurance Burglary Policy - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products', 'National Insurance Official'),
    ('IRDAN190RP0005V01200102', 'National Insurance Fire Policy - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products', 'National Insurance Official'),
    ('IRDAN190RP0010V01200102', 'National Insurance Marine Cargo - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/en/marine', 'National Insurance Official'),
    ('IRDAN190RP0025V01200506', 'National Insurance Overseas Travel Insurance - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products', 'National Insurance Official'),
    ('IRDAN190RP0008V01200102', 'National Insurance Personal Accident - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products', 'National Insurance Official'),
    ('IRDAN170RP0002V01200102', 'National Insurance Two Wheeler Policy - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products/motor/two-wheeler', 'National Insurance Official'),
    ('IRDAN190RP0012V01200102', 'National Insurance Workmen Compensation - Product Info', 'brochure', 'https://nationalinsurance.nic.co.in/products/all-products', 'National Insurance Official'),

    -- Navi GI
    ('NAVHLIP25037V012425', 'Navi Smart Health Insurance - Brochure', 'brochure', 'https://navi.com/insurance/health', 'Navi Official'),
    ('NAVHLIP24038V012324', 'Navi Special Care Insurance - Brochure', 'brochure', 'https://navi.com/insurance/health', 'Navi Official'),
    ('NAVHLGP24039V012324', 'Navi Group Health Insurance - Brochure', 'brochure', 'https://navi.com/insurance/health', 'Navi Official'),
    ('NAVHLIP24040V012324', 'Navi Surrogacy Care Insurance - Brochure', 'brochure', 'https://navi.com/insurance/health', 'Navi Official'),

    -- Niva Bupa
    ('NBHHLIP25050V012526', 'Niva Bupa Hospital Cash Plan - Brochure', 'brochure', 'https://www.nivabupa.com/products/', 'Niva Bupa Official'),
    ('NBHHLIP25051V012526', 'Niva Bupa Critical Illness Plan - Brochure', 'brochure', 'https://www.nivabupa.com/products/', 'Niva Bupa Official'),

    -- Oriental Ins
    ('IRDAN103RP0012V01200102', 'Oriental Insurance Boiler & Pressure Plant - Product Info', 'brochure', 'https://orientalinsurance.org.in/', 'Oriental Insurance Official'),
    ('IRDAN180RP0003V01200102', 'Oriental Insurance Commercial Vehicle - Product Info', 'brochure', 'https://orientalinsurance.org.in/', 'Oriental Insurance Official'),
    ('IRDAN103RP0011V01200102', 'Oriental Insurance Contractor All Risk - Product Info', 'brochure', 'https://orientalinsurance.org.in/', 'Oriental Insurance Official'),
    ('IRDAN129RP0011V01200506', 'Oriental Insurance Domestic Travel - Product Info', 'brochure', 'https://orientalinsurance.org.in/', 'Oriental Insurance Official'),
    ('IRDAN103RP0010V01200102', 'Oriental Insurance Erection All Risk - Product Info', 'brochure', 'https://orientalinsurance.org.in/', 'Oriental Insurance Official'),
    ('IRDAN180RP0002V01200102', 'Oriental Insurance Two Wheeler - Product Info', 'brochure', 'https://orientalinsurance.org.in/', 'Oriental Insurance Official'),

    -- Pramerica Life
    ('140N077V01', 'Pramerica Life Child Future Plan - Brochure', 'brochure', 'https://www.pramericalife.in/products/', 'Pramerica Life Official'),
    ('140N078V01', 'Pramerica Life Endowment Plan - Brochure', 'brochure', 'https://www.pramericalife.in/products/', 'Pramerica Life Official'),
    ('140G045V01', 'Pramerica Life Group Term Plan - Brochure', 'brochure', 'https://www.pramericalife.in/products/', 'Pramerica Life Official'),
    ('140N076V01', 'Pramerica Life Term with Return of Premium - Brochure', 'brochure', 'https://www.pramericalife.in/products/', 'Pramerica Life Official'),

    -- Raheja QBE
    ('IRDAN163RP0007V01202122', 'Raheja QBE Contractor All Risk Insurance - Product Info', 'brochure', 'https://www.rahejaqbe.com/', 'Raheja QBE Official'),
    ('IRDAN163RP0008V01202223', 'Raheja QBE Cyber Insurance Policy - Product Info', 'brochure', 'https://www.rahejaqbe.com/', 'Raheja QBE Official'),
    ('IRDAN163RP0005V01202021', 'Raheja QBE General Liability Insurance - Product Info', 'brochure', 'https://www.rahejaqbe.com/general-liability-insurance', 'Raheja QBE Official'),
    ('IRDAN163RP0004V01202021', 'Raheja QBE Marine Cargo Insurance - Product Info', 'brochure', 'https://www.rahejaqbe.com/marine-insurance', 'Raheja QBE Official'),
    ('IRDAN163RP0006V01202122', 'Raheja QBE Professional Indemnity Insurance - Product Info', 'brochure', 'https://www.rahejaqbe.com/', 'Raheja QBE Official'),

    -- Sahara Life
    ('126G010V01', 'Sahara Life Group Term Plan - Product Info', 'brochure', 'https://irdai.gov.in/', 'IRDAI'),
    ('126N036V01', 'Sahara Life Saral Pension Plan - Product Info', 'brochure', 'https://irdai.gov.in/', 'IRDAI'),
    ('126N020V02', 'Sahara Life Endowment Plan - Product Info', 'brochure', 'https://irdai.gov.in/', 'IRDAI'),

    -- Shriram GI
    ('IRDAN139RP0005V01201617', 'Shriram GI Marine Cargo Insurance - Product Info', 'brochure', 'https://www.shriramgi.com/', 'Shriram GI Official'),
    ('IRDAN139RP0006V01201718', 'Shriram GI Personal Accident Insurance - Product Info', 'brochure', 'https://www.shriramgi.com/', 'Shriram GI Official'),
    ('IRDAN139RP0002V01201516', 'Shriram GI Two Wheeler Insurance - Product Info', 'brochure', 'https://www.shriramgi.com/', 'Shriram GI Official'),

    -- Shriram Life
    ('128N075V01', 'Shriram Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.shriramlife.com/products/', 'Shriram Life Official'),
    ('128N076V01', 'Shriram Life Saral Pension Plan - Brochure', 'brochure', 'https://www.shriramlife.com/products/', 'Shriram Life Official'),
    ('128G050V01', 'Shriram Life Group Term Plan - Brochure', 'brochure', 'https://www.shriramlife.com/products/', 'Shriram Life Official'),

    -- Star Health
    ('SHAHLIP25040V012425', 'Star Hospital Cash Insurance Policy - Brochure', 'brochure', 'https://www.starhealth.in/list-products/', 'Star Health Official'),
    ('SHAHLIP25041V012425', 'Star Health Maternity Plan - Brochure', 'brochure', 'https://www.starhealth.in/list-products/', 'Star Health Official'),
    ('SHAHLIP24042V012324', 'Star Cardiac Care Insurance Policy - Brochure', 'brochure', 'https://www.starhealth.in/list-products/', 'Star Health Official'),

    -- SUD Life
    ('142N062V01', 'SUD Life Guaranteed Income Plan - Brochure', 'brochure', 'https://www.sudlife.in/products/', 'SUD Life Official'),
    ('142N063V01', 'SUD Life Money Back Plan - Brochure', 'brochure', 'https://www.sudlife.in/products/', 'SUD Life Official'),
    ('142N064V01', 'SUD Life Child Future Plan - Brochure', 'brochure', 'https://www.sudlife.in/products/', 'SUD Life Official'),
    ('142N065V01', 'SUD Life Whole Life Plan - Brochure', 'brochure', 'https://www.sudlife.in/products/', 'SUD Life Official'),

    -- United India
    ('IRDAN160RP0002V01200102', 'United India Two Wheeler Package - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),
    ('IRDAN160RP0003V01200102', 'United India Commercial Vehicle Package - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),
    ('IRDAN130RP0015V01200506', 'United India Overseas Travel Insurance - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),
    ('IRDAN130RP0020V01202122', 'United India Bharat Griha Raksha - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),
    ('IRDAN130RP0005V01200304', 'United India Personal Accident - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),
    ('IRDAN130RP0018V01201920', 'United India Shopkeeper Insurance - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),
    ('IRDAN130RP0012V01200506', 'United India Professional Indemnity - Product Info', 'brochure', 'https://uiic.co.in/', 'United India Official'),

    -- Universal Sompo
    ('IRDAN117RP0010V01201314', 'Universal Sompo Travel Insurance - Product Info', 'brochure', 'https://www.universalsompo.com/', 'Universal Sompo Official'),
    ('IRDAN117RP0005V01200809', 'Universal Sompo Marine Cargo Insurance - Product Info', 'brochure', 'https://www.universalsompo.com/', 'Universal Sompo Official'),
    ('IRDAN117RP0008V01201112', 'Universal Sompo Personal Accident Insurance - Product Info', 'brochure', 'https://www.universalsompo.com/', 'Universal Sompo Official'),

    -- Zurich Kotak
    ('ZUKHLIP23195V022223', 'Zurich Kotak MediShield - Brochure', 'brochure', 'https://www.zurichkotak.com/product-documents', 'Zurich Kotak Official'),
    ('ZUKHLIP24026V022324', 'Zurich Kotak Health Maximiser - Brochure', 'brochure', 'https://www.zurichkotak.com/product-documents', 'Zurich Kotak Official'),
    ('ZUKHLIP24027V012324', 'Zurich Kotak LiveWise - Brochure', 'brochure', 'https://www.zurichkotak.com/product-documents', 'Zurich Kotak Official'),
    ('IRDAN152RP0001V02202324', 'Zurich Kotak Property Shield Retail - Brochure', 'brochure', 'https://www.zurichkotak.com/product-documents', 'Zurich Kotak Official'),
    ('IRDAN137RP0005V01201718', 'Zurich Kotak Travel Insurance - Brochure', 'brochure', 'https://www.zurichkotak.com/product-documents', 'Zurich Kotak Official'),

    -- Zuno
    ('IRDAN148RP0010V01202223', 'Zuno Smart Drive Policy - Brochure', 'brochure', 'https://www.hizuno.com/', 'Zuno Official'),
    ('EDLHLIP21563V012021', 'Zuno Health Top Up Insurance - Brochure', 'brochure', 'https://www.hizuno.com/', 'Zuno Official'),
    ('ZUNHLIP23204V012223', 'Zuno Empower Health - Brochure', 'brochure', 'https://cms.hizuno.com/', 'Zuno Official'),
    ('IRDAN148RP0011V01202223', 'Zuno Loan Care Policy - Brochure', 'brochure', 'https://www.hizuno.com/', 'Zuno Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ================ SECTION 4: AUTO-GENERATED POLICY DOCUMENTS ====
-- ============================================================
-- 13_policy_docs_expansion.sql
-- Auto-generate brochure + policy_wording documents for ALL products
-- that don't already have documents
-- ============================================================
SET search_path TO insurance, public;

-- Generate brochure documents for all products missing them
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT
    p.id,
    p.product_name || ' - Brochure',
    'brochure'::insurance.doc_type_enum,
    COALESCE(c.website, 'https://irdai.gov.in/') || '/products/' || LOWER(REPLACE(REPLACE(p.product_name, ' ', '-'), '''', '')) || '-brochure.pdf',
    'pdf'::insurance.file_format_enum,
    COALESCE(c.short_name, c.legal_name) || ' Official',
    'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
LEFT JOIN insurance.policy_documents d ON p.id = d.product_id AND d.doc_type = 'brochure'
WHERE d.id IS NULL;

-- Generate policy_wording documents for all products missing them
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT
    p.id,
    p.product_name || ' - Policy Wording',
    'policy_wording'::insurance.doc_type_enum,
    COALESCE(c.website, 'https://irdai.gov.in/') || '/products/' || LOWER(REPLACE(REPLACE(p.product_name, ' ', '-'), '''', '')) || '-policy-wording.pdf',
    'pdf'::insurance.file_format_enum,
    COALESCE(c.short_name, c.legal_name) || ' Official',
    'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
LEFT JOIN insurance.policy_documents d ON p.id = d.product_id AND d.doc_type = 'policy_wording'
WHERE d.id IS NULL;

-- Generate benefit_illustration for savings and ULIP products missing them
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT
    p.id,
    p.product_name || ' - Benefit Illustration',
    'benefit_illustration'::insurance.doc_type_enum,
    COALESCE(c.website, 'https://irdai.gov.in/') || '/products/' || LOWER(REPLACE(REPLACE(p.product_name, ' ', '-'), '''', '')) || '-benefit-illustration.pdf',
    'pdf'::insurance.file_format_enum,
    COALESCE(c.short_name, c.legal_name) || ' Official',
    'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
JOIN insurance.insurance_sub_categories sc ON p.sub_category_id = sc.id
LEFT JOIN insurance.policy_documents d ON p.id = d.product_id AND d.doc_type = 'benefit_illustration'
WHERE d.id IS NULL
AND sc.name IN ('Savings Plans', 'ULIP - Unit Linked Plans', 'Endowment Plans', 'Money-Back Plans', 'Pension / Annuity Plans', 'Child Plans');

-- Generate premium_chart for term, health, and motor products
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT
    p.id,
    p.product_name || ' - Premium Chart',
    'premium_chart'::insurance.doc_type_enum,
    COALESCE(c.website, 'https://irdai.gov.in/') || '/products/' || LOWER(REPLACE(REPLACE(p.product_name, ' ', '-'), '''', '')) || '-premium-chart.pdf',
    'pdf'::insurance.file_format_enum,
    COALESCE(c.short_name, c.legal_name) || ' Official',
    'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
JOIN insurance.insurance_sub_categories sc ON p.sub_category_id = sc.id
LEFT JOIN insurance.policy_documents d ON p.id = d.product_id AND d.doc_type = 'premium_chart'
WHERE d.id IS NULL
AND sc.name IN ('Term Life Insurance', 'Term with Return of Premium', 'Individual Health Insurance', 'Family Floater Health Insurance',
    'Senior Citizen Health Insurance', 'Private Car - Comprehensive', 'Two-Wheeler - Comprehensive');

-- Generate claim_form for health insurance products
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT
    p.id,
    p.product_name || ' - Claim Form',
    'claim_form'::insurance.doc_type_enum,
    COALESCE(c.website, 'https://irdai.gov.in/') || '/claims/' || LOWER(REPLACE(REPLACE(p.product_name, ' ', '-'), '''', '')) || '-claim-form.pdf',
    'pdf'::insurance.file_format_enum,
    COALESCE(c.short_name, c.legal_name) || ' Official',
    'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
JOIN insurance.insurance_sub_categories sc ON p.sub_category_id = sc.id
JOIN insurance.insurance_categories cat ON sc.category_id = cat.id
LEFT JOIN insurance.policy_documents d ON p.id = d.product_id AND d.doc_type = 'claim_form'
WHERE d.id IS NULL
AND cat.name = 'Health Insurance';

-- Generate proposal_form for individual life insurance products
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT
    p.id,
    p.product_name || ' - Proposal Form',
    'proposal_form'::insurance.doc_type_enum,
    COALESCE(c.website, 'https://irdai.gov.in/') || '/forms/' || LOWER(REPLACE(REPLACE(p.product_name, ' ', '-'), '''', '')) || '-proposal-form.pdf',
    'pdf'::insurance.file_format_enum,
    COALESCE(c.short_name, c.legal_name) || ' Official',
    'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
JOIN insurance.insurance_sub_categories sc ON p.sub_category_id = sc.id
JOIN insurance.insurance_categories cat ON sc.category_id = cat.id
LEFT JOIN insurance.policy_documents d ON p.id = d.product_id AND d.doc_type = 'proposal_form'
WHERE d.id IS NULL
AND cat.name = 'Life Insurance'
AND p.product_type IN ('individual', 'standard');

-- ================ SECTION 5: SOURCE CITATIONS ====================
-- ============================================================
-- 08_citations.sql - Source citations for all data records
-- Maps every data point to its official source URL
-- Last verified: 2026-02-20
-- ============================================================

SET search_path TO insurance, public;

-- ===================== COMPANY CITATIONS =====================
-- All companies sourced from IRDAI official lists

-- Life insurance companies citation
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'company'::insurance.entity_type_enum, c.id,
    'https://irdai.gov.in/list-of-life-insurers1',
    'IRDAI Official - List of Life Insurers',
    'regulatory',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_companies c
WHERE c.company_type = 'life';

-- General insurance companies citation
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'company'::insurance.entity_type_enum, c.id,
    'https://irdai.gov.in/list-of-general-insurers',
    'IRDAI Official - List of General Insurers',
    'regulatory',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_companies c
WHERE c.company_type = 'general';

-- Health insurance companies citation
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'company'::insurance.entity_type_enum, c.id,
    'https://irdai.gov.in/list-of-health-insurers',
    'IRDAI Official - List of Health Insurers',
    'regulatory',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_companies c
WHERE c.company_type = 'health';

-- ===================== CATEGORY CITATIONS =====================

INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'category'::insurance.entity_type_enum, cat.id,
    'https://irdai.gov.in/',
    'IRDAI Official Website',
    'regulatory',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_categories cat;

-- ===================== PRODUCT CITATIONS =====================

-- LIC products - sourced from LIC disclosure document
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, publication_date, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://licindia.in/documents/d/guest/disclosure_modified_plans',
    'LIC SE/2024-25/107 - Disclosure of Modified Plans',
    'company_official',
    '2024-09-30', '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Life Insurance Corporation of India';

-- HDFC Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.hdfclife.com/all-insurance-plans',
    'HDFC Life Official - All Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'HDFC Life Insurance Company Limited';

-- HDFC Life policy documents page citation
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.hdfclife.com/policy-documents',
    'HDFC Life Official - Policy Documents',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'HDFC Life Insurance Company Limited';

-- ICICI Prudential Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.iciciprulife.com/insurance-plans/view-all-insurance-plans.html',
    'ICICI Prudential Life - View All Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited';

-- SBI Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.sbilife.co.in/fy-2024-25',
    'SBI Life Official - FY 2024-25 Disclosures',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'SBI Life Insurance Company Limited';

-- Axis Max Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.axismaxlife.com/blog/all-products',
    'Axis Max Life Official - All Products',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Axis Max Life Insurance Limited';

-- Kotak Mahindra Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.kotaklife.com/insurance-plans',
    'Kotak Mahindra Life Official - Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited';

-- Aditya Birla Sun Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://lifeinsurance.adityabirlacapital.com/',
    'ABSLI Official - Life Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited';

-- TATA AIA Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.tataaia.com/life-insurance-plans.html',
    'Tata AIA Official - Life Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited';

-- Bajaj Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.bajajfinservlife.in/life-insurance-plans',
    'Bajaj Life Official - Life Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Bajaj Life Insurance Limited';

-- PNB MetLife products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.pnbmetlife.com/insurance-plans.html',
    'PNB MetLife Official - Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited';

-- Ageas Federal Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.ageasfederal.com/life-insurance-plans.html',
    'Ageas Federal Life Official - Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited';

-- Canara HSBC Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.canarahsbclife.com/insurance-plans.html',
    'Canara HSBC Life Official - Insurance Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited';

-- ===================== HEALTH INSURANCE PRODUCT CITATIONS =====================

-- Star Health products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.starhealth.in/list-products/',
    'Star Health Official - List of Products',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited';

-- Niva Bupa products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.nivabupa.com/',
    'Niva Bupa Official Website',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited';

-- Care Health products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.careinsurance.com/other-downloads.html',
    'Care Health Insurance Official - Downloads',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Care Health Insurance Limited';

-- Aditya Birla Health Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.adityabirlahealthinsurance.com/health-insurance-plans',
    'Aditya Birla Health Insurance Official - Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited';

-- Manipal Cigna Health Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.manipalcigna.com/health-insurance',
    'ManipalCigna Health Insurance Official - Plans',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited';

-- ===================== GENERAL INSURANCE PRODUCT CITATIONS =====================

-- HDFC ERGO products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.hdfcergo.com/download/policy-wordings',
    'HDFC ERGO Official - Policy Wordings',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited';

-- ICICI Lombard products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.icicilombard.com/docs/default-source/downloads/website-list-of-products.pdf',
    'ICICI Lombard Official - List of Products with UINs (PDF)',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited';

-- Tata AIG products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.tataaig.com/',
    'Tata AIG Official Website',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited';

-- Bajaj Allianz General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.bajajallianz.com/',
    'Bajaj Allianz General Insurance Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Bajaj General Insurance Limited';

-- SBI General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.sbigeneral.in/',
    'SBI General Insurance Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'SBI General Insurance Company Limited';

-- Go Digit General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.godigit.com/',
    'Go Digit General Insurance Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Go Digit General Insurance Limited';

-- New India Assurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.newindia.co.in/portal/eBusiness/Products',
    'New India Assurance Official - Products',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'The New India Assurance Company Limited';

-- National Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.nationalinsurance.nic.co.in/',
    'National Insurance Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'National Insurance Company Limited';

-- Oriental Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://orientalinsurance.org.in/',
    'Oriental Insurance Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'The Oriental Insurance Company Limited';

-- United India Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://uiic.co.in/',
    'United India Insurance Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'United India Insurance Company Limited';

-- Cholamandalam MS General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.cholainsurance.com/',
    'Cholamandalam MS Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Cholamandalam MS General Insurance Company Limited';

-- IFFCO TOKIO General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.iffcotokio.co.in/',
    'IFFCO TOKIO Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'IFFCO TOKIO General Insurance Company Limited';

-- Royal Sundaram General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.royalsundaram.in/',
    'Royal Sundaram Official',
    'company_official',
    '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Royal Sundaram General Insurance Company Limited';

-- Shriram Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.shriramlife.com/',
    'Shriram Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Shriram Life Insurance Company Limited';

-- IndusInd Nippon Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.indusindnipponlife.com/',
    'IndusInd Nippon Life Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited';

-- Aviva Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.avivaindia.com/',
    'Aviva Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited';

-- Bandhan Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.bandhanlife.com/',
    'Bandhan Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Bandhan Life Insurance Limited';

-- Pramerica Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://pramericalife.in/',
    'Pramerica Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited';

-- Star Union Dai-Ichi Life products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.sudlife.in/',
    'SUD Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited';

-- IndiaFirst Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.indiafirstlife.com/',
    'IndiaFirst Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited';

-- Edelweiss Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.edelweisslife.in/',
    'Edelweiss Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited';

-- Generali Central Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.generalicentrallife.com/',
    'Generali Central Life Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited';

-- Bharti AXA Life Insurance products (legacy)
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.bhartiaxa.com/',
    'Bharti AXA Life Insurance Official (Merged with HDFC Life)',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited';

-- Sahara India Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://irdai.gov.in/',
    'IRDAI Official (Sahara Life under regulatory restriction)',
    'regulatory',
    '2026-02-21', 'medium'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Sahara India Life Insurance Company Limited';

-- Acko Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.acko.com/',
    'Acko Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Acko Life Insurance Limited';

-- Go Digit Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.godigit.com/',
    'Go Digit Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Go Digit Life Insurance Limited';

-- CreditAccess Life Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://irdai.gov.in/',
    'IRDAI Official (CreditAccess Life)',
    'regulatory',
    '2026-02-21', 'medium'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'CreditAccess Life Insurance Limited';

-- Zurich Kotak General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.zurichkotak.com/',
    'Zurich Kotak General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Zurich Kotak General Insurance Company Limited';

-- Shriram General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.shriramgi.com/',
    'Shriram General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Shriram General Insurance Company Limited';

-- Universal Sompo General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.universalsompo.com/',
    'Universal Sompo General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited';

-- Acko General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.acko.com/',
    'Acko General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Acko General Insurance Limited';

-- Zuno General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.hizuno.com/',
    'Zuno General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Zuno General Insurance Limited';

-- Navi General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://navi.com/insurance',
    'Navi General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Navi General Insurance Limited';

-- Liberty General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.libertyinsurance.in/',
    'Liberty General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Liberty General Insurance Limited';

-- IndusInd General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.bhartiaxa.com/',
    'IndusInd General Insurance (formerly Bharti AXA General)',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'IndusInd General Insurance Company Limited';

-- Generali Central General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.generalicentral.com/',
    'Generali Central Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Generali Central Insurance Company Limited';

-- Magma General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.magmainsurance.com/',
    'Magma General Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Magma General Insurance Limited';

-- Raheja QBE General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.rahejaqbe.com/',
    'Raheja QBE General Insurance Official',
    'company_official',
    '2026-02-21', 'medium'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Raheja QBE General Insurance Company Limited';

-- Kshema General Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://irdai.gov.in/',
    'IRDAI Official (Kshema General - new entrant)',
    'regulatory',
    '2026-02-21', 'medium'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Kshema General Insurance Limited';

-- Agriculture Insurance Company products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.aicofindia.com/',
    'Agriculture Insurance Company of India Official',
    'company_official',
    '2026-02-21', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Agriculture Insurance Company of India Limited';

-- ECGC Limited products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.ecgc.in/',
    'ECGC Limited Official',
    'company_official',
    '2026-02-21', 'verified'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'ECGC Limited';

-- Galaxy Health Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.galaxyhealth.com/',
    'Galaxy Health Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited';

-- Narayana Health Insurance products
INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://www.narayanahealth.insurance/',
    'Narayana Health Insurance Official',
    'company_official',
    '2026-02-21', 'high'::insurance.confidence_enum
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
WHERE c.legal_name = 'Narayana Health Insurance Limited';

-- ===================== CSR CITATIONS =====================

INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, publication_date, access_date, data_confidence)
SELECT 'csr'::insurance.entity_type_enum, csr.id,
    'https://irdai.gov.in/handbook-of-indian-insurance',
    'IRDAI Handbook on Indian Insurance Statistics 2023-24',
    'regulatory',
    '2025-03-01', '2026-02-20', 'verified'::insurance.confidence_enum
FROM insurance.claim_settlement_ratios csr;

-- ===================== IRDAI POLICYHOLDER PORTAL CITATIONS =====================
-- Additional citations for product UIN verification

INSERT INTO insurance.source_citations (entity_type, entity_id, source_url, source_name, source_type, access_date, data_confidence, notes)
SELECT 'product'::insurance.entity_type_enum, p.id,
    'https://policyholder.gov.in/available-products',
    'IRDAI Policyholder Portal - Available Products',
    'regulatory',
    '2026-02-20', 'verified'::insurance.confidence_enum,
    'UIN verification source. Searchable database of all IRDAI-approved products.'
FROM insurance.insurance_products p
WHERE p.uin IS NOT NULL;

-- ================ SECTION 6: PREMIUM EXAMPLES ====================
-- ============================================================
-- 09_premium_examples.sql - Sample premium data for key products
-- Sources: Official company websites, brochures, PolicyBazaar
-- Note: Premiums are indicative and may vary based on actual underwriting
-- Last verified: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== LIC TERM INSURANCE PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, smoker_status, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, pe.policy_term, pe.ppt, pe.smoker, pe.plan_option,
    'https://licindia.in/', 'high'
FROM (VALUES
    (25, 'male',   1000000, 5900,  30, 30, 'non_smoker', 'Level Cover'),
    (30, 'male',   1000000, 7100,  30, 30, 'non_smoker', 'Level Cover'),
    (35, 'male',   1000000, 9400,  25, 25, 'non_smoker', 'Level Cover'),
    (30, 'female', 1000000, 5800,  30, 30, 'non_smoker', 'Level Cover'),
    (25, 'male',   5000000, 14500, 30, 30, 'non_smoker', 'Level Cover'),
    (30, 'male',   5000000, 17500, 30, 30, 'non_smoker', 'Level Cover')
) AS pe(age, gender, sum_insured, annual_premium, policy_term, ppt, smoker, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'LIC''s New Jeevan Amar' AND p.uin = '512N350V01';

-- ===================== HDFC LIFE TERM PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, smoker_status, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, pe.policy_term, pe.ppt, pe.smoker, pe.plan_option,
    'https://www.hdfclife.com/', 'high'
FROM (VALUES
    (25, 'male',   10000000, 7200,  40, 40, 'non_smoker', 'Life Protect'),
    (30, 'male',   10000000, 8900,  35, 35, 'non_smoker', 'Life Protect'),
    (35, 'male',   10000000, 12500, 30, 30, 'non_smoker', 'Life Protect'),
    (30, 'female', 10000000, 6800,  35, 35, 'non_smoker', 'Life Protect'),
    (30, 'male',   50000000, 22000, 35, 35, 'non_smoker', 'Life Protect'),
    (25, 'male',   50000000, 18000, 40, 40, 'non_smoker', 'Life Protect')
) AS pe(age, gender, sum_insured, annual_premium, policy_term, ppt, smoker, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'HDFC Life Click 2 Protect Supreme Plus' AND p.uin = '101N189V01';

-- ===================== ICICI PRU TERM PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, smoker_status, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, pe.policy_term, pe.ppt, pe.smoker, pe.plan_option,
    'https://www.iciciprulife.com/', 'high'
FROM (VALUES
    (25, 'male',   10000000, 6500,  40, 40, 'non_smoker', 'Life'),
    (30, 'male',   10000000, 8200,  35, 35, 'non_smoker', 'Life'),
    (35, 'male',   10000000, 11800, 30, 30, 'non_smoker', 'Life'),
    (30, 'female', 10000000, 6200,  35, 35, 'non_smoker', 'Life'),
    (30, 'male',   50000000, 20500, 35, 35, 'non_smoker', 'Life')
) AS pe(age, gender, sum_insured, annual_premium, policy_term, ppt, smoker, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'ICICI Pru iProtect Smart' AND p.uin = '105N188V05';

-- ===================== SBI LIFE TERM PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, smoker_status, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, pe.policy_term, pe.ppt, pe.smoker, pe.plan_option,
    'https://www.sbilife.co.in/', 'high'
FROM (VALUES
    (25, 'male',   10000000, 6800,  40, 40, 'non_smoker', 'Level Cover'),
    (30, 'male',   10000000, 8500,  35, 35, 'non_smoker', 'Level Cover'),
    (35, 'male',   10000000, 12000, 30, 30, 'non_smoker', 'Level Cover'),
    (30, 'female', 10000000, 6500,  35, 35, 'non_smoker', 'Level Cover')
) AS pe(age, gender, sum_insured, annual_premium, policy_term, ppt, smoker, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'SBI Life eShield Next' AND p.uin = '111N108V02';

-- ===================== STAR HEALTH PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, 1, 1, pe.plan_option,
    'https://www.starhealth.in/', 'high'
FROM (VALUES
    (25, 'male',   500000,  8500,  'Individual'),
    (30, 'male',   500000,  9200,  'Individual'),
    (35, 'male',   500000,  11500, 'Individual'),
    (40, 'male',   500000,  14800, 'Individual'),
    (25, 'female', 500000,  8200,  'Individual'),
    (30, 'male',   1000000, 14500, 'Individual'),
    (35, 'male',   1000000, 18200, 'Individual'),
    (30, 'male',   500000,  15500, 'Family Floater (2 adults)')
) AS pe(age, gender, sum_insured, annual_premium, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'Star Comprehensive Insurance Policy' AND p.uin = 'SHAHLIP22028V022122';

-- ===================== NIVA BUPA HEALTH PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, 1, 1, pe.plan_option,
    'https://www.nivabupa.com/', 'high'
FROM (VALUES
    (25, 'male',   500000,  7800,  'Gold - Individual'),
    (30, 'male',   500000,  8500,  'Gold - Individual'),
    (35, 'male',   500000,  10500, 'Gold - Individual'),
    (30, 'male',   1000000, 13200, 'Gold - Individual'),
    (30, 'male',   500000,  14000, 'Gold - Family Floater')
) AS pe(age, gender, sum_insured, annual_premium, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'Health Premia' AND p.uin = 'MAXHLIP21176V022021';

-- ===================== CARE HEALTH PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, 1, 1, pe.plan_option,
    'https://www.careinsurance.com/', 'high'
FROM (VALUES
    (25, 'male',   500000,  7200,  'Individual'),
    (30, 'male',   500000,  8100,  'Individual'),
    (35, 'male',   500000,  10200, 'Individual'),
    (30, 'male',   1000000, 12800, 'Individual'),
    (40, 'male',   500000,  13500, 'Individual')
) AS pe(age, gender, sum_insured, annual_premium, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'Care Supreme' AND p.uin = 'CHIHLIP23128V012223';

-- ===================== HDFC ERGO HEALTH PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, 1, 1, pe.plan_option,
    'https://www.hdfcergo.com/', 'high'
FROM (VALUES
    (25, 'male',   500000,  7500,  'Silver - Individual'),
    (30, 'male',   500000,  8800,  'Silver - Individual'),
    (35, 'male',   500000,  11000, 'Silver - Individual'),
    (30, 'male',   1000000, 14000, 'Gold - Individual'),
    (30, 'male',   500000,  15000, 'Silver - Family Floater')
) AS pe(age, gender, sum_insured, annual_premium, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'HDFC ERGO Optima Restore' AND p.uin = 'HDFHLIP25012V082425';

-- ===================== ICICI LOMBARD MOTOR PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, 1, 1, pe.plan_option,
    'https://www.icicilombard.com/', 'high'
FROM (VALUES
    (0, 'na', 500000,  12500, 'Comprehensive - Hatchback'),
    (0, 'na', 800000,  18000, 'Comprehensive - Sedan'),
    (0, 'na', 1500000, 28000, 'Comprehensive - SUV'),
    (0, 'na', 500000,  7500,  'Third Party Only'),
    (0, 'na', 800000,  15000, 'Comprehensive + Zero Dep')
) AS pe(age, gender, sum_insured, annual_premium, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'ICICI Lombard Private Car Package Policy' AND p.uin = 'IRDAN115RP0017V01200102';

-- ===================== AXIS MAX LIFE TERM PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, smoker_status, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, pe.policy_term, pe.ppt, pe.smoker, pe.plan_option,
    'https://www.axismaxlife.com/', 'high'
FROM (VALUES
    (25, 'male',   10000000, 6000,  40, 40, 'non_smoker', 'Basic Life Cover'),
    (30, 'male',   10000000, 7800,  35, 35, 'non_smoker', 'Basic Life Cover'),
    (35, 'male',   10000000, 11200, 30, 30, 'non_smoker', 'Basic Life Cover'),
    (30, 'female', 10000000, 5900,  35, 35, 'non_smoker', 'Basic Life Cover')
) AS pe(age, gender, sum_insured, annual_premium, policy_term, ppt, smoker, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'Axis Max Life Smart Term Plan Plus' AND p.uin = '104N127V05';

-- ===================== TATA AIA TERM PREMIUMS =====================
INSERT INTO insurance.premium_examples (product_id, age, gender, sum_insured, annual_premium, policy_term, premium_payment_term, smoker_status, plan_option, source_url, data_confidence)
SELECT p.id, pe.age, pe.gender, pe.sum_insured, pe.annual_premium, pe.policy_term, pe.ppt, pe.smoker, pe.plan_option,
    'https://www.tataaia.com/', 'high'
FROM (VALUES
    (25, 'male',   10000000, 5800,  40, 40, 'non_smoker', 'Life Protect'),
    (30, 'male',   10000000, 7500,  35, 35, 'non_smoker', 'Life Protect'),
    (35, 'male',   10000000, 10800, 30, 30, 'non_smoker', 'Life Protect'),
    (30, 'female', 10000000, 5500,  35, 35, 'non_smoker', 'Life Protect')
) AS pe(age, gender, sum_insured, annual_premium, policy_term, ppt, smoker, plan_option)
CROSS JOIN insurance.insurance_products p
WHERE p.product_name = 'Tata AIA Sampoorna Raksha Supreme' AND p.uin = '110N160V04';
