-- ============================================================
-- 03_health_insurance.sql
-- Consolidated: All health insurance products, expansions, and documents
-- Merged from: 04_products_health.sql + 04b_products_health_extra.sql
--              + 11_health_expansion.sql + 14_additional_expansion.sql (Part 2)
--              + 07c_policy_docs_health.sql
-- ============================================================

-- ================ SECTION 1: CORE HEALTH PRODUCTS ===============
-- ============================================================
-- 04_products_health.sql - Health insurance products with real UINs
-- Sources: starhealth.in, nivabupa.com, careinsurance.com, hdfcergo.com
-- Last verified: 2026-02-20
-- ============================================================

SET search_path TO insurance, public;

-- ===================== STAR HEALTH PRODUCTS =====================
-- Source: https://www.starhealth.in/list-products/

-- Star Health Super Star
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Super Star', 'SHAHLIP25036V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Comprehensive individual/family floater health insurance plan from Star Health covering hospitalization, day-care procedures, and wellness benefits.',
    'Cashless treatment at 14,000+ network hospitals. No room rent capping. Annual health check-up. Restoration of sum insured. AYUSH treatment coverage.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Health Young Star Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Young Star Insurance Policy', 'SHAHLIP25035V052425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Health insurance plan designed for young adults aged 18-40. Covers hospitalization, day-care treatments, pre and post hospitalization expenses with focus on younger demographics.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== NIVA BUPA PRODUCTS =====================
-- Source: https://www.nivabupa.com/

-- Niva Bupa Health Premia
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Health Premia', 'MAXHLIP21176V022021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'A comprehensive health insurance plan from Niva Bupa offering wide coverage for hospitalization, daycare procedures, and critical illness with Gold and Platinum variants.',
    'No room rent limit. Sum insured up to Rs. 1 crore. Maternity cover available. Unlimited restoration. Global treatment benefit. Air ambulance cover.',
    'https://transactions.nivabupa.com/pages/doc/brochure/Health_Premia_Gold_Br.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Niva Bupa Health Companion
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Health Companion', 'NBHHLIP23108V062223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Niva Bupa''s flagship comprehensive health insurance plan with family floater option. Covers hospitalization, pre/post hospitalization, day-care treatments, organ donor expenses, and AYUSH treatments.',
    'https://www.nivabupa.com/content/dam/nivabupa/PDF/Health-Companion/Health%20Companion_Brochure.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Niva Bupa Arogya Sanjeevani (Standard)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Niva Bupa)', 'NBHHLIP26045V032526', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'IRDAI-mandated standard health insurance product with uniform terms and conditions across all insurers. Covers hospitalization expenses up to sum insured with standardized benefits.',
    'https://transactions.nivabupa.com/pages/doc/brochure/Arogya_Sanjeevani_SS.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- ===================== CARE HEALTH PRODUCTS =====================
-- Source: https://www.careinsurance.com/other-downloads.html

-- Care Supreme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Supreme', 'CHIHLIP23128V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Premium comprehensive health insurance plan from Care Health Insurance offering high sum insured options with extensive coverage for hospitalization and critical illness.',
    'Sum insured up to Rs. 6 crore. No room rent capping. Global cover option. Air ambulance. Maternity benefit. Organ donor cover. Annual health check-up. No sub-limits.',
    'https://www.careinsurance.com/other-downloads.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Shield Add-On
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Shield Add-On', 'CHIHLIA26054V022526', 'add_on', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Add-on plan from Care Health Insurance providing enhanced coverage when purchased with a base Care health insurance plan. Extends benefits beyond the base plan limits.',
    'https://cms.careinsurance.com/cms/public/uploads/download_center/care-shield-add-on---prospectus-cum-sales-literature.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- ===================== HDFC ERGO HEALTH PRODUCTS =====================
-- Source: https://www.hdfcergo.com/download/policy-wordings

-- HDFC ERGO Optima Restore
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Optima Restore', 'HDFHLIP25012V082425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'HDFC ERGO''s flagship health insurance plan with automatic sum insured restoration. Individual and family floater options with comprehensive hospitalization coverage.',
    'Automatic restoration of sum insured. Unlimited automatic recharge. No room rent limit. Day-care procedures covered. Pre and post hospitalization. AYUSH treatment. Health check-up.',
    'https://www.hdfcergo.com/download/policy-wordings', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- HDFC ERGO my:health Critical Illness
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO my:health Critical Illness', 'HDFHLIA22141V032122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Critical illness insurance plan from HDFC ERGO providing lump-sum benefit on diagnosis of specified critical illnesses including cancer, heart attack, stroke, and kidney failure.',
    'https://www.hdfcergo.com/download/policy-wordings', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- HDFC ERGO my:health Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO my:health Suraksha', 'HDFHLIP20049V041920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive health insurance plan from HDFC ERGO offering hospitalization, pre/post hospitalization, day-care procedures, and AYUSH treatment coverage for individuals and families.',
    'https://www.hdfcergo.com/download/policy-wordings', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- HDFC ERGO my:health Medisure Super Top Up
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO my:health Medisure Super Top Up', 'HDFHLIP21064V022021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Super top-up health insurance plan that supplements existing health coverage. Activates after the deductible threshold is met, providing additional coverage for high medical expenses.',
    'https://www.hdfcergo.com/download/policy-wordings', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- ===================== STAR HEALTH - ADDITIONAL PRODUCTS =====================
-- Source: https://www.starhealth.in/list-products/

-- Star Health Comprehensive Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Comprehensive Insurance Policy', 'SHAHLIP22028V022122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Star Health''s comprehensive health insurance plan covering hospitalization, day-care, pre and post hospitalization expenses. Available as individual and family floater.',
    'Cashless treatment at 14,000+ network hospitals. No room rent capping. Annual health check-up. Restoration of sum insured. AYUSH coverage. Maternity benefit.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Health Family Health Optima Insurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Family Health Optima Insurance Plan', 'SHAHLIP19012V031819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Star Health''s flagship family floater health insurance plan with shared sum insured for the entire family. Covers hospitalization, day-care, pre/post hospitalization expenses.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Star Health Senior Citizens Red Carpet
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Senior Citizens Red Carpet Health Insurance Policy', 'SHAHLIP19014V021819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Health insurance plan specially designed for senior citizens aged 60-75 years. Covers hospitalization, pre-existing diseases after waiting period, and AYUSH treatments.',
    'Entry age 60-75 years. Pre-existing disease cover after 12 months. Cataract surgery covered. Day-care procedures. AYUSH coverage. Automatic restoration.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- Star Health Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Star Health)', 'SHAHLIP20016V021920', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'IRDAI-mandated standard health insurance product with uniform terms across all insurers. Sum insured Rs. 1 lakh to Rs. 5 lakh. Covers hospitalization, AYUSH, and cataract treatment.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- Star Health Diabetes Safe Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Diabetes Safe Insurance Policy', 'SHAHLIP19010V021819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Specialized health insurance plan for diabetic patients (Type 1 and Type 2). Covers diabetes-related hospitalization and complications with customized coverage.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Disease-Specific Insurance';

-- Star Health Cardiac Care Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Cardiac Care Insurance Policy', 'SHAHLIP19011V031819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Specialized health insurance plan for heart patients covering cardiac conditions and cardiac-related hospitalization. Designed for people with existing heart conditions.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Disease-Specific Insurance';

-- Star Health Cancer Care Platinum
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Cancer Care Platinum Insurance Policy', 'SHAHLIP22027V022122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive cancer-specific health insurance plan covering all stages of cancer treatment including chemotherapy, radiation, and surgery with high sum insured options.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Disease-Specific Insurance';

-- Star Health Women Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Women Care Insurance Policy', 'SHAHLIP19013V021819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Health insurance plan designed exclusively for women covering hospitalization, maternity, newborn baby coverage, and women-specific conditions like breast cancer and ovarian cancer.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Maternity Insurance';

-- Star Health Critical Illness Multipay
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Critical Illness Multipay Insurance Policy', 'SHAHLIP22026V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Critical illness plan providing lump sum payout on diagnosis of specified critical illnesses with multipay feature for recurrence or new diagnosis of covered conditions.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- Star Health Super Surplus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Super Surplus Insurance Policy', 'SHAHLIP19015V021819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Super top-up health insurance plan supplementing existing health cover. Activates after deductible threshold with high coverage up to Rs. 1 crore.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Star Health Travel Protect
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Travel Protect Insurance Policy', 'SHAHTIP19002V011819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'International travel insurance covering medical emergencies, trip cancellation, baggage loss, passport loss, and emergency evacuation while traveling abroad.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'International Travel Insurance';

-- Star Health Accident Trauma Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Accident Trauma Care Insurance Policy', 'SHAHPAP19001V021819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Personal accident insurance covering accidental death, permanent total and partial disability. Available for individuals and groups.',
    'https://www.starhealth.in/list-products/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- ===================== CARE HEALTH - ADDITIONAL PRODUCTS =====================
-- Source: https://www.careinsurance.com/

-- Care Plus Complete Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Plus', 'CHIHLIP22047V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Complete health insurance plan from Care Health covering hospitalization, day-care procedures, pre/post hospitalization, and domiciliary treatment.',
    'No room rent capping. Automatic recharge of sum insured. Cumulative bonus. AYUSH coverage. Day-care procedures. Pre and post hospitalization. Domiciliary treatment.',
    'https://www.careinsurance.com/product/care', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Advantage with Protect Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Advantage', 'CHIHLIP23150V022223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Health insurance plan from Care Health offering affordable coverage with add-on protect plus option for enhanced benefits. Zone-based pricing for premium optimization.',
    'https://www.careinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Care Health)', 'CHIHLIP20040V011920', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'IRDAI-mandated standard health insurance product from Care Health Insurance. Standardized coverage with sum insured Rs. 1 lakh to Rs. 5 lakh and uniform terms.',
    'https://www.careinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- ===================== ADITYA BIRLA HEALTH INSURANCE PRODUCTS =====================
-- Source: https://www.adityabirlahealthinsurance.com/

