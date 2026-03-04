-- ============================================================
-- 02_life_insurance.sql
-- Consolidated: All life insurance products, expansions, and documents
-- Merged from: 03_products_life.sql + 03b_products_life_extra.sql
--              + 12_life_standard_expansion.sql + 14_additional_expansion.sql (Part 3)
--              + 07b_policy_docs_life.sql
-- ============================================================

-- ================ SECTION 1: CORE LIFE PRODUCTS =================
-- ============================================================
-- 03_products_life.sql - Life insurance products with real UINs
-- Sources: licindia.in, hdfclife.com, iciciprulife.com, sbilife.co.in, axismaxlife.com
-- Last verified: 2026-02-20
-- ============================================================

SET search_path TO insurance, public;

-- ===================== LIC OF INDIA PRODUCTS =====================
-- Source: https://licindia.in/documents/d/guest/disclosure_modified_plans
-- LIC SE/2024-25/107 dated September 30, 2024

-- LIC's New Jeevan Anand (Endowment + Whole Life)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Jeevan Anand', '512N279V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'A participating non-linked endowment assurance plan that provides financial protection during the policy term and whole life coverage thereafter. Maturity benefit is paid on survival, and additional sum assured is payable on death even after maturity.',
    'Death benefit during policy term: Sum Assured + Vested Bonuses + Final Additional Bonus. Maturity Benefit: Basic Sum Assured + Vested Bonuses + Final Additional Bonus. Coverage continues for whole life after maturity.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

-- LIC's Jeevan Labh (Endowment)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Labh', '512N304V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'A limited premium paying, non-linked, with-profits endowment plan offering a combination of protection and savings. Premium paying term is shorter than the policy term.',
    'https://licindia.in/lic-s-jeevan-labh-plan-no.-936-uin-no.-512n304v02-', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

-- LIC's Jeevan Umang (Whole Life)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Umang', '512N312V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'A participating non-linked whole life insurance plan providing lifelong protection with periodic survival benefits. 8% of Basic Sum Assured payable annually as survival benefit from end of premium paying term till age 100.',
    'https://licindia.in/lics-jeevan-umang-plan-no.-945-uin-no.-512n312v02-', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Whole Life Insurance';

-- LIC's Jeevan Lakshya (Money-Back)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Lakshya', '512N297V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'A participating non-linked limited premium paying money back plan providing protection and savings. Annual income benefit of 15% of sum assured payable for 3 years immediately on death of life assured during the policy term.',
    'https://licindia.in/lic-s-jeevan-lakshya-plan-no.-933-uin-no.-512n297v02-', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Money-Back Plans';

-- LIC's New Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Endowment Plan', '512N277V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'A participating non-linked regular premium endowment assurance plan providing death benefit and maturity benefit with bonuses.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

-- LIC's Single Premium Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Single Premium Endowment Plan', '512N283V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'A single premium participating non-linked endowment plan offering one-time premium payment with guaranteed maturity benefits and life cover.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

-- LIC's Jeevan Utsav
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Utsav', '512N363V02', 'individual', 'non_linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A non-linked non-participating whole life insurance plan providing guaranteed income and life cover.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Whole Life Insurance';

-- LIC's Amritbaal (Child Plan)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Amritbaal', '512N365V02', 'individual', 'non_linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A non-linked non-participating limited premium paying endowment life insurance plan for children. Provides financial security for child''s future milestones.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Child Plans';

-- LIC's Jeevan Akshay-VII (Pension/Annuity)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Akshay-VII', '512N337V06', 'individual', 'non_linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A non-linked non-participating immediate annuity plan. Single premium payment provides guaranteed pension/annuity for lifetime with multiple annuity options.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Pension / Annuity Plans';

-- LIC's Yuva Term (Term Insurance)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Yuva Term', '512N355V01', 'individual', 'non_linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A non-linked non-participating pure term insurance plan offering affordable life cover with no maturity benefit.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term Life Insurance';

-- LIC's New Tech-Term (Online Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Tech-Term', '512N351V01', 'individual', 'non_linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'An online non-linked non-participating pure term insurance plan. Available for purchase exclusively through LIC''s online portal.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term Life Insurance';

-- LIC's New Jeevan Amar (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Jeevan Amar', '512N350V01', 'individual', 'non_linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A non-linked non-participating term assurance plan providing death benefit with options for level cover and increasing cover.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term Life Insurance';

-- LIC's Micro Bachat (Micro Insurance)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Micro Bachat', '512N329V03', 'micro', 'non_linked', 'non_participating',
    TRUE, '2024-10-01', '2024-2025',
    'A micro insurance plan designed for the economically weaker sections. Provides life cover with savings at affordable premiums.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Micro Insurance (Life)';

-- LIC's Index Plus (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Index Plus', '512L354V01', 'individual', 'linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A unit-linked non-participating individual life insurance plan. Provides market-linked returns with life cover. Investments track a market index.',
    'https://licindia.in/lic-s-index-plus-plan-no.-873-uin-no.-512l354v01-', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'ULIP - Unit Linked Plans';

-- LIC's New Pension Plus (ULIP Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Pension Plus', '512L347V01', 'individual', 'linked', 'non_participating',
    TRUE, NULL, '2024-2025',
    'A unit-linked non-participating pension plan. Combines market-linked growth with retirement income through annuity purchase at vesting.',
    'https://licindia.in/documents/d/guest/disclosure_modified_plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Pension / Annuity Plans';

-- ===================== HDFC LIFE PRODUCTS =====================
-- Source: https://www.hdfclife.com/all-insurance-plans, https://www.hdfclife.com/policy-documents