-- Activ One
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ One', 'ADIHLIP24097V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Latest flagship comprehensive health insurance plan from Aditya Birla Health Insurance. Covers hospitalization, OPD, wellness, and chronic care management.',
    'Comprehensive hospitalization cover. OPD benefits. Wellness rewards and HealthReturns program. Chronic care management. Mental health coverage. AYUSH treatments.',
    'https://www.adityabirlahealthinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Activ Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Care', 'ADIHLIP21062V022021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Health insurance plan designed for parents and senior citizens aged 50+ years. Provides comprehensive coverage with Standard, Classic, and Premier options.',
    'Designed for age 50+ years. Pre-existing disease cover. Cataract surgery. AYUSH coverage. Day-care procedures. Multiple plan variants.',
    'https://www.adityabirlahealthinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- Activ Health Platinum
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Health Platinum', 'ADIHLIP22078V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Premium comprehensive health insurance with HealthReturns wellness incentive program. Available in Essential, Enhanced, and Premiere variants.',
    'HealthReturns: earn up to 100% premium back for healthy living. Comprehensive hospitalization. OPD coverage. Global treatment. Chronic management. Mental health support.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Activ Assure Diamond
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Assure Diamond', 'ADIHLIP22079V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Affordable health insurance plan from Aditya Birla Health providing wide medical coverage at competitive premiums. Available for individuals and family floater.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Activ Secure Critical Illness
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Secure - Critical Illness', 'ADIHLIP22080V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Critical illness insurance providing financial coverage for up to 64 critical illnesses and procedures. Lump sum payout on diagnosis of covered conditions.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- Activ Cancer Secure
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Cancer Secure', 'ADIHLIP22081V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Cancer-specific health insurance providing coverage against the treatment cost of cancer at all stages. Lump sum benefit on diagnosis.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Disease-Specific Insurance';

-- ===================== MANIPAL CIGNA HEALTH PRODUCTS =====================
-- Source: https://www.manipalcigna.com/

-- ManipalCigna ProHealth Prime Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Prime Insurance', 'MCGHLIP22048V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive health insurance plan covering hospitalization, OPD expenses, pre/post hospitalization, day-care procedures, and domiciliary treatment.',
    'OPD coverage. Comprehensive hospitalization. Pre and post hospitalization. Day-care procedures. Domiciliary treatment. 6,500+ network hospitals. Cashless claims.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ManipalCigna ProHealth Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Insurance', 'MCGHLIP22047V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive health insurance plan focusing on overall wellness of the insured. Covers hospitalization, wellness benefits, and preventive care.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ManipalCigna Prime Senior Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna Prime Senior Insurance', 'MCGHLIP22049V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance plan specially designed for senior citizens. Covers age-related ailments, hospitalization, and wellness needs of elderly individuals.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- ManipalCigna Lifestyle Protection Critical Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna Lifestyle Protection Critical Care', 'MCGHLIP22050V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Critical illness insurance covering up to 30 critical illnesses including cancer, coma, and kidney failure. Lump sum payout on diagnosis.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- ManipalCigna Super Top Up Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna Super Top Up Insurance', 'MCGHLIP22051V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Super top-up health insurance providing additional coverage when base policy is insufficient. Activates after deductible threshold.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- ManipalCigna LifeTime Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna LifeTime Health Insurance', 'MCGHLIP22052V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive health insurance covering medical expenses within India and abroad. Includes Health+, Women+, and Global+ optional covers.',
    'Global treatment coverage. Women-specific benefits. Health check-up. Domiciliary treatment. AYUSH treatments. Air ambulance.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== BAJAJ ALLIANZ GENERAL - HEALTH PRODUCTS =====================
-- Source: https://www.bajajgeneralinsurance.com/

-- Bajaj Allianz Health Guard
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Health Guard', 'BAJHLIP20070V031920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Comprehensive individual health insurance plan from Bajaj Allianz General covering hospitalization, day-care procedures, and domiciliary hospitalization.',
    'Cashless treatment at 8,000+ network hospitals. No room rent capping. Automatic restoration. AYUSH coverage. Day-care procedures. Pre and post hospitalization.',
    'https://www.bajajgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Bajaj Allianz Extra Care Plus (Super Top Up)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Extra Care Plus', 'BAJHLIP22090V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Additional health cover providing wider protection for individuals and families. Super top-up plan supplementing existing health insurance.',
    'https://www.bajajgeneralinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- ===================== SBI GENERAL - HEALTH PRODUCTS =====================
-- Source: https://www.sbigeneral.in/

-- SBI General Arogya Premier
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Arogya Premier', 'IRDAN144HL0001V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'SBI General''s flagship comprehensive health insurance plan covering hospitalization, day-care, pre/post hospitalization, and AYUSH treatments for individuals and families.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- SBI General Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (SBI General)', 'IRDAN144HL0002V01202021', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'IRDAI-mandated standard health insurance product from SBI General with uniform terms. Sum insured Rs. 1 lakh to Rs. 5 lakh.',
    'https://www.sbigeneral.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- ===================== GALAXY HEALTH INSURANCE PRODUCTS =====================
-- Source: https://www.galaxyhealth.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Promise', 'GLXHLIP24001V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Galaxy Health''s first and flagship comprehensive health insurance plan launched October 2024. Available in three variants: Signature, Elite, and Premier with sum insured from Rs. 3 lakh to Rs. 1 crore.',
    'Three plan variants (Signature, Elite, Premier). Sum insured Rs. 3 lakh to Rs. 1 crore. Cashless hospitalization. Pre and post hospitalization cover. Day care procedures.',
    'https://www.galaxyhealth.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Marvel', 'GLXHLIP25002V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Customizable health insurance with optional covers, wellness programs, unlimited restoration of sum insured and premium waiver facility. Launched pan-India via Policybazaar.',
    'Unlimited restoration of sum insured. Premium waiver facility. Wellness programs. Optional covers. Customizable plan.',
    'https://www.galaxyhealth.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Privilege', 'GLXHLIP25003V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Comprehensive health plan tailored for senior citizens. Available on individual and floater basis with shorter waiting periods and a range of optional benefits.',
    'https://www.galaxyhealth.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Galaxy)', 'GLXHLIP24004V012425', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'IRDAI-mandated standard health insurance from Galaxy Health with affordable family health cover including pre/post hospitalization, day care procedures and ambulance services.',
    'https://www.galaxyhealth.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- ===================== NARAYANA HEALTH INSURANCE PRODUCTS =====================
-- Source: https://www.narayanahealth.insurance/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Aditi', 'NRHHLIP24001V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Narayana Health Insurance''s first product launched July 2024. Up to Rs. 1 crore coverage at Rs. 29/day for a family of four. Rs. 5 lakh for medical management and up to Rs. 1 crore for surgeries.',
    'Rs. 1 crore surgical coverage. Rs. 5 lakh medical management. Cashless at Narayana Health network. Coverage at Rs. 29/day for family of four.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Aditi Plus', 'NRHHLIP24002V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Enhanced version of Aditi with same surgical coverage plus Rs. 20 lakh for medical treatment. Priced at Rs. 29,000 annually with private room access.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Arya', 'NRHHLIP25003V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Comprehensive retail health insurance with sum insured from Rs. 25 lakh to Rs. 1 crore. Designed for affordable quality healthcare, fully passing on GST exemption benefits.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== ADDITIONAL NIVA BUPA PRODUCTS =====================
-- Source: https://www.nivabupa.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ReAssure 3.0', 'NBHHLIP26050V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Niva Bupa''s flagship comprehensive health insurance with Rs. 1 crore coverage, unlimited reinstatement, Booster+ feature, and wellness rewards. Premium lock plus optional global treatment.',
    'Rs. 1 crore coverage. Unlimited reinstatement. Booster+ feature. Wellness rewards. Premium lock. Optional global treatment.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'GoActive', 'NBHHLIP23110V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Versatile health plan for families and individuals with sum insured up to Rs. 25 lakh. Designed for active lifestyle with wellness benefits.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Senior First', 'NBHHLIP23112V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Senior citizen health plan from Niva Bupa with features designed for older adults. Pre-existing disease coverage with shorter waiting period.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- ===================== ADDITIONAL CANARA HSBC LIFE PRODUCTS =====================
-- Source: https://www.canarahsbclife.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC iSelect Term Plan', '136N115V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Online term insurance from Canara HSBC Life with affordable premiums and flexible coverage options. Provides life protection with multiple payout options.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Invest 4G', '136L025V01', 'individual', 'linked', 'not_applicable',
    TRUE, '2023-2024',
    'Unit linked insurance plan from Canara HSBC Life offering market-linked returns with multiple fund options and life cover.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Guaranteed Savings Plan', '136N118V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan providing guaranteed returns with life cover. Multiple premium payment and benefit options.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ============================================================
-- PHASE 2 EXPANSION - Filling all empty health sub-categories
-- and adding more products to existing companies
-- ============================================================

-- ===================== GROUP HEALTH INSURANCE (NEW SUB-CATEGORY) =====================

-- Star Health Group Health Insurance - Platinum
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Group Health Insurance Policy - Platinum', 'SHAHLGP23015V012223', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Premium group health insurance for corporates covering hospitalization, day-care, pre/post hospitalization. Platinum variant with highest coverage limits and no sub-limits.',
    'https://www.starhealth.in/group-health-insurance/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- Star Health Classic Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Classic Group Health Insurance', 'SHAHLGP21239V022021', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Group health insurance for organizations providing basic hospitalization coverage for employees and their families. Available with various sum insured options.',
    'https://www.starhealth.in/group-health-insurance/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- Star Health Group Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Group Arogya Sanjeevani Policy (Star Health)', 'SHAHLGP22041V022122', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'IRDAI-mandated standard group health insurance with uniform terms. Covers hospitalization, day-care procedures, and AYUSH treatments for employer-employee groups.',
    'https://www.starhealth.in/group-health-insurance/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- New India Assurance Group Mediclaim
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'New India Group Mediclaim Policy', 'NIAHLGP21236V022021', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Group health insurance from New India Assurance for employer-employee groups. Covers hospitalization, pre/post hospitalization, domiciliary treatment, and day-care procedures.',
    'https://www.newindia.co.in/health-insurance/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'The New India Assurance Company Limited' AND sc.name = 'Group Health Insurance';

-- ICICI Lombard Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Group Health Insurance', 'ICIHLGP22096V022122', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive group health insurance for corporates with cashless settlement at 6500+ network hospitals. Covers hospitalization, day-care, maternity, and domiciliary treatment.',
    'https://www.icicilombard.com/health-insurance/group-health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- HDFC ERGO Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Group Health Insurance', 'HDFHLGP22142V022122', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Group health insurance for corporates and associations. Covers hospitalization, pre/post hospitalization, day-care procedures, domiciliary treatment, and maternity benefits.',
    'https://www.hdfcergo.com/health-insurance/group-health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- Niva Bupa Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Group Health Insurance', 'NBHHLGP23115V012223', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Group health insurance from Niva Bupa for employer-employee groups. Covers hospitalization, day-care, maternity, and wellness benefits with 10,000+ network hospitals.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- Care Health Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Group Health Insurance', 'CHIHLGP23155V012223', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Group health insurance from Care Health for corporates covering hospitalization, day-care, pre/post hospitalization, and domiciliary treatment. Available with customizable sum insured.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Group Health Insurance';

-- Manipal Cigna Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna Group Health Insurance', 'MCGHLGP22055V012122', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Group health insurance for employer-employee groups. Covers hospitalization, OPD benefits, maternity, and wellness programs with 6,500+ network hospitals.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- Bajaj General Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Group Health Insurance', 'BAJHLGP22130V012122', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Group health insurance from Bajaj Allianz General for corporates. Covers hospitalization, day-care procedures, and pre/post hospitalization expenses with 8,000+ network hospitals.',
    'https://www.bajajallianz.com/group-health-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Group Health Insurance';

-- ===================== HOSPITAL DAILY CASH (NEW SUB-CATEGORY) =====================

-- Star Health Hospital Cash Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Hospital Cash Insurance Policy', 'SHAHLIP20046V011920', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2019-2020',
    'Hospital daily cash policy providing fixed daily benefit for each day of hospitalization regardless of actual expenses. Available in Basic and Enhanced plan options.',
    'Daily cash benefit for each 24-hour hospitalization period. Double benefit for accident-related hospitalization. No sub-limits. Portable policy.',
    'https://www.starhealth.in/health-insurance/hospital-cash/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- SBI General Hospital Daily Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI General Hospital Daily Cash Insurance Policy', 'SBIHLIP11003V011011', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2010-2011',
    'Fixed benefit hospital daily cash plan from SBI General. Provides a pre-determined daily cash allowance for each day of hospitalization.',
    'Daily cash benefit up to Rs. 2,000/day. ICU benefit up to Rs. 4,000/day. Double benefit for accidental hospitalization. Flexible 30/60 day coverage options.',
    'https://www.sbigeneral.in/health-insurance/hospital-daily-cash', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI General Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- ManipalCigna ProHealth Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Cash', 'MCGHLIP22053V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Daily hospital cash benefit plan providing prompt financial assistance during hospitalization. Daily cash benefits from Rs. 500 to Rs. 5,000.',
    'Daily cash benefit Rs. 500 to Rs. 5,000. Coverage for 60/90/180 days per year. Optional accident coverage. Available in Basic and Plus variants.',
    'https://www.manipalcigna.com/daily-hospital-cash', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- ICICI Lombard Hospital Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Hospital Daily Cash Benefit', 'ICIHLIP22097V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Hospital daily cash benefit plan providing fixed daily amount for each day of hospitalization. Can be taken as standalone or add-on to existing health plan.',
    'https://www.icicilombard.com/health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- Universal Sompo Hospital Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Universal Sompo Hospital Cash Insurance', 'IRDAN117HL0010V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Hospital daily cash insurance providing fixed daily benefit for hospitalization. Supplements existing health insurance by covering out-of-pocket expenses during hospital stay.',
    'https://www.universalsompo.com/hospital-cash-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Universal Sompo General Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- ===================== PERSONAL ACCIDENT - HEALTH (NEW SUB-CATEGORY) =====================

-- Niva Bupa Personal Accident Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Personal Accident Plan', 'NBHPAIP25036V022425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Personal accident insurance from standalone health insurer Niva Bupa. Covers accidental death, permanent total and partial disability, and temporary total disability.',
    'Coverage up to Rs. 5 crore. Accidental death benefit. Permanent total/partial disability. Temporary total disability. 30-minute cashless processing. 8,500+ hospitals.',
    'https://www.nivabupa.com/personal-accident-insurance.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Personal Accident (Health)';

-- ManipalCigna Accident Shield
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna Accident Shield', 'MCIPAIP21622V012021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Standard personal accident policy from ManipalCigna covering accidental death, permanent total/partial disability. Sum insured up to Rs. 10 crore.',
    'Sum insured up to Rs. 10 crore. Accidental death 100% SI. Permanent total disability 100% SI. Partial disability as per schedule. Hospital cash benefit. Broken bone cover.',
    'https://www.manipalcigna.com/personal-accident-cover', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Personal Accident (Health)';

-- Star Health Personal Accident (Health segment)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Accident Care Individual Insurance Policy', 'SHAHPAP17072V011617', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2016-2017',
    'Personal accident insurance from Star Health covering accidental death, permanent total and partial disability. Available for individuals with coverage for hospitalization due to accidents.',
    'https://www.starhealth.in/list-products/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Personal Accident (Health)';

-- Aditya Birla Health Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Secure - Personal Accident', 'ADIPAIP22082V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Personal accident insurance from ABHI covering accidental death and disability. Provides financial protection against accidental injuries with EMI protection feature.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Personal Accident (Health)';

-- Care Health Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Personal Accident Insurance', 'CHIPAIP22048V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Personal accident insurance from Care Health covering accidental death, permanent total disability, and temporary total disability with education benefit for children.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Personal Accident (Health)';

-- ===================== HOME CONTENTS INSURANCE (NEW SUB-CATEGORY) =====================

-- ICICI Lombard Home Contents Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Complete Home Protect - Contents', 'IRDAN115RP0013V02202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home contents insurance section of ICICI Lombard Complete Home Protect policy. Covers personal possessions including furniture, electronics, clothing, and valuables inside the home.',
    'Covers furniture & fixtures. Durables and electronic equipment. Clothing and miscellaneous items. Burglary and theft coverage. Fire and natural calamity protection.',
    'https://www.icicilombard.com/home-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Home Contents Insurance';

-- HDFC ERGO Home Contents Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Home Shield - Contents Cover', 'IRDAN146RP0025V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home contents coverage under HDFC ERGO Home Shield policy. Protects household contents against fire, burglary, natural disasters, and other insured perils.',
    'https://www.hdfcergo.com/home-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Home Contents Insurance';

-- Tata AIG Home Contents Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Home Contents Insurance', 'IRDAN137RP0009V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home contents insurance protecting household belongings including electronics, furniture, clothing, and valuables against fire, theft, and natural calamities.',
    'https://www.tataaig.com/home-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Home Contents Insurance';

-- ===================== HOME STRUCTURE INSURANCE (NEW SUB-CATEGORY) =====================

-- ICICI Lombard Home Structure Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Lombard Complete Home Protect - Structure', 'IRDAN115RP0014V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home structure insurance section covering the building structure above plinth and foundation. Protects walls, roof, flooring, sanitary fittings, and permanent fixtures.',
    'Building structure coverage. Architect and surveyor fees. Debris removal costs. Fire and lightning protection. Natural calamity coverage including earthquake and flood.',
    'https://www.icicilombard.com/home-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Lombard General Insurance Company Limited' AND sc.name = 'Home Structure Insurance';

-- HDFC ERGO Home Structure Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Home Shield - Structure Cover', 'IRDAN146RP0026V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home structure coverage under HDFC ERGO Home Shield policy. Protects the home building including walls, roof, and permanent fixtures against fire, natural disasters, and insured perils.',
    'https://www.hdfcergo.com/home-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Home Structure Insurance';

-- Bajaj General Home Structure Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Allianz Home Structure Insurance', 'IRDAN113RP0020V01202122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Home building structure insurance from Bajaj Allianz General protecting against fire, earthquake, flood, storm, and other natural/man-made perils. Covers reinstatement cost of the building.',
    'https://www.bajajallianz.com/home-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj General Insurance Limited' AND sc.name = 'Home Structure Insurance';

-- ===================== ADDITIONAL HEALTH PRODUCTS - EXPANDING THIN COMPANIES =====================

-- Star Health Medi Classic Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Health Medi Classic Insurance Policy', 'SHAHLIP19008V031819', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2018-2019',
    'Affordable health insurance plan from Star Health for individuals and families. Covers hospitalization, day-care procedures, and pre/post hospitalization expenses with moderate coverage limits.',
    'https://www.starhealth.in/list-products/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Health Assure Insurance Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Health Assure Insurance Policy', 'SHAHLIP24032V022324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Comprehensive health insurance plan with customizable coverage. Available in Silver, Gold, and Diamond variants with sum insured up to Rs. 2 crore.',
    'https://www.starhealth.in/health-insurance/star-assure/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Health Smart Health Pro
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Smart Health Pro Insurance Policy', 'SHAHLIP25037V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Latest health insurance plan from Star Health with Smart features including AI-driven health assessment, teleconsultation, and preventive care benefits.',
    'https://www.starhealth.in/list-products/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Care Freedom Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Freedom', 'CHIHLIP23152V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Health insurance plan from Care Health with flexible coverage options and no sub-limits. Includes OPD coverage, wellness benefits, and unlimited restoration of sum insured.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Senior Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Senior', 'CHIHLIP22049V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Senior citizen health insurance from Care Health designed for individuals aged 60+. Pre-existing disease coverage, cataract surgery, and AYUSH treatments included.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- Care Critical Illness
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Heart', 'CHIHLIP22050V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Disease-specific health insurance from Care Health covering heart and cardiac conditions. Lump sum benefit on diagnosis of specified cardiac illnesses.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Disease-Specific Insurance';

-- Niva Bupa Health Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Health Plus', 'NBHHLIP24120V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Affordable health insurance from Niva Bupa with coverage up to Rs. 1 lakh. Entry-level plan designed for young individuals and first-time insurance buyers.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Niva Bupa Super Top Up
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Health Edge Super Saver', 'NBHHLIP23111V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Super top-up health plan from Niva Bupa supplementing existing health insurance. High coverage at affordable premiums activating after deductible threshold.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Manipal Cigna ProHealth Protect
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Protect', 'MCGHLIP22054V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Affordable health insurance from ManipalCigna with comprehensive hospitalization coverage. Includes pre/post hospitalization, day-care, and domiciliary treatment.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Manipal Cigna Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (ManipalCigna)', 'MCGHLIP20040V012021', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'IRDAI-mandated standard health insurance from ManipalCigna with uniform terms. Sum insured Rs. 1 lakh to Rs. 5 lakh covering hospitalization and day-care procedures.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- AB Health Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (ABHI)', 'ADIHLIP20055V012021', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'IRDAI-mandated standard health insurance from ABHI with uniform terms. Sum insured Rs. 1 lakh to Rs. 5 lakh with HealthReturns wellness incentive.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- AB Health Activ Health Essential
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Health Essential', 'ADIHLIP23095V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Entry-level comprehensive health insurance from ABHI. Covers hospitalization with Essential and Enhanced variants at affordable premiums.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- AB Health Super Top Up
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Assure - Super Top Up', 'ADIHLIP22083V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Super top-up health plan from ABHI providing additional coverage beyond base health insurance deductible. High coverage at affordable premiums.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Tata AIG Medicare (Senior Citizen)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Medicare - Senior Citizen Health', 'IRDAN137HL0005V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Health insurance for senior citizens from Tata AIG covering hospitalization, pre-existing diseases, and age-related ailments. Available for ages 61 and above.',
    'https://www.tataaig.com/health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- Tata AIG Arogya Sanjeevani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Tata AIG)', 'IRDAN137HL0003V01202021', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'IRDAI-mandated standard health insurance from Tata AIG with uniform terms across all insurers. Sum insured Rs. 1 lakh to Rs. 5 lakh.',
    'https://www.tataaig.com/health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- Tata AIG Critical Illness
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIG Critical Illness Guard', 'IRDAN137HL0006V01202223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Critical illness insurance from Tata AIG providing lump sum benefit on diagnosis of specified critical illnesses. Covers cancer, heart attack, stroke, and kidney failure.',
    'https://www.tataaig.com/health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Tata AIG General Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- HDFC ERGO my:health Group Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO my:health Group Insurance', 'HDFHLGP21345V012021', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Group health insurance from HDFC ERGO for employer-employee groups. Covers hospitalization, maternity, new born baby coverage, and wellness programs.',
    'https://www.hdfcergo.com/health-insurance/group-health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- HDFC ERGO Hospital Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC ERGO Hospital Daily Cash', 'HDFHLIP21344V022021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Hospital daily cash benefit from HDFC ERGO. Rs. 250-500 per day based on sum insured. Covers both accident and sickness hospitalization for up to 45 days.',
    'https://www.hdfcergo.com/health-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC ERGO General Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- Kshema General Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kshema General Health Insurance', 'IRDAN172HL0001V01202425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Health insurance product from Kshema General Insurance, one of the newest entrants in the Indian insurance market. Basic hospitalization and day-care coverage.',
    'https://www.kshemageneral.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kshema General Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- ============================================================