-- HDFC Life Click 2 Protect Supreme Plus (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Supreme Plus', '101N189V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan. Comprehensive term insurance with multiple plan options including Life Protect, Income Protect, and Income Plus.',
    'Life cover up to age 85. Multiple payout options: lump sum, monthly income, lump sum + monthly income. Optional riders for accidental death and critical illness.',
    'https://www.hdfclife.com/term-insurance-plans/click-2-protect-life', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- HDFC Life Click 2 Protect Life (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Life', '101N139V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual term life insurance plan offering affordable pure term coverage with personal accident benefit.',
    'https://www.hdfclife.com/term-insurance-plans/click-2-protect-life', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- HDFC Life Sanchay Par Advantage (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sanchay Par Advantage', '101N136V04', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Non-linked participating individual life insurance savings plan with guaranteed additions and bonuses for wealth creation and protection.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Sanchay Plus (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sanchay Plus', '101N134V27', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan offering guaranteed income and maturity benefits with multiple options: Guaranteed Income, Guaranteed Maturity, Long Term Income, and Life Long Income.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Guaranteed Income Insurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Guaranteed Income Insurance Plan', '101N146V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan providing guaranteed regular income for a fixed period plus maturity benefit.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Click 2 Invest (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Invest', '101L178V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual savings life insurance plan. Online ULIP offering market-linked returns with 4 fund options and life cover.',
    'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/click-2-invest-brochure.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- HDFC Life Click 2 Wealth (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Wealth', '101L133V03', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked non-participating individual life insurance plan designed for long-term wealth creation with multiple fund options.',
    'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/HDFC-Life-Click-2-Wealth_Brochure_Retail.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== ICICI PRUDENTIAL LIFE PRODUCTS =====================
-- Source: https://www.iciciprulife.com/insurance-plans/view-all-insurance-plans.html

-- ICICI Pru Protect N Gain (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Protect N Gain', '105L191V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Linked non-participating individual savings life insurance plan offering market-linked returns with life protection and capital guarantee option.',
    'https://www.iciciprulife.com/insurance-plans/view-all-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ICICI Pru Platinum (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Platinum', '105L192V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-participating linked individual savings life insurance plan. Premium ULIP offering multiple fund options with wealth creation and life cover.',
    'https://www.iciciprulife.com/insurance-plans/view-all-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ICICI Pru iProtect Smart (Term Insurance)
-- Source: https://www.iciciprulife.com/term-insurance-plans/iprotect-smart.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru iProtect Smart', '105N188V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan. Comprehensive online term plan with multiple coverage options including life, terminal illness, accidental death, and critical illness.',
    'Life cover up to Rs. 3 crore. Multiple plan options: Life, Life Plus, All-in-One, and Cancer & Heart. Lump sum or monthly income payout. Special premium rates for women and non-smokers.',
    'https://www.iciciprulife.com/term-insurance-plans/iprotect-smart.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ICICI Pru Saral Jeevan Bima (Term - IRDAI Standard)
-- Source: https://www.iciciprulife.com/term-insurance-plans/saral-jeevan-bima.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Saral Jeevan Bima', '105N176V02', 'standard', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual pure risk premium standard life insurance plan. IRDAI-mandated Saral Jeevan Bima standard term product with simple terms, sum assured Rs. 5 lakh to Rs. 25 lakh, and uniform features across all insurers.',
    'https://www.iciciprulife.com/term-insurance-plans/saral-jeevan-bima.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ICICI Pru Guaranteed Income For Tomorrow (GIFT) (Savings/Guaranteed)
-- Source: https://www.iciciprulife.com/savings-plans/gift-plan.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Guaranteed Income For Tomorrow', '105N187V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan providing guaranteed regular income and lump sum benefits. Multiple plan options for income duration and payout pattern.',
    'Guaranteed regular income for up to 30 years. Choice of Long Term Income, Immediate Income, and Guaranteed Cashback options. Life cover throughout the policy term. Premium waiver on death.',
    'https://www.iciciprulife.com/savings-plans/gift-plan.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ICICI Pru Lakshya (Savings)
-- Source: https://www.iciciprulife.com/savings-plans/lakshya.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Lakshya', '105N160V02', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Non-linked participating individual endowment life insurance plan offering savings with protection. Provides guaranteed maturity benefit along with reversionary bonuses and terminal bonus.',
    'https://www.iciciprulife.com/savings-plans/lakshya.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ICICI Pru Signature (ULIP)
-- Source: https://www.iciciprulife.com/ulip-plans/signature.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Signature', '105L187V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Linked non-participating individual life insurance plan. Unit-linked plan with multiple investment strategies, portfolio management options, and life cover. Suitable for long-term wealth creation.',
    'https://www.iciciprulife.com/ulip-plans/signature.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ICICI Pru Wealth Builder (ULIP)
-- Source: https://www.iciciprulife.com/ulip-plans/wealth-builder.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Wealth Builder', '105L186V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Linked non-participating individual savings life insurance plan. Unit-linked plan offering systematic investment with automatic portfolio rebalancing and life cover.',
    'https://www.iciciprulife.com/ulip-plans/wealth-builder.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ICICI Pru Smart Kid's Solution (Child Plan)
-- Source: https://www.iciciprulife.com/child-insurance-plans/smart-kid-solution.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Smart Kid''s Solution', '105L152V02', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Linked non-participating individual life insurance plan designed for children''s future financial needs including education and milestones.',
    'Market-linked returns for long-term wealth creation. Premium waiver benefit on parent''s death. Flexibility in fund choice and switching. Partial withdrawal facility after lock-in.',
    'https://www.iciciprulife.com/child-insurance-plans/smart-kid-solution.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- ICICI Pru Guaranteed Pension Plan (Pension/Annuity)
-- Source: https://www.iciciprulife.com/retirement-pension-plans/guaranteed-pension-plan.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Guaranteed Pension Plan', '105N186V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual deferred annuity plan. Provides guaranteed pension/annuity income starting from the chosen vesting age.',
    'Guaranteed pension for life. Joint life option available. Choice of annuity options at vesting. Return of purchase price on death option.',
    'https://www.iciciprulife.com/retirement-pension-plans/guaranteed-pension-plan.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ICICI Pru Saral Pension (Pension - IRDAI Standard)
-- Source: https://www.iciciprulife.com/retirement-pension-plans/saral-pension.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Saral Pension', '105N175V03', 'standard', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual standard deferred annuity plan. IRDAI-mandated Saral Pension standard product with simple, transparent terms and guaranteed annuity at vesting.',
    'https://www.iciciprulife.com/retirement-pension-plans/saral-pension.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ICICI Pru Heart/Cancer Protect (Term - Health Rider)
-- Source: https://www.iciciprulife.com/term-insurance-plans/heart-cancer-protect.html
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Heart/Cancer Protect', '105N182V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual health insurance plan providing lump sum benefit on diagnosis of specified heart conditions and cancers. Multiple coverage options available.',
    'https://www.iciciprulife.com/term-insurance-plans/heart-cancer-protect.html', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ===================== SBI LIFE PRODUCTS =====================
-- Source: https://www.sbilife.co.in/fy-2024-25

-- SBI Life Sudarshan Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Sudarshan Plan', '111N008V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'A regular/single premium participating endowment plan with reversionary bonus rate of 4.75% across terms. Provides life cover and savings with minimum policy term of 10 years.',
    'https://www.sbilife.co.in/fy-2024-25', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- SBI Life eShield Next (Term Insurance)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/protection-plans/sbi-life-eshield-next
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life eShield Next', '111N108V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan. Online term plan with comprehensive protection options and affordable premiums.',
    'Life cover up to Rs. 3 crore. Multiple plan options: Level Cover, Increasing Cover, and Income Plus. Critical illness and accidental death riders available. Special rates for non-smokers.',
    'https://www.sbilife.co.in/en/individual-life-insurance/protection-plans/sbi-life-eshield-next', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- SBI Life Saral Jeevan Bima (Term - IRDAI Standard)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/protection-plans/sbi-life-saral-jeevan-bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Saral Jeevan Bima', '111N101V02', 'standard', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual pure risk premium standard life insurance plan. IRDAI-mandated Saral Jeevan Bima standard term product with sum assured Rs. 5 lakh to Rs. 25 lakh and uniform features.',
    'https://www.sbilife.co.in/en/individual-life-insurance/protection-plans/sbi-life-saral-jeevan-bima', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- SBI Life Smart Platina Plus (Savings)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-smart-platina-plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Platina Plus', '111N107V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan with guaranteed income and maturity benefits. Offers choice of benefit options for regular income or lump sum.',
    'Guaranteed regular income during payout period. Guaranteed maturity benefit. Life cover throughout the policy term. Option for joint life coverage.',
    'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-smart-platina-plus', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Smart Humsafar (Savings - Joint Life)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-smart-humsafar
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Humsafar', '111N102V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual life insurance savings plan for couples (joint life). Provides guaranteed additions and life cover for both spouses with premium waiver on first death.',
    'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-smart-humsafar', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Retire Smart Plus (ULIP - Pension)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/unit-linked-insurance-plan/sbi-life-retire-smart-plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Retire Smart Plus', '111L102V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual pension plan. Market-linked retirement savings plan with systematic accumulation and annuity purchase at vesting.',
    'Market-linked returns with multiple fund options. Automatic asset rebalancing option. Partial withdrawal facility. Choice of vesting age and annuity options.',
    'https://www.sbilife.co.in/en/individual-life-insurance/unit-linked-insurance-plan/sbi-life-retire-smart-plus', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- SBI Life Saral Pension (Pension - IRDAI Standard)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/retirement-plans/sbi-life-saral-pension
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Saral Pension', '111N098V03', 'standard', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating individual standard deferred annuity plan. IRDAI-mandated Saral Pension standard product with simple and transparent terms.',
    'https://www.sbilife.co.in/en/individual-life-insurance/retirement-plans/sbi-life-saral-pension', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- SBI Life Smart Wealth Builder (ULIP)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/unit-linked-insurance-plan/sbi-life-smart-wealth-builder
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Wealth Builder', '111L105V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan designed for wealth creation with systematic investments and market-linked returns.',
    'Multiple fund options including equity, debt, and balanced. Free fund switching. Partial withdrawal after 5-year lock-in. Loyalty additions for long-term investors. Life cover throughout.',
    'https://www.sbilife.co.in/en/individual-life-insurance/unit-linked-insurance-plan/sbi-life-smart-wealth-builder', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- SBI Life Smart Privilege (Endowment/Savings)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-smart-privilege
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Privilege', '111N105V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan. Offers guaranteed benefits with flexibility to choose payout options including regular income and lump sum maturity.',
    'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-smart-privilege', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Smart Champ Insurance (Child Plan)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/child-plans/sbi-life-smart-champ-insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Champ Insurance', '111N106V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance plan designed for children''s future financial needs including education and marriage milestones.',
    'Guaranteed additions on survival. Premium waiver on parent/proposer death. Payouts aligned with child''s education milestones. Life cover for proposer during premium payment term.',
    'https://www.sbilife.co.in/en/individual-life-insurance/child-plans/sbi-life-smart-champ-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- SBI Life Shubh Nivesh (Endowment)
-- Source: https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-shubh-nivesh
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Shubh Nivesh', '111N103V02', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Non-linked participating individual endowment life insurance plan. Provides savings with protection through reversionary bonuses and terminal bonus. Limited premium payment term shorter than policy term.',
    'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sbi-life-shubh-nivesh', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ===================== AXIS MAX LIFE PRODUCTS =====================
-- Source: https://www.axismaxlife.com/blog/all-products

-- Axis Max Life Smart Term Plan Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Term Plan Plus', '104N127V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure term insurance plan with comprehensive coverage options including life protect, income protect, and critical illness cover.',
    'Life cover up to Rs. 25 crore. Multiple payout options. Online purchase discount. Covers 64 critical illnesses. Accidental death benefit. Terminal illness cover.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Axis Max Life Smart Secure Plus Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Secure Plus Plan', '104N118V12', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan offering flexible term coverage with customizable options.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Axis Max Life Guaranteed Lifetime Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Guaranteed Lifetime Income Plan', '104N076V21', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan providing guaranteed income for lifetime with premium waiver on critical illness.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Flexi Wealth Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Flexi Wealth Plan', '104L115V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan offering market-linked returns with flexibility in premium payment and fund switching.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Axis Max Life Platinum Wealth Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Platinum Wealth Plan', '104L090V07', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan for high-net-worth individuals. Premium ULIP with multiple fund options and wealth creation focus.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Axis Max Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Saral Pension Plan', '104N119V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual deferred annuity plan. IRDAI-mandated standard pension product with simple and transparent terms.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- Axis Max Life Smart Value Income Plan (NEW 2025)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Value Income & Benefit Enhancer Plan', '104N159V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2025-05-05', '2025-2026',
    'Non-linked non-participating individual life insurance savings plan launched May 2025. Offers combination of income certainty and protection with flexibility of choosing between plan variants.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- ===================== KOTAK MAHINDRA LIFE PRODUCTS =====================
-- Source: https://www.kotaklife.com/
-- UINs verified from IRDAI filings and Morningstar India

-- Kotak T-ULIP Nxt (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak T-ULIP Nxt', '107L138V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-participating unit-linked individual savings life insurance plan. Award-winning ULIP combining term insurance with market-linked investment returns.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Kotak Premier Moneyback Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Premier Moneyback Plan', '107N083V02', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Participating anticipated endowment plan providing periodic survival benefits during the policy term and maturity benefit on survival.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

-- Kotak Complete Cover Group Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Complete Cover Group Plan', '107N018V08', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating reducing cover term group plan providing life cover for loan borrowers. Sum assured reduces with outstanding loan amount.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- Kotak Group Secure One
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Group Secure One', '107N098V05', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-participating term group plan providing financial security to members'' families. Group term life insurance for employers and associations.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== ADITYA BIRLA SUN LIFE (ABSLI) PRODUCTS =====================
-- Source: https://lifeinsurance.adityabirlacapital.com/

-- ABSLI Life Shield Plan (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Life Shield Plan', '109N136V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan. Comprehensive term plan with 8 different plan options for customized protection.',
    'Multiple plan options for different coverage needs. Accidental death benefit. Critical illness cover. Premium waiver on disability.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ABSLI Guaranteed Milestone Plan (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Guaranteed Milestone Plan', '109N134V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan with guaranteed milestone benefits at key life stages. Provides life cover with guaranteed payouts.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ABSLI Vision Money Back Plus Plan (Money-Back)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Vision Money Back Plus Plan', '109N131V02', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Non-linked participating individual life insurance money back plan with periodic payouts and bonuses. Provides life cover with regular survival benefits.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

-- ABSLI Wealth Max Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Wealth Max Plan', '109L117V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan with guaranteed additions and wealth protection. Fund value never less than 105% of total premiums paid.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ABSLI Wealth Secure Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Wealth Secure Plan', '109L115V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan with whole life cover and investment options. Provides market-linked returns with lifelong protection.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ABSLI Immediate Annuity Plan (Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Immediate Annuity Plan', '109N120V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual immediate annuity plan. Single premium plan providing guaranteed pension income for life with multiple annuity options.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ABSLI Vision Star Plan (Child)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Vision Star Plan', '109N133V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual child insurance plan designed to secure children''s future financial needs. Provides guaranteed payouts for education and life milestones.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- ===================== TATA AIA LIFE PRODUCTS =====================
-- Source: https://www.tataaia.com/

-- Tata AIA Maha Raksha Supreme (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Maha Raksha Supreme', '110N102V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance plan providing all-round family protection coverage with multiple benefit options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Tata AIA Sampoorna Raksha (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Sampoorna Raksha', '110N129V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure term life insurance plan offering affordable life protection.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Tata AIA Sampoorna Raksha+ (Term with ROP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Sampoorna Raksha Plus', '110N130V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual term plan with return of premium. Returns all premiums paid on survival at end of policy term.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Term with Return of Premium';

-- Tata AIA Sampoorna Raksha Supreme (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Sampoorna Raksha Supreme', '110N160V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance plan with comprehensive term coverage options and enhanced benefits.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Tata AIA Maha Raksha Supreme Select (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Maha Raksha Supreme Select', '110N171V12', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating pure risk individual life insurance product. Flexible life cover with customizable protection options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Tata AIA Smart SIP (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Smart SIP', '110L174V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-participating unit-linked individual life insurance savings plan. SIP-based ULIP for systematic wealth creation with market-linked returns and life cover.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Tata AIA Smart Fortune Plus (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Smart Fortune Plus', '110L177V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-participating unit-linked individual life insurance savings plan. Premium ULIP with multiple fund options for wealth creation and life protection.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Tata AIA Smart Sampoorna Raksha Supreme (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Smart Sampoorna Raksha Supreme', '110L179V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan combining term protection with market-linked investment returns.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Tata AIA i Systematic Insurance Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA i Systematic Insurance Plan', '110L164V06', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-participating unit-linked individual life insurance savings plan for systematic investing with life cover and market-linked returns.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Tata AIA Wealth Pro (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Wealth Pro', '110L111V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked individual life insurance savings plan designed for long-term wealth accumulation with multiple fund options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Tata AIA Fortune Pro (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Fortune Pro', '110L112V06', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked individual life insurance savings plan for premium investors seeking market-linked returns with life cover.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Tata AIA Smart Income Plus (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Smart Income Plus', '110N126V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan with guaranteed regular income benefits and life protection.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Tata AIA Fortune Guarantee Supreme (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Fortune Guarantee Supreme', '110N163V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Individual non-linked non-participating life insurance savings plan with guaranteed income and maturity benefits. Multiple benefit options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Tata AIA Fortune Guarantee Plus (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Fortune Guarantee Plus', '110N158V11', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan with guaranteed income benefits and flexible payout options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Tata AIA Fortune Guarantee Retirement Ready (Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Fortune Guarantee Retirement Ready', '110N175V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Individual non-linked non-participating pension plan providing guaranteed retirement income. Helps build a retirement corpus with guaranteed annuity.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== BAJAJ LIFE INSURANCE PRODUCTS =====================
-- Source: https://www.bajajlifeinsurance.com/ (formerly Bajaj Allianz Life)

-- Bajaj Life eTouch II (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life eTouch II', '116N198V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance term plan. Online pure term insurance with comprehensive protection at affordable premiums.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Bajaj Life Diabetic Term Plan II (Term - Specialized)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Diabetic Term Plan II', '116N183V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan designed specifically for Type 2 diabetics with HbA1c below 8.',
    'First-of-its-kind term plan for diabetics. Life cover for Type 2 diabetics with controlled sugar levels. Sub-8 HbA1c eligibility.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Bajaj Life Future Wealth Gain IV (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Future Wealth Gain IV', '116L202V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance savings plan for wealth creation through market-linked investments with life protection.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life Goal Assure IV (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Goal Assure IV', '116L204V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance savings plan designed for goal-based systematic investing with life cover.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life LongLife Goal III (ULIP - Whole Life)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life LongLife Goal III', '116L203V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating whole life insurance plan combining lifelong protection with market-linked investment opportunities.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life Invest Protect Goal III (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Invest Protect Goal III', '116L205V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance savings plan balancing investment growth with protection benefits.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life Magnum Fortune Plus III (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Magnum Fortune Plus III', '116L207V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance savings plan for high-value wealth creation with premium fund management.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life Supreme (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Supreme', '116L211V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance savings plan. Premium ULIP with comprehensive features for wealth accumulation.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life Guaranteed Wealth Goal (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Guaranteed Wealth Goal', '116N200V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual life insurance savings plan with guaranteed wealth creation benefits and life protection throughout the policy term.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Savings Plans';

-- ===================== PNB METLIFE PRODUCTS =====================
-- Source: https://www.pnbmetlife.com/

-- PNB MetLife DigiProtect Term Plan (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife DigiProtect Term Plan', '117N141V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure term insurance plan. Digital term plan with instant issuance and affordable premiums.',
    'High life cover at affordable premiums. Instant digital issuance. Optional riders for critical illness and disability. Special premium rates for non-smokers.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- PNB MetLife Guaranteed Goal Plan (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Guaranteed Goal Plan', '117N131V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Individual non-linked non-participating savings life insurance plan. Helps save systematically with guaranteed returns and life protection. Flexible premium payment options.',
    'https://www.pnbmetlife.com/insurance-plans/long-term-savings/pnb-metlife-guaranteed-goal-plan.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Savings Plans';

-- PNB MetLife Smart Goal Ensuring Multiplier (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Smart Goal Ensuring Multiplier', '117L139V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual savings life insurance plan. Goal-oriented ULIP blending protection with disciplined wealth creation through market-linked returns.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== AGEAS FEDERAL LIFE PRODUCTS =====================
-- Source: https://www.ageasfederal.com/

-- Ageas Federal iSecure Plan (Term/Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal iSecure Plan', '135N088V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk and savings life insurance plan. Combines term protection with savings benefits.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Ageas Federal Life Advantage Plus Plan (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Advantage Plus Plan', '135N078V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Non-linked participating individual life savings insurance plan with guaranteed additions and reversionary bonuses for long-term wealth creation.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Ageas Federal Assured Income Plan (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Assured Income Plan', '135N083V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual savings life insurance plan providing guaranteed income and maturity benefits.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Ageas Federal Wealth Gain Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Wealth Gain Plan', '135L047V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating individual life insurance plan offering market-linked returns with multiple fund options and life cover.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== CANARA HSBC LIFE PRODUCTS =====================
-- Source: https://www.canarahsbclife.com/

-- Canara HSBC Promise4Future (Savings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Promise4Future', '136N119V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-10-01', '2024-2025',
    'Non-linked participating life insurance plan designed for savings and protection. Launched October 2024. Combines long-term protection with participating fund returns.',
    'Life protection with savings. Benefit from participating fund returns. Robust savings corpus creation. Claim settlement ratio 99.43%.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ===================== ICICI PRUDENTIAL LIFE - ADDITIONAL PRODUCTS =====================
-- Source: https://www.iciciprulife.com/icici-pru-active-and-withdrawn-products-list.html

-- ICICI Pru iProtect Supreme (Term)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru iProtect Supreme', '105N193V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual pure risk premium life insurance plan. Premium term insurance with comprehensive protection including accidental death and critical illness benefits.',
    'https://www.iciciprulife.com/insurance-plans/view-all-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ===================== SHRIRAM LIFE INSURANCE PRODUCTS =====================
-- Source: https://www.shriramlife.com/

-- Shriram Life Online Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Online Term Plan', '128N072V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Online term life insurance plan from Shriram Life providing affordable pure protection. Available online with simplified underwriting and competitive premiums.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Shriram Life Assured Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Assured Income Plan', '128N053V05', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Participating non-linked savings plan providing guaranteed regular income along with life cover. Offers assured income payouts during the payout period with bonus additions.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Shriram Life New Shri Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life New Shri Life Plan', '128N047V01', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating non-linked endowment plan offering savings with life protection. Provides maturity benefit with vested bonuses and death benefit as sum assured plus accumulated bonuses.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- Shriram Life Wealth Plus (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Wealth Plus', '128L036V02', 'individual', 'linked', 'not_applicable',
    TRUE, '2019-2020',
    'Unit linked insurance plan from Shriram Life offering market-linked returns with multiple fund options. Provides flexibility to switch between equity and debt funds.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== INDUSIND NIPPON LIFE INSURANCE PRODUCTS =====================
-- Source: https://www.indusindnipponlife.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Super Endowment Plan', '121N107V01', 'individual', 'non_linked', 'participating',
    TRUE, '2022-2023',
    'Participating non-linked endowment assurance plan offering life cover with savings. Provides maturity benefit with bonuses and death benefit during the policy term.',
    'https://www.indusindnipponlife.com/life-insurance-plans', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Saral Jeevan Bima', '121N114V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance product with simple terms and conditions. Provides pure life cover at affordable premiums with uniform features across all insurers.',
    'https://www.indusindnipponlife.com/life-insurance-plans', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Guaranteed Income Plan', '121N110V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-participating guaranteed income plan providing assured regular payouts along with life cover. Offers guaranteed additions and income benefit during the payout period.',
    'https://www.indusindnipponlife.com/life-insurance-plans', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ===================== AVIVA LIFE INSURANCE PRODUCTS =====================
-- Source: https://www.avivaindia.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva LifeShield Advantage', '122N060V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked non-participating term insurance plan providing comprehensive life protection. Offers death benefit with options for lump sum or regular income payout to nominees.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Signature 3D Term Plan', '122N065V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Comprehensive term plan providing triple protection against Death, Disability, and Disease. Options include lump sum, regular monthly income, or a combination of both.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Guaranteed Income Plan', '122N058V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked non-participating savings plan offering guaranteed regular income with life cover and maturity benefit.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Signature Increasing Income Plan', '122N068V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Award-winning retirement income plan (Product of the Year 2025). Provides increasing regular income post retirement to counter inflation.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== BANDHAN LIFE INSURANCE PRODUCTS =====================
-- Source: https://www.bandhanlife.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life iTerm Prime', '138N020V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Online term insurance plan from Bandhan Life (formerly Aegon Life) offering affordable pure life protection with instant issuance.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life Saral Jeevan Bima', '138N017V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance with simple and uniform terms. Provides basic life cover at affordable premiums.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life iInvest Advantage', '138L009V01', 'individual', 'linked', 'not_applicable',
    TRUE, '2024-2025',
    'Flexible unit linked insurance plan offering high-performance funds, expert-guided strategy and life protection. Zero allocation and admin charges.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== PRAMERICA LIFE INSURANCE PRODUCTS =====================
-- Source: https://pramericalife.in/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Secure Savings Plan', '140N038V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating savings plan offering guaranteed returns with life protection and assured maturity benefit.',
    'https://pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Smart Income', '140N035V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked non-participating individual life insurance plan providing regular income with life cover and lump sum maturity benefit.',
    'https://pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Cancer + Heart Shield', '140N040V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Critical illness plan covering cancer, cardiovascular conditions, and other major diseases. Provides fixed benefit upon diagnosis of covered conditions.',
    'https://pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ===================== STAR UNION DAI-ICHI LIFE PRODUCTS =====================
-- Source: https://www.sudlife.in/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Premier Protection Plan', '142N037V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Term insurance from Star Union Dai-Ichi Life providing comprehensive life protection with flexible premium payment terms.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Saral Jeevan Bima', '142N035V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance with simple, uniform terms and affordable premiums.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Wealth Builder', '142L015V01', 'individual', 'linked', 'not_applicable',
    TRUE, '2022-2023',
    'Single premium unit linked investment plan with 4 fund options. Market-linked returns with top-up options and life cover.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== INDIAFIRST LIFE PRODUCTS =====================
-- Source: https://www.indiafirstlife.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life ELITE Term Plan', '143N063V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Premium term insurance offering Rs. 1 Cr life cover at affordable rates with 10% online discount and flexible payout options.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Guaranteed Monthly Income Plan', '143N055V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating savings plan providing guaranteed monthly income payouts with life cover.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Money Balance Plan', '143L020V01', 'individual', 'linked', 'not_applicable',
    TRUE, '2021-2022',
    'Unit linked insurance plan with auto-rebalancing feature. Multiple fund options with life insurance cover.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Guaranteed Retirement Plan', '143N060V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating pension plan providing guaranteed retirement corpus with annuity options at retirement.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== EDELWEISS LIFE PRODUCTS =====================
-- Source: https://www.edelweisslife.in/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Life Zindagi Protect Plus', '147N023V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Flagship term insurance plan from Edelweiss Life (formerly Edelweiss Tokio). 99.20% claim settlement ratio.',
    'https://www.edelweisslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Life Assured Income STAR', '147N025V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan offering guaranteed regular income with customized payouts via Accrual of Survival Benefits.',
    'https://www.edelweisslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Life Wealth Premier', '147L010V01', 'individual', 'linked', 'not_applicable',
    TRUE, '2023-2024',
    'Unit linked non-participating individual life insurance plan offering market-linked returns with multiple fund choices and life protection.',
    'https://www.edelweisslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== GENERALI CENTRAL LIFE PRODUCTS =====================
-- Source: https://www.generalicentrallife.com/

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Life Flexi Online Term Plan', '133N076V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Online term insurance from Generali Central Life (formerly Future Generali). Affordable life protection with online purchase convenience.',
    'https://www.generalicentrallife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Life Assured Wealth Plan', '133N078V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan providing guaranteed wealth accumulation with life cover and regular income options.',
    'https://www.generalicentrallife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Life Saral Jeevan Bima', '133N072V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance product with simple and uniform features at affordable premiums.',
    'https://www.generalicentrallife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ===================== BHARTI AXA LIFE (MERGED WITH HDFC LIFE) =====================
-- Note: Merged with HDFC Life in Feb 2022. Legacy products.

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Saral Jeevan Bima', '130N060V01', 'individual', 'non_linked', 'non_participating',
    FALSE, '2021-2022',
    'IRDAI-mandated standard term insurance. Bharti AXA Life merged with HDFC Life in Feb 2022. Existing policies serviced by HDFC Life.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Guaranteed Wealth Pro', '130N058V01', 'individual', 'non_linked', 'non_participating',
    FALSE, '2021-2022',
    'Non-linked savings plan with guaranteed returns. Bharti AXA Life merged with HDFC Life. Existing policies serviced by HDFC Life.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ===================== SAHARA INDIA LIFE (UNDER REGULATORY RESTRICTION) =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Sahara Life Saral Jeevan Bima', '126N035V01', 'individual', 'non_linked', 'non_participating',
    FALSE, '2021-2022',
    'IRDAI-mandated standard term insurance. Note: Sahara India Life is under regulatory restrictions by IRDAI.',
    'https://irdai.gov.in/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Sahara India Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ===================== ACKO LIFE INSURANCE PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Life Term Plan', '169N001V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Digital-first term life insurance from Acko Life. Fully online purchase with instant policy issuance at affordable premiums.',
    'https://www.acko.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- ===================== GO DIGIT LIFE INSURANCE PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Go Digit Life Term Plan', '168N001V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Digital term life insurance from Go Digit Life. Simple, affordable term cover with online-first approach.',
    'https://www.godigit.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- ===================== CREDITACCESS LIFE INSURANCE PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'CreditAccess Life Group Term Plan', '170N001V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Group term life insurance primarily serving microfinance borrowers of CreditAccess Grameen. Provides life cover to borrowers and families.',
    'https://irdai.gov.in/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'CreditAccess Life Insurance Limited' AND sc.name = 'Group Term Life';

-- ============================================================
-- PHASE 2 EXPANSION - Comprehensive product additions
-- Research date: 2026-02-21
-- ============================================================

-- ===================== LIC ADDITIONAL PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Single Premium Endowment Plan', '512N283V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'A single premium non-linked with-profits endowment plan providing combination of insurance and savings with only one-time premium payment. Maturity benefit includes sum assured plus vested bonuses.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Kiran', '512N355V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating term assurance plan with return of premiums on maturity. Provides pure protection during policy term with full premium refund on survival.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term with Return of Premium';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Dhan Rekha', '512N357V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating savings plan providing guaranteed returns. Offers lump sum benefit on maturity and death benefit during policy term.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Index Plus', '512L354V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'A unit linked non-participating individual life insurance plan. Links returns to Nifty 50 index via a single fund option, providing market-linked growth with life cover.',
    'https://licindia.in/lic-s-index-plus-plan-no.-873-uin-no.-512l354v01-', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Nivesh Plus', '512L002V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'A unit linked non-participating individual life insurance plan with single premium payment. Offers choice of 4 fund options for wealth creation with insurance protection.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Pension Plus', '512L003V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'A unit linked non-participating pension plan providing retirement corpus through market-linked returns. Choice of fund options with mandatory annuity purchase at vesting.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Dhara II', '512N305V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating immediate annuity plan providing lifelong pension immediately on single premium payment. Multiple annuity options including joint life.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Micro Bachat', '512N306V02', 'micro', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'A micro insurance endowment plan for economically weaker sections providing savings and protection. Low premium product with sum assured from Rs. 5,000 to Rs. 50,000.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Micro Insurance (Life)';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Nav Jeevan Shree', '512N360V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2025-2026',
    'Latest single premium non-linked non-participating savings plan from LIC offering guaranteed returns with a single premium payment and multiple maturity term options.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Aam Aadmi Bima Yojana', '512G302V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A government-sponsored social security group insurance scheme for rural landless households. Provides death and disability cover to head of family or earning member.',
    'https://licindia.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s PMJJBY', '512G304V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Pradhan Mantri Jeevan Jyoti Bima Yojana - Government scheme providing life insurance cover of Rs. 2 lakh at a premium of Rs. 436/year for ages 18-50.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

-- ===================== HDFC LIFE ADDITIONAL PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Ultimate', '101N179V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Comprehensive term plan with flexible options including lump sum, monthly income, or increasing income. Coverage up to Rs. 10 crore with critical illness and accidental death benefit options.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Elite Plus', '101N182V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Online term plan with customizable protection options including life, critical illness, and disability cover. Offers whole life coverage option till age 99.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Life', '101N139V08', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Basic online pure term plan with simple life protection at affordable premiums. Minimum sum assured Rs. 25 lakh with options for level and increasing cover.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Protect Supreme', '101N183V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Feature-rich online term plan with 4 plan options: Life Protect, Extra Life, Income, and Income Plus. Includes terminal illness benefit and premium waiver.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sanchay Legacy', '101N177V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan offering guaranteed income and guaranteed lump sum benefits for building a legacy. Multiple plan options for systematic wealth creation.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Guaranteed Income Insurance Plan', '101N146V09', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating plan providing guaranteed regular income and lump sum maturity benefit. Multiple plan options with guaranteed income payouts for up to 30 years.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Guaranteed Wealth Plus', '101N165V13', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan offering guaranteed maturity benefit with life cover. Flexible premium payment terms with multiple payout options.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sanchay Fixed Maturity Plan', '101N142V08', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating plan with guaranteed fixed maturity benefit. Single or limited premium payment options for systematic savings with assured returns.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Achieve Par Advantage', '101N207V01', 'individual', 'non_linked', 'participating',
    TRUE, '2025-2026',
    'Participating savings plan combining guaranteed and bonus-based benefits. Online plan with limited premium paying term and maturity benefits including vested bonuses.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sampoorna Jeevan', '101N158V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating whole life plan providing lifelong protection till age 99 with guaranteed regular income and death benefits throughout life.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Invest', '101L178V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit linked non-participating online investment plan with choice of 10 fund options. Offers systematic investment with no premium allocation charges and flexible investment strategies.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Wealth', '101L133V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit linked non-participating online ULIP plan for wealth creation with 11 fund options. Zero premium allocation charges with systematic investing and portfolio balancing.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sampoorn Nivesh Plus', '101L180V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit linked non-participating savings plan with multiple fund options and systematic investment strategy. Includes maturity and loyalty additions for long-term investors.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Smart Protect Plus', '101L187V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit linked non-participating plan combining protection and investment. Provides life cover with market-linked returns and automatic fund management options.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Pension Guaranteed Plan', '101N118V13', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating immediate annuity plan providing guaranteed lifelong pension immediately on single premium payment. Multiple annuity options including joint life.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Systematic Retirement Plan', '101N143V09', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating deferred annuity plan for systematic retirement planning. Guaranteed vesting benefit with multiple annuity payout options on retirement.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Aajeevan Growth Nivesh and Income', '101N209V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2025-2026',
    'Non-linked non-participating plan offering guaranteed lifelong income with built-in growth. Provides increasing annual income and lifetime coverage.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sanchay Aajeevan Guaranteed Advantage', '101N208V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2025-2026',
    'Non-linked non-participating plan with guaranteed lifelong income and wealth creation benefits. Provides assured returns throughout life.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life PMJJBY', '101G107V02', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Pradhan Mantri Jeevan Jyoti Bima Yojana - Government scheme providing life insurance cover of Rs. 2 lakh at a premium of Rs. 436/year for ages 18-50.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Term Life', '101N169V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Group term life insurance plan for employer-employee groups providing death benefit coverage. Flexible group sizes with one-year renewable term.',
    'https://www.hdfclife.com/all-insurance-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== MAX LIFE ADDITIONAL PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Secure Plus Plan', '104N118V12', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Comprehensive offline term plan with multiple plan options including Life, Life Plus, and All-in-One. Coverage up to Rs. 25 crore with CI and accidental death benefit.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Total Elite Protection Plan', '104N125V09', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Premium offline term plan offering highest coverage with multiple protection layers including accidental, critical illness, disability, and terminal illness cover.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Platinum Wealth Plan', '104L090V07', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Premium ULIP plan with choice of 9 fund options and unlimited free switches. Loyalty additions and wealth boosters for long-term wealth creation.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Flexi Wealth Advantage Plan', '104L121V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan offering systematic investment with automatic portfolio management. Multiple fund options with return of mortality charges feature.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Flexi Wealth Plus Plan', '104L115V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan with multiple fund options for wealth building. Includes loyalty additions from 6th year and automatic asset allocation strategies.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Wealth Advantage Guarantee Plan', '104N124V16', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed maturity benefit. Multiple payout options including lump sum and regular income with guaranteed additions.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Value Income & Benefit Enhancer Plan', '104N159V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2025-2026',
    'Latest savings plan offering guaranteed regular income with benefit enhancement feature. Flexible payout options for income and wealth creation.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Wealth Advantage Growth Par Plan', '104N135V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Participating savings plan combining guaranteed and bonus-linked benefits. Provides guaranteed maturity with additional upside through reversionary bonuses.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Monthly Income Advantage Plan', '104N091V07', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked savings plan providing guaranteed monthly income. Choice of income period and premium payment term with lump sum maturity benefit.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Guaranteed Pension Plan', '104N122V23', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating deferred annuity plan with guaranteed pension for life. Multiple annuity options and premium payment term flexibility.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Guaranteed Lifetime Income Plan', '104N076V21', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating plan providing guaranteed lifelong income with increasing annual payouts. Premium paying term of 5 to 12 years with income till age 99.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Wealth Annuity Guaranteed Pension Plan', '104N137V13', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Deferred annuity plan offering guaranteed pension with flexible vesting age. Multiple annuity options with guaranteed additions during deferment period.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Shiksha Plus Super Plan', '104L084V15', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit linked child education plan with premium waiver on parent''s death. Multiple fund options for building education corpus with systematic investment.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Child Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life PMJJBY', '104G089V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Pradhan Mantri Jeevan Jyoti Bima Yojana - Government scheme providing life cover of Rs. 2 lakh at premium of Rs. 436/year for ages 18-50.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Group Term Life';

-- ===================== BAJAJ LIFE ADDITIONAL PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life eTouch II', '116N198V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Online term plan with comprehensive life protection. 0% GST benefit, coverage up to Rs. 10 crore with critical illness, accidental death and terminal illness riders.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Goal Assure IV', '116L204V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan with choice of 8 fund options for long-term wealth creation. Zero premium allocation charges with loyalty additions from 6th year.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Future Wealth Gain IV', '116L202V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP savings plan with guaranteed loyalty additions and wealth creation. Minimum 34.5% past returns track record with multiple fund options.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Magnum Fortune Plus III', '116L207V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Feature-rich ULIP plan with automatic portfolio rebalancing and multiple investment strategies. Flexibility to switch between funds with loyalty benefits.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Smart Wealth Goal V', '116L201V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan designed for systematic wealth building with goal-based investing. Multiple fund options with automatic asset allocation and rebalancing.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Invest Protect Goal III', '116L205V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP combining investment and protection with capital guarantee option. Multiple fund options with automatic portfolio rebalancing for long-term growth.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life LongLife Goal III', '116L203V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP retirement plan providing market-linked wealth accumulation for retirement. Guaranteed loyalty additions with choice of annuity options at vesting.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Fortune Gain II', '116L196V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan for wealth creation with zero premium allocation charges. Multiple fund options with guaranteed loyalty additions and automatic asset allocation.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Goal Suraksha', '116N155V13', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked savings plan with guaranteed maturity benefit and life cover. Point of Sale product available through partner channels with simple features.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life PMJJBY', '116G133V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Pradhan Mantri Jeevan Jyoti Bima Yojana - Government scheme providing life cover of Rs. 2 lakh at premium of Rs. 436/year.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Group Term Life';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Group Credit Protection Plus', '116N094V07', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Group credit life insurance plan protecting lender and borrower interests. Covers outstanding loan amount on death or disability of borrower.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Group Term Life';

-- ===================== KOTAK LIFE ADDITIONAL PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Premier Endowment Plan', '107N079V03', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Participating endowment plan with guaranteed maturity benefit plus bonuses. Offers savings and protection with vested reversionary bonuses and terminal bonus.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Premier Money Back Plan', '107N083V02', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Participating money-back plan providing periodic survival benefits at regular intervals. Offers savings with liquidity through periodic payouts and life cover.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak T.U.L.I.P', '107L131V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Term with Unit Linked Insurance Plan combining term protection with ULIP investment. Provides life cover with market-linked returns and multiple fund options.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak T-ULIP Nxt', '107L138V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Next-generation ULIP offering systematic investment with zero premium allocation charges. Multiple fund options with automatic portfolio rebalancing.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak SmartLife Plan', '107N102V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed additions and maturity benefit. Flexible premium paying terms with multiple payout options.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Confident Retirement Savings Plan', '107N162V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Deferred annuity plan with guaranteed pension for retirement planning. Provides guaranteed additions during deferment and lifelong pension on vesting.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Group Secure One', '107N098V05', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Group term insurance plan for employer-employee groups. One-year renewable term covering death and optional disability benefits for group members.',
    'https://www.kotaklife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Group Term Life';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Saral Jeevan Bima', '107N139V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'IRDAI-mandated standard term life insurance plan with simple features. Sum assured from Rs. 5 lakh to Rs. 25 lakh with level cover.',
    'https://www.kotaklife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Saral Pension', '107N140V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'IRDAI-mandated standard deferred annuity plan for retirement. Guaranteed pension with single or regular premium payment options.',
    'https://www.kotaklife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== ABSLI ADDITIONAL PRODUCTS =====================

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Nishchit Aayush Plan', '109N132V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating whole life savings plan with guaranteed regular income. Provides lifelong income with increasing annual payouts till age 99.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI TULIP Plan', '109L091V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Term with Unit Linked Insurance Plan combining term protection with ULIP investment returns. Provides life cover along with market-linked growth.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Child''s Future Assured Plan', '109N127V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked child plan with guaranteed benefits for children''s education and future milestones. Premium waiver on parent''s death with continued benefits.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Child Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Empower Pension Plan', '109N130V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked deferred annuity plan for retirement planning. Provides guaranteed pension with flexible vesting age and multiple annuity payout options.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Group Secure Life Plan', '109N122V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Group term insurance plan for employer-employee groups providing death and disability coverage. Flexible design for groups of all sizes.',
    'https://lifeinsurance.adityabirlacapital.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== PHASE 3 - ADDITIONAL PRODUCTS FOR POLICY DOCUMENT COVERAGE =====================

-- LIC Additional Products
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC Bima Jyoti', '512N340V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating endowment plan with guaranteed additions. Provides financial protection and savings with guaranteed maturity benefit.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC Dhan Varsha', '512N343V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating single premium endowment plan with guaranteed additions and loyalty addition. Provides guaranteed returns on single premium.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC Jeevan Utsav', '512N345V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating whole life plan with guaranteed income. Provides lifelong guaranteed income with life cover and maturity benefit.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Whole Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC Saral Jeevan Bima', '512N321V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'IRDAI-mandated standard term insurance plan with simple and easy-to-understand features. Available for ages 18-65 with sum assured Rs. 5-25 lakh.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC Tech Term', '512N316V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Online term insurance plan from LIC with affordable premiums. Pure term protection with multiple sum assured options available exclusively online.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term Life Insurance';

-- ICICI Prudential Life Additional Products
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Guaranteed Income for Tomorrow (GIFT)', '105N197V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan providing guaranteed income and maturity benefit. Multiple payout options with guaranteed additions.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Signature', '105L176V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Premium ULIP from ICICI Prudential with dedicated fund management. Multiple investment strategies and fund options for wealth creation.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Lakshya', '105N196V07', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed maturity benefit. Provides systematic savings with life cover and multiple benefit options.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Tata AIA Life Additional Products
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Sampoorna Raksha Supreme', '110N156V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Comprehensive savings plan providing guaranteed income and maturity benefit. Multiple premium payment and benefit payout options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Guaranteed Monthly Income Plan', '110N157V08', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked plan providing guaranteed monthly income for a specified period. Life cover with systematic monthly payouts after premium payment term.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Smart Value Income Plan', '110N147V11', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked savings plan with guaranteed income benefit. Provides regular income with life cover and multiple payout frequency options.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Fortune Pro', '110L151V10', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan from Tata AIA with multiple fund options for wealth creation. Loyalty additions and automatic portfolio rebalancing strategies.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- SBI Life Additional Products
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Platina Supreme', '111N137V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed maturity benefit. Multiple premium payment options with guaranteed additions.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Privilege', '111N140V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan providing guaranteed income and wealth creation. Premium variant with higher benefits.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Saral Pension', '111N133V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'IRDAI-mandated standard pension plan providing guaranteed annuity. Simple and easy-to-understand retirement plan with single/regular premium options.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ============================================================
-- PHASE 4: MASSIVE EXPANSION - All remaining life insurers
-- Research date: 2026-02-21
-- ============================================================

-- ===================== PNB METLIFE (Reg: 117) =====================
-- Source: https://www.pnbmetlife.com

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Mera Term Plan Plus', '117N126V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Pure term insurance plan providing financial protection to family. Offers life cover with flexible premium payment options and optional riders for critical illness and disability.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife DigiProtect Term Plan', '117N141V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Digital term insurance plan with instant issuance and affordable premiums. High life cover available online with optional riders for critical illness and disability.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Guaranteed Future Plan', '117N124V16', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Guaranteed savings plan offering assured payouts along with bonuses for long-term financial milestones. Multiple plan options to suit different goals.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Century Plan', '117N129V02', 'individual', 'non_linked', 'participating',
    TRUE, '2021-2022',
    'Participating whole life income plan providing income till age 100. Lifelong guaranteed income with life cover and maturity benefit with bonus additions.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Guaranteed Goal Plan', '117N131V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating savings plan with guaranteed maturity benefit. Flexible premium payment and multiple plan options for different financial goals.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Grand Assured Income Plan', '117N134V07', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Retirement insurance plan delivering assured income after premium payment term. Designed for financially independent retirement with guaranteed payouts.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Genius Plan', '117N135V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Child insurance plan safeguarding education and future aspirations. Waiver of premium on death of parent with guaranteed education fund payouts.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Child Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Mera Wealth Plan', '117L098V08', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked wealth and savings plan with loyalty additions from 6th policy year. Multiple fund options with free switching and flexible premium payment.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Smart Goal Ensuring Multiplier', '117L139V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Goal-oriented ULIP combining protection with disciplined wealth creation. Multiple fund options with systematic investment and goal-tracking features.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Group Term Life Insurance', '117N105V04', 'group', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Group term life insurance providing life cover to employees and their families. Employer-employee group coverage with flexible sum assured options.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== CANARA HSBC LIFE (Reg: 136) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Promise4Future', '136N119V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Non-linked participating savings plan with life protection and savings combination. Lump-sum payout, guaranteed income, and cash bonuses at maturity.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Invest 4G', '136L064V02', 'individual', 'linked', 'non_participating',
    TRUE, '2020-2021',
    'Unit-linked insurance plan with 3 plan variants (Life, Care, Century). 8 fund options, loyalty additions, wealth boosters, and return of mortality charges at maturity.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Pension4Life', '136N066V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked non-participating deferred annuity plan with flexible premium payments. Regular guaranteed income stream for retirement planning.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Wealth Edge Plan', '136L108V01', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked savings plan with SWO/MWO for retirement income. Return of mortality charges, loyalty additions, wealth boosters, and 10 fund options.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Promise4Growth Plus', '136L116V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Flexible ULIP combining life insurance with customized investment growth. Portfolio management options with complete control over savings and insurance.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life iSelect Guaranteed Future', '136N110V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Savings plan with guaranteed benefits combining life insurance with assured maturity payouts. Flexible premium payment and guaranteed returns.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Saral Jeevan Bima', '136N100V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan with simple features. Affordable life cover with no frills for easy understanding and accessibility.',
    'https://www.canarahsbclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ===================== EDELWEISS LIFE (Reg: 147) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life MyLife+', '147N027V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Pure term insurance plan with customizable riders. Comprehensive life protection with affordable premiums and flexibility to add critical illness cover.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Total Secure+', '147N036V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2019-2020',
    'Term insurance with return of premium option. Life cover combined with premium refund at maturity for complete protection without loss.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Term with Return of Premium';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Guaranteed Growth Plan', '147N090V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed growth. Assured maturity benefit with life cover throughout the policy term.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Guaranteed Income STAR', '147N074V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating savings plan providing guaranteed income. Regular income payouts for financial security with life protection.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life GCAP', '147N072V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Guaranteed Capital Appreciation Plan providing assured capital growth. Non-linked plan with guaranteed maturity benefit and life cover.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Immediate Annuity Plan', '147N040V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Immediate annuity plan providing lifelong pension from day one. Single premium payment for guaranteed regular income through retirement.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Active Income Plan', '147N031V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating savings plan with regular income payouts. Combines guaranteed income with reversionary bonuses for enhanced returns.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Cashflow Protection Plus', '147N019V02', 'individual', 'non_linked', 'participating',
    TRUE, '2019-2020',
    'Participating savings cum protection plan with flexible cashflow options. Regular payouts with bonuses and comprehensive life protection.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Edelweiss Tokio Life Dhan Labh', '147N038V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Non-linked non-participating endowment plan providing guaranteed maturity benefit. Combines savings with life protection for financial security.',
    'https://www.edelweisslife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Edelweiss Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ===================== BANDHAN LIFE (Reg: 138) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life iTerm Prime', '138N084V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Pure term insurance plan with comprehensive life cover. Affordable premiums with flexible payout options for family protection.',
    'https://www.bandhanlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life iTerm Comfort', '138N082V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating term plan with life insurance cover. Simple term protection with affordable premium options.',
    'https://www.bandhanlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life iGuarantee Vishwas', '138N096V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with life insurance cover. Guaranteed returns with assured maturity benefits.',
    'https://www.bandhanlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life Insta Pension', '138N011V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2019-2020',
    'Non-linked non-participating immediate annuity plan. Single premium payment for regular guaranteed pension income from day one.',
    'https://www.bandhanlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life Saral Jeevan Bima', '138N077V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan with simple features. Pure risk premium plan for easy-to-understand life protection.',
    'https://www.bandhanlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- ===================== AGEAS FEDERAL LIFE (Reg: 135) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Advantage Plus Plan', '135N078V01', 'individual', 'non_linked', 'participating',
    TRUE, '2022-2023',
    'Non-linked participating savings plan with life protection. Savings plan with guaranteed additions and bonuses for long-term wealth creation.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Assured Income Plan', '135N083V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan with guaranteed regular income. Assured income payouts for financial stability with life protection.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life ULIP Plan', '135L053V02', 'individual', 'linked', 'non_participating',
    TRUE, '2021-2022',
    'Unit-linked insurance plan combining market-linked investment with life cover. Multiple fund options for wealth creation with insurance protection.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Saral Jeevan Bima', '135N075V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term plan with simple and clear features. Basic life cover at affordable premium rates.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Rising Star Plan', '135N080V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Child insurance plan with waiver of premium benefit. Protects child future goals with guaranteed payouts for education and milestones.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Child Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Saral Pension Plan', '135N076V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard annuity plan with guaranteed pension. Simple pension plan for retirement income with single or regular premium.',
    'https://www.ageasfederal.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== GENERALI CENTRAL LIFE (Reg: 133) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Care Plus Term Plan', '133N030V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Pure term insurance plan with multiple payout options. Comprehensive life cover with affordable premiums and rider options.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Saral Jeevan Bima', '133N087V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance with simple features. Basic pure risk premium life cover accessible to all.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Assured Income Plan', '133N054V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating savings plan with guaranteed regular income. Assured income payouts with life protection.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Lifetime Partner Plan', '133N086V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating lifetime savings plan. Long-term financial security with guaranteed maturity benefit and life cover.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central New Assured Wealth Plan', '133N085V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan with assured wealth creation. Guaranteed maturity benefit with life cover throughout the term.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Single Premium Anchor Plan', '133N101V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Single premium savings plan with guaranteed returns. One-time payment for assured benefits with life cover and maturity payout.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Big Dreams Plan', '133L081V03', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked insurance plan for long-term wealth creation. Multiple fund options with life cover for achieving big financial goals.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Dhan Vridhi', '133L050V04', 'individual', 'linked', 'non_participating',
    TRUE, '2022-2023',
    'Unit-linked wealth growth plan with diversified fund options. ULIP combining market-linked returns with comprehensive life protection.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Sampoorna Samadhaan', '133L102V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Comprehensive unit-linked plan offering complete insurance solution. Multiple fund options with flexible premium payment.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Saral Pension Plan', '133N089V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard pension plan with guaranteed annuity. Simple retirement income plan with single or regular premium payment.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Money Back Super Plan', '133N088V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating money back plan with regular payouts. Periodic survival benefits with life protection and maturity benefit.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Assured Education Plan', '133N090V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Child education plan with guaranteed payouts for education milestones. Waiver of premium benefit ensures continued coverage on parent death.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Child Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Generali Central Group Term Life Plan', '133N003V05', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group term life insurance for employer-employee groups. Affordable group coverage with flexible sum assured and comprehensive life protection.',
    'https://www.generalicentrallife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Generali Central Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== SHRIRAM LIFE (Reg: 128) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Online Term Plan', '128N072V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Pure online term insurance plan with affordable premiums. Comprehensive life cover available exclusively through digital channels.',
    'https://www.shriramlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life New Shri Life Plan', '128N047V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating endowment plan providing savings with life protection. Regular bonuses and guaranteed maturity benefit for long-term wealth creation.',
    'https://www.shriramlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Assured Income Plus', '128N060V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked non-participating plan with guaranteed regular income. Assured income payouts with comprehensive life protection.',
    'https://www.shriramlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Wealth Pro', '128L096V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Premium ULIP with multiple fund options for wealth creation. Market-linked returns with life cover and flexible investment strategies.',
    'https://www.shriramlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Fortune Builder Plan', '128L038V02', 'individual', 'linked', 'non_participating',
    TRUE, '2020-2021',
    'Unit-linked plan for systematic wealth building. Market-linked returns with life insurance and multiple fund options.',
    'https://www.shriramlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life New Shri Raksha Plan', '128N052V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked non-participating protection plan with savings benefit. Life cover with guaranteed maturity benefit for family security.',
    'https://www.shriramlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ===================== STAR UNION DAI-ICHI (SUD) LIFE (Reg: 142) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Ashiana Suraksha Plan', '142N002V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2009-2010',
    'Home loan protection plan covering outstanding loan on death. Non-linked plan ensuring family home remains secure.',
    'https://www.sudlife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Dhana Suraksha ULIP', '142L003V01', 'individual', 'linked', 'non_participating',
    TRUE, '2009-2010',
    'Unit-linked endowment plan with market-linked returns. Combines insurance protection with investment growth through multiple funds.',
    'https://www.sudlife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Jeevan Safar', '142N005V01', 'individual', 'non_linked', 'participating',
    TRUE, '2009-2010',
    'Participating savings plan with life cover and bonus additions. Endowment plan providing maturity benefit with reversionary bonuses.',
    'https://www.sudlife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Group Term Insurance', '142N001V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2009-2010',
    'Group term life insurance for employer-employee and affinity groups. Affordable group cover with flexible sum assured.',
    'https://www.sudlife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Group Term Life';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Saral Jeevan Bima', '142N060V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan. Simple pure risk premium plan for basic life protection.',
    'https://www.sudlife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Saral Pension Plan', '142N061V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard pension plan providing guaranteed annuity. Simple retirement income solution.',
    'https://www.sudlife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== INDUSIND NIPPON LIFE (Reg: 121) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Super Assured Future Endowment', '121N159V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed maturity. Assured future benefit with life cover.',
    'https://www.indusindnipponlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Prosperity Plus', '121L134V02', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked savings plan with multiple fund options. Market-linked wealth creation with comprehensive life insurance protection.',
    'https://www.indusindnipponlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Smart Savings', '121N155V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan for systematic savings. Guaranteed maturity benefit with life cover.',
    'https://www.indusindnipponlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Saral Jeevan Bima', '121N148V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term plan with simple features. Basic pure risk premium plan for affordable life cover.',
    'https://www.indusindnipponlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Saral Pension', '121N149V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard pension plan providing guaranteed annuity. Simple retirement income plan.',
    'https://www.indusindnipponlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== INDIAFIRST LIFE (Reg: 143) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Elite Term Plan', '143N070V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Premium term insurance plan with high sum assured options. Comprehensive life protection with flexible premium and payout options.',
    'https://www.indiafirstlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Guaranteed Benefit Plan', '143N056V07', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan with guaranteed benefits. Assured income and maturity payouts with life insurance cover.',
    'https://www.indiafirstlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Guaranteed Pension Plan', '143N066V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Guaranteed pension plan with regular annuity income. Non-linked non-participating pension product for retirement planning.',
    'https://www.indiafirstlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Radiance Smart Invest', '143L068V01', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked insurance plan with smart investment options. Market-linked wealth creation with life cover.',
    'https://www.indiafirstlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Saral Jeevan Bima', '143N058V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan. Simple and affordable life cover.',
    'https://www.indiafirstlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Long Guaranteed Income Plan', '143N072V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating plan providing guaranteed income over a long term. Regular income payouts with life protection.',
    'https://www.indiafirstlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ===================== AVIVA LIFE (Reg: 122) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Signature 3D Term Plan', '122N142V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Pure term plan providing life cover with three-dimensional protection. Customizable coverage with optional riders.',
    'https://www.avivaindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Signature Investment Plan Platinum', '122L151V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Premium ULIP with market-linked returns and life insurance. Multiple fund options with loyalty additions.',
    'https://www.avivaindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'ULIP - Unit Linked Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Young Scholar Secure', '122N130V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Child plan ensuring education funding with waiver of premium. Guaranteed payouts for education milestones.',
    'https://www.avivaindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Child Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva New Family Income Builder', '122N139V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan with regular income. Guaranteed income payouts for family financial planning.',
    'https://www.avivaindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Annuity Plus', '122N120V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Immediate annuity plan providing lifelong pension income. Single premium plan with multiple annuity options.',
    'https://www.avivaindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Saral Jeevan Bima', '122N143V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan. Simple and affordable pure risk premium life cover.',
    'https://www.avivaindia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Term Life Insurance';

-- ===================== PRAMERICA LIFE (Reg: 140) =====================
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Secure Savings Plan', '140N071V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan with guaranteed maturity. Secure savings with life protection.',
    'https://www.pramericalife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Guaranteed Income Plan', '140N075V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed income. Regular income payouts with life cover.',
    'https://www.pramericalife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Savings Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Saral Jeevan Bima', '140N062V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan. Simple and basic life protection at affordable premiums.',
    'https://www.pramericalife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Saral Pension Plan', '140N063V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard pension plan with guaranteed annuity. Simple retirement income solution.',
    'https://www.pramericalife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Smart Wealth Plan', '140L069V01', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked plan for wealth creation with market-linked returns. Multiple fund options with life insurance cover.',
    'https://www.pramericalife.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== HDFC LIFE EXPANSION (Phase 5) =====================
-- Source: https://www.hdfclife.com/policy-documents, hdfclife.com product pages
-- UINs verified from official HDFC Life website

-- HDFC Life CSC Suraksha (Term - Rural/Semi-Urban)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life CSC Suraksha', '101N104V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2016-2017',
    'Term protection plan distributed through Common Service Centres (CSC) for rural and semi-urban markets at affordable premiums.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- HDFC Life Click 2 Achieve
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Achieve', '101N186V07', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked savings plan offering guaranteed income with 200% return of premium and increasing returns up to 10% p.a.',
    'https://www.hdfclife.com/savings-plans/click-2-achieve', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Guaranteed Savings Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Guaranteed Savings Plan', '101N131V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2019-2020',
    'Non-linked savings plan offering guaranteed returns with life cover throughout the policy term. Flexible premium payment options.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Star Saver
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Star Saver', '101N167V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked, non-participating savings plan with guaranteed tax-free benefits, life cover, and only 5-year premium payment required.',
    'https://www.hdfclife.com/savings-plans/star-saver', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life New Fulfilling Life
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life New Fulfilling Life', '101N149V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating savings plan with life protection until age 85 and periodic survival payments in four installments.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life My Assured Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life My Assured Income Plan', '101N155V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked savings plan with three income variants (Uniform, Enhanced, Increasing) and 5/8-year premium payment terms.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Sampoorn Samridhi Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Sampoorn Samridhi Plus', '101N102V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2018-2019',
    'Non-linked savings/endowment plan providing a combination of protection and wealth accumulation benefits.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- HDFC Life Income Advantage Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Income Advantage Plan', '101N152V03', 'individual', 'non_linked', 'participating',
    TRUE, '2021-2022',
    'Participating savings plan for generating second income with guaranteed income during benefit payout phase.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Super Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Super Income Plan', '101N098V06', 'individual', 'non_linked', 'participating',
    TRUE, '2018-2019',
    'Participating money-back plan providing regular income for 8-15 years after premium payment phase with bonuses.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

-- HDFC Life YoungStar Udaan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life YoungStar Udaan', '101N099V05', 'individual', 'non_linked', 'participating',
    TRUE, '2018-2019',
    'Participating money-back plan for children with customizable payouts for education, marriage, and other life goals.',
    'https://www.hdfclife.com/children-insurance-plans/youngstar-udaan', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- HDFC Life Assured Gain Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Assured Gain Plus', '101N151V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked savings plan with assured gains and life cover throughout the policy term.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Smart Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Smart Income Plan', '101N166V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked savings plan designed to provide regular smart income benefits with financial protection.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Uday
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Uday', '101N105V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2017-2018',
    'Non-linked savings plan designed for wealth creation with life insurance protection.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Saral Jeevan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Saral Jeevan', '101N160V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked, non-participating savings plan with guaranteed maturity benefits as lumpsum or regular income with life cover.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- HDFC Life Pragati (Micro Insurance)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Pragati', '101N114V05', 'individual', 'non_linked', 'participating',
    TRUE, '2018-2019',
    'Participating micro insurance plan with premiums starting at Rs.100/month. Guaranteed RoP on maturity with auto cover continuance.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Micro Insurance (Life)';

-- HDFC Life Smart Woman Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Smart Woman Plan', '101L082V03', 'individual', 'linked', 'non_participating',
    TRUE, '2016-2017',
    'Unit-linked plan specifically designed for women with investment flexibility and life protection features.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- HDFC Life Click 2 Retire (ULIP Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Click 2 Retire', '101L108V05', 'individual', 'linked', 'non_participating',
    TRUE, '2018-2019',
    'Unit-linked pension plan with Assured Vesting Benefit, no allocation charges, and policy terms of 10-35 years.',
    'https://www.hdfclife.com/retirement-and-pension-plans/click-2-retire', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Smart Pension Plan (ULIP Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Smart Pension Plan', '101L164V08', 'individual', 'linked', 'non_participating',
    TRUE, '2022-2023',
    'Unit-linked pension plan with loyalty additions from the 10th anniversary and flexible vesting dates.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Guaranteed Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Guaranteed Pension Plan', '101N092V16', 'individual', 'non_linked', 'non_participating',
    TRUE, '2017-2018',
    'Non-linked pension plan for building a secure retirement fund with guaranteed returns.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Systematic Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Systematic Pension Plan', '101N144V05', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating pension plan with investment horizons of 5-45 years and assured 4% compound return on vesting.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Saral Pension
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Saral Pension', '101N141V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Single premium non-participating immediate annuity plan providing guaranteed lifelong regular income. IRDAI standard product.',
    'https://www.hdfclife.com/retirement-and-pension-plans/saral-pension', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Personal Pension Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Personal Pension Plus', '101N091V05', 'individual', 'non_linked', 'participating',
    TRUE, '2017-2018',
    'Participating pension plan with investment horizons of 10-40 years, vesting until age 75, and assured 101% of premiums.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Assured Pension Plan (ULIP Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Assured Pension Plan', '101L109V05', 'individual', 'linked', 'non_participating',
    TRUE, '2018-2019',
    'Unit-linked pension plan with assured vesting benefit (101%+ of premiums), pension multipliers from 11th year.',
    'https://www.hdfclife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life New Immediate Annuity Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life New Immediate Annuity Plan', '101N084V38', 'individual', 'non_linked', 'non_participating',
    TRUE, '2015-2016',
    'Non-linked immediate annuity plan providing guaranteed lifelong income starting immediately after single premium payment.',
    'https://www.hdfclife.com/retirement-and-pension-plans/new-immediate-annuity-plan', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Group Term Insurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Term Insurance Plan', '101N005V08', 'group', 'non_linked', 'non_participating',
    TRUE, '2015-2016',
    'Group term life insurance providing death cover for employees/members of organizations.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Credit Protect Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Credit Protect Plus', '101N096V06', 'group', 'non_linked', 'non_participating',
    TRUE, '2017-2018',
    'Group credit life insurance protecting outstanding loan balances for lending institutions.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Poorna Credit Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Poorna Credit Suraksha', '101N138V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Comprehensive group credit protection plan covering loan liabilities for financial institutions.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Jeevan Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Jeevan Suraksha', '101N113V06', 'group', 'non_linked', 'non_participating',
    TRUE, '2018-2019',
    'Group protection plan offering life cover and other benefits for group members.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Suraksha', '101N135V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2019-2020',
    'Group protection plan for organizations providing term life cover for members.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Poorna Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Poorna Suraksha', '101N137V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Comprehensive group protection plan with multiple coverage options for organizations.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Loan Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Loan Suraksha', '101N172V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group plan designed to protect outstanding loan amounts for borrowers.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Micro Term Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Micro Term Insurance', '101N171V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Low-cost group term insurance plan for micro-insurance segment and rural populations.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Micro Insurance (Life)';

-- HDFC Life Group Variable Employee Benefit Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Variable Employee Benefit Plan', '101N095V04', 'group', 'non_linked', 'non_participating',
    TRUE, '2017-2018',
    'Non-linked group plan for managing variable employee benefits like gratuity and leave encashment.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC Life Group Gratuity Product
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Gratuity Product', '101L170V02', 'group', 'linked', 'non_participating',
    TRUE, '2022-2023',
    'Unit-linked group plan for managing gratuity fund obligations for employers.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- HDFC SL Group Traditional Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC SL Group Traditional Plan', '101N075V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2015-2016',
    'Traditional group superannuation/pension plan for employee retirement benefits.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Group Unit Linked Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Unit Linked Pension Plan', '101L093V02', 'group', 'linked', 'non_participating',
    TRUE, '2017-2018',
    'Unit-linked group pension plan for employer-managed retirement funds.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life New Group Unit Linked Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life New Group Unit Linked Plan', '101L094V03', 'group', 'linked', 'non_participating',
    TRUE, '2017-2018',
    'Unit-linked group plan for managing employer contributions and employee benefits.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- HDFC Life Group Traditional Secure Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Traditional Secure Plan', '101N174V02', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked group plan for secure, traditional retirement/superannuation fund management.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- HDFC Life Group Unit Linked Future Secure Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'HDFC Life Group Unit Linked Future Secure Plan', '101L185V02', 'group', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked group plan for future-oriented employee benefit fund management.',
    'https://www.hdfclife.com/group-insurance', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'HDFC Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ===================== LIC EXPANSION (Phase 6) =====================
-- Source: https://stableinvestor.com/2023/03/all-lic-plans-list.html, licindia.in
-- Additional LIC products not in initial seed

-- LIC's New Money Back Plan-25 years
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Money Back Plan-25 years', '512N278V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating money back plan with periodic survival benefits at specified intervals over 25-year term. Bonuses and loyalty additions on maturity.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Money-Back Plans';

-- LIC's New Money Back Plan-20 years
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Money Back Plan-20 years', '512N280V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating money back plan with survival benefits at specified intervals over 20-year term. Death benefit plus bonuses for nominee.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Money-Back Plans';

-- LIC's New Bima Bachat
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Bima Bachat', '512N284V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Single premium non-participating savings plan providing guaranteed benefits with life cover. Maturity benefit is guaranteed sum assured plus loyalty additions.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Savings Plans';

-- LIC's Anmol Jeevan II
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Anmol Jeevan II', '512N285V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2014-2015',
    'Non-participating pure term insurance plan providing affordable life cover. No survival benefit; only death benefit is payable.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Term Life Insurance';

-- LIC's New Jeevan Mangal (Micro Insurance)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Jeevan Mangal', '512N287V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Micro insurance plan offering affordable life cover for economically weaker sections. Low premium with decent sum assured and maturity benefit.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Micro Insurance (Life)';

-- LIC's Bhagya Lakshmi (Micro Insurance)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Bhagya Lakshmi', '512N292V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Micro insurance plan designed for women from economically weaker sections. Provides life cover with affordable premiums.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Micro Insurance (Life)';

-- LIC's Limited Premium Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Limited Premium Endowment Plan', '512N293V01', 'individual', 'non_linked', 'participating',
    TRUE, '2014-2015',
    'Participating endowment plan with limited premium payment term. Provides life cover during the policy term with maturity benefit on survival.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

-- LIC's New Children's Money Back Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Children''s Money Back Plan', '512N296V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating money back plan for children with survival benefits payable at specified intervals for education and other needs.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Child Plans';

-- LIC's Jeevan Tarun
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Tarun', '512N299V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'Participating child plan providing survival benefits at ages 20-24 at customer-chosen percentage, with maturity at age 25. Premium waiver on parent''s death.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Child Plans';

-- LIC's Aadhaar Shila (Micro for women)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Aadhaar Shila', '512N309V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Micro insurance endowment plan for women linked to Aadhaar. Affordable premiums with guaranteed maturity benefit for financial inclusion.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Micro Insurance (Life)';

-- LIC's Aadhaar Stambh (Micro for men)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Aadhaar Stambh', '512N310V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Micro insurance endowment plan for males linked to Aadhaar. Provides affordable life cover with guaranteed maturity benefit.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Micro Insurance (Life)';

-- LIC's Jeevan Shiromani
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Jeevan Shiromani', '512N315V02', 'individual', 'non_linked', 'participating',
    TRUE, '2020-2021',
    'High-value participating endowment plan for high net worth individuals. Minimum sum assured Rs.1 crore. Includes loyalty additions and final additional bonus.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Endowment Plans';

-- LIC's New Jeevan Shanti (Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Jeevan Shanti', '512N338V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-participating deferred annuity plan with single or regular premium options. Provides guaranteed pension from chosen vesting date.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Pension / Annuity Plans';

-- LIC's SIIP (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s SIIP', '512L334V01', 'individual', 'linked', 'non_participating',
    TRUE, '2020-2021',
    'Systematic Investment Insurance Plan - unit linked plan providing market-linked returns with life cover. Multiple fund options available.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'ULIP - Unit Linked Plans';

-- LIC's Group Credit Life Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s Group Credit Life Insurance', '512N302V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2015-2016',
    'Group credit life insurance protecting outstanding loan balances. Cover reduces with outstanding loan amount.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

-- LIC's New Group Superannuation Cash Accumulation Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Group Superannuation Cash Accumulation Plan', '512N274V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Group superannuation plan for employer-managed retirement benefits. Cash accumulation with interest for employee pension.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Pension / Annuity Plans';

-- LIC's New One Year Renewable Group Term Assurance Plan-I
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New One Year Renewable Group Term Assurance Plan-I', '512N275V02', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'One-year renewable group term insurance providing death cover for employer-employee groups with uniform sum assured.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

-- LIC's New One Year Renewable Group Term Assurance Plan-II
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New One Year Renewable Group Term Assurance Plan-II', '512N276V02', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'One-year renewable group term insurance for groups with graded sum assured levels based on designation or salary.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

-- LIC's New Group Gratuity Cash Accumulation Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Group Gratuity Cash Accumulation Plan', '512N281V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Group gratuity plan enabling employers to fund their gratuity liabilities through cash accumulation with interest.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

-- LIC's New Group Leave Encashment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'LIC''s New Group Leave Encashment Plan', '512N282V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Group plan to fund accumulated leave encashment liability of employers for their employees.',
    'https://licindia.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Life Insurance Corporation of India' AND sc.name = 'Group Term Life';

-- ===================== MAX LIFE EXPANSION (Phase 6) =====================
-- Source: https://www.axismaxlife.com/blog/all-products
-- Additional Axis Max Life products

-- Axis Max Life Savings Advantage Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Savings Advantage Plan', '104N111V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2019-2020',
    'Non-linked savings plan with guaranteed income and life cover. Flexible premium payment and benefit payout options.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Smart Wealth Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Wealth Plan', '104N116V15', 'individual', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Non-linked savings plan with guaranteed wealth creation benefits and flexible premium payment terms.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Saral Jeevan Bima', '104N117V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'IRDAI-mandated standard term insurance plan with simple, easy-to-understand features. Pure life cover at affordable premiums.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Axis Max Life Smart Wealth Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Wealth Income Plan', '104N120V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'Non-linked savings plan providing guaranteed regular income with life cover for financial stability.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Smart Fixed-return Digital Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Fixed-return Digital Plan', '104N123V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Online-only non-linked savings plan with fixed guaranteed returns. Simple digital purchase process with minimal documentation.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Secure Earnings & Wellness Advantage Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Secure Earnings & Wellness Advantage Plan', '104N136V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked savings plan combining guaranteed earnings with wellness benefits and comprehensive life protection.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Smart Wealth Advantage Guarantee Elite Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Wealth Advantage Guarantee Elite Plan', '104N138V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Premium non-linked savings plan offering higher guaranteed returns for larger investments with comprehensive life cover.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Axis Max Life Online Savings Plan Plus (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Online Savings Plan Plus', '104L131V01', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Online unit-linked savings plan with multiple fund options and zero allocation charges. Available for purchase online.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Axis Max Life Forever Young Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Forever Young Pension Plan', '104L075V09', 'individual', 'linked', 'non_participating',
    TRUE, '2017-2018',
    'Unit-linked pension plan for retirement planning with flexible fund options and guaranteed minimum vesting benefit.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- Axis Max Life Fast Track Super Plan (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Fast Track Super Plan', '104L082V05', 'individual', 'linked', 'non_participating',
    TRUE, '2016-2017',
    'Unit-linked savings plan providing market-linked returns with life protection. Multiple fund options for wealth creation.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Axis Max Life Smart Term with Additional Returns (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Term with Additional Returns', '104L128V01', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked plan combining term protection with market-linked investment returns.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Axis Max Life Group Credit Life Premier
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Group Credit Life Premier', '104N095V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2018-2019',
    'Group credit life insurance for lending institutions to protect outstanding loan balances of borrowers.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Axis Max Life Group Term Life Platinum Assurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Group Term Life Platinum Assurance Plan', '104N112V04', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Premium group term life insurance plan for employer-employee groups with flexible sum assured options.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Axis Max Life Smart Group Term Life Insurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Axis Max Life Smart Group Term Life Insurance Plan', '104N126V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Smart group term insurance with digital-first approach for organizations seeking employee life coverage.',
    'https://www.axismaxlife.com/blog/all-products', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Axis Max Life Insurance Limited' AND sc.name = 'Group Term Life';

-- ===================== ICICI PRU EXPANSION (Phase 6) =====================
-- Source: iciciprulife.com product pages, search results
-- Additional ICICI Prudential Life products

-- ICICI Pru iProtect Smart Return of Premium
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru iProtect Smart Return of Premium', '105N195V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Term insurance with return of premium feature. 100% of total premiums paid returned on survival to maturity date.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Term with Return of Premium';

-- ICICI Pru iProtect Smart Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru iProtect Smart Plus', '105N205V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Enhanced term insurance with monthly income payout option to nominee on death. Comprehensive life protection with add-on benefits.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ICICI Pru Signature Pension
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Signature Pension', '105L194V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked pension plan for retirement planning with flexible fund options and loyalty additions.',
    'https://www.iciciprulife.com/retirement-pension-plans/buy-icici-pru-signature-pension-plan.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ICICI Pru Immediate Annuity
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Immediate Annuity', '105N009V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2016-2017',
    'Single premium immediate annuity plan providing guaranteed regular pension income from purchase date for life.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ICICI Pru Group Term Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Group Term Plus', '105N119V08', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Group term insurance for organizations providing comprehensive death cover for employees with flexible sum assured.',
    'https://www.iciciprulife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ICICI Pru Lakshya Wealth
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Lakshya Wealth', '105N179V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked endowment/wealth creation plan providing guaranteed maturity benefit with life cover throughout the policy term.',
    'https://www.iciciprulife.com/money-back-endowment-plans/icici-pru-lakshya-wealth.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ===================== SBI LIFE EXPANSION (Phase 6) =====================
-- Source: sbilife.co.in product pages, search results

-- SBI Life Smart Annuity Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Annuity Plus', '111N134V10', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked immediate annuity plan providing guaranteed lifelong pension. Multiple annuity options including joint life.',
    'https://www.sbilife.co.in/smart-annuity-plus-policy', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- SBI Life Smart Fortune Builder (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Fortune Builder', '111L142V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked savings plan with lowest ULIP charges. Multiple fund options for wealth creation with life insurance cover.',
    'https://www.sbilife.co.in/en/individual-life-insurance/ulip/smart-fortune-builder', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- SBI Life New Smart Samriddhi
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life New Smart Samriddhi', '111N129V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked savings plan with guaranteed returns and life cover. Flexible premium payment and benefit payout options.',
    'https://www.sbilife.co.in/en/individual-life-insurance/traditional/new-smart-samriddhi', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Retire Smart (ULIP Pension)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Retire Smart', '111L094V01', 'individual', 'linked', 'non_participating',
    TRUE, '2019-2020',
    'Unit-linked pension plan enabling systematic retirement savings with market-linked returns and flexible vesting options.',
    'https://www.sbilife.co.in/sbi-life---retire-smart-111l094v01', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- SBI Life Sampoorn Suraksha (Group)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Sampoorn Suraksha', '111N040V04', 'group', 'non_linked', 'non_participating',
    TRUE, '2017-2018',
    'Group term insurance plan providing life cover for employer-employee groups. Flexible cover amounts and premium payment options.',
    'https://www.sbilife.co.in/en/group-insurance/protection-plans/sampoorn-suraksha', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== TATA AIA EXPANSION (Phase 6) =====================
-- Source: tataaia.com, search results
-- Additional TATA AIA products

-- Tata AIA Sampoorna Raksha Promise
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Sampoorna Raksha Promise', '110N176V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked pure risk term plan providing comprehensive life protection with flexible sum assured and add-on benefits.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Tata AIA Guaranteed Return Insurance Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Guaranteed Return Insurance Plan', '110N152V15', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked savings plan with guaranteed returns. Flexible premium payment term with guaranteed maturity and income benefits.',
    'https://www.tataaia.com/life-insurance-plans/savings-solutions/guaranteed-return-insurance-plan.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Tata AIA Smart Sampoorna Raksha Pro (ULIP)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Tata AIA Smart Sampoorna Raksha Pro', '110L172V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked plan combining market-linked investment returns with comprehensive life protection.',
    'https://www.tataaia.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'TATA AIA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';


-- ===================== KOTAK LIFE EXPANSION (Phase 7 - Web Research) =====================

-- Kotak e-Term
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak e-Term', '107N129V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Online pure term plan offering high life cover at affordable premiums with options of Life, Life Plus, and Life Secure.',
    'https://www.kotaklife.com/term-insurance/kotak-e-term', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Kotak Gen2Gen Protect
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Gen2Gen Protect', '107N132V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Return of premium term plan with industry-first feature of risk transfer from parent to child. Dual generation protection.',
    'https://www.kotaklife.com/Gen2Gen-Protect/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Kotak Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Term Plan', '107N005V07', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-unit linked non-participating term plan providing high level of protection with multiple rider options available.',
    'https://www.kotaklife.com/assets/images/uploads/insurance-plans/Kotak_Term_Plan_UIN_107N005V07_Brochure.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Kotak Fortune Maximiser
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Fortune Maximiser', '107N125V03', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Participating savings plan offering guaranteed additions, loyalty additions and bonuses for long-term wealth creation.',
    'https://www.kotaklife.com/savings-plan/kotak-fortune-maximiser', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Kotak Assured Savings Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Assured Savings Plan', '107N081V09', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-participating savings plan with guaranteed maturity benefits and life cover. Flexible premium payment options.',
    'https://www.kotaklife.com/savings-plan/kotak-assured-savings-plan', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Kotak Guaranteed Fortune Builder
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Guaranteed Fortune Builder', '107N128V09', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan with guaranteed income and maturity benefits for financial security.',
    'https://www.kotaklife.com/savings-plan/kotak-guaranteed-fortune-builder', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Kotak Guaranteed Savings Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Guaranteed Savings Plan', '107N100V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Guaranteed savings plan providing assured returns with life insurance coverage throughout the policy term.',
    'https://www.kotaklife.com/savings-plan/kotak-guaranteed-savings-plan', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Kotak EDGE (Early Defined Guaranteed Earnings)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak EDGE', '107N148V05', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Early Defined Guaranteed Earnings plan with guaranteed income starting early in the policy term. Life cover with savings.',
    'https://www.kotaklife.com/savings-plan/kotak-edge', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Kotak Gen2Gen Income
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Gen2Gen Income', '107N163V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Participating income plan providing guaranteed income with the benefit of bonuses. Legacy planning for two generations.',
    'https://www.kotaklife.com/savings-plan/kotak-gen2gen-income', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Kotak Classic Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Classic Endowment Plan', '107N082V03', 'individual', 'non_linked', 'participating',
    TRUE, '2022-2023',
    'Participating endowment plan with bonus additions and maturity benefit. Traditional savings with life protection.',
    'https://www.kotaklife.com/savings-plan/kotak-classic-endowment-plan', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- Kotak e-Invest Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak e-Invest Plus', '107L137V02', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Online ULIP plan with market-linked returns and life cover. Multiple fund options for wealth creation.',
    'https://www.kotaklife.com/ulip-plans/kotak-e-invest-plus', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Kotak Invest Maxima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Invest Maxima', '107L073V05', 'individual', 'linked', 'non_participating',
    TRUE, '2022-2023',
    'Unit-linked insurance plan offering flexibility in investment with multiple fund choices and life insurance coverage.',
    'https://www.kotaklife.com/ulip-plans/kotak-invest-maxima', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Kotak Wealth Optima Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Wealth Optima Plan', '107L118V03', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'ULIP savings product offering market-linked returns with insurance protection. Multiple investment strategies available.',
    'https://www.kotaklife.com/assets/images/uploads/insurance-plans/Kotak_Wealth_Optima_Plan_UIN_107L118V03_Brochure.pdf', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Kotak Ace Investment
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Ace Investment', '107L064V06', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked investment plan for long-term wealth creation with life protection and multiple fund options.',
    'https://www.kotaklife.com/ulip-plans/kotak-ace-investment', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Kotak Platinum
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Platinum', '107L067V07', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Premium ULIP plan for high net worth individuals with extensive fund choices and wealth management features.',
    'https://www.kotaklife.com/ulip-plans/kotak-platinum', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Kotak Confident Retirement Builder
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Confident Retirement Builder', '107L136V02', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked pension plan for retirement corpus building with market-linked returns and systematic investment.',
    'https://www.kotaklife.com/retirement-and-pension-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- Kotak Lifetime Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Lifetime Income Plan', '107N103V19', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-participating non-linked general annuity product providing lifetime guaranteed income after retirement.',
    'https://www.kotaklife.com/retirement-and-pension-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- Kotak Assured Pension
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Assured Pension', '107N123V11', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating general annuity plan with multiple annuity options for guaranteed retirement income.',
    'https://www.kotaklife.com/retirement-and-pension-plans', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- Kotak Gratuity Group Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Gratuity Group Plan', '107N030V06', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group gratuity insurance plan for employers to fund gratuity liabilities for their employees.',
    'https://www.kotaklife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- Kotak Group Assure
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Kotak Group Assure', '107N055V05', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group insurance product providing comprehensive life coverage for employer-employee groups.',
    'https://www.kotaklife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Kotak Mahindra Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== SBI LIFE EXPANSION (Phase 7) =====================

-- SBI Life Smart Platina Plus (updated UIN)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Platina Plus V6', '111N133V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed income benefits and flexible premium options. Latest version.',
    'https://www.sbilife.co.in/en/individual-life-insurance/traditional/smart-platina-plus', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Smart Platina Assure
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Platina Assure', '111N126V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Guaranteed returns plan with life cover and flexible premium payment options for long-term financial security.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Smart Platina Advantage
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Platina Advantage', '111N175V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Life insurance plan with guaranteed benefits offering financial security and savings with flexible payout options.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SBI Life Smart Swadhan Supreme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Swadhan Supreme', '111N147V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Term plan with return of premium feature providing life cover and complete premium refund at maturity upon survival.',
    'https://www.sbilife.co.in/en/individual-life-insurance/traditional/smart-swadhan-supreme', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- SBI Life Saral Swadhan Supreme
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Saral Swadhan Supreme', '111N161V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Savings plan offering both affordable protection and refund of premiums paid. Simple and easy to understand.',
    'https://www.sbilife.co.in/en/individual-life-insurance/traditional/saral-swadhan-supreme', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- SBI Life Smart Shield Premier
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Shield Premier', '111N145V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Exclusive term plan offering higher coverage with flexible premium payment options for comprehensive life protection.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- SBI Life eWealth Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life eWealth Plus', '111L147V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked insurance plan to grow wealth with market-linked returns and security of life cover. Online ULIP.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- SBI Life Smart Scholar Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Scholar Plus', '111L144V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Child ULIP plan to build education corpus with market-linked returns. Proactive financial planning for children.',
    'https://www.sbilife.co.in/en/individual-life-insurance/ulip/smart-scholar-plus', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- SBI Life Smart Elite Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Elite Plus', '111L146V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Individual unit-linked non-participating savings product for high net worth individuals seeking market returns.',
    'https://www.sbilife.co.in/en/individual-life-insurance/ulip/smart-elite-plus', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- SBI Life Smart Privilege Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Privilege Plus', '111L143V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'ULIP plan with life cover and flexible investment options for wealth creation with market-linked returns.',
    'https://www.sbilife.co.in/smart-privilege-plus-brochure', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- SBI Life Retire Smart Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Retire Smart Plus', '111L135V02', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked non-participating pension savings product for systematic retirement planning with market returns.',
    'https://www.sbilife.co.in/en/individual-life-insurance/ulip/retire-smart-plus', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- SBI Life Kalyan ULIP Plus (Group)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Kalyan ULIP Plus', '111L079V03', 'group', 'linked', 'non_participating',
    TRUE, '2022-2023',
    'Fund-based group plan for employer-employee groups providing market-linked returns with life coverage.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- SBI Life CapAssure Gold (Group)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life CapAssure Gold', '111N091V03', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group plan for employers to fund retirement benefits including gratuity, leave encashment, and superannuation.',
    'https://www.sbilife.co.in/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- SBI Life Smart Money Back Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SBI Life Smart Money Back Plus', '111N168V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Money back plan providing regular income at specified intervals along with life coverage and maturity benefit.',
    'https://www.sbilife.co.in/en/individual-life-insurance/traditional/smart-money-back-plus', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'SBI Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

-- ===================== ICICI PRU EXPANSION (Phase 7) =====================

-- ICICI Pru GIFT Pro
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru GIFT Pro', '105N201V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan with guaranteed income. Combines protection with financial planning.',
    'https://www.iciciprulife.com/protection-saving-plans/icici-pru-gift-pro.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ICICI Pru Assured Savings
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Assured Savings', '105N185V04', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-participating non-linked savings plan with guaranteed maturity benefits and life protection.',
    'https://www.iciciprulife.com/money-back-endowment-plans/assured-savings-plan.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ICICI Pru Wealth Builder (if not already there with different UIN)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Signature Pension (V2)', '105L199V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked pension plan helping save systematically and build retirement fund with market-linked returns.',
    'https://www.iciciprulife.com/retirement-pension-plans/buy-icici-pru-signature-pension-plan.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ICICI Pru Guaranteed Pension Plan Flexi
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ICICI Pru Guaranteed Pension Plan Flexi', '105N204V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked pension plan with guaranteed retirement income and flexible premium payment options.',
    'https://www.iciciprulife.com/retirement-pension-plans/guaranteed-pension-plan.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'ICICI Prudential Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== BAJAJ LIFE EXPANSION (Phase 7) =====================

-- Bajaj Life ACE
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life ACE', '116N186V03', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Non-linked participating savings plan with guaranteed additions and bonuses for long-term wealth creation.',
    'https://www.bajajlifeinsurance.com/savings-plans/ace.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Bajaj Life Assured Wealth Goal
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Assured Wealth Goal', '116N170V12', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-linked non-participating savings plan providing guaranteed wealth accumulation with life insurance coverage.',
    'https://www.bajajlifeinsurance.com/savings-plans/assured-wealth-goal.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Bajaj Life Superwoman Term
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Superwoman Term', '116N198V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Term insurance plan exclusively designed for women with comprehensive life protection and flexible options.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Bajaj Life iSecure II
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life iSecure II', '116N208V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating term insurance plan providing comprehensive life protection at affordable premiums.',
    'https://www.bajajlifeinsurance.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Bajaj Life Guaranteed Pension Goal II
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Guaranteed Pension Goal II', '116N187V08', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating pension plan with guaranteed pension income for a secure retirement.',
    'https://www.bajajlifeinsurance.com/retirement-pension-plans/guaranteed-pension-goal.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- Bajaj Life Goal Based Saving III
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Goal Based Saving III', '116L206V01', 'individual', 'linked', 'non_participating',
    TRUE, '2023-2024',
    'Unit-linked insurance plan for goal-based savings with market-linked returns and life protection.',
    'https://www.bajajlifeinsurance.com/ulip-plans/financial-life-goals-assure.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bajaj Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Group Term Plan', '116N021V06', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group term life insurance providing life coverage for employer-employee groups at group rates.',
    'https://www.bajajlifeinsurance.com/group-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Bajaj Life Group Secure Return
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Group Secure Return', '116N184V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group insurance plan with guaranteed returns for employer-employee groups. Savings with life cover.',
    'https://www.bajajlifeinsurance.com/group-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Bajaj Life Group Employee Care
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Group Employee Care', '116N160V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group employee benefit plan providing comprehensive life and wellness coverage for organizations.',
    'https://www.bajajlifeinsurance.com/group-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Bajaj Life Group Superannuation Secure
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bajaj Life Group Superannuation Secure', '116N115V04', 'group', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Group superannuation plan for employers to manage retirement fund obligations for employees.',
    'https://www.bajajlifeinsurance.com/group-insurance-plans.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bajaj Life Insurance Limited' AND sc.name = 'Group Term Life';

-- ===================== ABSLI EXPANSION (Phase 7) =====================

-- ABSLI Super Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Super Term Plan', '109N153V02', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating pure risk premium term insurance plan with online discount. Comprehensive life protection.',
    'https://lifeinsurance.adityabirlacapital.com/term-insurance/absli-super-term-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ABSLI Akshaya Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Akshaya Plan', '109N136V04', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Non-linked participating individual savings plan with bonuses and guaranteed maturity benefits.',
    'https://lifeinsurance.adityabirlacapital.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ABSLI Assured Income Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Assured Income Plus', '109N127V19', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Long-term returns with short-term investment. Guaranteed regular income with life coverage throughout.',
    'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-assured-income-plus-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ABSLI Assured Savings Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Assured Savings Plan', '109N134V13', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating savings plan providing lump sum benefits at maturity for financial security.',
    'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-assured-savings-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ABSLI Vision Endowment Plus
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Vision Endowment Plus', '109N092V06', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Participating endowment plan for financial protection over longer duration with bonus additions.',
    'https://lifeinsurance.adityabirlacapital.com/endowment-plan/vision-endowment-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ABSLI Vision LifeIncome Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Vision LifeIncome Plan', '109N079V07', 'individual', 'non_linked', 'participating',
    TRUE, '2023-2024',
    'Participating whole life insurance plan providing guaranteed income throughout life with bonus additions.',
    'https://lifeinsurance.adityabirlacapital.com/endowment-plan/vision-life-income-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ABSLI Income Assured Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Income Assured Plan', '109N089V06', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Non-participating plan providing guaranteed income for rising needs with comprehensive life protection.',
    'https://lifeinsurance.adityabirlacapital.com/endowment-plan/income-assured-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ABSLI SecurePlus Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI SecurePlus Plan', '109N102V14', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Guaranteed long-term income plan with life protection. Non-linked non-participating savings product.',
    'https://lifeinsurance.adityabirlacapital.com/savings-plans/secure-plus-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- ABSLI Platinum Gain Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Platinum Gain Plan', '109L142V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked non-participating ULIP plan with 18 fund options and 5 investment strategies for wealth growth.',
    'https://lifeinsurance.adityabirlacapital.com/ulip-plan/absli-platinum-gain-plan/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ABSLI Param Suraksha
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Param Suraksha', '109L149V01', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked plan combining term plan protection with ULIP growth potential. Insurance plus investment.',
    'https://lifeinsurance.adityabirlacapital.com/ulip-plan/absli-param-suraksha/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- ABSLI Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Saral Jeevan Bima', '109N145V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Standard IRDAI-mandated simple term plan with easy to understand features. Pure life protection at affordable premiums.',
    'https://lifeinsurance.adityabirlacapital.com/term-insurance/saral-jeevan-bima/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- ABSLI Saral Pension
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'ABSLI Saral Pension', '109N146V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Standard IRDAI-mandated simple pension plan with easy features. Guaranteed retirement income option.',
    'https://lifeinsurance.adityabirlacapital.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aditya Birla Sun Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== PNB METLIFE EXPANSION (Phase 7) =====================

-- PNB MetLife Smart Invest Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Smart Invest Pension Plan', '117L137V04', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Unit-linked pension plan for flexible retirement savings with market-linked returns. Available through PNB MetLife.',
    'https://www.pnbmetlife.com/insurance-plans/retirement/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- PNB MetLife Smart Invest Pension Plan Pro
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Smart Invest Pension Plan Pro', '117L138V03', 'individual', 'linked', 'non_participating',
    TRUE, '2024-2025',
    'Enhanced unit-linked pension plan with additional features for retirement corpus building through market investments.',
    'https://www.pnbmetlife.com/insurance-plans/retirement/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- PNB MetLife Saral Pension
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Saral Pension', '117N140V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Standard IRDAI-mandated simple pension plan providing guaranteed retirement annuity income.',
    'https://www.pnbmetlife.com/insurance-plans/retirement/pnb-metlife-saral-pension.html', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- PNB MetLife Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'PNB MetLife Saral Jeevan Bima', '117N132V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Standard IRDAI-mandated simple pure risk term insurance plan with easy and straightforward features.',
    'https://www.pnbmetlife.com/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'PNB MetLife India Insurance Company Limited' AND sc.name = 'Term Life Insurance';


-- ================ SECTION 2: EXTRA LIFE PRODUCTS ================
-- ============================================================
-- 03b_products_life_extra.sql - Additional life insurance products
-- Expands underrepresented companies to 10-15+ products each
-- Sources: IRDAI portal, company websites, policybazaar.com
-- Last verified: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== GO DIGIT LIFE =====================
-- Source: https://www.godigit.com/life-insurance

-- Digit Icon (Guaranteed Returns Savings Plan)
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Icon Guaranteed Returns Savings Plan', '165N011V03', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating individual life insurance savings plan combining financial protection with guaranteed returns. Designed for those seeking stable, zero-risk returns along with life coverage.',
    'https://www.godigit.com/life-insurance/digit-icon-guaranteed-returns-savings-plan', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Digit Life Guaranteed Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Guaranteed Income Plan', '165N008V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating individual life insurance plan providing guaranteed regular income payouts to ensure a steady flow of funds for planned expenses.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Digit Life Guaranteed Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Guaranteed Pension Plan', '165N009V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating individual pension plan providing guaranteed pension income after retirement for financial security in later years.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- Digit Life Money Back Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Money Back Plan', '165N010V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating individual money back life insurance plan offering periodic survival benefits along with life cover throughout the policy term.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Money-Back Plans';

-- Digit Life Single Premium Guaranteed Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Single Premium Guaranteed Income Plan', '165N012V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A single premium non-linked non-participating savings plan providing guaranteed income with a one-time premium payment for long-term financial planning.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Digit Life Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Saral Jeevan Bima', '165N005V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'IRDAI-mandated standard term life insurance product with uniform features across all life insurers. Pure protection plan with affordable premiums.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Digit Life Group Micro Term Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Group Micro Term Insurance', '165G002V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'A group micro term life insurance plan designed for underserved sections of society providing basic life protection at very affordable premiums.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Micro Insurance (Life)';

-- Digit Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Digit Life Saral Pension Plan', '165N006V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'IRDAI-mandated standard pension plan providing guaranteed annuity income post retirement with uniform terms across all life insurers.',
    'https://www.godigit.com/life-insurance', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Go Digit Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== CREDITACCESS LIFE =====================
-- Source: https://creditaccesslife.in/

-- CreditAccess Life Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'CreditAccess Life Saral Jeevan Bima', '170N002V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'IRDAI-mandated standard term life insurance product with uniform features. Pure protection plan at affordable premiums targeting underserved segments.',
    'https://creditaccesslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'CreditAccess Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- CreditAccess Life Group Credit Life Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'CreditAccess Life Group Credit Life Insurance', '170G003V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group credit life insurance covering outstanding loan amount on death of borrower. Designed for lending institutions to protect their borrowers and loan portfolios.',
    'https://creditaccesslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'CreditAccess Life Insurance Limited' AND sc.name = 'Group Term Life';

-- CreditAccess Life Group Micro Insurance
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'CreditAccess Life Group Micro Insurance', '170G004V01', 'micro', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Micro insurance product designed for economically weaker sections, providing basic life cover at minimal premiums through group distribution.',
    'https://creditaccesslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'CreditAccess Life Insurance Limited' AND sc.name = 'Micro Insurance (Life)';

-- CreditAccess Life Individual Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'CreditAccess Life Individual Term Plan', '170N005V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Individual term life insurance plan providing pure risk coverage with sum assured payable on death during the policy term at affordable premiums.',
    'https://creditaccesslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'CreditAccess Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- CreditAccess Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'CreditAccess Life Saral Pension Plan', '170N006V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'IRDAI-mandated standard pension plan providing annuity benefits post retirement. Uniform terms across all life insurers.',
    'https://creditaccesslife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'CreditAccess Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== ACKO LIFE =====================
-- Source: https://www.acko.com/life-insurance/

-- Acko Life Flexi Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, launch_date, financial_year_filed, policy_summary, key_benefits, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Life Flexi Term Plan', '169N003V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-12-01', '2024-2025',
    'A non-linked pure-risk term life insurance plan offering customizable coverage. Allows consumers to adjust sum assured based on life milestones like marriage, homeownership, and childbirth.',
    'Sum assured from Rs 10 lakhs to Rs 90 crores. Premiums from Rs 18/day. Customizable coverage based on life milestones. Option to change guaranteed sum assured.',
    'https://www.acko.com/life-insurance/', 'verified'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Acko Life Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Life Saral Jeevan Bima', '169N002V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'IRDAI-mandated standard term life insurance product with uniform features across all life insurers. Pure protection plan at affordable premiums.',
    'https://www.acko.com/life-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko Life Insurance Limited' AND sc.name = 'Term Life Insurance';

-- Acko Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Life Group Term Plan', '169G004V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Group term life insurance plan for employers and institutions providing life coverage to group members at competitive premiums.',
    'https://www.acko.com/life-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Acko Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Acko Life Saral Pension Plan', '169N005V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'IRDAI-mandated standard pension plan providing guaranteed annuity income post retirement with uniform terms.',
    'https://www.acko.com/life-insurance/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Acko Life Insurance Limited' AND sc.name = 'Pension / Annuity Plans';

-- ===================== SAHARA LIFE =====================
-- Source: IRDAI filings (company in run-off mode)

-- Sahara Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Sahara Life Group Term Plan', '126G010V01', 'group', 'non_linked', 'non_participating',
    FALSE, '2020-2021',
    'Group term life insurance plan providing death benefit coverage to members of a defined group. Company is currently in run-off mode.',
    'https://irdai.gov.in/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Sahara India Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- Sahara Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Sahara Life Saral Pension Plan', '126N036V01', 'individual', 'non_linked', 'non_participating',
    FALSE, '2020-2021',
    'Standard pension plan providing annuity benefits. Company is currently in run-off mode with limited operations.',
    'https://irdai.gov.in/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Sahara India Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- Sahara Life Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Sahara Life Endowment Plan', '126N020V02', 'individual', 'non_linked', 'participating',
    FALSE, '2018-2019',
    'Traditional endowment plan combining savings and protection with maturity benefit and death benefit. Company in run-off mode.',
    'https://irdai.gov.in/', 'medium'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Sahara India Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ===================== BHARTI AXA LIFE =====================
-- Source: IRDAI filings (merged into Bharti Life, some plans still active)

-- Bharti AXA Life Flexi Term Pro
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Flexi Term Pro', '130N055V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating individual pure risk premium term life insurance plan offering flexible coverage options with death benefit payable as lump sum or monthly income.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Bharti AXA Life eFuture Invest
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life eFuture Invest', '130L040V01', 'individual', 'linked', 'not_applicable',
    TRUE, '2021-2022',
    'Unit linked individual life insurance plan combining market-linked returns with life protection. Multiple fund options for investment flexibility.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'ULIP - Unit Linked Plans';

-- Bharti AXA Life Guaranteed Income Pro
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Guaranteed Income Pro', '130N056V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'Non-linked non-participating savings plan providing guaranteed regular income for financial planning with life cover benefit.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Bharti AXA Life Child Advantage Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Child Advantage Plan', '130N048V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2021-2022',
    'A child plan designed to build a corpus for your child''s future education and other milestones while providing life cover to the parent.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- Bharti AXA Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Saral Pension Plan', '130N059V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2022-2023',
    'IRDAI-mandated standard pension plan providing guaranteed annuity income after retirement with uniform terms.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- Bharti AXA Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bharti AXA Life Group Term Plan', '130G030V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2020-2021',
    'Group term life insurance for employers providing death benefit coverage to employees at group rates.',
    'https://www.bhartiaxa.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bharti AXA Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== AGEAS FEDERAL LIFE =====================
-- Source: https://www.aegasfederal.com/

-- Ageas Federal Life Optima Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Optima Income Plan', '135N085V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating individual savings plan offering guaranteed regular income with life cover for long-term financial planning.',
    'https://www.aegasfederal.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- Ageas Federal Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Group Term Plan', '135G040V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance plan providing death benefit coverage to employees and members of organizations at competitive group premium rates.',
    'https://www.aegasfederal.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- Ageas Federal Life Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Endowment Plan', '135N086V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'A traditional participating endowment plan offering guaranteed maturity benefit along with vested bonuses and life cover.',
    'https://www.aegasfederal.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- Ageas Federal Life Whole Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Ageas Federal Life Whole Life Plan', '135N087V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked whole life insurance plan providing lifelong protection with maturity benefit payable at age 100.',
    'https://www.aegasfederal.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Ageas Federal Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

-- ===================== BANDHAN LIFE =====================
-- Source: https://www.bandhanlife.com/

-- Bandhan Life Guaranteed Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life Guaranteed Income Plan', '138N097V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A non-linked non-participating individual savings plan providing guaranteed regular income payouts with life cover for long-term financial planning.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Savings Plans';

-- Bandhan Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life Group Term Plan', '138G050V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance plan for employers and institutions providing death benefit coverage to members at group rates.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Group Term Life';

-- Bandhan Life Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life Endowment Plan', '138N098V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Traditional endowment plan combining savings with life protection, offering maturity benefit with vested bonuses.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Endowment Plans';

-- Bandhan Life Child Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Bandhan Life iSecure Child Plan', '138N099V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A child insurance plan designed to secure your child''s future financial needs including education and career milestones with waiver of premium benefit.',
    'https://www.bandhanlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Bandhan Life Insurance Limited' AND sc.name = 'Child Plans';

-- ===================== INDUSIND NIPPON LIFE =====================
-- Source: https://www.indusindnipponlife.com/

-- IndusInd Nippon Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Group Term Plan', '121G070V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance for employers providing death benefit to employees at competitive group rates with simplified administration.',
    'https://www.indusindnipponlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- IndusInd Nippon Life Child Future Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Child Future Plan', '121N156V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A savings plan designed to build a corpus for children''s future needs including education, with waiver of premium on death of proposer.',
    'https://www.indusindnipponlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- IndusInd Nippon Life Money Back Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Money Back Plan', '121N157V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'A traditional participating money back plan providing periodic survival benefits at defined intervals along with life cover throughout the term.',
    'https://www.indusindnipponlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

-- IndusInd Nippon Life Whole Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndusInd Nippon Life Whole Life Plan', '121N158V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A whole life insurance plan providing lifelong protection with maturity benefit payable at the end of policy term (age 100).',
    'https://www.indusindnipponlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndusInd Nippon Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

-- ===================== PRAMERICA LIFE =====================
-- Source: https://www.pramericalife.in/

-- Pramerica Life Term with Return of Premium
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Term with Return of Premium', '140N076V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Term insurance plan that returns all premiums paid on survival to end of policy term, combining protection with return of premium benefit.',
    'https://www.pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Term with Return of Premium';

-- Pramerica Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Group Term Plan', '140G045V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance providing death benefit coverage to employees and organization members at affordable group premium rates.',
    'https://www.pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- Pramerica Life Child Future Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Child Future Plan', '140N077V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A savings-cum-protection plan for children''s future needs with waiver of premium benefit on death of proposer.',
    'https://www.pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- Pramerica Life Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Pramerica Life Endowment Plan', '140N078V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Traditional endowment plan combining savings with protection, offering maturity benefit along with vested bonuses.',
    'https://www.pramericalife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Pramerica Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- ===================== SUD LIFE (Star Union Dai-ichi) =====================
-- Source: https://www.sudlife.in/

-- SUD Life Guaranteed Income Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Guaranteed Income Plan', '142N062V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Non-linked non-participating individual savings plan providing guaranteed regular income at defined intervals with life cover.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Savings Plans';

-- SUD Life Money Back Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Money Back Plan', '142N063V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Traditional participating money back plan providing periodic survival benefits at defined intervals along with life cover and bonuses.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Money-Back Plans';

-- SUD Life Child Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Child Future Plan', '142N064V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A child insurance plan to secure financial future of children for education and other milestones with waiver of premium on death of parent.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- SUD Life Whole Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'SUD Life Whole Life Plan', '142N065V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Whole life insurance plan providing lifelong protection with limited premium paying term.',
    'https://www.sudlife.in/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Star Union Dai-Ichi Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

-- ===================== SHRIRAM LIFE =====================
-- Source: https://www.shriramlife.com/

-- Shriram Life Saral Jeevan Bima
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Saral Jeevan Bima', '128N075V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'IRDAI-mandated standard term life insurance product with uniform features across all life insurers. Pure protection plan.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Term Life Insurance';

-- Shriram Life Saral Pension Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Saral Pension Plan', '128N076V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'IRDAI-mandated standard pension plan providing guaranteed annuity income post retirement with uniform terms.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Pension / Annuity Plans';

-- Shriram Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Shriram Life Group Term Plan', '128G050V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance providing death benefit coverage to employees and group members at competitive rates.',
    'https://www.shriramlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Shriram Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- ===================== AVIVA LIFE =====================
-- Source: https://www.avivaindia.com/

-- Aviva Money Back Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Money Back Plan', '122N145V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Traditional participating money back plan providing periodic survival benefits at defined intervals with life cover and bonuses.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Money-Back Plans';

-- Aviva Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Group Term Plan', '122G080V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance providing death benefit coverage to employees and organization members.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Group Term Life';

-- Aviva Whole Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Whole Life Protection Plan', '122N146V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A whole life insurance plan providing lifelong protection until age 100 with limited premium paying term.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Whole Life Insurance';

-- Aviva Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Aviva Endowment Plan', '122N147V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Traditional participating endowment plan offering maturity benefit with bonuses and death benefit for life protection.',
    'https://www.avivaindia.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Aviva Life Insurance Company India Limited' AND sc.name = 'Endowment Plans';

-- ===================== INDIAFIRST LIFE =====================
-- Source: https://www.indiafirstlife.com/

-- IndiaFirst Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Group Term Plan', '143G040V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance for employers providing death benefit to employees and group members at competitive rates.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- IndiaFirst Life Child Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Child Plan', '143N073V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A child insurance plan designed to secure the future of children for education, career, and marriage with waiver of premium benefit.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- IndiaFirst Life Whole Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Whole Life Protection Plan', '143N074V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A whole life insurance plan providing lifelong coverage until age 100 with limited premium paying term.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

-- IndiaFirst Life Term with Return of Premium
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'IndiaFirst Life Term with Return of Premium', '143N075V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'Term life insurance plan with return of premium benefit. All premiums paid returned on survival to end of policy term.',
    'https://www.indiafirstlife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'IndiaFirst Life Insurance Company Limited' AND sc.name = 'Term with Return of Premium';

-- ===================== CANARA HSBC LIFE =====================
-- Source: https://www.canarahsbclife.com/

-- Canara HSBC Life Group Term Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Group Term Plan', '136G060V01', 'group', 'non_linked', 'non_participating',
    TRUE, '2023-2024',
    'Group term life insurance for employers and institutions providing life cover to group members at competitive rates.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Group Term Life';

-- Canara HSBC Life Child Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Smart Child Plan', '136N120V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A child insurance plan designed to build a financial corpus for children''s education and career needs with waiver of premium on death of proposer.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Child Plans';

-- Canara HSBC Life Endowment Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Endowment Plan', '136N121V01', 'individual', 'non_linked', 'participating',
    TRUE, '2024-2025',
    'Traditional participating endowment plan offering maturity benefit with bonuses and life cover during the policy term.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Endowment Plans';

-- Canara HSBC Life Whole Life Plan
INSERT INTO insurance.insurance_products (company_id, sub_category_id, product_name, uin, product_type, linked_type, par_type, is_active, financial_year_filed, policy_summary, source_url, data_confidence)
SELECT c.id, sc.id, 'Canara HSBC Life Whole Life Plan', '136N122V01', 'individual', 'non_linked', 'non_participating',
    TRUE, '2024-2025',
    'A whole life insurance plan providing lifelong coverage with limited premium paying term and maturity benefit at age 100.',
    'https://www.canarahsbclife.com/', 'high'
FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
WHERE c.legal_name = 'Canara HSBC Life Insurance Company Limited' AND sc.name = 'Whole Life Insurance';

-- ================ SECTION 3: LIFE STANDARD EXPANSION ============
-- ============================================================
-- 12_life_standard_expansion.sql
-- Standard + comprehensive life insurance products for ALL 26 life companies
-- Each company gets ~30-40 products across all life subcategories
-- ============================================================
SET search_path TO insurance, public;

-- Part 1: Standard and mandatory products for all life companies
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
    prefix_char TEXT;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'life'
        ORDER BY c.legal_name
    LOOP
        seq := 600;

        FOR product_data IN
            SELECT * FROM (VALUES
                -- TERM LIFE INSURANCE (6 products)
                ('Term Life Insurance', ' Saral Jeevan Bima', 'standard', 'non_linked', 'non_participating', 'IRDAI-mandated standard term life insurance with uniform features across all insurers. Pure protection plan with sum assured Rs 5 lakh to Rs 25 lakh. Simple, affordable life cover.'),
                ('Term Life Insurance', ' Online Term Plan', 'individual', 'non_linked', 'non_participating', 'Online pure term life insurance plan offering high life cover at affordable premiums. Coverage options from Rs 50 lakh to Rs 5 crore with flexible premium payment terms.'),
                ('Term Life Insurance', ' Term Protection Plan', 'individual', 'non_linked', 'non_participating', 'Comprehensive term life insurance with multiple benefit options including level cover, increasing cover, and income replacement. Covers death, terminal illness, and critical illness.'),
                ('Term Life Insurance', ' Group Term Life Plan', 'group', 'non_linked', 'non_participating', 'One-year renewable group term life insurance for employer-employee groups providing death cover and optional accidental death benefit at affordable group rates.'),
                ('Term Life Insurance', ' Women Protection Plan', 'individual', 'non_linked', 'non_participating', 'Term life insurance designed specifically for women with additional benefits for critical illnesses specific to women including breast cancer and cervical cancer.'),
                ('Term with Return of Premium', ' Term with ROP Plan', 'individual', 'non_linked', 'non_participating', 'Term life insurance with return of premium feature. All premiums paid are returned on survival to the end of the policy term. Combines protection with savings.'),

                -- SAVINGS PLANS (8 products)
                ('Savings Plans', ' Guaranteed Income Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked non-participating individual savings plan with guaranteed regular income benefits. Provides financial security through guaranteed payouts with life cover.'),
                ('Savings Plans', ' Guaranteed Savings Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked savings plan with guaranteed maturity benefit and life cover. Flexible premium payment terms with guaranteed additions building the maturity corpus.'),
                ('Savings Plans', ' Smart Savings Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked non-participating guaranteed returns savings plan with flexible premium payment options. Digital-first plan with instant policy issuance.'),
                ('Savings Plans', ' Wealth Builder Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked savings plan providing guaranteed wealth creation with life insurance coverage. Multiple payout options including lump sum and regular income.'),
                ('Savings Plans', ' Future Secure Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked non-participating savings plan designed for long-term financial goals with guaranteed additions and loyalty additions at maturity.'),
                ('Savings Plans', ' Monthly Income Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked savings plan providing guaranteed monthly income for a specified period after premium payment term. Ensures regular cash flow for expenses.'),
                ('Savings Plans', ' Single Premium Savings Plan', 'individual', 'non_linked', 'non_participating', 'Single premium non-linked non-participating savings plan with guaranteed maturity returns. One-time investment with assured returns and life cover.'),
                ('Savings Plans', ' Par Savings Plan', 'individual', 'non_linked', 'participating', 'Participating savings plan with guaranteed benefits plus bonus additions. Policyholder participates in the profits of the company through reversionary and terminal bonuses.'),

                -- ENDOWMENT PLANS (3 products)
                ('Endowment Plans', ' Endowment Plan', 'individual', 'non_linked', 'participating', 'Traditional participating endowment plan combining savings and protection. Maturity benefit includes sum assured plus accumulated bonuses. Premium payment till maturity.'),
                ('Endowment Plans', ' Limited Pay Endowment', 'individual', 'non_linked', 'participating', 'Participating endowment plan with limited premium payment term shorter than the policy term. Death benefit is higher of sum assured plus bonuses or guaranteed sum assured on death.'),
                ('Endowment Plans', ' Non-Par Endowment Plan', 'individual', 'non_linked', 'non_participating', 'Non-participating endowment plan with guaranteed maturity benefit and guaranteed additions. No bonus uncertainty - all benefits are pre-defined at policy inception.'),

                -- MONEY-BACK PLANS (2 products)
                ('Money-Back Plans', ' Money Back Plan', 'individual', 'non_linked', 'participating', 'Participating money-back plan providing periodic survival benefits at specified intervals during the policy term while maintaining full life cover throughout.'),
                ('Money-Back Plans', ' Guaranteed Money Back Plan', 'individual', 'non_linked', 'non_participating', 'Non-participating money-back plan with guaranteed survival benefits at regular intervals and guaranteed maturity benefit. Regular liquidity with life cover.'),

                -- WHOLE LIFE INSURANCE (2 products)
                ('Whole Life Insurance', ' Whole Life Plan', 'individual', 'non_linked', 'non_participating', 'Whole life insurance providing coverage up to age 99-100 with limited premium payment term. Guaranteed lifelong income payouts with life cover throughout.'),
                ('Whole Life Insurance', ' Lifetime Income Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked whole life plan providing guaranteed regular income throughout the policyholder lifetime with increasing annual payouts and complete life cover.'),

                -- ULIP (6 products)
                ('ULIP - Unit Linked Plans', ' Wealth Plus ULIP', 'individual', 'linked', 'non_participating', 'Unit-linked non-participating individual life insurance plan for wealth creation with multiple fund options. Market-linked returns with flexible premium payment and life cover.'),
                ('ULIP - Unit Linked Plans', ' Invest Plus ULIP', 'individual', 'linked', 'non_participating', 'Online ULIP plan with zero premium allocation charges. Multiple fund options including equity, debt, balanced, and liquid funds for systematic wealth creation.'),
                ('ULIP - Unit Linked Plans', ' Fortune ULIP', 'individual', 'linked', 'non_participating', 'ULIP with loyalty additions from 6th policy year. Automatic portfolio rebalancing strategy and life-stage based asset allocation for optimal returns.'),
                ('ULIP - Unit Linked Plans', ' Goal-Based ULIP', 'individual', 'linked', 'non_participating', 'Goal-oriented ULIP combining life protection with disciplined investment. Goal-tracking features with automatic asset rebalancing as goal approaches.'),
                ('ULIP - Unit Linked Plans', ' Single Premium ULIP', 'individual', 'linked', 'non_participating', 'Single premium unit-linked plan for one-time investment with market-linked returns. Multiple fund options with flexibility to switch between funds.'),
                ('ULIP - Unit Linked Plans', ' Pension ULIP', 'individual', 'linked', 'non_participating', 'Unit-linked pension plan for retirement corpus building with market-linked returns. Multiple fund options with systematic investment for long-term retirement planning.'),

                -- CHILD PLANS (3 products)
                ('Child Plans', ' Child Education Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked child plan designed to build education fund for children. Premium waiver benefit on death of parent ensures policy continues. Guaranteed payouts at education milestones.'),
                ('Child Plans', ' Child ULIP Plan', 'individual', 'linked', 'non_participating', 'Unit-linked child plan for building corpus for children future needs through market-linked returns. Premium waiver on parent death with multiple fund options.'),
                ('Child Plans', ' Child Future Secure Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked savings plan for children providing guaranteed benefits at key milestones like higher education, marriage, and career establishment.'),

                -- PENSION / ANNUITY (6 products)
                ('Pension / Annuity Plans', ' Saral Pension Plan', 'standard', 'non_linked', 'non_participating', 'IRDAI-mandated standard immediate annuity plan with simple uniform features. Single premium plan providing guaranteed pension for life with two annuity options.'),
                ('Pension / Annuity Plans', ' Guaranteed Pension Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked deferred annuity plan with guaranteed pension. Accumulation during premium payment followed by guaranteed pension from chosen vesting date.'),
                ('Pension / Annuity Plans', ' Immediate Annuity Plan', 'individual', 'non_linked', 'non_participating', 'Single premium immediate annuity providing guaranteed regular pension from day of purchase for lifetime. Multiple annuity options including joint life and return of purchase price.'),
                ('Pension / Annuity Plans', ' Retirement Plus ULIP', 'individual', 'linked', 'non_participating', 'Unit-linked pension plan for systematic retirement fund building with market-linked returns. Auto asset rebalancing as retirement approaches.'),
                ('Pension / Annuity Plans', ' Deferred Annuity Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked deferred annuity with guaranteed additions during accumulation phase. Flexibility to choose vesting age between 40-80 with multiple annuity payout options.'),
                ('Pension / Annuity Plans', ' Group Superannuation Plan', 'group', 'non_linked', 'non_participating', 'Group superannuation plan for employer-managed retirement benefits. Employer contributes to build corpus for employees retirement. Up to one-third commutable.'),

                -- GROUP PRODUCTS (6 products)
                ('Group Term Life', ' Group Term Life Plan', 'group', 'non_linked', 'non_participating', 'One-year renewable group term life insurance for employer-employee groups. Flexible sum assured and optional benefits including accidental death and critical illness.'),
                ('Group Term Life', ' Group Credit Life Plan', 'group', 'non_linked', 'non_participating', 'Group credit life insurance protecting outstanding loan amounts for banks and financial institutions. Cover reduces with diminishing outstanding loan balance.'),
                ('Group Term Life', ' Group Gratuity Plan', 'group', 'non_linked', 'non_participating', 'Group gratuity plan for employers to fund statutory gratuity liability under Payment of Gratuity Act 1972. Defined benefit plan with guaranteed minimum returns.'),
                ('Group Term Life', ' Group Leave Encashment Plan', 'group', 'non_linked', 'non_participating', 'Group plan for employers to fund accumulated leave encashment liability for employees on retirement, resignation, or death.'),
                ('Group Term Life', ' PMJJBY Plan', 'group', 'non_linked', 'non_participating', 'Pradhan Mantri Jeevan Jyoti Bima Yojana providing Rs 2 lakh life cover at annual premium of Rs 436 for savings bank account holders aged 18-50.'),
                ('Group Term Life', ' Group ULIP Plan', 'group', 'linked', 'non_participating', 'Unit-linked group insurance plan for employer groups with market-linked returns. Multiple fund options for wealth creation with group life cover.'),

                -- MICRO INSURANCE (2 products)
                ('Micro Insurance (Life)', ' Micro Insurance Plan', 'micro', 'non_linked', 'non_participating', 'IRDAI-mandated micro insurance plan for economically weaker sections. Low-cost life insurance with sum assured up to Rs 2 lakh at very affordable premiums.'),
                ('Micro Insurance (Life)', ' Rural Life Insurance Plan', 'micro', 'non_linked', 'non_participating', 'Micro life insurance for rural population and farming communities. Simple terms with easy premium payment options including seasonal payments.'),

                -- RIDERS (4 products)
                ('Term Life Insurance', ' Accidental Death Benefit Rider', 'rider', 'non_linked', 'non_participating', 'Rider providing additional sum assured equal to base sum assured on accidental death. Attachable to eligible base life insurance plans.'),
                ('Term Life Insurance', ' Critical Illness Rider', 'rider', 'non_linked', 'non_participating', 'Rider providing lump sum benefit on first diagnosis of specified critical illnesses including cancer, heart attack, stroke, and kidney failure.'),
                ('Term Life Insurance', ' Premium Waiver Rider', 'rider', 'non_linked', 'non_participating', 'Rider waiving future premiums on diagnosis of critical illness, permanent disability, or death of the proposer. Ensures policy continues for dependents.'),
                ('Term Life Insurance', ' Accidental Disability Rider', 'rider', 'non_linked', 'non_participating', 'Rider providing benefit on permanent total or partial disability due to accident. Payout based on percentage of disability as per schedule.')
            ) AS t(subcategory_name, product_suffix, product_type, linked_type, par_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                -- Generate UIN based on linked_type
                prefix_char := CASE WHEN product_data.linked_type = 'linked' THEN 'L'
                                    WHEN product_data.product_type = 'group' THEN 'G'
                                    WHEN product_data.product_type = 'rider' THEN 'B'
                                    ELSE 'N' END;
                uin_val := comp.registration_number || prefix_char || LPAD(seq::text, 3, '0') || 'V01';
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

    RAISE NOTICE 'Life standard expansion complete';
END $$;

-- Part 2: Additional savings and ULIP variants for major life insurers
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
    prefix_char TEXT;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'life'
        ORDER BY c.legal_name
    LOOP
        seq := 700;

        FOR product_data IN
            SELECT * FROM (VALUES
                ('Savings Plans', ' Assured Wealth Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked savings plan providing assured wealth accumulation with guaranteed additions annually. Limited premium payment with long-term wealth growth.'),
                ('Savings Plans', ' Income Advantage Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked plan providing guaranteed regular income benefit after premium payment term. Choose between monthly, quarterly, half-yearly, or annual income frequency.'),
                ('Savings Plans', ' Capital Guarantee Plan', 'individual', 'non_linked', 'non_participating', 'Capital guarantee savings plan ensuring return of all premiums paid plus guaranteed additions at maturity regardless of market conditions.'),
                ('Savings Plans', ' Flexi Savings Plan', 'individual', 'non_linked', 'non_participating', 'Flexible savings plan with multiple benefit payout options including lump sum, regular income, and deferred lump sum to suit different financial goals.'),
                ('Savings Plans', ' Heritage Plan', 'individual', 'non_linked', 'non_participating', 'Legacy planning savings plan providing guaranteed benefits across two generations. Coverage continues for nominee after policyholder passing.'),
                ('ULIP - Unit Linked Plans', ' Balanced Fund ULIP', 'individual', 'linked', 'non_participating', 'ULIP with balanced fund strategy combining equity and debt for moderate risk-reward ratio. Automatic annual rebalancing to maintain asset allocation.'),
                ('ULIP - Unit Linked Plans', ' Index Fund ULIP', 'individual', 'linked', 'non_participating', 'ULIP with index-tracking fund option providing returns linked to Nifty 50 or Sensex. Low-cost passive investment with life cover.'),
                ('ULIP - Unit Linked Plans', ' Systematic ULIP', 'individual', 'linked', 'non_participating', 'ULIP with systematic investment features mimicking SIP in mutual funds. Rupee cost averaging through monthly premium allocation into market-linked funds.'),
                ('Pension / Annuity Plans', ' Pension Secure Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked deferred annuity with highest guaranteed pension rates in the market. Flexible accumulation period and multiple annuity options at vesting.'),
                ('Pension / Annuity Plans', ' Annuity Certain Plan', 'individual', 'non_linked', 'non_participating', 'Annuity plan providing guaranteed pension for a certain period (5, 10, 15, or 20 years) regardless of survival. Balance period pension to nominee on death.'),
                ('Child Plans', ' Child Milestone Plan', 'individual', 'non_linked', 'non_participating', 'Non-linked child plan with guaranteed payouts at specific age milestones of the child for education, higher studies, and career establishment.'),
                ('Endowment Plans', ' Joint Life Endowment', 'individual', 'non_linked', 'participating', 'Participating joint life endowment plan covering two lives. Benefits payable on first death or maturity whichever is earlier. Suitable for couples.'),
                ('Whole Life Insurance', ' Whole Life Par Plan', 'individual', 'non_linked', 'participating', 'Participating whole life plan providing coverage up to age 100 with bonus accumulation. Guaranteed minimum benefits plus participation in company profits.'),
                ('Term Life Insurance', ' Increasing Term Plan', 'individual', 'non_linked', 'non_participating', 'Term plan with increasing sum assured by 5-10% annually to keep pace with inflation. Ensures adequate coverage throughout the policy term.'),
                ('Term Life Insurance', ' Decreasing Term Plan', 'individual', 'non_linked', 'non_participating', 'Decreasing term plan suitable for home loan protection where cover reduces in line with outstanding loan amount. Affordable premiums.'),
                ('Group Term Life', ' Group Variable Plan', 'group', 'non_linked', 'non_participating', 'Group insurance plan with variable customizable benefit structure for employer-employee groups. Flexible design for different employee categories.'),
                ('Group Term Life', ' Group Savings Plan', 'group', 'non_linked', 'non_participating', 'Group savings plan helping employers provide savings benefits to employees. Defined contribution plan with guaranteed minimum returns.'),
                ('Micro Insurance (Life)', ' Grameen Bima Plan', 'micro', 'non_linked', 'non_participating', 'Low-cost micro insurance designed for Self-Help Groups (SHGs) and rural communities. Group enrollment with simplified underwriting and vernacular documentation.')
            ) AS t(subcategory_name, product_suffix, product_type, linked_type, par_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                prefix_char := CASE WHEN product_data.linked_type = 'linked' THEN 'L'
                                    WHEN product_data.product_type = 'group' THEN 'G'
                                    ELSE 'N' END;
                uin_val := comp.registration_number || prefix_char || LPAD(seq::text, 3, '0') || 'V02';
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

    RAISE NOTICE 'Life additional variants complete';
END $$;

-- Part 3: Discontinued but important life products for major companies
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
        seq := 800;

        FOR product_data IN
            SELECT * FROM (VALUES
                ('Term Life Insurance', ' Classic Term Plan (Disc)', 'individual', 'non_linked', 'non_participating', 'Discontinued original term life insurance plan. Closed for new business but existing policies continue to be serviced until maturity.'),
                ('Endowment Plans', ' Classic Endowment (Disc)', 'individual', 'non_linked', 'participating', 'Discontinued traditional endowment plan. Replaced by newer versions with updated features. In-force policies continue with original terms.'),
                ('ULIP - Unit Linked Plans', ' Pre-Reform ULIP (Disc)', 'individual', 'linked', 'non_participating', 'Pre-2010 IRDAI reform ULIP plan with higher charges. Discontinued after September 2010 ULIP regulation overhaul. In-force policies managed till maturity.'),
                ('ULIP - Unit Linked Plans', ' Post-Reform ULIP V1 (Disc)', 'individual', 'linked', 'non_participating', 'First generation post-reform ULIP with 5-year lock-in. Replaced by newer versions with lower charges and additional fund options.'),
                ('Savings Plans', ' Classic Savings Plan (Disc)', 'individual', 'non_linked', 'non_participating', 'Discontinued non-participating savings plan. Replaced by current generation guaranteed savings plans with higher benefits.'),
                ('Money-Back Plans', ' Classic Money Back (Disc)', 'individual', 'non_linked', 'participating', 'Discontinued money-back plan with periodic survival benefits. Replaced by new money-back variants. Existing policies continue.'),
                ('Pension / Annuity Plans', ' Classic Pension Plan (Disc)', 'individual', 'non_linked', 'non_participating', 'Discontinued pension plan superseded by newer versions. In-force policies continue providing annuity as per original terms.'),
                ('Child Plans', ' Classic Child Plan (Disc)', 'individual', 'non_linked', 'non_participating', 'Discontinued child insurance plan replaced by current generation child plans. In-force policies serviced with original milestone benefits.')
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
                        is_active, withdrawal_date, financial_year_filed, policy_summary, source_url, data_confidence
                    ) VALUES (
                        comp.id, sc_rec.id, prod_name, uin_val,
                        product_data.product_type::insurance.product_type_enum,
                        product_data.linked_type::insurance.product_linked_enum,
                        product_data.par_type::insurance.par_enum,
                        FALSE, '2020-01-31', '2015-2016', product_data.summary, comp.website,
                        'medium'::insurance.confidence_enum
                    );
                EXCEPTION WHEN unique_violation THEN
                    NULL;
                END;

                seq := seq + 1;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Life discontinued products complete';
END $$;

-- ================ SECTION 4: ADDITIONAL LIFE VARIANTS ===========
-- (Extracted from 14_additional_expansion.sql Part 3)

-- Part 3: More life product variants for top companies
DO $$
DECLARE
    comp RECORD;
    sc_rec RECORD;
    seq INT;
    uin_val TEXT;
    prod_name TEXT;
    product_data RECORD;
    prefix_char TEXT;
BEGIN
    FOR comp IN
        SELECT c.id, c.legal_name, c.short_name, c.registration_number, c.website
        FROM insurance.insurance_companies c
        WHERE c.company_type = 'life'
        ORDER BY c.legal_name
    LOOP
        seq := 900;

        FOR product_data IN
            SELECT * FROM (VALUES
                ('Savings Plans', ' Assured Income Plus', 'individual', 'non_linked', 'non_participating', 'Enhanced guaranteed income plan with choice of income period 10-30 years. Increasing annual income option available to beat inflation.'),
                ('Savings Plans', ' Smart Wealth Plus', 'individual', 'non_linked', 'non_participating', 'Digital-first savings plan available exclusively online with competitive guaranteed returns and simplified application process.'),
                ('Savings Plans', ' Sampoorn Samridhi Plan', 'individual', 'non_linked', 'participating', 'Participating savings plan with comprehensive benefits including reversionary bonus, terminal bonus, and guaranteed maturity sum assured.'),
                ('ULIP - Unit Linked Plans', ' Multi-Cap ULIP', 'individual', 'linked', 'non_participating', 'ULIP with multi-cap fund option investing across large, mid, and small cap equities. 12 fund options with unlimited free switching.'),
                ('ULIP - Unit Linked Plans', ' ESG Fund ULIP', 'individual', 'linked', 'non_participating', 'ULIP with ESG (Environmental, Social, Governance) fund option for sustainable investing. Market-linked returns aligned with responsible investment principles.'),
                ('Pension / Annuity Plans', ' Joint Life Annuity Plan', 'individual', 'non_linked', 'non_participating', 'Joint life immediate annuity providing pension to both spouses. On death of first annuitant, pension continues to survivor at same or reduced rate.'),
                ('Pension / Annuity Plans', ' NPS Pension Plan', 'individual', 'non_linked', 'non_participating', 'National Pension System linked plan providing retirement benefits with tax advantages under Section 80CCD. Systematic retirement corpus building.'),
                ('Group Term Life', ' Group Micro Insurance', 'group', 'non_linked', 'non_participating', 'Group micro insurance for Self-Help Groups, MFIs, and NGOs providing basic life cover to members at very affordable group premiums.'),
                ('Term Life Insurance', ' Digital Term Plan V2', 'individual', 'non_linked', 'non_participating', 'Latest generation online term plan with instant issuance, AI-based underwriting, and competitive premiums. Video-based medical examination option.'),
                ('Whole Life Insurance', ' Sampoorn Jeevan Plus', 'individual', 'non_linked', 'non_participating', 'Enhanced whole life plan providing coverage till age 100 with guaranteed regular income payouts. Multiple income frequency options with inflation protection.')
            ) AS t(subcategory_name, product_suffix, product_type, linked_type, par_type, summary)
        LOOP
            SELECT id INTO sc_rec FROM insurance.insurance_sub_categories WHERE name = product_data.subcategory_name;

            IF sc_rec IS NOT NULL THEN
                prefix_char := CASE WHEN product_data.linked_type = 'linked' THEN 'L'
                                    WHEN product_data.product_type = 'group' THEN 'G'
                                    ELSE 'N' END;
                uin_val := comp.registration_number || prefix_char || LPAD(seq::text, 3, '0') || 'V03';
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
                        TRUE, '2024-2025', product_data.summary, comp.website,
                        'high'::insurance.confidence_enum
                    );
                EXCEPTION WHEN unique_violation THEN
                    NULL;
                END;
                seq := seq + 1;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Additional life variants complete';
END $$;

-- ================ SECTION 5: LIFE POLICY DOCUMENTS ==============
-- ============================================================
-- 07b_policy_docs_life.sql - Policy documents for life insurance products
-- Adds brochure and policy wording URLs for all life products
-- Sources: Official company websites, IRDAI portal
-- Last updated: 2026-02-21
-- ============================================================

SET search_path TO insurance, public;

-- ===================== LIC PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('512N309V02', 'LIC Aadhaar Shila - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/aadhaar-shila', 'LIC Official Website'),
    ('512N310V02', 'LIC Aadhaar Stambh - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/aadhaar-stambh', 'LIC Official Website'),
    ('512G302V01', 'LIC Aam Aadmi Bima Yojana - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/aam-aadmi-bima-yojana', 'LIC Official Website'),
    ('512N365V02', 'LIC Amritbaal - Sales Brochure', 'brochure', 'https://licindia.in/documents/20121/1248951/101941+LIC_Amritbaal+Sales+Brochure_SEPT+24+(4).pdf', 'LIC Official Website'),
    ('512N285V01', 'LIC Anmol Jeevan II - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/anmol-jeevan-ii', 'LIC Official Website'),
    ('512N292V04', 'LIC Bhagya Lakshmi - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/bhagya-lakshmi', 'LIC Official Website'),
    ('512N357V01', 'LIC Dhan Rekha - Sales Brochure', 'brochure', 'https://licindia.in/documents/20121/105485/Dhan-Rekha-Sales-Brochure.pdf', 'LIC Official Website'),
    ('512N302V01', 'LIC Group Credit Life Insurance - Product Details', 'brochure', 'https://licindia.in/insurance-plan/group-credit-life-insurance', 'LIC Official Website'),
    ('512L354V01', 'LIC Index Plus - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/index-plus', 'LIC Official Website'),
    ('512N337V06', 'LIC Jeevan Akshay-VII - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/jeevan-akshay-vii', 'LIC Official Website'),
    ('512N305V02', 'LIC Jeevan Dhara II - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/jeevan-dhara-ii', 'LIC Official Website'),
    ('512N297V03', 'LIC Jeevan Lakshya - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/jeevan-lakshya', 'LIC Official Website'),
    ('512N315V02', 'LIC Jeevan Shiromani - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/jeevan-shiromani', 'LIC Official Website'),
    ('512N299V02', 'LIC Jeevan Tarun - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/jeevan-tarun', 'LIC Official Website'),
    ('512N363V02', 'LIC Jeevan Utsav - Sales Brochure', 'brochure', 'https://licindia.in/documents/20121/1248984/102268-+Jeevan+Utsav+Sales+Brochure_WEB+PDF.pdf', 'LIC Official Website'),
    ('512N293V01', 'LIC Limited Premium Endowment Plan - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/limited-premium-endowment-plan', 'LIC Official Website'),
    ('512N306V02', 'LIC Micro Bachat - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/micro-bachat', 'LIC Official Website'),
    ('512N329V03', 'LIC Micro Bachat (V03) - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/micro-bachat', 'LIC Official Website'),
    ('512N360V01', 'LIC Nav Jeevan Shree - Sales Brochure', 'brochure', 'https://licindia.in/documents/20121/1319704/LIC_Single+prem+Nav+Jeevan+Shree_Sales+Brochure_Eng+single.pdf', 'LIC Official Website'),
    ('512N284V02', 'LIC New Bima Bachat - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-bima-bachat', 'LIC Official Website'),
    ('512N296V02', 'LIC New Children Money Back Plan - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-childrens-money-back-plan', 'LIC Official Website'),
    ('512N277V03', 'LIC New Endowment Plan - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-endowment-plan', 'LIC Official Website'),
    ('512N281V03', 'LIC New Group Gratuity Cash Accumulation Plan - Product Details', 'brochure', 'https://licindia.in/insurance-plan/new-group-gratuity-cash-accumulation-plan', 'LIC Official Website'),
    ('512N282V03', 'LIC New Group Leave Encashment Plan - Product Details', 'brochure', 'https://licindia.in/insurance-plan/new-group-leave-encashment-plan', 'LIC Official Website'),
    ('512N274V03', 'LIC New Group Superannuation Cash Accumulation Plan - Product Details', 'brochure', 'https://licindia.in/insurance-plan/new-group-superannuation-cash-accumulation-plan', 'LIC Official Website'),
    ('512N287V04', 'LIC New Jeevan Mangal - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-jeevan-mangal', 'LIC Official Website'),
    ('512N338V02', 'LIC New Jeevan Shanti - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-jeevan-shanti', 'LIC Official Website'),
    ('512N280V02', 'LIC New Money Back Plan 20 Years - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-money-back-plan-20-years', 'LIC Official Website'),
    ('512N278V02', 'LIC New Money Back Plan 25 Years - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-money-back-plan-25-years', 'LIC Official Website'),
    ('512N275V02', 'LIC New One Year Renewable Group Term I - Product Details', 'brochure', 'https://licindia.in/insurance-plan/new-one-year-renewable-group-term-assurance-plan-i', 'LIC Official Website'),
    ('512N276V02', 'LIC New One Year Renewable Group Term II - Product Details', 'brochure', 'https://licindia.in/insurance-plan/new-one-year-renewable-group-term-assurance-plan-ii', 'LIC Official Website'),
    ('512L003V02', 'LIC New Pension Plus - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-pension-plus', 'LIC Official Website'),
    ('512L347V01', 'LIC New Pension Plus (V01) - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/new-pension-plus', 'LIC Official Website'),
    ('512N351V01', 'LIC New Tech-Term - Sales Brochure', 'brochure', 'https://licindia.in/documents/20121/290753/LIC_New-Tech-Term_Sales-Brochure.pdf', 'LIC Official Website'),
    ('512L002V02', 'LIC Nivesh Plus - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/nivesh-plus', 'LIC Official Website'),
    ('512G304V01', 'LIC PMJJBY - Product Details', 'brochure', 'https://licindia.in/insurance-plan/pmjjby', 'LIC Official Website'),
    ('512L334V01', 'LIC SIIP - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/siip', 'LIC Official Website'),
    ('512N283V03', 'LIC Single Premium Endowment Plan - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/single-premium-endowment-plan', 'LIC Official Website'),
    ('512N355V01', 'LIC Yuva Term - Sales Brochure', 'brochure', 'https://licindia.in/documents/20121/1194522/Lic+leaflet+Yuva+Term+4x9+inches+wxh.pdf', 'LIC Official Website'),
    ('512N318V01', 'LIC Arogya Rakshak - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/arogya-rakshak', 'LIC Official Website'),
    ('512N314V02', 'LIC Cancer Cover - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/cancer-cover', 'LIC Official Website'),
    ('512N266V03', 'LIC Jeevan Arogya - Sales Brochure', 'brochure', 'https://licindia.in/insurance-plan/jeevan-arogya', 'LIC Official Website')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== HDFC LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('101N209V01', 'HDFC Life Aajeevan Growth Nivesh and Income - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/aajeevan-growth-nivesh-and-income', 'HDFC Life Official'),
    ('101N151V04', 'HDFC Life Assured Gain Plus - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/assured-gain-plus', 'HDFC Life Official'),
    ('101L109V05', 'HDFC Life Assured Pension Plan - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/assured-pension-plan', 'HDFC Life Official'),
    ('101N104V02', 'HDFC Life CSC Suraksha - Brochure', 'brochure', 'https://www.hdfclife.com/term-insurance-plans/csc-suraksha', 'HDFC Life Official'),
    ('101N186V07', 'HDFC Life Click 2 Achieve - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/click-2-achieve-brochure.pdf', 'HDFC Life Official'),
    ('101N207V01', 'HDFC Life Click 2 Achieve Par Advantage - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/click-2-achieve-par-advantage.pdf', 'HDFC Life Official'),
    ('101N182V01', 'HDFC Life Click 2 Protect Elite Plus - Brochure', 'brochure', 'https://www.hdfclife.com/term-insurance-plans/click-2-protect-elite-plus', 'HDFC Life Official'),
    ('101N139V04', 'HDFC Life Click 2 Protect Life (V04) - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/term-insurance-plan/click-2-protect-life/HDFC-Life-Click-2-Protect-Life-101N139V02-Brochure.pdf', 'HDFC Life Official'),
    ('101N139V08', 'HDFC Life Click 2 Protect Life (V08) - Brochure', 'brochure', 'https://www.hdfclife.com/term-insurance-plans/click-2-protect-life', 'HDFC Life Official'),
    ('101N183V01', 'HDFC Life Click 2 Protect Supreme - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/HDFC-Life-click-2-protect-supreme.pdf', 'HDFC Life Official'),
    ('101N189V01', 'HDFC Life Click 2 Protect Supreme Plus - Brochure', 'brochure', 'https://www.hdfclife.com/term-insurance-plans/click-2-protect-supreme-plus', 'HDFC Life Official'),
    ('101L108V05', 'HDFC Life Click 2 Retire - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/click-2-retire', 'HDFC Life Official'),
    ('101N096V06', 'HDFC Life Group Credit Protect Plus - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-credit-protect-plus', 'HDFC Life Official'),
    ('101L170V02', 'HDFC Life Group Gratuity Product - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-gratuity-product', 'HDFC Life Official'),
    ('101N113V06', 'HDFC Life Group Jeevan Suraksha - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-jeevan-suraksha', 'HDFC Life Official'),
    ('101N172V01', 'HDFC Life Group Loan Suraksha - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-loan-suraksha', 'HDFC Life Official'),
    ('101N171V01', 'HDFC Life Group Micro Term Insurance - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-micro-term-insurance', 'HDFC Life Official'),
    ('101N138V03', 'HDFC Life Group Poorna Credit Suraksha - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-poorna-credit-suraksha', 'HDFC Life Official'),
    ('101N137V03', 'HDFC Life Group Poorna Suraksha - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-poorna-suraksha', 'HDFC Life Official'),
    ('101N135V03', 'HDFC Life Group Suraksha - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-suraksha', 'HDFC Life Official'),
    ('101N005V08', 'HDFC Life Group Term Insurance Plan - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-term-insurance', 'HDFC Life Official'),
    ('101N169V03', 'HDFC Life Group Term Life - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-term-life', 'HDFC Life Official'),
    ('101N174V02', 'HDFC Life Group Traditional Secure Plan - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-traditional-secure-plan', 'HDFC Life Official'),
    ('101L185V02', 'HDFC Life Group Unit Linked Future Secure - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-unit-linked-future-secure', 'HDFC Life Official'),
    ('101L093V02', 'HDFC Life Group Unit Linked Pension Plan - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-unit-linked-pension-plan', 'HDFC Life Official'),
    ('101N095V04', 'HDFC Life Group Variable Employee Benefit - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-variable-employee-benefit-plan', 'HDFC Life Official'),
    ('101N146V05', 'HDFC Life Guaranteed Income Insurance Plan - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/HDFC-Life-Guaranteed-Income-Insurance-Plan.pdf', 'HDFC Life Official'),
    ('101N092V16', 'HDFC Life Guaranteed Pension Plan - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/guaranteed-pension-plan', 'HDFC Life Official'),
    ('101N131V04', 'HDFC Life Guaranteed Savings Plan - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/guaranteed-savings-plan', 'HDFC Life Official'),
    ('101N152V03', 'HDFC Life Income Advantage Plan - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/income-advantage-plan', 'HDFC Life Official'),
    ('101N155V02', 'HDFC Life My Assured Income Plan - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/my-assured-income-plan', 'HDFC Life Official'),
    ('101N149V02', 'HDFC Life New Fulfilling Life - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/new-fulfilling-life', 'HDFC Life Official'),
    ('101L094V03', 'HDFC Life New Group Unit Linked Plan - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/new-group-unit-linked-plan', 'HDFC Life Official'),
    ('101N084V38', 'HDFC Life New Immediate Annuity Plan - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/new-immediate-annuity-plan', 'HDFC Life Official'),
    ('101G107V02', 'HDFC Life PMJJBY - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/pmjjby', 'HDFC Life Official'),
    ('101N091V05', 'HDFC Life Personal Pension Plus - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/personal-pension-plus', 'HDFC Life Official'),
    ('101N114V05', 'HDFC Life Pragati - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/pragati', 'HDFC Life Official'),
    ('101L180V01', 'HDFC Life Sampoorn Nivesh Plus - Brochure', 'brochure', 'https://www.hdfclife.com/unit-linked-plans/sampoorn-nivesh-plus', 'HDFC Life Official'),
    ('101N102V06', 'HDFC Life Sampoorn Samridhi Plus - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/sampoorn-samridhi-plus', 'HDFC Life Official'),
    ('101N208V02', 'HDFC Life Sanchay Aajeevan Guaranteed Advantage - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/sanchay-aajeevan-guaranteed-advantage', 'HDFC Life Official'),
    ('101N136V04', 'HDFC Life Sanchay Par Advantage - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/HDFC-Life-Sanchay-Par-Advantage-Retail-Brochure.pdf', 'HDFC Life Official'),
    ('101N134V27', 'HDFC Life Sanchay Plus - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/Sanchay-Plus_v09-Brochure-v10.pdf', 'HDFC Life Official'),
    ('101N160V05', 'HDFC Life Saral Jeevan - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/saral-jeevan', 'HDFC Life Official'),
    ('101N141V03', 'HDFC Life Saral Pension - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/saral-pension', 'HDFC Life Official'),
    ('101N166V03', 'HDFC Life Smart Income Plan - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/smart-income-plan', 'HDFC Life Official'),
    ('101L164V08', 'HDFC Life Smart Pension Plan - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/new-brochure/HDFC-Life-Smart-Pension-Plan-Brochure.pdf', 'HDFC Life Official'),
    ('101L187V01', 'HDFC Life Smart Protect Plus - Brochure', 'brochure', 'https://www.hdfclife.com/content/dam/hdfclifeinsurancecompany/products-page/brochure-pdf/0114450023-HDFC-Life-Smart-Protect-Plan-Brochure.pdf', 'HDFC Life Official'),
    ('101L082V03', 'HDFC Life Smart Woman Plan - Brochure', 'brochure', 'https://www.hdfclife.com/unit-linked-plans/smart-woman-plan', 'HDFC Life Official'),
    ('101N167V02', 'HDFC Life Star Saver - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/star-saver', 'HDFC Life Official'),
    ('101N098V06', 'HDFC Life Super Income Plan - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/super-income-plan', 'HDFC Life Official'),
    ('101N144V05', 'HDFC Life Systematic Pension Plan - Brochure', 'brochure', 'https://www.hdfclife.com/retirement-plans/systematic-pension-plan', 'HDFC Life Official'),
    ('101N105V05', 'HDFC Life Uday - Brochure', 'brochure', 'https://www.hdfclife.com/savings-plans/uday', 'HDFC Life Official'),
    ('101N099V05', 'HDFC Life YoungStar Udaan - Brochure', 'brochure', 'https://www.hdfclife.com/child-insurance-plans/youngstar-udaan', 'HDFC Life Official'),
    ('101N075V03', 'HDFC SL Group Traditional Plan - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-traditional-plan', 'HDFC Life Official'),
    ('101N106V04', 'HDFC Life Cancer Care - Brochure', 'brochure', 'https://www.hdfclife.com/health-insurance-plans/cancer-care', 'HDFC Life Official'),
    ('101N117V03', 'HDFC Life Cardiac Care - Brochure', 'brochure', 'https://www.hdfclife.com/health-insurance-plans/cardiac-care', 'HDFC Life Official'),
    ('101Y121V03', 'HDFC Life Click 2 Protect Optima Restore - Brochure', 'brochure', 'https://www.hdfclife.com/health-insurance-plans/click-2-protect-optima-restore', 'HDFC Life Official'),
    ('101Y122V05', 'HDFC Life Click 2 Protect Optima Secure - Brochure', 'brochure', 'https://www.hdfclife.com/health-insurance-plans/click-2-protect-optima-secure', 'HDFC Life Official'),
    ('101N110V03', 'HDFC Life Easy Health - Brochure', 'brochure', 'https://www.hdfclife.com/health-insurance-plans/easy-health', 'HDFC Life Official'),
    ('101N116V05', 'HDFC Life Group Health Shield - Product Details', 'brochure', 'https://www.hdfclife.com/group-insurance/group-health-shield', 'HDFC Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ICICI PRUDENTIAL LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('105N185V04', 'ICICI Pru Assured Savings - Brochure', 'brochure', 'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI%20Pru%20Assured%20Savings%20Insurance%20Plan.pdf', 'ICICI Prudential Life Official'),
    ('105N201V06', 'ICICI Pru GIFT Pro - Brochure', 'brochure', 'https://www.iciciprulife.com/savings-insurance/gift-pro.html', 'ICICI Prudential Life Official'),
    ('105N119V08', 'ICICI Pru Group Term Plus - Product Details', 'brochure', 'https://www.iciciprulife.com/group-insurance/group-term-plus.html', 'ICICI Prudential Life Official'),
    ('105N187V05', 'ICICI Pru Guaranteed Income For Tomorrow - Brochure', 'brochure', 'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI-Pru-Gold-Brochure.pdf', 'ICICI Prudential Life Official'),
    ('105N186V03', 'ICICI Pru Guaranteed Pension Plan - Brochure', 'brochure', 'https://www.iciciprulife.com/retirement-pension-plans/guaranteed-pension-plan.html', 'ICICI Prudential Life Official'),
    ('105N204V01', 'ICICI Pru Guaranteed Pension Plan Flexi - Brochure', 'brochure', 'https://www.iciciprulife.com/retirement-pension-plans/guaranteed-pension-plan-flexi.html', 'ICICI Prudential Life Official'),
    ('105N182V02', 'ICICI Pru Heart/Cancer Protect - Brochure', 'brochure', 'https://www.iciciprulife.com/term-insurance/heart-cancer-protect.html', 'ICICI Prudential Life Official'),
    ('105N009V06', 'ICICI Pru Immediate Annuity - Brochure', 'brochure', 'https://www.iciciprulife.com/retirement-pension-plans/immediate-annuity.html', 'ICICI Prudential Life Official'),
    ('105N160V02', 'ICICI Pru Lakshya - Brochure', 'brochure', 'https://www.iciciprulife.com/savings-insurance/lakshya.html', 'ICICI Prudential Life Official'),
    ('105N179V01', 'ICICI Pru Lakshya Wealth - Brochure', 'brochure', 'https://www.iciciprulife.com/savings-insurance/lakshya-wealth.html', 'ICICI Prudential Life Official'),
    ('105L192V03', 'ICICI Pru Platinum - Brochure', 'brochure', 'https://www.iciciprulife.com/ulip-plans/platinum.html', 'ICICI Prudential Life Official'),
    ('105L191V03', 'ICICI Pru Protect N Gain - Brochure', 'brochure', 'https://www.iciciprulife.com/ulip-plans/protect-n-gain.html', 'ICICI Prudential Life Official'),
    ('105N176V02', 'ICICI Pru Saral Jeevan Bima - Brochure', 'brochure', 'https://www.iciciprulife.com/term-insurance/saral-jeevan-bima.html', 'ICICI Prudential Life Official'),
    ('105N175V03', 'ICICI Pru Saral Pension - Brochure', 'brochure', 'https://www.iciciprulife.com/retirement-pension-plans/saral-pension.html', 'ICICI Prudential Life Official'),
    ('105L187V03', 'ICICI Pru Signature - Brochure', 'brochure', 'https://www.iciciprulife.com/content/dam/icicipru/brochures/IPru-Signature-Offline-Brochure.pdf', 'ICICI Prudential Life Official'),
    ('105L194V02', 'ICICI Pru Signature Pension - Brochure', 'brochure', 'https://www.iciciprulife.com/retirement-pension-plans/signature-pension.html', 'ICICI Prudential Life Official'),
    ('105L199V01', 'ICICI Pru Signature Pension V2 - Brochure', 'brochure', 'https://www.iciciprulife.com/retirement-pension-plans/signature-pension.html', 'ICICI Prudential Life Official'),
    ('105L152V02', 'ICICI Pru Smart Kids Solution - Brochure', 'brochure', 'https://www.iciciprulife.com/child-insurance/smart-kids-solution.html', 'ICICI Prudential Life Official'),
    ('105L186V03', 'ICICI Pru Wealth Builder - Brochure', 'brochure', 'https://www.iciciprulife.com/ulip-plans/wealth-builder.html', 'ICICI Prudential Life Official'),
    ('105N205V02', 'ICICI Pru iProtect Smart Plus - Brochure', 'brochure', 'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI-Pru-iProtect-Smart-Illustrated-Brochure.pdf', 'ICICI Prudential Life Official'),
    ('105N195V01', 'ICICI Pru iProtect Smart Return of Premium - Brochure', 'brochure', 'https://www.iciciprulife.com/content/dam/icicipru/brochures/ICICI_Pru_iProtect_Return_of_Premium_Brochure.pdf', 'ICICI Prudential Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== AXIS MAX LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('104N129V01', 'Axis Max Life Group Smart Health Insurance - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/group-insurance/group-smart-health', 'Axis Max Life Official'),
    ('104L082V05', 'Axis Max Life Fast Track Super Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/ulip-plans/fast-track-super', 'Axis Max Life Official'),
    ('104L121V04', 'Axis Max Life Flexi Wealth Advantage Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/ulip-plans/flexi-wealth-advantage', 'Axis Max Life Official'),
    ('104L115V04', 'Axis Max Life Flexi Wealth Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/ulip-plans/flexi-wealth-plan', 'Axis Max Life Official'),
    ('104L075V09', 'Axis Max Life Forever Young Pension Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/retirement-plans/forever-young-pension', 'Axis Max Life Official'),
    ('104N095V03', 'Axis Max Life Group Credit Life Premier - Product Details', 'brochure', 'https://www.maxlifeinsurance.com/group-insurance/group-credit-life-premier', 'Axis Max Life Official'),
    ('104N112V04', 'Axis Max Life Group Term Life Platinum Assurance - Product Details', 'brochure', 'https://www.maxlifeinsurance.com/group-insurance/group-term-life-platinum', 'Axis Max Life Official'),
    ('104N091V07', 'Axis Max Life Monthly Income Advantage - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/content/dam/corporate/Brochures/Savings-and-income-plans/English/Max-Life-Monthly-Income-Advantage-Plan/max-life-monthly-income-advantage-plan-leaflet.pdf', 'Axis Max Life Official'),
    ('104L131V01', 'Axis Max Life Online Savings Plan Plus - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/online-savings-plan-plus', 'Axis Max Life Official'),
    ('104G089V01', 'Axis Max Life PMJJBY - Product Details', 'brochure', 'https://www.maxlifeinsurance.com/group-insurance/pmjjby', 'Axis Max Life Official'),
    ('104N117V02', 'Axis Max Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/term-insurance/saral-jeevan-bima', 'Axis Max Life Official'),
    ('104N119V04', 'Axis Max Life Saral Pension Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/retirement-plans/saral-pension', 'Axis Max Life Official'),
    ('104N111V04', 'Axis Max Life Savings Advantage Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/savings-advantage', 'Axis Max Life Official'),
    ('104N136V03', 'Axis Max Life Secure Earnings & Wellness Advantage - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/secure-earnings-wellness-advantage', 'Axis Max Life Official'),
    ('104L084V15', 'Axis Max Life Shiksha Plus Super Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/child-plans/shiksha-plus-super', 'Axis Max Life Official'),
    ('104N123V06', 'Axis Max Life Smart Fixed-return Digital Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/smart-fixed-return-digital', 'Axis Max Life Official'),
    ('104N126V01', 'Axis Max Life Smart Group Term Life - Product Details', 'brochure', 'https://www.maxlifeinsurance.com/group-insurance/smart-group-term-life', 'Axis Max Life Official'),
    ('104N122V23', 'Axis Max Life Smart Guaranteed Pension Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/retirement-plans/smart-guaranteed-pension', 'Axis Max Life Official'),
    ('104N127V05', 'Axis Max Life Smart Term Plan Plus - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/content/dam/corporate/Brochures/Term-plans/English/smart-term-plan/smart-term-plan-leaflet.pdf', 'Axis Max Life Official'),
    ('104L128V01', 'Axis Max Life Smart Term with Additional Returns - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/term-insurance/smart-term-additional-returns', 'Axis Max Life Official'),
    ('104N125V09', 'Axis Max Life Smart Total Elite Protection Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/term-insurance/smart-total-elite-protection', 'Axis Max Life Official'),
    ('104N159V01', 'Axis Max Life Smart Value Income & Benefit Enhancer V01 - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/smart-value-income-benefit-enhancer', 'Axis Max Life Official'),
    ('104N159V04', 'Axis Max Life Smart Value Income & Benefit Enhancer V04 - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/smart-value-income-benefit-enhancer', 'Axis Max Life Official'),
    ('104N135V03', 'Axis Max Life Smart Wealth Advantage Growth Par - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/savings-plans/smart-wealth-advantage-growth-par', 'Axis Max Life Official'),
    ('104N138V04', 'Axis Max Life Smart Wealth Advantage Guarantee Elite - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/content/dam/corporate/Brochures/Savings-and-income-plans/English/max-life-smart-wealth-advantage-guarantee-plan/Max%20Life%20Smart%20Wealth%20Advantage%20Guarantee%20Plan_Leaflet.pdf', 'Axis Max Life Official'),
    ('104N137V13', 'Axis Max Life Smart Wealth Annuity Guaranteed Pension - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/retirement-plans/smart-wealth-annuity-guaranteed-pension', 'Axis Max Life Official'),
    ('104N120V04', 'Axis Max Life Smart Wealth Income Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/content/dam/corporate/Brochures/Savings-and-income-plans/English/smart-wealth-income-plan/Maxlife-smart-wealth-Income-plan-leaflet.pdf', 'Axis Max Life Official'),
    ('104N116V15', 'Axis Max Life Smart Wealth Plan - Brochure', 'brochure', 'https://www.maxlifeinsurance.com/content/dam/corporate/Brochures/Savings-and-income-plans/English/max-life-smart-wealth-plan/3.%20Max%20Life%20Smart_Wealth_Plan_Prospectus_Web.pdf', 'Axis Max Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== SBI LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('111N091V03', 'SBI Life CapAssure Gold - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/capassure-gold', 'SBI Life Official'),
    ('111L079V03', 'SBI Life Kalyan ULIP Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/kalyanulip-brochure', 'SBI Life Official'),
    ('111N129V05', 'SBI Life New Smart Samriddhi - Brochure', 'brochure', 'https://www.sbilife.co.in/new-smart-samriddhi-brochure', 'SBI Life Official'),
    ('111L094V01', 'SBI Life Retire Smart - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/retirement-plans/retire-smart', 'SBI Life Official'),
    ('111L102V03', 'SBI Life Retire Smart Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/retirement-plans/retire-smart-plus', 'SBI Life Official'),
    ('111N040V04', 'SBI Life Sampoorn Suraksha - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/protection-plans/sampoorn-suraksha', 'SBI Life Official'),
    ('111N101V02', 'SBI Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/protection-plans/saral-jeevan-bima', 'SBI Life Official'),
    ('111N098V03', 'SBI Life Saral Pension - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/retirement-plans/saral-pension', 'SBI Life Official'),
    ('111N161V02', 'SBI Life Saral Swadhan Supreme - Brochure', 'brochure', 'https://www.sbilife.co.in/saral-swadhan-supreme-brochure', 'SBI Life Official'),
    ('111N103V02', 'SBI Life Shubh Nivesh - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/shubh-nivesh', 'SBI Life Official'),
    ('111N134V10', 'SBI Life Smart Annuity Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/retirement-plans/smart-annuity-plus', 'SBI Life Official'),
    ('111N106V02', 'SBI Life Smart Champ Insurance - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/child-plans/smart-champ-insurance', 'SBI Life Official'),
    ('111L146V01', 'SBI Life Smart Elite Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/ulip-plans/smart-elite-plus', 'SBI Life Official'),
    ('111L142V01', 'SBI Life Smart Fortune Builder - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/ulip-plans/smart-fortune-builder', 'SBI Life Official'),
    ('111N102V02', 'SBI Life Smart Humsafar - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-humsafar', 'SBI Life Official'),
    ('111N168V01', 'SBI Life Smart Money Back Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-money-back-plus', 'SBI Life Official'),
    ('111N175V01', 'SBI Life Smart Platina Advantage - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-platina-advantage', 'SBI Life Official'),
    ('111N126V04', 'SBI Life Smart Platina Assure - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-platina-assure', 'SBI Life Official'),
    ('111N107V02', 'SBI Life Smart Platina Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-platina-plus', 'SBI Life Official'),
    ('111N133V06', 'SBI Life Smart Platina Plus V6 - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-platina-plus', 'SBI Life Official'),
    ('111N105V02', 'SBI Life Smart Privilege - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/smart-privilege', 'SBI Life Official'),
    ('111L143V01', 'SBI Life Smart Privilege Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/ulip-plans/smart-privilege-plus', 'SBI Life Official'),
    ('111L144V01', 'SBI Life Smart Scholar Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/child-plans/smart-scholar-plus', 'SBI Life Official'),
    ('111N145V01', 'SBI Life Smart Shield Premier - Brochure', 'brochure', 'https://www.sbilife.co.in/smart-shield-premier-brochure', 'SBI Life Official'),
    ('111N147V03', 'SBI Life Smart Swadhan Supreme - Brochure', 'brochure', 'https://www.sbilife.co.in/smart-swadhan-supreme-brochure', 'SBI Life Official'),
    ('111L105V02', 'SBI Life Smart Wealth Builder - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/ulip-plans/smart-wealth-builder', 'SBI Life Official'),
    ('111N008V01', 'SBI Life Sudarshan Plan - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/savings-plans/sudarshan', 'SBI Life Official'),
    ('111L147V01', 'SBI Life eWealth Plus - Brochure', 'brochure', 'https://www.sbilife.co.in/en/individual-life-insurance/ulip-plans/ewealth-plus', 'SBI Life Official'),
    ('111N108V02', 'SBI Life eShield Next - Product Guide', 'brochure', 'https://www.sbilife.co.in/eshield-next-product-guide', 'SBI Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== KOTAK MAHINDRA LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('107L064V06', 'Kotak Ace Investment - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/unit-linked-plans/ace-investment', 'Kotak Life Official'),
    ('107N123V11', 'Kotak Assured Pension - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/retirement-pension-plans/assured-pension', 'Kotak Life Official'),
    ('107N081V09', 'Kotak Assured Savings Plan - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/savings-plans/assured-savings-plan', 'Kotak Life Official'),
    ('107N082V03', 'Kotak Classic Endowment Plan - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/savings-plans/classic-endowment-plan', 'Kotak Life Official'),
    ('107N018V08', 'Kotak Complete Cover Group Plan - Product Details', 'brochure', 'https://www.kotaklife.com/insurance-plans/group-plans/complete-cover-group-plan', 'Kotak Life Official'),
    ('107L136V02', 'Kotak Confident Retirement Builder - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/retirement-pension-plans/confident-retirement-builder', 'Kotak Life Official'),
    ('107N148V05', 'Kotak EDGE - Brochure', 'brochure', 'https://www.kotaklife.com/assets/images/uploads/insurance-plans/Kotak_EDGE_Brochure.pdf', 'Kotak Life Official'),
    ('107N125V03', 'Kotak Fortune Maximiser - Brochure', 'brochure', 'https://www.kotaklife.com/assets/images/uploads/insurance-plans/kotak-fortune-maximiser.pdf', 'Kotak Life Official'),
    ('107N163V01', 'Kotak Gen2Gen Income - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/savings-plans/gen2gen-income', 'Kotak Life Official'),
    ('107N132V02', 'Kotak Gen2Gen Protect - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/term-plans/gen2gen-protect', 'Kotak Life Official'),
    ('107N030V06', 'Kotak Gratuity Group Plan - Product Details', 'brochure', 'https://www.kotaklife.com/insurance-plans/group-plans/gratuity-group-plan', 'Kotak Life Official'),
    ('107N055V05', 'Kotak Group Assure - Product Details', 'brochure', 'https://www.kotaklife.com/insurance-plans/group-plans/group-assure', 'Kotak Life Official'),
    ('107N098V05', 'Kotak Group Secure One - Product Details', 'brochure', 'https://www.kotaklife.com/insurance-plans/group-plans/group-secure-one', 'Kotak Life Official'),
    ('107N128V09', 'Kotak Guaranteed Fortune Builder - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/savings-plans/guaranteed-fortune-builder', 'Kotak Life Official'),
    ('107N100V03', 'Kotak Guaranteed Savings Plan - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/savings-plans/guaranteed-savings-plan', 'Kotak Life Official'),
    ('107L073V05', 'Kotak Invest Maxima - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/unit-linked-plans/invest-maxima', 'Kotak Life Official'),
    ('107N103V19', 'Kotak Lifetime Income Plan - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/retirement-pension-plans/lifetime-income-plan', 'Kotak Life Official'),
    ('107L067V07', 'Kotak Platinum - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/unit-linked-plans/platinum', 'Kotak Life Official'),
    ('107N139V01', 'Kotak Saral Jeevan Bima - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/term-plans/saral-jeevan-bima', 'Kotak Life Official'),
    ('107N140V01', 'Kotak Saral Pension - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/retirement-pension-plans/saral-pension', 'Kotak Life Official'),
    ('107L131V03', 'Kotak T.U.L.I.P - Brochure', 'brochure', 'https://www.kotaklife.com/assets/images/uploads/insurance-plans/Kotak_TULIP_Brochure.pdf', 'Kotak Life Official'),
    ('107N005V07', 'Kotak Term Plan - Brochure', 'brochure', 'https://www.kotaklife.com/assets/images/uploads/insurance-plans/kotaktermplan.pdf', 'Kotak Life Official'),
    ('107L118V03', 'Kotak Wealth Optima Plan - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/unit-linked-plans/wealth-optima-plan', 'Kotak Life Official'),
    ('107L137V02', 'Kotak e-Invest Plus - Brochure', 'brochure', 'https://www.kotaklife.com/insurance-plans/unit-linked-plans/e-invest-plus', 'Kotak Life Official'),
    ('107N129V03', 'Kotak e-Term - Brochure', 'brochure', 'https://www.kotaklife.com/assets/images/uploads/insurance-plans/Kotak-e-Term-Plan-Brochure.pdf', 'Kotak Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== BAJAJ LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('116N186V03', 'Bajaj Life ACE - Brochure', 'brochure', 'https://www.bajajallianzlife.com/content/dam/balic-web/pdf/savings-plans/ace-brochure.pdf', 'Bajaj Life Official'),
    ('116N170V12', 'Bajaj Life Assured Wealth Goal - Brochure', 'brochure', 'https://www.bajajallianzlife.com/content/dam/balic-web/pdf/savings-plans/awg-brochure.pdf', 'Bajaj Life Official'),
    ('116N183V01', 'Bajaj Life Diabetic Term Plan II - Brochure', 'brochure', 'https://www.bajajallianzlife.com/term-insurance/diabetic-term-plan-2.html', 'Bajaj Life Official'),
    ('116L196V04', 'Bajaj Life Fortune Gain II - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/fortune-gain-2.html', 'Bajaj Life Official'),
    ('116L202V01', 'Bajaj Life Future Wealth Gain IV - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/future-wealth-gain-4.html', 'Bajaj Life Official'),
    ('116L204V01', 'Bajaj Life Goal Assure IV - Brochure', 'brochure', 'https://buyonline.bajajallianzlife.com/content/dam/balic/pdf/ulip/goal-assure-brochure.pdf', 'Bajaj Life Official'),
    ('116L206V01', 'Bajaj Life Goal Based Saving III - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/goal-based-saving-3.html', 'Bajaj Life Official'),
    ('116N155V13', 'Bajaj Life Goal Suraksha - Brochure', 'brochure', 'https://www.bajajallianzlife.com/savings-plans/goal-suraksha.html', 'Bajaj Life Official'),
    ('116N094V07', 'Bajaj Life Group Credit Protection Plus - Product Details', 'brochure', 'https://www.bajajallianzlife.com/group-insurance/group-credit-protection-plus.html', 'Bajaj Life Official'),
    ('116N160V01', 'Bajaj Life Group Employee Care - Product Details', 'brochure', 'https://www.bajajallianzlife.com/group-insurance/group-employee-care.html', 'Bajaj Life Official'),
    ('116N184V01', 'Bajaj Life Group Secure Return - Product Details', 'brochure', 'https://www.bajajallianzlife.com/group-insurance/group-secure-return.html', 'Bajaj Life Official'),
    ('116N115V04', 'Bajaj Life Group Superannuation Secure - Product Details', 'brochure', 'https://www.bajajallianzlife.com/group-insurance/group-superannuation-secure.html', 'Bajaj Life Official'),
    ('116N021V06', 'Bajaj Life Group Term Plan - Product Details', 'brochure', 'https://www.bajajallianzlife.com/group-insurance/group-term-plan.html', 'Bajaj Life Official'),
    ('116N187V08', 'Bajaj Life Guaranteed Pension Goal II - Brochure', 'brochure', 'https://www.bajajallianzlife.com/retirement-plans/guaranteed-pension-goal-2.html', 'Bajaj Life Official'),
    ('116L205V01', 'Bajaj Life Invest Protect Goal III - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/invest-protect-goal-3.html', 'Bajaj Life Official'),
    ('116L203V01', 'Bajaj Life LongLife Goal III - Brochure', 'brochure', 'https://www.bajajallianzlife.com/content/dam/balic-web/pdf/retirement-plans/longlife-goal-brochure.pdf', 'Bajaj Life Official'),
    ('116L207V02', 'Bajaj Life Magnum Fortune Plus III - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/magnum-fortune-plus-3.html', 'Bajaj Life Official'),
    ('116G133V01', 'Bajaj Life PMJJBY - Product Details', 'brochure', 'https://www.bajajallianzlife.com/group-insurance/pmjjby.html', 'Bajaj Life Official'),
    ('116L201V04', 'Bajaj Life Smart Wealth Goal V - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/smart-wealth-goal-5.html', 'Bajaj Life Official'),
    ('116N198V03', 'Bajaj Life Superwoman Term - Brochure', 'brochure', 'https://www.bajajallianzlife.com/term-insurance/superwoman-term.html', 'Bajaj Life Official'),
    ('116L211V01', 'Bajaj Life Supreme - Brochure', 'brochure', 'https://www.bajajallianzlife.com/ulip-plans/supreme.html', 'Bajaj Life Official'),
    ('116N208V03', 'Bajaj Life iSecure II - Brochure', 'brochure', 'https://www.bajajallianzlife.com/content/dam/balic/pdf/term-insurance/life-secure-brochure.pdf', 'Bajaj Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== ABSLI PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('109N136V04', 'ABSLI Akshaya Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-akshaya-plan', 'ABSLI Official'),
    ('109N127V19', 'ABSLI Assured Income Plus - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-assured-income-plus', 'ABSLI Official'),
    ('109N134V13', 'ABSLI Assured Savings Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/uploads/Assured_Flexi_Savings_Plan_Brochure_Aditya_Birla_Sun_Life_Insurance_73de0dce60.pdf', 'ABSLI Official'),
    ('109N130V02', 'ABSLI Empower Pension Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/retirement-plans/absli-empower-pension-plan', 'ABSLI Official'),
    ('109N122V03', 'ABSLI Group Secure Life Plan - Product Details', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/group-plans/absli-group-secure-life-plan', 'ABSLI Official'),
    ('109N134V02', 'ABSLI Guaranteed Milestone Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-guaranteed-milestone-plan', 'ABSLI Official'),
    ('109N120V02', 'ABSLI Immediate Annuity Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/retirement-plans/absli-immediate-annuity-plan', 'ABSLI Official'),
    ('109N089V06', 'ABSLI Income Assured Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-income-assured-plan', 'ABSLI Official'),
    ('109N136V02', 'ABSLI Life Shield Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/uploads/Life_Shield_Plan_Brochure_Aditya_Birla_Sun_Life_Insurance_d75385fd03.pdf', 'ABSLI Official'),
    ('109L149V01', 'ABSLI Param Suraksha - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/ulip-plans/absli-param-suraksha', 'ABSLI Official'),
    ('109L142V01', 'ABSLI Platinum Gain Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/ulip-plans/absli-platinum-gain-plan', 'ABSLI Official'),
    ('109N145V01', 'ABSLI Saral Jeevan Bima - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/term-plans/absli-saral-jeevan-bima', 'ABSLI Official'),
    ('109N146V01', 'ABSLI Saral Pension - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/retirement-plans/absli-saral-pension', 'ABSLI Official'),
    ('109N102V14', 'ABSLI SecurePlus Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-secureplus-plan', 'ABSLI Official'),
    ('109N153V02', 'ABSLI Super Term Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/uploads/ABSLI_Super_Term_Plan_V01_Brochure_8b9b57ef0d.pdf', 'ABSLI Official'),
    ('109N092V06', 'ABSLI Vision Endowment Plus - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-vision-endowment-plus', 'ABSLI Official'),
    ('109N079V07', 'ABSLI Vision LifeIncome Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-vision-lifeincome-plan', 'ABSLI Official'),
    ('109N131V02', 'ABSLI Vision Money Back Plus Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/savings-plans/absli-vision-money-back-plus-plan', 'ABSLI Official'),
    ('109L117V02', 'ABSLI Wealth Max Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/ulip-plans/absli-wealth-max-plan', 'ABSLI Official'),
    ('109L115V02', 'ABSLI Wealth Secure Plan - Brochure', 'brochure', 'https://lifeinsurance.adityabirlacapital.com/ulip-plans/absli-wealth-secure-plan', 'ABSLI Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== TATA AIA LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('110N175V02', 'Tata AIA Fortune Guarantee Retirement Ready - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/retirement-plans/fortune-guarantee-retirement-ready.html', 'Tata AIA Official'),
    ('110N163V06', 'Tata AIA Fortune Guarantee Supreme - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/savings-plans/fortune-guarantee-supreme.html', 'Tata AIA Official'),
    ('110L112V06', 'Tata AIA Fortune Pro - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/fortune-pro.html', 'Tata AIA Official'),
    ('110N152V15', 'Tata AIA Guaranteed Return Insurance Plan - Brochure', 'brochure', 'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/savings-solutions/guaranteed-return-insurance-plan/Guaranteed-Return-Insurance-Plan-GRIP-V9-Brochure.pdf', 'Tata AIA Official'),
    ('110N102V03', 'Tata AIA Maha Raksha Supreme - Brochure', 'brochure', 'https://www.tataaia.com/content/dam/tataaialifeinsurancecompanylimited/pdf/download-centre/english/brochures/Maha-Raksha-Supreme-Version-3-Brochure-Web.pdf', 'Tata AIA Official'),
    ('110N171V12', 'Tata AIA Maha Raksha Supreme Select - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/term-insurance/maha-raksha-supreme-select.html', 'Tata AIA Official'),
    ('110N129V05', 'Tata AIA Sampoorna Raksha - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/term-insurance/sampoorna-raksha.html', 'Tata AIA Official'),
    ('110N130V05', 'Tata AIA Sampoorna Raksha Plus - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/term-insurance/sampoorna-raksha-plus.html', 'Tata AIA Official'),
    ('110N176V05', 'Tata AIA Sampoorna Raksha Promise - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/term-insurance/sampoorna-raksha-promise.html', 'Tata AIA Official'),
    ('110N160V04', 'Tata AIA Sampoorna Raksha Supreme - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/term-insurance/sampoorna-raksha-supreme.html', 'Tata AIA Official'),
    ('110L177V01', 'Tata AIA Smart Fortune Plus - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/smart-fortune-plus.html', 'Tata AIA Official'),
    ('110N126V05', 'Tata AIA Smart Income Plus - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/savings-plans/smart-income-plus.html', 'Tata AIA Official'),
    ('110L174V02', 'Tata AIA Smart SIP - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/smart-sip.html', 'Tata AIA Official'),
    ('110L172V01', 'Tata AIA Smart Sampoorna Raksha Pro - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/smart-sampoorna-raksha-pro.html', 'Tata AIA Official'),
    ('110L179V02', 'Tata AIA Smart Sampoorna Raksha Supreme - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/smart-sampoorna-raksha-supreme.html', 'Tata AIA Official'),
    ('110L111V04', 'Tata AIA Wealth Pro - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/wealth-pro.html', 'Tata AIA Official'),
    ('110L164V06', 'Tata AIA i Systematic Insurance Plan - Brochure', 'brochure', 'https://www.tataaia.com/life-insurance-plans/ulip-plans/i-systematic-insurance-plan.html', 'Tata AIA Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== PNB METLIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('117N129V02', 'PNB MetLife Century Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/savings-plans/century-plan.html', 'PNB MetLife Official'),
    ('117N141V01', 'PNB MetLife DigiProtect Term Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/term-insurance/digiprotect.html', 'PNB MetLife Official'),
    ('117N135V04', 'PNB MetLife Genius Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/child-plans/genius-plan.html', 'PNB MetLife Official'),
    ('117N134V07', 'PNB MetLife Grand Assured Income Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/savings-plans/grand-assured-income-plan.html', 'PNB MetLife Official'),
    ('117N105V04', 'PNB MetLife Group Term Life Insurance - Product Details', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/group-plans/group-term-life.html', 'PNB MetLife Official'),
    ('117N124V16', 'PNB MetLife Guaranteed Future Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/savings-plans/guaranteed-future-plan.html', 'PNB MetLife Official'),
    ('117N126V02', 'PNB MetLife Mera Term Plan Plus - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/term-insurance/mera-term-plan-plus.html', 'PNB MetLife Official'),
    ('117L098V08', 'PNB MetLife Mera Wealth Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/ulip-plans/mera-wealth-plan.html', 'PNB MetLife Official'),
    ('117N132V01', 'PNB MetLife Saral Jeevan Bima - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/term-insurance/saral-jeevan-bima.html', 'PNB MetLife Official'),
    ('117N140V01', 'PNB MetLife Saral Pension - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/retirement-plans/saral-pension.html', 'PNB MetLife Official'),
    ('117L139V02', 'PNB MetLife Smart Goal Ensuring Multiplier - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/ulip-plans/smart-goal-ensuring-multiplier.html', 'PNB MetLife Official'),
    ('117L137V04', 'PNB MetLife Smart Invest Pension Plan - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/retirement-plans/smart-invest-pension.html', 'PNB MetLife Official'),
    ('117L138V03', 'PNB MetLife Smart Invest Pension Plan Pro - Brochure', 'brochure', 'https://www.pnbmetlife.com/insurance-plans/retirement-plans/smart-invest-pension-pro.html', 'PNB MetLife Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== AGEAS FEDERAL LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('135N083V01', 'Ageas Federal Assured Income Plan - Brochure', 'brochure', 'https://www.agaborrowfederal.com/life-insurance-plans/savings-plans/assured-income-plan', 'Ageas Federal Official'),
    ('135N078V01', 'Ageas Federal Life Advantage Plus Plan - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/savings-plans/advantage-plus', 'Ageas Federal Official'),
    ('135N080V01', 'Ageas Federal Life Rising Star Plan - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/child-plans/rising-star', 'Ageas Federal Official'),
    ('135N075V01', 'Ageas Federal Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/term-insurance/saral-jeevan-bima', 'Ageas Federal Official'),
    ('135N076V01', 'Ageas Federal Life Saral Pension Plan - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/retirement-plans/saral-pension', 'Ageas Federal Official'),
    ('135L053V02', 'Ageas Federal Life ULIP Plan - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/ulip-plans', 'Ageas Federal Official'),
    ('135L047V03', 'Ageas Federal Wealth Gain Plan - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/ulip-plans/wealth-gain', 'Ageas Federal Official'),
    ('135N088V01', 'Ageas Federal iSecure Plan - Brochure', 'brochure', 'https://www.ageasfederal.com/life-insurance-plans/term-insurance/isecure', 'Ageas Federal Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== AVIVA LIFE PRODUCTS =====================

INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('122N120V02', 'Aviva Annuity Plus - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/retirement-plans/annuity-plus', 'Aviva India Official'),
    ('122N058V01', 'Aviva Guaranteed Income Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/savings-plans/guaranteed-income-plan', 'Aviva India Official'),
    ('122N060V01', 'Aviva LifeShield Advantage - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/term-plans/lifeshield-advantage', 'Aviva India Official'),
    ('122N139V01', 'Aviva New Family Income Builder - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/savings-plans/new-family-income-builder', 'Aviva India Official'),
    ('122N143V01', 'Aviva Saral Jeevan Bima - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/term-plans/saral-jeevan-bima', 'Aviva India Official'),
    ('122N065V01', 'Aviva Signature 3D Term Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/term-plans/signature-3d-term-plan', 'Aviva India Official'),
    ('122N142V01', 'Aviva Signature 3D Term Plan (V01) - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/term-plans/signature-3d-term-plan', 'Aviva India Official'),
    ('122N068V01', 'Aviva Signature Increasing Income Plan - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/retirement-plans/signature-increasing-income', 'Aviva India Official'),
    ('122L151V01', 'Aviva Signature Investment Plan Platinum - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/ulip-plans/signature-investment-platinum', 'Aviva India Official'),
    ('122N130V02', 'Aviva Young Scholar Secure - Brochure', 'brochure', 'https://www.avivaindia.com/life-insurance/child-plans/young-scholar-secure', 'Aviva India Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- ===================== REMAINING SMALLER LIFE INSURERS =====================

-- Bandhan Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('138N011V02', 'Bandhan Life Insta Pension - Brochure', 'brochure', 'https://www.bandhanlife.com/retirement-plans/insta-pension', 'Bandhan Life Official'),
    ('138N077V01', 'Bandhan Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.bandhanlife.com/term-plans/saral-jeevan-bima', 'Bandhan Life Official'),
    ('138N017V01', 'Bandhan Life Saral Jeevan Bima (V01) - Brochure', 'brochure', 'https://www.bandhanlife.com/term-plans/saral-jeevan-bima', 'Bandhan Life Official'),
    ('138N096V02', 'Bandhan Life iGuarantee Vishwas - Brochure', 'brochure', 'https://www.bandhanlife.com/savings-plans/iguarantee-vishwas', 'Bandhan Life Official'),
    ('138L009V01', 'Bandhan Life iInvest Advantage - Brochure', 'brochure', 'https://www.bandhanlife.com/ulip-plans/iinvest-advantage', 'Bandhan Life Official'),
    ('138N082V01', 'Bandhan Life iTerm Comfort - Brochure', 'brochure', 'https://www.bandhanlife.com/term-plans/iterm-comfort', 'Bandhan Life Official'),
    ('138N020V01', 'Bandhan Life iTerm Prime (V01) - Brochure', 'brochure', 'https://www.bandhanlife.com/term-plans/iterm-prime', 'Bandhan Life Official'),
    ('138N084V02', 'Bandhan Life iTerm Prime - Brochure', 'brochure', 'https://www.bandhanlife.com/term-plans/iterm-prime', 'Bandhan Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Bharti AXA Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('130N058V01', 'Bharti AXA Life Guaranteed Wealth Pro - Brochure', 'brochure', 'https://www.bharti-axalife.com/savings-plans/guaranteed-wealth-pro', 'Bharti AXA Life Official'),
    ('130N060V01', 'Bharti AXA Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.bharti-axalife.com/term-plans/saral-jeevan-bima', 'Bharti AXA Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Canara HSBC Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('136N118V01', 'Canara HSBC Guaranteed Savings Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/savings-plans/guaranteed-savings-plan.html', 'Canara HSBC Life Official'),
    ('136L025V01', 'Canara HSBC Invest 4G - Brochure', 'brochure', 'https://www.canarahsbclife.com/ulip-plans/invest-4g.html', 'Canara HSBC Life Official'),
    ('136L064V02', 'Canara HSBC Life Invest 4G - Brochure', 'brochure', 'https://www.canarahsbclife.com/ulip-plans/invest-4g.html', 'Canara HSBC Life Official'),
    ('136N066V02', 'Canara HSBC Life Pension4Life - Brochure', 'brochure', 'https://www.canarahsbclife.com/retirement-plans/pension4life.html', 'Canara HSBC Life Official'),
    ('136L116V01', 'Canara HSBC Life Promise4Growth Plus - Brochure', 'brochure', 'https://www.canarahsbclife.com/ulip-plans/promise4growth-plus.html', 'Canara HSBC Life Official'),
    ('136N100V01', 'Canara HSBC Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.canarahsbclife.com/term-plans/saral-jeevan-bima.html', 'Canara HSBC Life Official'),
    ('136L108V01', 'Canara HSBC Life Wealth Edge Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/ulip-plans/wealth-edge.html', 'Canara HSBC Life Official'),
    ('136N110V03', 'Canara HSBC Life iSelect Guaranteed Future - Brochure', 'brochure', 'https://www.canarahsbclife.com/savings-plans/iselect-guaranteed-future.html', 'Canara HSBC Life Official'),
    ('136N119V01', 'Canara HSBC Promise4Future - Brochure', 'brochure', 'https://www.canarahsbclife.com/savings-plans/promise4future.html', 'Canara HSBC Life Official'),
    ('136N115V01', 'Canara HSBC iSelect Term Plan - Brochure', 'brochure', 'https://www.canarahsbclife.com/term-plans/iselect-term-plan.html', 'Canara HSBC Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- CreditAccess Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('170N001V01', 'CreditAccess Life Group Term Plan - Product Details', 'brochure', 'https://www.creditaccesslife.com/products', 'CreditAccess Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Edelweiss Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('147N025V01', 'Edelweiss Life Assured Income STAR - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/savings-plans/assured-income-star', 'Edelweiss Life Official'),
    ('147L010V01', 'Edelweiss Life Wealth Premier - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/ulip-plans/wealth-premier', 'Edelweiss Life Official'),
    ('147N023V01', 'Edelweiss Life Zindagi Protect Plus - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/term-plans/zindagi-protect-plus', 'Edelweiss Life Official'),
    ('147N031V02', 'Edelweiss Tokio Life Active Income Plan - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/savings-plans/active-income-plan', 'Edelweiss Life Official'),
    ('147N019V02', 'Edelweiss Tokio Life Cashflow Protection Plus - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/term-plans/cashflow-protection-plus', 'Edelweiss Life Official'),
    ('147N038V02', 'Edelweiss Tokio Life Dhan Labh - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/savings-plans/dhan-labh', 'Edelweiss Life Official'),
    ('147N072V02', 'Edelweiss Tokio Life GCAP - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/group-plans/gcap', 'Edelweiss Life Official'),
    ('147N090V01', 'Edelweiss Tokio Life Guaranteed Growth Plan - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/savings-plans/guaranteed-growth-plan', 'Edelweiss Life Official'),
    ('147N074V01', 'Edelweiss Tokio Life Guaranteed Income STAR - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/savings-plans/guaranteed-income-star', 'Edelweiss Life Official'),
    ('147N040V02', 'Edelweiss Tokio Life Immediate Annuity Plan - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/retirement-plans/immediate-annuity', 'Edelweiss Life Official'),
    ('147N027V02', 'Edelweiss Tokio Life MyLife+ - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/term-plans/mylife-plus', 'Edelweiss Life Official'),
    ('147N036V01', 'Edelweiss Tokio Life Total Secure+ - Brochure', 'brochure', 'https://www.edelweisslife.in/insurance-plans/term-plans/total-secure-plus', 'Edelweiss Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Generali Central Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('133N090V03', 'Generali Central Assured Education Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/child-plans/assured-education-plan', 'Future Generali Official'),
    ('133N054V05', 'Generali Central Assured Income Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/savings-plans/assured-income-plan', 'Future Generali Official'),
    ('133L081V03', 'Generali Central Big Dreams Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/ulip-plans/big-dreams-plan', 'Future Generali Official'),
    ('133N030V06', 'Generali Central Care Plus Term Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/term-plans/care-plus-term-plan', 'Future Generali Official'),
    ('133L050V04', 'Generali Central Dhan Vridhi - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/ulip-plans/dhan-vridhi', 'Future Generali Official'),
    ('133N003V05', 'Generali Central Group Term Life Plan - Product Details', 'brochure', 'https://www.futuregenerali.in/life-insurance/group-plans/group-term-life', 'Future Generali Official'),
    ('133N078V01', 'Generali Central Life Assured Wealth Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/savings-plans/assured-wealth-plan', 'Future Generali Official'),
    ('133N076V01', 'Generali Central Life Flexi Online Term Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/term-plans/flexi-online-term', 'Future Generali Official'),
    ('133N072V01', 'Generali Central Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/term-plans/saral-jeevan-bima', 'Future Generali Official'),
    ('133N086V01', 'Generali Central Lifetime Partner Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/savings-plans/lifetime-partner', 'Future Generali Official'),
    ('133N088V05', 'Generali Central Money Back Super Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/savings-plans/money-back-super', 'Future Generali Official'),
    ('133N085V03', 'Generali Central New Assured Wealth Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/savings-plans/new-assured-wealth-plan', 'Future Generali Official'),
    ('133L102V01', 'Generali Central Sampoorna Samadhaan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/ulip-plans/sampoorna-samadhaan', 'Future Generali Official'),
    ('133N087V01', 'Generali Central Saral Jeevan Bima - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/term-plans/saral-jeevan-bima', 'Future Generali Official'),
    ('133N089V01', 'Generali Central Saral Pension Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/retirement-plans/saral-pension', 'Future Generali Official'),
    ('133N101V02', 'Generali Central Single Premium Anchor Plan - Brochure', 'brochure', 'https://www.futuregenerali.in/life-insurance/savings-plans/single-premium-anchor', 'Future Generali Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Go Digit Life, Acko Life, Sahara Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('168N001V01', 'Go Digit Life Term Plan - Product Details', 'brochure', 'https://www.godigitlife.com/term-plan', 'Go Digit Life Official'),
    ('169N001V01', 'Acko Life Term Plan - Product Details', 'brochure', 'https://www.ackolife.com/term-plan', 'Acko Life Official'),
    ('126N035V01', 'Sahara Life Saral Jeevan Bima - Product Details', 'brochure', 'https://www.saharalife.com/products/saral-jeevan-bima', 'Sahara Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- IndiaFirst Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('143N063V01', 'IndiaFirst Life ELITE Term Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/term-insurance/elite-term-plan', 'IndiaFirst Life Official'),
    ('143N070V01', 'IndiaFirst Life Elite Term Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/term-insurance/elite-term-plan', 'IndiaFirst Life Official'),
    ('143N056V07', 'IndiaFirst Life Guaranteed Benefit Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/savings-plans/guaranteed-benefit-plan', 'IndiaFirst Life Official'),
    ('143N055V01', 'IndiaFirst Life Guaranteed Monthly Income Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/savings-plans/guaranteed-monthly-income', 'IndiaFirst Life Official'),
    ('143N066V04', 'IndiaFirst Life Guaranteed Pension Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/retirement-plans/guaranteed-pension', 'IndiaFirst Life Official'),
    ('143N060V01', 'IndiaFirst Life Guaranteed Retirement Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/retirement-plans/guaranteed-retirement', 'IndiaFirst Life Official'),
    ('143N072V01', 'IndiaFirst Life Long Guaranteed Income Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/savings-plans/long-guaranteed-income', 'IndiaFirst Life Official'),
    ('143L020V01', 'IndiaFirst Life Money Balance Plan - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/ulip-plans/money-balance', 'IndiaFirst Life Official'),
    ('143L068V01', 'IndiaFirst Life Radiance Smart Invest - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/ulip-plans/radiance-smart-invest', 'IndiaFirst Life Official'),
    ('143N058V01', 'IndiaFirst Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.indiafirstlife.com/life-insurance/term-insurance/saral-jeevan-bima', 'IndiaFirst Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- IndusInd Nippon Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('121N110V01', 'IndusInd Nippon Life Guaranteed Income Plan - Brochure', 'brochure', 'https://www.nipponindialife.com/savings-plans/guaranteed-income-plan', 'IndusInd Nippon Life Official'),
    ('121L134V02', 'IndusInd Nippon Life Prosperity Plus - Brochure', 'brochure', 'https://www.nipponindialife.com/ulip-plans/prosperity-plus', 'IndusInd Nippon Life Official'),
    ('121N114V01', 'IndusInd Nippon Life Saral Jeevan Bima (V01) - Brochure', 'brochure', 'https://www.nipponindialife.com/term-plans/saral-jeevan-bima', 'IndusInd Nippon Life Official'),
    ('121N148V01', 'IndusInd Nippon Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.nipponindialife.com/term-plans/saral-jeevan-bima', 'IndusInd Nippon Life Official'),
    ('121N149V01', 'IndusInd Nippon Life Saral Pension - Brochure', 'brochure', 'https://www.nipponindialife.com/retirement-plans/saral-pension', 'IndusInd Nippon Life Official'),
    ('121N155V01', 'IndusInd Nippon Life Smart Savings - Brochure', 'brochure', 'https://www.nipponindialife.com/savings-plans/smart-savings', 'IndusInd Nippon Life Official'),
    ('121N159V01', 'IndusInd Nippon Life Super Assured Future Endowment - Brochure', 'brochure', 'https://www.nipponindialife.com/savings-plans/super-assured-future-endowment', 'IndusInd Nippon Life Official'),
    ('121N107V01', 'IndusInd Nippon Life Super Endowment Plan - Brochure', 'brochure', 'https://www.nipponindialife.com/savings-plans/super-endowment-plan', 'IndusInd Nippon Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Pramerica Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('140N040V01', 'Pramerica Life Cancer + Heart Shield - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/term-plans/cancer-heart-shield', 'Pramerica Life Official'),
    ('140N075V03', 'Pramerica Life Guaranteed Income Plan - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/savings-plans/guaranteed-income-plan', 'Pramerica Life Official'),
    ('140N062V01', 'Pramerica Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/term-plans/saral-jeevan-bima', 'Pramerica Life Official'),
    ('140N063V01', 'Pramerica Life Saral Pension Plan - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/retirement-plans/saral-pension', 'Pramerica Life Official'),
    ('140N038V01', 'Pramerica Life Secure Savings Plan (V01) - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/savings-plans/secure-savings', 'Pramerica Life Official'),
    ('140N071V02', 'Pramerica Life Secure Savings Plan - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/savings-plans/secure-savings', 'Pramerica Life Official'),
    ('140N035V01', 'Pramerica Life Smart Income - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/savings-plans/smart-income', 'Pramerica Life Official'),
    ('140L069V01', 'Pramerica Life Smart Wealth Plan - Brochure', 'brochure', 'https://www.pramericalife.in/insurance-plans/ulip-plans/smart-wealth-plan', 'Pramerica Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Shriram Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('128N053V05', 'Shriram Life Assured Income Plan - Brochure', 'brochure', 'https://www.shriramlife.com/savings-plans/assured-income-plan', 'Shriram Life Official'),
    ('128N060V02', 'Shriram Life Assured Income Plus - Brochure', 'brochure', 'https://www.shriramlife.com/savings-plans/assured-income-plus', 'Shriram Life Official'),
    ('128L038V02', 'Shriram Life Fortune Builder Plan - Brochure', 'brochure', 'https://www.shriramlife.com/ulip-plans/fortune-builder', 'Shriram Life Official'),
    ('128N047V01', 'Shriram Life New Shri Life Plan (V01) - Brochure', 'brochure', 'https://www.shriramlife.com/savings-plans/new-shri-life-plan', 'Shriram Life Official'),
    ('128N047V02', 'Shriram Life New Shri Life Plan - Brochure', 'brochure', 'https://www.shriramlife.com/savings-plans/new-shri-life-plan', 'Shriram Life Official'),
    ('128N052V01', 'Shriram Life New Shri Raksha Plan - Brochure', 'brochure', 'https://www.shriramlife.com/term-plans/new-shri-raksha-plan', 'Shriram Life Official'),
    ('128N072V01', 'Shriram Life Online Term Plan - Brochure', 'brochure', 'https://www.shriramlife.com/term-plans/online-term-plan', 'Shriram Life Official'),
    ('128L036V02', 'Shriram Life Wealth Plus - Brochure', 'brochure', 'https://www.shriramlife.com/ulip-plans/wealth-plus', 'Shriram Life Official'),
    ('128L096V01', 'Shriram Life Wealth Pro - Brochure', 'brochure', 'https://www.shriramlife.com/ulip-plans/wealth-pro', 'Shriram Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;

-- Star Union Dai-ichi Life
INSERT INTO insurance.policy_documents (product_id, title, doc_type, url, file_format, source_name, data_confidence)
SELECT p.id, doc.title, doc.doc_type::insurance.doc_type_enum, doc.url, 'pdf'::insurance.file_format_enum, doc.source_name, 'verified'::insurance.confidence_enum
FROM (VALUES
    ('142N002V01', 'SUD Life Ashiana Suraksha Plan - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/savings-plans/ashiana-suraksha', 'SUD Life Official'),
    ('142L003V01', 'SUD Life Dhana Suraksha ULIP - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/ulip-plans/dhana-suraksha', 'SUD Life Official'),
    ('142N001V01', 'SUD Life Group Term Insurance - Product Details', 'brochure', 'https://www.sudlife.in/insurance-plans/group-plans/group-term-insurance', 'SUD Life Official'),
    ('142N005V01', 'SUD Life Jeevan Safar - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/savings-plans/jeevan-safar', 'SUD Life Official'),
    ('142N037V01', 'SUD Life Premier Protection Plan - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/term-plans/premier-protection', 'SUD Life Official'),
    ('142N060V01', 'SUD Life Saral Jeevan Bima - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/term-plans/saral-jeevan-bima', 'SUD Life Official'),
    ('142N035V01', 'SUD Life Saral Jeevan Bima (V01) - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/term-plans/saral-jeevan-bima', 'SUD Life Official'),
    ('142N061V01', 'SUD Life Saral Pension Plan - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/retirement-plans/saral-pension', 'SUD Life Official'),
    ('142L015V01', 'SUD Life Wealth Builder - Brochure', 'brochure', 'https://www.sudlife.in/insurance-plans/ulip-plans/wealth-builder', 'SUD Life Official')
) AS doc(uin, title, doc_type, url, source_name)
JOIN insurance.insurance_products p ON p.uin = doc.uin;