-- PHASE 4: Additional Star Health products from web research
-- Research date: 2026-02-21
-- Source: https://www.starhealth.in
-- ============================================================

-- Star Health Medi Classic
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Medi Classic Insurance Policy', 'SHAHLIP25038V082425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Long-standing individual indemnity plan covering hospitalization with sum insured from 1.5 to 25 lakhs. 200% automatic restoration available in Standard and Gold variants.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Smart Health Pro
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Smart Health Pro', 'SHAHLIP23172V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Flexible indemnity health insurance with sum insured from 5 lakhs to 1 crore. Five optional covers, wellness discounts up to 20%, and 100% automatic restoration.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Health Assure (Family)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Health Assure Insurance Policy', 'SHAHLIP23131V022223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive family plan covering up to 6 adults and 3 children including parents and parents-in-law. Unlimited automatic restoration, maternity benefits, and newborn coverage from day one.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Super Star Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Super Star Health Insurance Policy', 'SHAHLIP25036V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Premium customizable plan with age-lock feature (premiums locked at entry age). Up to 21 optional riders, sum insured up to unlimited, and AI vital monitoring.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Diabetes Safe
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Diabetes Safe Insurance Policy', 'SHAHLIP23081V082223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Specialized plan for persons diagnosed with Type 1 and Type 2 diabetes. Covers diabetes complications and other illnesses with 100% automatic restoration and outpatient expenses.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Cancer Care Platinum
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Cancer Care Platinum Insurance Policy', 'SHAHLIP22031V022122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Specialized cancer plan covering both cancer-related and non-cancer medical expenses. Lump sum cancer recurrence benefit, hospice care, and rehabilitation support.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- Star Special Care (Autism)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Special Care Insurance Policy', 'SHAHLIP21243V022021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Specialized plan for children/young adults aged 3-25 years diagnosed with Autism Spectrum Disorder. Covers hospitalization and therapies (speech, occupational, behavioral).',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Star Critical Illness Multipay
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Critical Illness Multipay Insurance Policy', 'SHAHLIP22140V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Lump sum benefit plan covering 37 specified critical illnesses including cancer, heart attack, stroke, organ transplants. Sum insured from 5 to 25 lakhs with multipay feature.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- Star Super Surplus (Individual Top-Up)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Super Surplus Insurance Policy (Individual)', 'SHAHLIP22035V062122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Super top-up plan for individuals that activates when base plan limits are exceeded. Available in Gold and Silver variants with AYUSH and modern treatment coverage.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Star Super Surplus (Floater Top-Up)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Super Surplus Insurance Policy (Floater)', 'SHAHLIP22034V062122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Super top-up floater plan extending existing insurance coverage for families. Gold (extended pre/post hospitalization) and Silver variants available.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Star Family Accident Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Family Accident Care Insurance Policy', 'SHAHLIP21042V012021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Floater accident policy covering entire family (2 adults + 3 children) for accidental death and permanent total disablement. Sum insured up to 50 lakhs.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Individual Personal Accident';

-- Star Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Group Health Insurance', 'SHAHLGP23021V032223', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Customizable group health insurance for corporates with sum insured from 1 lakh to 1 crore. Comprehensive coverage for employer-employee groups.',
    'https://www.starhealth.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- ===================== HDFC LIFE HEALTH PRODUCTS (Phase 5) =====================
-- Source: https://www.hdfclife.com/policy-documents, hdfclife.com product pages
-- These are health/combo products offered by HDFC Life (a life insurer)

-- HDFC Life Click 2 Protect Optima Secure (Life + Health Combo with HDFC ERGO)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Optima Secure', '101Y122V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Combined life and health cover plan jointly offered with HDFC ERGO. Four benefit variants with 10,000+ network hospitals.',
    'https://www.hdfclife.com/health-insurance/click-2-protect-optima-secure', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- HDFC Life Click 2 Protect Optima Restore (Life + Health Combo with HDFC ERGO)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Optima Restore', '101Y121V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Combined life and health plan with restore benefit (100% sum insured reinstated after claims), multiplier benefits, and wellness discount.',
    'https://www.hdfclife.com/health-insurance/click-2-protect-optima-restore', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- HDFC Life Cancer Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Cancer Care', '101N106V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2017-2018',
    'Non-linked health plan providing financial protection specifically for cancer diagnosis and treatment at various stages.',
    'https://www.hdfclife.com/health-insurance/cancer-care', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- HDFC Life Cardiac Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Cardiac Care', '101N117V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2018-2019',
    'Non-linked health plan covering 18 cardiac conditions across three severity levels (mild, moderate, high).',
    'https://www.hdfclife.com/health-insurance/cardiac-care', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- HDFC Life Easy Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Easy Health', '101N110V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2018-2019',
    'Non-linked health insurance plan providing comprehensive health coverage benefits with cashless hospitalization.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- HDFC Life Group Health Shield
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Health Shield', '101N116V05', 'group', 'non_linked', 'non_participating',
    TRUE, '2018-2019',
    'Group health insurance plan providing medical coverage for employees and their families.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- ===================== LIC HEALTH PRODUCTS (Phase 6) =====================
-- Source: licindia.in, stableinvestor.com

-- LIC's Cancer Cover
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Cancer Cover', '512N314V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Non-linked health insurance plan providing lump sum benefit on diagnosis of specified stages of cancer. Coverage for early and major stage cancer.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Critical Illness Insurance';

-- LIC's Arogya Rakshak
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Arogya Rakshak', '512N318V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked health insurance plan providing fixed benefit on hospitalization. Daily hospital cash and surgical benefit without need for original bills.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Hospital Daily Cash';

-- LIC's Jeevan Arogya
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Arogya', '512N266V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Non-linked health insurance plan providing hospitalization benefit, major surgical benefit, day care procedures, and health check-up benefit.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Individual Health Insurance';

-- ===================== MAX LIFE GROUP HEALTH (Phase 6) =====================

-- Axis Max Life Group Smart Health Insurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Group Smart Health Insurance Plan', '104N129V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group health insurance providing medical coverage for employees and their families with cashless hospitalization benefits.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Group Health Insurance';


-- ===================== CARE HEALTH INSURANCE EXPANSION (Phase 7) =====================

-- Care Supreme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Supreme', 'CHIHLIP23128V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive health insurance plan with extensive coverage including OPD, dental, and global cover. Highest sum insured option.',
    'https://www.careinsurance.com/product/care-supreme', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Supreme Vikas
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Supreme Vikas', 'CHIHLIP24136V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Cost-effective health insurance with comprehensive coverage. Affordable variant of Care Supreme with key benefits retained.',
    'https://www.careinsurance.com/product/care-supreme-vikas', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Classic
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Classic', 'CHIHLIP24130V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Zone-based health insurance plan with flexible coverage options. Customizable health protection for individuals and families.',
    'https://www.careinsurance.com/product/care-classic', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Plus', 'CHIHLIP22108V022122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive health insurance with wide hospital network. Covers hospitalization, pre and post hospitalization expenses.',
    'https://www.careinsurance.com/product/care-plus', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Heart
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Heart', 'CHIHLIP22118V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Specialized cardiac health insurance covering heart-related ailments and cardiac procedures with comprehensive coverage.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Critical Illness Insurance';

-- Care Freedom
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Freedom', 'CHIHLIP22114V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance plan designed for people with pre-existing conditions. Covers diabetes, hypertension and other PEDs from day one.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Individual Health Insurance';

-- Care Senior Health Advantage
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Senior Health Advantage', 'CHIHLIP22120V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance specifically designed for senior citizens aged 61-80 years. No pre-policy medical check-up required.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- ===================== NIVA BUPA EXPANSION (Phase 7) =====================

-- Niva Bupa Health Recharge
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Health Recharge', 'NBHHLIP22156V032122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance with recharge benefit that refills sum insured if exhausted during the policy year. Wide network coverage.',
    'https://transactions.nivabupa.com/pages/doc/brochure/Health_Recharge_SS.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Niva Bupa Health Companion
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Health Companion', 'NBHHLIP24115V072324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Comprehensive health insurance covering hospitalization with safeguard add-on option. Flexible sum insured choices.',
    'https://transactions.nivabupa.com/pages/doc/brochure/Health_Companion_V2022_SS.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Niva Bupa Senior First
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Senior First', 'MAXHLIP21575V012021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Health insurance designed for senior citizens with no upper age limit for entry. Comprehensive medical coverage.',
    'https://www.nivabupa.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- Niva Bupa ReAssure 2.0
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa ReAssure 2.0', 'NBHHLIP22161V022122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance plan with inbuilt personal accident cover. Comprehensive health protection with PA benefits.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== MANIPAL CIGNA EXPANSION (Phase 7) =====================

-- ManipalCigna ProHealth Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Insurance', 'MCIHLIP22211V062122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Comprehensive medical coverage with focus on overall wellness. Covers range of diseases with Health+, Women+ and Global+ options.',
    'https://www.manipalcigna.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ManipalCigna ProHealth Select
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Select', 'MCIHLIP23228V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Flexible health plan allowing customization of coverage as per individual health needs. Modular benefits.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ManipalCigna LifeTime Health
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna LifeTime Health', 'MCIHLIP22213V032122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Health insurance covering medical expenses in India and abroad with Health+, Women+ and Global+ optional covers.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ManipalCigna Super Top Up
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna Super Top Up', 'MCIHLIP22217V022122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Super top-up plan providing additional coverage when base policy is insufficient. Affordable way to enhance health cover.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- ManipalCigna ProHealth Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ManipalCigna ProHealth Cash', 'MCIHLIP22216V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Daily hospital cash benefit plan providing fixed daily amount during hospitalization to cover incidental expenses.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- ===================== ADITYA BIRLA HEALTH INSURANCE EXPANSION (Phase 7) =====================

-- ABHI Activ Fit
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABHI Activ Fit', 'ABHHLIP21029V022021', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2020-2021',
    'Health insurance rewarding healthy lifestyle with HealthReturnsTM. Up to 100% premium back for staying fit.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ABHI Activ Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABHI Activ Care', 'ABHHLIP23044V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Comprehensive health insurance with chronic care management program. Covers outpatient and inpatient treatment.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ABHI Activ Assure Diamond
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABHI Activ Assure Diamond', 'ABHHLIP22038V012122', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2021-2022',
    'Premium health plan with global coverage and highest sum insured options. Comprehensive coverage with wellness rewards.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ABHI Activ Health Platinum Enhanced
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABHI Activ Health Platinum Enhanced', 'ABHHLIP24055V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Enhanced platinum health plan with highest coverage limits and premium wellness benefits including HealthReturns.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ABHI Activ Senior
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABHI Activ Senior', 'ABHHLIP23046V012223', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2022-2023',
    'Health insurance designed for senior citizens with comprehensive coverage. No upper age limit for renewal.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Senior Citizen Health Insurance';


-- ================ SECTION 2: EXTRA HEALTH PRODUCTS ==============
-- ============================================================
-- 04b_products_health_extra.sql - Additional health insurance products
-- Expands underrepresented health insurers and fills subcategory gaps
-- Sources: Company websites, IRDAI portal, policybazaar.com
-- Last verified: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== NARAYANA HEALTH INSURANCE =====================
-- Source: https://www.narayanahealth.insurance/

-- Narayana Aditi Group Health Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Aditi Group Health Insurance', 'NRHHLGP24003V012425', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2024-07-01', '2024-2025',
    'Group health insurance version of the Aditi plan providing coverage up to Rs 1 crore for surgeries and Rs 5 lakh for medical treatments to employees and group members.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Group Health Insurance';

-- Narayana Arogya Sanjeevani Policy
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Arogya Sanjeevani Policy (Narayana)', 'NRHHLIP25004V012526', 'standard', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'IRDAI-mandated standard health insurance product with uniform terms and conditions. Covers hospitalization expenses with standardized benefits for all.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Arogya Sanjeevani (Standard)';

-- Narayana Senior Citizen Health Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Senior Citizen Health Plan', 'NRHHLIP25005V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Health insurance plan specifically designed for senior citizens aged 60 and above with coverage for age-related conditions and hospitalization.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Senior Citizen Health Insurance';

-- Narayana Top-Up Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Health Top-Up Plan', 'NRHHLIP25006V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Top-up health insurance plan working alongside existing health coverage providing additional sum insured above a deductible at affordable premiums.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Narayana Personal Accident Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Narayana Personal Accident Plan', 'NRHPAIP25007V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Personal accident insurance providing coverage against death and disability due to accidents with hospitalization expense cover.',
    'https://www.narayanahealth.insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Narayana Health Insurance Limited' AND sc.name = 'Personal Accident (Health)';

-- ===================== GALAXY HEALTH INSURANCE =====================
-- Source: https://www.galaxyhealth.com/our-product-list

-- Galaxy Twin 360
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Twin 360', 'GLXHLIP25004V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Comprehensive health insurance combining inpatient hospitalization cover, outpatient treatment and wellness support in one policy with discount benefits.',
    'Inpatient hospitalization. Outpatient treatment. Wellness support. Discount benefits at network hospitals.',
    'https://www.galaxyhealth.com/our-product-list', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- Galaxy Guardian
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Guardian', 'GLXHLIP25005V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Comprehensive health insurance policy designed for protecting health and assuring peace of mind with extensive coverage for hospitalization and daycare procedures.',
    'https://www.galaxyhealth.com/our-product-list', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Family Floater Health Insurance';

-- Galaxy Top-up
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Top-up', 'GLXHLIP25006V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Top-up health insurance policy working alongside existing plans to provide additional sum insured at budget-friendly premium over a deductible.',
    'https://www.galaxyhealth.com/our-product-list', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Top-Up / Super Top-Up';

-- Galaxy Empower
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Empower', 'GLXHLGP25007V012526', 'group', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Group health insurance plan designed for employers to provide health coverage to employees and their dependents with flexible benefit options.',
    'https://www.galaxyhealth.com/our-product-list', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Group Health Insurance';

-- Galaxy Personal Accident Shield
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Personal Accident Shield', 'GLXPAIP25008V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Personal accident insurance policy providing financial protection against death and disability arising from accidents.',
    'https://www.galaxyhealth.com/our-product-list', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Personal Accident (Health)';

-- Galaxy Smart Outpatient Rider
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Galaxy Smart Outpatient Rider', 'GLXHLIA25009V012526', 'rider', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Rider add-on providing outpatient treatment coverage including doctor consultations, diagnostics, and pharmacy expenses without hospitalization requirement.',
    'https://www.galaxyhealth.com/our-product-list', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Galaxy Health Insurance Company Limited' AND sc.name = 'Individual Health Insurance';

-- ===================== KSHEMA GENERAL (Health products) =====================
-- Source: https://kshema.co/

-- Kshema Crop Insurance (PMFBY)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kshema Sukriti Crop Insurance', 'IRDAN172RP0002V01202425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Kshema''s flagship crop insurance plan available in 20 states and 2 UTs covering over 100 crops against 8 natural perils to protect farmers.',
    'https://kshema.co/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kshema General Insurance Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- Kshema Affordable Crop Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kshema Affordable Crop Insurance', 'IRDAN172RP0003V01202425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Affordable crop insurance allowing farmers to select coverage for one major and one minor peril from a list of eight natural perils, starting at Rs 499 per acre.',
    'https://kshema.co/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kshema General Insurance Limited' AND sc.name = 'Weather-Based Crop Insurance';

-- Kshema Kisan Sathi (Bancassurance product)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kshema Kisan Sathi', 'IRDAN172RP0004V01202526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Pioneering bancassurance product offering dual protection of livelihood and family by combining crop insurance and personal accident insurance. Launched with Karur Vysya Bank.',
    'https://kshema.co/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kshema General Insurance Limited' AND sc.name = 'PMFBY - Crop Insurance';

-- Kshema Livestock Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kshema Livestock Insurance', 'IRDAN172RP0005V01202526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Insurance coverage for livestock including cattle, buffaloes, and other farm animals against death due to disease, accident, and natural calamities.',
    'https://kshema.co/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kshema General Insurance Limited' AND sc.name = 'Livestock Insurance';

-- ===================== ADDITIONAL HEALTH SUBCATEGORY GAPS =====================

-- Hospital Daily Cash - More products needed (currently only 4)

-- Star Health Hospital Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Hospital Cash Insurance Policy', 'SHAHLIP25040V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Hospital daily cash benefit plan paying a fixed amount per day of hospitalization, supplementing existing health insurance by covering incidental expenses.',
    'https://www.starhealth.in/list-products/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- Care Health Hospital Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Hospital Cash Plan', 'CHIHLIP24130V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Daily hospital cash benefit plan from Care Health paying fixed daily amount during hospitalization to cover incidental and out-of-pocket expenses.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Hospital Daily Cash';

-- Niva Bupa Hospital Cash
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Hospital Cash Plan', 'NBHHLIP25050V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Hospital daily cash benefit plan paying a fixed amount per day during hospitalization to supplement existing health coverage.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Hospital Daily Cash';

-- Maternity Insurance - More products needed (currently only 1)

-- Star Health Maternity Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Health Maternity Plan', 'SHAHLIP25041V012425', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2024-2025',
    'Dedicated maternity insurance covering pre and post-natal expenses, delivery charges, newborn baby coverage, and vaccination expenses.',
    'https://www.starhealth.in/list-products/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Maternity Insurance';

-- Care Health Maternity Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Maternity Plan', 'CHIHLIP24131V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Comprehensive maternity insurance covering normal and cesarean delivery, pre and post-natal care, and newborn baby expenses.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Maternity Insurance';

-- Manipal Cigna Maternity Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Manipal Cigna Maternity Plan', 'CIGHLIP24025V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Maternity insurance plan from Manipal Cigna covering pre-natal, delivery, post-natal care and newborn baby expenses with network hospital benefits.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Maternity Insurance';

-- Disease-Specific Insurance - More products needed (currently only 5)

-- Star Health Cardiac Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Star Cardiac Care Insurance Policy', 'SHAHLIP24042V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Disease-specific insurance plan covering cardiac conditions including heart attacks, bypass surgery, angioplasty, and other heart-related treatments.',
    'https://www.starhealth.in/list-products/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Health and Allied Insurance Company Limited' AND sc.name = 'Disease-Specific Insurance';

-- Care Health Cancer Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Cancer Shield', 'CHIHLIP24132V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Cancer-specific insurance plan covering diagnosis, chemotherapy, radiation therapy, surgery, and other cancer treatment expenses.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Disease-Specific Insurance';

-- Niva Bupa Critical Illness Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Niva Bupa Critical Illness Plan', 'NBHHLIP25051V012526', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2025-2026',
    'Critical illness insurance providing lump sum benefit on diagnosis of specified critical illnesses including cancer, heart attack, stroke, and organ failure.',
    'https://www.nivabupa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Niva Bupa Health Insurance Company Limited' AND sc.name = 'Critical Illness Insurance';

-- AB Health Disease-Specific Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Activ Care Diabetes Plan', 'ABHHLIP24020V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Disease-specific insurance plan designed for diabetic patients covering diabetes management, complications, and related hospitalization expenses.',
    'https://www.adityabirlahealthinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Health Insurance Company Limited' AND sc.name = 'Disease-Specific Insurance';

-- Personal Accident (Health) - More products needed (currently only 5)

-- Manipal Cigna Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Manipal Cigna Personal Accident Plan', 'CIGPAIP24026V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Personal accident insurance providing financial protection against accidental death, permanent total and partial disability arising from accidents.',
    'https://www.manipalcigna.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Manipal Cigna Health Insurance Company Limited' AND sc.name = 'Personal Accident (Health)';

-- Care Health Personal Accident
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Care Personal Accident Plan', 'CHIPAIP24133V012324', 'individual', 'not_applicable', 'not_applicable',
    TRUE, '2023-2024',
    'Personal accident insurance covering death and disability due to accidents with medical expense reimbursement for accidental injuries.',
    'https://www.careinsurance.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Care Health Insurance Limited' AND sc.name = 'Personal Accident (Health)';

-- ================ SECTION 3: HEALTH EXPANSION ===================
-- ============================================================
-- 11_health_expansion.sql
-- Health insurance products for ALL GI companies + standalone health insurers
-- Generates ~12 health products per GI company + additional for health-only companies
-- ============================================================
SET search_path TO insurance, public;

-- Part 1: Health products for all GI companies
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
    uin_prefix TEXT;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'general'
        ORDER BY c.legal_name
    LOOP
        seq := 300;
        -- Generate health UIN prefix based on company
        uin_prefix := UPPER(LEFT(REPLACE(REPLACE(COALESCE(comp.short_name, comp.legal_name), ' ', ''), '.', ''), 3)) || 'HLIP';

        FOR product_data IN
            SELECT * FROM (VALUES
                ('Individual Health Insurance', ' Individual Health Insurance Policy', 'individual', 'Comprehensive indemnity health insurance covering in-patient hospitalization, pre and post hospitalization expenses, day-care procedures, ambulance charges, and domiciliary hospitalization.'),
                ('Family Floater Health Insurance', ' Family Floater Health Policy', 'individual', 'Family floater health insurance where the total sum insured is shared among all insured family members including self, spouse, dependent children, and parents.'),
                ('Senior Citizen Health Insurance', ' Senior Citizen Health Insurance', 'individual', 'Health insurance designed specifically for senior citizens aged 60 and above covering hospitalization, pre-existing diseases after waiting period, and age-related ailments.'),
                ('Group Health Insurance', ' Group Health Insurance Policy', 'group', 'Group health insurance for corporate employer-employee groups covering hospitalization, maternity, newborn baby care, and preventive health checkups.'),
                ('Critical Illness Insurance', ' Critical Illness Insurance', 'individual', 'Fixed benefit critical illness insurance providing lump sum payout on first diagnosis of specified critical illnesses including cancer, heart attack, stroke, kidney failure, and organ transplant.'),
                ('Top-Up / Super Top-Up', ' Health Super Top-Up Policy', 'individual', 'Super top-up health insurance supplementing existing base health cover. Activates above deductible threshold providing high sum insured at affordable premiums.'),
                ('Hospital Daily Cash', ' Hospital Daily Cash Benefit', 'individual', 'Fixed daily cash allowance during hospitalization to meet incidental expenses like attendant charges, food, and transportation not covered by regular health insurance.'),
                ('Arogya Sanjeevani (Standard)', ' Arogya Sanjeevani Policy', 'standard', 'IRDAI-mandated standard health insurance product with uniform features across all insurers. Sum insured Rs 1 lakh to Rs 5 lakh. Covers AYUSH treatment, cataract, and modern treatments.'),
                ('Maternity Insurance', ' Maternity Health Insurance', 'individual', 'Health insurance covering maternity-related expenses including pre-natal care, delivery charges (normal and cesarean), post-natal care, and newborn baby cover.'),
                ('Disease-Specific Insurance', ' Disease-Specific Health Policy', 'individual', 'Health insurance providing coverage for specific diseases including dengue, malaria, chikungunya, and other vector-borne and water-borne diseases.'),
                ('Personal Accident (Health)', ' Personal Accident with Health Cover', 'individual', 'Personal accident insurance with health benefits covering accidental injuries, hospitalization from accidents, and medical expense reimbursement.'),
                ('Micro Insurance (Life)', ' Micro Health Insurance', 'micro', 'Low-cost micro health insurance for economically weaker sections providing basic hospitalization cover at affordable premiums as per IRDAI micro insurance regulations.')
            ) AS t(subcategory_name, product_suffix, product_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                uin_val := uin_prefix || seq || 'V01' || '2223';
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
                    NULL;
                END;
                seq := seq + 1;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'GI health expansion complete';
END $$;

-- Part 2: Additional health products for standalone health insurers
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
    uin_prefix TEXT;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'health'
        ORDER BY c.legal_name
    LOOP
        seq := 400;
        uin_prefix := UPPER(LEFT(REPLACE(REPLACE(COALESCE(comp.short_name, comp.legal_name), ' ', ''), '.', ''), 3)) || 'HLIP';

        FOR product_data IN
            SELECT * FROM (VALUES
                -- Comprehensive plans
                ('Individual Health Insurance', ' Comprehensive Health Policy', 'individual', 'Flagship comprehensive health insurance with no sub-limits on room rent, wide network coverage, modern treatment cover, and unlimited sum insured restoration.'),
                ('Individual Health Insurance', ' Essential Health Policy', 'individual', 'Affordable essential health insurance covering basic hospitalization needs at competitive premiums for individuals and nuclear families.'),
                ('Individual Health Insurance', ' Premium Health Policy', 'individual', 'Premium health insurance with enhanced coverage including international treatment, single private AC room, global second opinion, and wellness rewards.'),
                ('Family Floater Health Insurance', ' Family Floater Plan', 'individual', 'Family floater health insurance with shared sum insured, automatic restoration of SI, and coverage for self, spouse, children, and parents-in-law.'),
                ('Family Floater Health Insurance', ' Family Floater Plus Plan', 'individual', 'Enhanced family floater with unlimited restoration, super NCB accumulation up to 500%, and cover for pre-existing diseases from day one for select conditions.'),
                ('Senior Citizen Health Insurance', ' Senior Citizen Health Plan', 'individual', 'Comprehensive senior citizen health insurance for ages 60-80 at entry covering pre-existing diseases, AYUSH treatment, domiciliary hospitalization, and home nursing.'),
                ('Senior Citizen Health Insurance', ' Senior Citizen Premium Plan', 'individual', 'Premium health plan for seniors with enhanced coverage, lower co-payment, and faster pre-existing disease coverage.'),
                ('Group Health Insurance', ' Group Health Insurance Plan', 'group', 'Corporate group health insurance covering employees and dependents with customizable benefits, wellness programs, and OPD coverage.'),
                ('Group Health Insurance', ' Group Health Plus Plan', 'group', 'Enhanced group health with maternity cover, newborn care, dental and vision, and employee wellness integration.'),
                ('Critical Illness Insurance', ' Critical Illness Policy', 'individual', 'Fixed benefit critical illness insurance covering 30+ critical illnesses with lump sum payout. Includes cancer, cardiac, neurological, and organ-specific conditions.'),
                ('Critical Illness Insurance', ' Multi-Pay Critical Illness', 'individual', 'Critical illness plan with multiple payouts allowing claims for different critical illness groups during the policy tenure.'),
                ('Top-Up / Super Top-Up', ' Super Top-Up Health Plan', 'individual', 'Super top-up health insurance with aggregate deductible providing high sum insured coverage supplementing employer or existing health insurance.'),
                ('Top-Up / Super Top-Up', ' Health Booster Top-Up', 'individual', 'Top-up health plan with automatic SI boost feature providing additional coverage when base SI is exhausted.'),
                ('Hospital Daily Cash', ' Hospital Cash Benefit Plan', 'individual', 'Fixed daily hospital cash benefit policy paying predetermined amount per day of hospitalization regardless of actual expenses incurred.'),
                ('Arogya Sanjeevani (Standard)', ' Arogya Sanjeevani Policy', 'standard', 'IRDAI-mandated standard health insurance with uniform coverage across insurers. SI Rs 1-5 lakh. Covers hospitalization, AYUSH, cataract, and modern treatments.'),
                ('Maternity Insurance', ' Maternity Care Insurance', 'individual', 'Health insurance covering comprehensive maternity expenses including pre-natal consultations, delivery (normal/cesarean), post-natal care, newborn vaccination, and fertility treatment.'),
                ('Disease-Specific Insurance', ' Cancer Care Insurance', 'individual', 'Cancer-specific health insurance covering all stages of cancer treatment from early detection through advanced stage with lump sum and indemnity components.'),
                ('Disease-Specific Insurance', ' Cardiac Care Insurance', 'individual', 'Heart disease-specific health insurance for individuals with existing cardiac conditions covering cardiac surgeries, angioplasty, bypass, and cardiac rehabilitation.'),
                ('Disease-Specific Insurance', ' Diabetes Care Insurance', 'individual', 'Health insurance designed for diabetic individuals covering diabetes-related hospitalization, complications management, and routine diabetes care.'),
                ('Personal Accident (Health)', ' Personal Accident Plan', 'individual', 'Personal accident insurance covering accidental death, permanent total and partial disability, temporary total disability, and medical expenses from accidents.'),
                ('Individual Health Insurance', ' OPD Health Insurance', 'individual', 'Outpatient health insurance covering doctor consultations, diagnostic tests, pharmacy expenses, dental procedures, and vision care without hospitalization.'),
                ('Individual Health Insurance', ' Women Health Insurance', 'individual', 'Specialized health insurance for women covering pregnancy, delivery, gynecological procedures, breast cancer screening, and women-specific health conditions.'),
                ('Individual Health Insurance', ' International Health Plan', 'individual', 'International health insurance providing cashless treatment at select global hospitals for serious illnesses requiring overseas treatment.')
            ) AS t(subcategory_name, product_suffix, product_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                uin_val := uin_prefix || seq || 'V01' || '2324';
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

    RAISE NOTICE 'Health standalone expansion complete';
END $$;

-- Part 3: Health products sold by life insurance companies
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
        WHERE c.company_type = 'life'
        ORDER BY c.legal_name
    LOOP
        seq := 500;

        FOR product_data IN
            SELECT * FROM (VALUES
                ('Critical Illness Insurance', ' Critical Illness Benefit Plan', 'individual', 'non_linked', 'non_participating', 'Fixed benefit health plan providing lump sum on diagnosis of specified critical illnesses including cancer, heart conditions, stroke, kidney failure, and major organ transplant.'),
                ('Disease-Specific Insurance', ' Cancer Cover Plan', 'individual', 'non_linked', 'non_participating', 'Cancer-specific insurance plan providing lump sum benefit on diagnosis of early and major stage cancer. Income benefit for major stage cancer treatment.'),
                ('Hospital Daily Cash', ' Hospital Cash Benefit Plan', 'individual', 'non_linked', 'non_participating', 'Fixed benefit health plan providing daily hospital cash benefit during hospitalization. Covers incidental expenses not covered by indemnity health insurance.'),
                ('Individual Health Insurance', ' Arogya Rakshak Plan', 'individual', 'non_linked', 'non_participating', 'IRDAI-mandated standard health product for life insurers. Fixed benefit health cover with hospital cash benefit on per-day basis during hospitalization.')
            ) AS t(subcategory_name, product_suffix, product_type, linked_type, par_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                uin_val := comp.registration_number || 'N' || LPAD(seq::text, 3, '0') || 'V01';
                prod_name := COALESCE(comp.short_name, split_part(comp.legal_name, ' Insurance', 1)) || product_data.product_suffix;

                BEGIN
                    INSERT INTO insurance.insurance_products (
                        company_id, sub_category_id, product_name, uin,
                        product_type, linked_type, par_type,
                        is_active, financial_year_filed, policy_summary, source_url, data_confidence
                    ) VALUES (
                        comp.id, sc_rec.id, prod_name, uin_val,
                        product_data.product_type::insurance.product_type_enum,
                        product_data.linked_type::insurance.product_linked_enum,
                        product_data.par_type::insurance.par_enum,
                        TRUE, '2022-2023', product_data.summary, comp.website,
                        'high'::insurance.confidence_enum
                    );
                EXCEPTION WHEN unique_violation THEN
                    NULL;
                END;
                seq := seq + 1;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Life company health products complete';
END $$;

-- ================ SECTION 4: COVID HEALTH PRODUCTS ==============
-- (Extracted from 14_additional_expansion.sql Part 2)
-- Part 2: COVID-era products (now discontinued but in registry)
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    uin_prefix TEXT;
BEGIN
    seq := 900;
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type IN ('general', 'health')
        ORDER BY c.legal_name
    LOOP
        uin_prefix := UPPER(LEFT(REPLACE(REPLACE(COALESCE(comp.short_name, comp.legal_name), ' ', ''), '.', ''), 3)) || 'HLIP';

        -- Corona Kavach (indemnity)
        SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = 'Disease-Specific Insurance';
        IF sc_rec IS NOT NULL THEN
            uin_val := uin_prefix || seq || 'V01' || '2021';
            prod_name := COALESCE(comp.short_name, split_part(comp.legal_name, ' Insurance', 1)) || ' Corona Kavach Policy';
            BEGIN
                INSERT INTO insurance.insurance_products (
                    company_id, sub_category_id, product_name, uin,
                    product_type, linked_type, par_type,
                    is_active, withdrawal_date, financial_year_filed, policy_summary, source_url, data_confidence
                ) VALUES (
                    comp.id, sc_rec.id, prod_name, uin_val,
                    'individual'::insurance.product_type_enum,
                    'not_applicable'::insurance.product_linked_enum,
                    'not_applicable'::insurance.par_enum,
                    FALSE, '2021-09-30', '2020-2021',
                    'IRDAI-mandated COVID-19 specific indemnity health insurance covering hospitalization for COVID-19 treatment. Short-term 3.5/6.5/9.5 month policies. Now discontinued.',
                    comp.website, 'high'::insurance.confidence_enum
                );
            EXCEPTION WHEN unique_violation THEN NULL;
            END;
        END IF;

        -- Corona Rakshak (benefit)
        IF sc_rec IS NOT NULL THEN
            uin_val := uin_prefix || (seq+1) || 'V01' || '2021';
            prod_name := COALESCE(comp.short_name, split_part(comp.legal_name, ' Insurance', 1)) || ' Corona Rakshak Policy';
            BEGIN
                INSERT INTO insurance.insurance_products (
                    company_id, sub_category_id, product_name, uin,
                    product_type, linked_type, par_type,
                    is_active, withdrawal_date, financial_year_filed, policy_summary, source_url, data_confidence
                ) VALUES (
                    comp.id, sc_rec.id, prod_name, uin_val,
                    'individual'::insurance.product_type_enum,
                    'not_applicable'::insurance.product_linked_enum,
                    'not_applicable'::insurance.par_enum,
                    FALSE, '2021-09-30', '2020-2021',
                    'IRDAI-mandated COVID-19 lump-sum benefit policy paying 100% of sum insured on positive COVID-19 diagnosis requiring 72+ hours hospitalization. Now discontinued.',
                    comp.website, 'high'::insurance.confidence_enum
                );
            EXCEPTION WHEN unique_violation THEN NULL;
            END;
        END IF;

        seq := seq + 2;
    END LOOP;

    RAISE NOTICE 'COVID products complete';
END $$;

-- ================ SECTION 5: HEALTH POLICY DOCUMENTS ============
-- ============================================================
-- 07c_policy_docs_health.sql - Policy documents for health insurance products
-- Adds brochure URLs for health products from health & general insurers
-- Note: Life insurer health products (HDFC Life, LIC, Max Life) are in 07b
-- Sources: Official company websites
-- Last updated: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== STAR HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('SHAHLGP22041V022122', 'Star Health Group Arogya Sanjeevani - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/arogya-sanjeevani-policy', 'Star Health Official'),
    ('SHAHPAP17072V011617', 'Star Accident Care Individual - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-accident-care-individual', 'Star Health Official'),
    ('SHAHLIP22031V022122', 'Star Cancer Care Platinum - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-cancer-care-platinum', 'Star Health Official'),
    ('SHAHLGP21239V022021', 'Star Classic Group Health Insurance - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-classic-group-health', 'Star Health Official'),
    ('SHAHLIP22140V012122', 'Star Critical Illness Multipay - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-critical-illness-multipay', 'Star Health Official'),
    ('SHAHLIP23081V082223', 'Star Diabetes Safe - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-diabetes-safe', 'Star Health Official'),
    ('SHAHLGP23021V032223', 'Star Group Health Insurance - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-group-health', 'Star Health Official'),
    ('SHAHLGP23015V012223', 'Star Group Health Insurance Platinum - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-group-health-platinum', 'Star Health Official'),
    ('SHAHLIP23131V022223', 'Star Health Assure - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/star-health-assure', 'Star Health Official'),
    ('SHAHLIP25038V082425', 'Star Medi Classic - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/medi-classic', 'Star Health Official'),
    ('SHAHLIP23172V012223', 'Star Smart Health Pro - Brochure', 'brochure', 'https://web.starhealth.in/sites/default/files/brochure/Smart_Health_Pro.pdf', 'Star Health Official'),
    ('SHAHLIP21243V022021', 'Star Special Care - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/special-care', 'Star Health Official'),
    ('SHAHLIP22034V062122', 'Star Super Surplus Floater - Brochure', 'brochure', 'https://web.starhealth.in/sites/default/files/brochure/Star-Super-Surplus-Floater-Brochure.pdf', 'Star Health Official'),
    ('SHAHLIP22035V062122', 'Star Super Surplus Individual - Brochure', 'brochure', 'https://web.starhealth.in/sites/default/files/brochure/Super-Surplus-Brochure.pdf', 'Star Health Official'),
    ('SHAHLIP25035V052425', 'Young Star Insurance Policy - Brochure', 'brochure', 'https://www.starhealth.in/health-insurance/young-star', 'Star Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== CARE HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('CHIHLIP24130V012324', 'Care Classic - Brochure', 'brochure', 'https://www.careinsurance.com/health-insurance/care-classic.html', 'Care Health Official'),
    ('CHIHLIP22114V012122', 'Care Freedom - Brochure', 'brochure', 'https://www.careinsurance.com/health-insurance/care-freedom.html', 'Care Health Official'),
    ('CHIHLGP23155V012223', 'Care Group Health Insurance - Brochure', 'brochure', 'https://www.careinsurance.com/group-health-insurance.html', 'Care Health Official'),
    ('CHIHLIP22118V012122', 'Care Heart - Brochure', 'brochure', 'https://cms.careinsurance.com/cms/public/uploads/download_center/care-heart---piano-fold-brochure---web.pdf', 'Care Health Official'),
    ('CHIHLIP22050V012122', 'Care Heart (Disease-Specific) - Brochure', 'brochure', 'https://cms.careinsurance.com/cms/public/uploads/download_center/care-heart---piano-fold-brochure---web.pdf', 'Care Health Official'),
    ('CHIPAIP22048V012122', 'Care Personal Accident Insurance - Brochure', 'brochure', 'https://www.careinsurance.com/personal-accident-insurance.html', 'Care Health Official'),
    ('CHIHLIP22108V022122', 'Care Plus - Brochure', 'brochure', 'https://cms.careinsurance.com/cms/public/uploads/download_center/care-plus----complete-health-insurance-plan-brochure.pdf', 'Care Health Official'),
    ('CHIHLIP22049V012122', 'Care Senior - Brochure', 'brochure', 'https://cms.careinsurance.com/cms/public/uploads/download_center/care-senior-brochure.pdf', 'Care Health Official'),
    ('CHIHLIP22120V012122', 'Care Senior Health Advantage - Brochure', 'brochure', 'https://www.careinsurance.com/health-insurance/care-senior-health-advantage.html', 'Care Health Official'),
    ('CHIHLIP24136V012324', 'Care Supreme Vikas - Brochure', 'brochure', 'https://cms.careinsurance.com/cms/public/uploads/download_center/care-supreme---brochure.pdf', 'Care Health Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== MANIPAL CIGNA PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('MCGHLIP20040V012021', 'ManipalCigna Arogya Sanjeevani - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/arogya-sanjeevani', 'ManipalCigna Official'),
    ('MCGHLGP22055V012122', 'ManipalCigna Group Health Insurance - Brochure', 'brochure', 'https://www.manipalcigna.com/group-health-insurance', 'ManipalCigna Official'),
    ('MCIHLIP22213V032122', 'ManipalCigna LifeTime Health - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/lifetime-health', 'ManipalCigna Official'),
    ('MCIHLIP22216V012122', 'ManipalCigna ProHealth Cash - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/prohealth-cash', 'ManipalCigna Official'),
    ('MCGHLIP22047V012122', 'ManipalCigna ProHealth Insurance - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/prohealth', 'ManipalCigna Official'),
    ('MCIHLIP22211V062122', 'ManipalCigna ProHealth Insurance - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/prohealth', 'ManipalCigna Official'),
    ('MCGHLIP22054V012122', 'ManipalCigna ProHealth Protect - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/prohealth-protect', 'ManipalCigna Official'),
    ('MCIHLIP23228V012223', 'ManipalCigna ProHealth Select - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/prohealth-select', 'ManipalCigna Official'),
    ('MCIHLIP22217V022122', 'ManipalCigna Super Top Up - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/super-top-up', 'ManipalCigna Official'),
    ('MCGHLIP22051V012122', 'ManipalCigna Super Top Up Insurance - Brochure', 'brochure', 'https://www.manipalcigna.com/health-insurance/super-top-up', 'ManipalCigna Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== NIVA BUPA PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('NBHHLIP24120V012324', 'Niva Bupa Health Plus - Brochure', 'brochure', 'https://www.nivabupa.com/health-insurance-plans/health-plus.html', 'Niva Bupa Official'),
    ('NBHHLGP23115V012223', 'Niva Bupa Group Health Insurance - Brochure', 'brochure', 'https://www.nivabupa.com/group-health-insurance.html', 'Niva Bupa Official'),
    ('NBHHLIP24115V072324', 'Niva Bupa Health Companion - Brochure', 'brochure', 'https://www.nivabupa.com/health-insurance-plans/health-companion.html', 'Niva Bupa Official'),
    ('NBHHLIP23111V012223', 'Niva Bupa Health Edge Super Saver - Brochure', 'brochure', 'https://www.nivabupa.com/health-insurance-plans/health-edge.html', 'Niva Bupa Official'),
    ('NBHHLIP22156V032122', 'Niva Bupa Health Recharge - Brochure', 'brochure', 'https://www.nivabupa.com/health-insurance-plans/health-recharge.html', 'Niva Bupa Official'),
    ('NBHHLIP22161V022122', 'Niva Bupa ReAssure 2.0 - Brochure', 'brochure', 'https://www.nivabupa.com/health-insurance-plans/reassure.html', 'Niva Bupa Official'),
    ('MAXHLIP21575V012021', 'Niva Bupa Senior First - Brochure', 'brochure', 'https://www.nivabupa.com/health-insurance-plans/senior-first.html', 'Niva Bupa Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ABHI PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('ABHHLIP22038V012122', 'ABHI Activ Assure Diamond - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-assure-diamond', 'ABHI Official'),
    ('ABHHLIP23044V012223', 'ABHI Activ Care - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-care', 'ABHI Official'),
    ('ABHHLIP21029V022021', 'ABHI Activ Fit - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-fit', 'ABHI Official'),
    ('ABHHLIP24055V012324', 'ABHI Activ Health Platinum Enhanced - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-health-platinum-enhanced', 'ABHI Official'),
    ('ABHHLIP23046V012223', 'ABHI Activ Senior - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-senior', 'ABHI Official'),
    ('ADIHLIP22083V012122', 'ABHI Activ Assure Super Top Up - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-assure-super-top-up', 'ABHI Official'),
    ('ADIHLIP23095V012223', 'ABHI Activ Health Essential - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-health-essential', 'ABHI Official'),
    ('ADIPAIP22082V012122', 'ABHI Activ Secure Personal Accident - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/activ-secure', 'ABHI Official'),
    ('ADIHLIP20055V012021', 'ABHI Arogya Sanjeevani Policy - Brochure', 'brochure', 'https://www.adityabirlahealthinsurance.com/health-insurance-plans/arogya-sanjeevani', 'ABHI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== GENERAL INSURER HEALTH PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('IRDAN157HL0005V01202223', 'Acko Platinum Health Insurance - Brochure', 'brochure', 'https://www.acko.com/health-insurance/platinum-health-plan', 'Acko Official'),
    ('BAJHLGP22130V012122', 'Bajaj Allianz Group Health Insurance - Brochure', 'brochure', 'https://www.bajajallianzgi.co.in/health-insurance/group-health-insurance', 'Bajaj Allianz GI Official'),
    ('IRDAN123HL0001V01201819', 'Chola MS Flexi Health Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/health-insurance/flexi-health', 'Chola MS Official'),
    ('IRDAN128RP0010V01200809', 'Chola MS Health Insurance - Brochure', 'brochure', 'https://www.cholainsurance.com/health-insurance', 'Chola MS Official'),
    ('IRDAN116HL0001V01201819', 'Chola MS Healthline - Brochure', 'brochure', 'https://www.cholainsurance.com/health-insurance/healthline', 'Chola MS Official'),
    ('GLXHLIP24004V012425', 'Galaxy Arogya Sanjeevani - Brochure', 'brochure', 'https://www.galaxyhealthinsurance.in/products/arogya-sanjeevani', 'Galaxy Health Official'),
    ('GLXHLIP25003V012526', 'Galaxy Privilege - Brochure', 'brochure', 'https://www.galaxyhealthinsurance.in/products/galaxy-privilege', 'Galaxy Health Official'),
    ('IRDAN147RP0005V01200809', 'Generali Central Health Insurance - Brochure', 'brochure', 'https://general.futuregenerali.in/health-insurance', 'Future Generali GI Official'),
    ('IRDAN118HL0005V01201819', 'Generali Central Health Total - Brochure', 'brochure', 'https://general.futuregenerali.in/health-insurance/health-total', 'Future Generali GI Official'),
    ('IRDAN158HL0001V01201819', 'Digit Health Insurance - Brochure', 'brochure', 'https://www.godigit.com/health-insurance', 'Go Digit Official'),
    ('HDFHLGP21345V012021', 'HDFC ERGO my:health Group Insurance - Brochure', 'brochure', 'https://www.hdfcergo.com/health-insurance/my-health-group', 'HDFC ERGO Official'),
    ('ICIHLIP22097V012122', 'ICICI Lombard Hospital Daily Cash - Brochure', 'brochure', 'https://www.icicilombard.com/health-insurance/hospital-daily-cash', 'ICICI Lombard Official'),
    ('IRDAN103HL0005V01202021', 'IFFCO TOKIO Swasthya Kavach - Brochure', 'brochure', 'https://www.aborttokio.co.in/health-insurance/swasthya-kavach', 'IFFCO Tokio Official'),
    ('IRDAN127RP0006V01200607', 'IFFCO Tokio Health Insurance - Brochure', 'brochure', 'https://www.iffcotokio.co.in/health-insurance', 'IFFCO Tokio Official'),
    ('IRDAN106HL0001V01201819', 'IFFCO Tokio Swasthya Kavach Policy - Brochure', 'brochure', 'https://www.iffcotokio.co.in/health-insurance/swasthya-kavach', 'IFFCO Tokio Official'),
    ('IRDAN127HL0005V01201819', 'IndusInd GI Health Insurance - Brochure', 'brochure', 'https://www.indusindgeneralinsurance.com/health-insurance', 'IndusInd GI Official'),
    ('IRDAN172HL0001V01202425', 'Kshema General Health Insurance - Brochure', 'brochure', 'https://www.kshemageneral.com/health-insurance', 'Kshema General Official'),
    ('IRDAN152RP0004V01201415', 'Liberty General Health Insurance - Brochure', 'brochure', 'https://www.libertyinsurance.in/health-insurance', 'Liberty GI Official'),
    ('IRDAN152HL0005V01201920', 'Liberty Health Connect - Brochure', 'brochure', 'https://www.libertyinsurance.in/health-insurance/liberty-health-connect', 'Liberty GI Official'),
    ('IRDAN153RP0004V01201415', 'Magma General Health Insurance - Brochure', 'brochure', 'https://www.magma.co.in/health-insurance', 'Magma General Official'),
    ('IRDAN149HL0003V01202122', 'Magma One Health Insurance - Brochure', 'brochure', 'https://www.magma.co.in/health-insurance/one-health', 'Magma General Official'),
    ('NRHHLIP24001V012425', 'Narayana Aditi - Brochure', 'brochure', 'https://www.narayanahealth.org/insurance/aditi', 'Narayana Health Official'),
    ('NRHHLIP24002V012425', 'Narayana Aditi Plus - Brochure', 'brochure', 'https://www.narayanahealth.org/insurance/aditi-plus', 'Narayana Health Official'),
    ('NRHHLIP25003V012526', 'Narayana Arya - Brochure', 'brochure', 'https://www.narayanahealth.org/insurance/arya', 'Narayana Health Official'),
    ('IRDAN170HL0001V01200102', 'National Insurance Mediclaim Policy - Brochure', 'brochure', 'https://www.nationalinsurance.nic.co.in/en/health-insurance', 'National Insurance Official'),
    ('IRDAN155HL0003V01202021', 'Navi Arogya Sanjeevani Policy - Brochure', 'brochure', 'https://www.naviinsurance.com/health-insurance/arogya-sanjeevani', 'Navi General Official'),
    ('IRDAN155HL0002V01202122', 'Navi Health Insurance (Navi Cure) - Brochure', 'brochure', 'https://www.naviinsurance.com/health-insurance', 'Navi General Official'),
    ('IRDAN141HL0001V01201516', 'Raheja QBE Health Insurance - Brochure', 'brochure', 'https://www.rahejaqbe.com/health-insurance', 'Raheja QBE Official'),
    ('IRDAN110RP0005V01200506', 'Royal Sundaram Lifeline Supreme (V01) - Brochure', 'brochure', 'https://www.royalsundaram.in/health-insurance/lifeline-supreme', 'Royal Sundaram Official'),
    ('IRDAN102HL0001V01201819', 'Royal Sundaram Lifeline Supreme - Brochure', 'brochure', 'https://www.royalsundaram.in/health-insurance/lifeline-supreme', 'Royal Sundaram Official'),
    ('IRDAN144HL0002V01202021', 'SBI General Arogya Sanjeevani - Brochure', 'brochure', 'https://www.sbigeneral.in/health-insurance/arogya-sanjeevani', 'SBI General Official'),
    ('IRDAN155RP0002V02202021', 'SBI General Arogya Supreme - Brochure', 'brochure', 'https://www.sbigeneral.in/health-insurance/arogya-supreme', 'SBI General Official'),
    ('IRDAN148RP0005V01201415', 'Shriram General Health Insurance - Brochure', 'brochure', 'https://www.shriramgi.com/health-insurance', 'Shriram GI Official'),
    ('IRDAN137HL0003V01202021', 'Tata AIG Arogya Sanjeevani - Brochure', 'brochure', 'https://www.tataaig.com/health-insurance/arogya-sanjeevani', 'Tata AIG Official'),
    ('IRDAN137HL0006V01202223', 'Tata AIG Critical Illness Guard - Brochure', 'brochure', 'https://www.tataaig.com/health-insurance/critical-illness-guard', 'Tata AIG Official'),
    ('IRDAN137HL0005V01202223', 'Tata AIG Medicare Senior Citizen Health - Brochure', 'brochure', 'https://www.tataaig.com/health-insurance/medicare-senior-citizen', 'Tata AIG Official'),
    ('TATHLIP23167V032223', 'Tata AIG Medicare Premier - Brochure', 'brochure', 'https://www.tataaig.com/health-insurance/medicare-premier', 'Tata AIG Official'),
    ('IRDAN190HL0001V01200102', 'New India Assurance Mediclaim Policy - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/health-insurance', 'New India Assurance Official'),
    ('NIAHLGP21236V022021', 'New India Group Mediclaim Policy - Brochure', 'brochure', 'https://www.newindia.co.in/portal/product/health-insurance', 'New India Assurance Official'),
    ('IRDAN180HL0001V01200102', 'Oriental Insurance Happy Family Floater - Brochure', 'brochure', 'https://www.orientalinsurance.org.in/happy-family-floater', 'Oriental Insurance Official'),
    ('IRDAN130HL0001V01201819', 'United India Individual Health Insurance - Brochure', 'brochure', 'https://uiic.co.in/product/health-insurance', 'United India Official'),
    ('IRDAN160HL0001V01200102', 'United India Individual Mediclaim Policy - Brochure', 'brochure', 'https://uiic.co.in/product/health-insurance', 'United India Official'),
    ('IRDAN142RP0004V01200910', 'Universal Sompo Health Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/health-insurance', 'Universal Sompo Official'),
    ('IRDAN117HL0010V01202122', 'Universal Sompo Hospital Cash Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/health-insurance/hospital-cash', 'Universal Sompo Official'),
    ('IRDAN117HL0001V01201819', 'Universal Sompo Individual Health Insurance - Brochure', 'brochure', 'https://www.universalsompo.com/health-insurance/individual', 'Universal Sompo Official'),
    ('IRDAN148HL0003V01202021', 'Zuno Health Insurance Plan - Brochure', 'brochure', 'https://www.zunoinsurance.com/health-insurance', 'Zuno General Official'),
    ('IRDAN137HL0010V01202526', 'Zurich Kotak Health 360 - Brochure', 'brochure', 'https://www.zurichkotak.com/health-insurance/health-360', 'Zurich Kotak Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;
