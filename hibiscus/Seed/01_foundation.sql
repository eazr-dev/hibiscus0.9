-- ============================================================
-- 01_foundation.sql
-- Consolidated: Insurance categories, sub-categories, and companies
-- Merged from: 01_categories.sql + 02_companies.sql
-- ============================================================

-- ======================== CATEGORIES ========================
-- ============================================================
-- 01_categories.sql - Insurance categories and sub-categories
-- Source: IRDAI (Re-insurance) Regulations 2018, IRDAI Policyholder Portal
-- URLs: https://irdai.gov.in/, https://policyholder.gov.in/
-- ============================================================

SET search_path TO insurance, public;

-- ===================== CATEGORIES =====================

INSERT INTO insurance.insurance_categories (name, description, irdai_segment_code, applicable_to) VALUES
('Life Insurance',       'Insurance covering risks related to human life including death, disability, and survival benefits. Governed by Insurance Act, 1938 and IRDAI Act, 1999.',                NULL, ARRAY['life']::insurance.company_type_enum[]),
('Health Insurance',     'Insurance covering medical and hospitalization expenses. Includes indemnity and fixed-benefit plans. Governed by IRDAI Master Circular on Health Insurance Business.',  'G',  ARRAY['health', 'general', 'life']::insurance.company_type_enum[]),
('Motor Insurance',      'Mandatory insurance under Motor Vehicles Act, 1988. Covers third-party liability (mandatory) and own damage (optional) for vehicles.',                                'F',  ARRAY['general']::insurance.company_type_enum[]),
('Fire Insurance',       'Covers loss or damage to property due to fire and allied perils. Standard Fire & Special Perils Policy (SFSP) is the base form.',                                    'A',  ARRAY['general']::insurance.company_type_enum[]),
('Marine Insurance',     'Covers goods in transit and vessels. Governed by Marine Insurance Act, 1963. Includes cargo, hull, and freight insurance.',                                           NULL, ARRAY['general']::insurance.company_type_enum[]),
('Travel Insurance',     'Covers risks during domestic and international travel including medical emergencies, trip cancellation, and baggage loss.',                                           'G',  ARRAY['general']::insurance.company_type_enum[]),
('Home Insurance',       'Covers residential property structure and contents against fire, natural disasters, burglary, and allied perils. Includes IRDAI standard product Bharat Griha Raksha.', 'A', ARRAY['general']::insurance.company_type_enum[]),
('Liability Insurance',  'Covers legal liability arising from third-party bodily injury or property damage. Includes Public Liability (mandatory for hazardous industries under PL Act, 1991).', 'K', ARRAY['general']::insurance.company_type_enum[]),
('Engineering Insurance','Covers risks during construction, erection, and operation of machinery and industrial equipment.',                                                                     'D',  ARRAY['general']::insurance.company_type_enum[]),
('Crop Insurance',       'Agricultural insurance covering crop yield losses, weather-based risks, and livestock. Includes PMFBY and RWBCIS government schemes.',                                 'H',  ARRAY['general', 'specialized']::insurance.company_type_enum[]),
('Personal Accident',    'Covers accidental death, permanent total/partial disability. Can be standalone or rider. Regulated under IRDAI PA guidelines.',                                       'G',  ARRAY['general', 'life']::insurance.company_type_enum[]),
('Miscellaneous',        'Includes surety bonds, credit insurance, cyber insurance, fidelity guarantee, and other specialty lines not covered in main categories.',                              NULL, ARRAY['general']::insurance.company_type_enum[]);

-- ===================== SUB-CATEGORIES =====================

-- Life Insurance sub-categories (category_id = 1)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(1, 'Term Life Insurance',         'Pure risk cover with death benefit only, no maturity payout. Most affordable life insurance.'),
(1, 'Term with Return of Premium', 'Term insurance that returns all premiums paid if insured survives the policy term.'),
(1, 'Endowment Plans',             'Savings + protection. Pays maturity benefit on survival or death benefit on death during term.'),
(1, 'Money-Back Plans',            'Periodic survival benefits (e.g., 15-25% of sum assured) paid at intervals during the policy term.'),
(1, 'Whole Life Insurance',        'Coverage for entire lifetime (usually up to age 99/100) with participating bonuses.'),
(1, 'ULIP - Unit Linked Plans',    'Market-linked investment + insurance. 5-year IRDAI-mandated lock-in. Equity/debt/balanced fund options.'),
(1, 'Child Plans',                 'Insurance plans for children education and milestones. Feature: premium waiver on parent death.'),
(1, 'Pension / Annuity Plans',     'Retirement income plans including immediate annuity, deferred annuity, and NPS-linked products.'),
(1, 'Group Term Life',             'Employer-provided life cover for employees. Lower premiums due to group pooling.'),
(1, 'Micro Insurance (Life)',      'Low-premium plans for economically weaker sections. Sum insured Rs. 30,000 to Rs. 50,000.'),
(1, 'Savings Plans',               'Traditional savings-oriented life insurance with guaranteed and bonus returns.');

-- Health Insurance sub-categories (category_id = 2)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(2, 'Individual Health Insurance',      'Covers a single individual for hospitalization, pre/post-hospitalization, day-care procedures.'),
(2, 'Family Floater Health Insurance',  'Single policy covering entire family with shared sum insured.'),
(2, 'Critical Illness Insurance',       'Lump-sum payout on diagnosis of specified critical diseases (cancer, heart attack, stroke, etc.).'),
(2, 'Senior Citizen Health Insurance',  'Designed for individuals aged 60/65+. Covers age-related ailments with higher premiums.'),
(2, 'Group Health Insurance',           'Employer-provided health coverage for employees and dependents.'),
(2, 'Top-Up / Super Top-Up',           'Supplements primary health insurance. Activates after a deductible threshold.'),
(2, 'Hospital Daily Cash',             'Fixed daily payout during hospitalization for incidental expenses.'),
(2, 'Arogya Sanjeevani (Standard)',     'IRDAI-mandated standard health product offered by all insurers. Standardized benefits and coverage.'),
(2, 'Disease-Specific Insurance',       'Covers treatment for specific diseases like cancer, diabetes, heart disease.'),
(2, 'Maternity Insurance',             'Covers prenatal, delivery, and postnatal expenses. Typically 2-year waiting period.'),
(2, 'Personal Accident (Health)',       'Covers accidental death and disability. Available as standalone or rider.');

-- Motor Insurance sub-categories (category_id = 3)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(3, 'Private Car - Comprehensive',     'Own Damage + Third-Party Liability for private cars. Covers accident, theft, fire, natural disasters.'),
(3, 'Private Car - Third Party Only',  'Mandatory third-party liability cover for private cars under Motor Vehicles Act, 1988.'),
(3, 'Two-Wheeler - Comprehensive',     'Own Damage + Third-Party for motorcycles and scooters. 5-year TP mandatory for new vehicles.'),
(3, 'Two-Wheeler - Third Party Only',  'Mandatory third-party liability cover for two-wheelers.'),
(3, 'Commercial Vehicle Insurance',    'Coverage for trucks, buses, taxis, auto-rickshaws. Includes HCV, LCV, passenger/goods carrying.'),
(3, 'Standalone Own Damage',           'Covers only damage/loss to the insured vehicle. Available separately since detariffing.'),
(3, 'Motor Add-Ons / Riders',          'Zero depreciation, engine protection, roadside assistance, NCB protection, return to invoice, etc.');

-- Fire Insurance sub-categories (category_id = 4)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(4, 'Standard Fire & Special Perils',  'Standard policy covering fire, lightning, explosion, storm, cyclone, flood, earthquake, riot, strike.'),
(4, 'Industrial All Risk (IAR)',       'Comprehensive coverage for large industrial properties with sum insured > Rs. 50 crores.'),
(4, 'Business Interruption',           'Covers loss of profits due to interruption of business from insured perils.'),
(4, 'Burglary Insurance',              'Covers theft/burglary involving forcible entry. Covers contents, stock, cash in safe.');

-- Marine Insurance sub-categories (category_id = 5)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(5, 'Marine Cargo',       'Covers goods in transit by sea, air, road, rail. Includes single transit, open, and turnover policies.'),
(5, 'Marine Hull',         'Covers physical damage to ships/vessels, engines, machinery. Risks: collision, grounding, fire, piracy.'),
(5, 'Inland Transit',      'Goods transported within India. ITC-A (All Risk) and ITC-B (Basic Risk) coverage.'),
(5, 'Marine Liability',    'Protection & Indemnity for shipowners. Covers cargo damage liability, crew injury, pollution.');

-- Travel Insurance sub-categories (category_id = 6)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(6, 'Domestic Travel Insurance',           'Covers medical emergencies, trip cancellation, baggage loss within India. Includes Bharat Yatra Suraksha standard product.'),
(6, 'International Travel Insurance',      'Overseas medical emergencies, evacuation, trip cancellation, lost baggage, passport loss.'),
(6, 'Student Travel Insurance',            'Long-validity (up to 3 years) for study abroad. Covers study interruption and tuition fees.'),
(6, 'Corporate / Multi-Trip Travel',       'Covers multiple journeys in a policy year for frequent business travellers.');

-- Home Insurance sub-categories (category_id = 7)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(7, 'Bharat Griha Raksha (Standard)',  'IRDAI-mandated standard home insurance product (April 2021). Covers structure and contents.'),
(7, 'Home Structure Insurance',        'Covers building walls, roof, foundation, permanent fixtures against fire and allied perils.'),
(7, 'Home Contents Insurance',         'Covers furniture, appliances, electronics, valuables inside the home.'),
(7, 'Householder Package Policy',      'Comprehensive: structure + contents + burglary + PA + liability.');

-- Liability Insurance sub-categories (category_id = 8)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(8, 'Public Liability Insurance',          'Mandatory for hazardous industries under Public Liability Insurance Act, 1991.'),
(8, 'Product Liability Insurance',         'Liability for defective products causing harm to consumers.'),
(8, 'Professional Indemnity / E&O',        'For doctors, lawyers, architects, engineers, consultants. IRDAI-approved policy wordings.'),
(8, 'Directors & Officers Liability',      'Covers D&O against securities fraud, mismanagement, non-compliance claims.'),
(8, 'Cyber Liability Insurance',           'Data breaches, cyberattacks, extortion. First-party + third-party coverage.'),
(8, 'Workmen Compensation',               'Employee injury/death during employment. Governed by Workmen Compensation Act, 1923.'),
(8, 'Commercial General Liability (CGL)',  'Broad coverage for business premises and operations liability.');

-- Engineering Insurance sub-categories (category_id = 9)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(9, 'Contractor All Risk (CAR)',           'Civil construction projects (roads, buildings, bridges). Material damage + third-party liability.'),
(9, 'Erection All Risk (EAR)',             'Mechanical/electrical installation projects (power plants, turbines).'),
(9, 'Machinery Breakdown',                'Sudden/unforeseen damage to operational machinery. Internal defects, overheating, electrical damage.'),
(9, 'Electronic Equipment Insurance',      'Computers, UPS, medical equipment. Repair/replacement costs.'),
(9, 'Boiler & Pressure Plant',            'Explosion, collapse of boilers and pressure vessels. Extends to third-party coverage.');

-- Crop Insurance sub-categories (category_id = 10)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(10, 'PMFBY - Crop Insurance',            'Pradhan Mantri Fasal Bima Yojana. Yield-based comprehensive crop insurance. Premium: 2% Kharif, 1.5% Rabi.'),
(10, 'Weather-Based Crop Insurance',       'Index-based using weather parameters as proxy for yield. Restructured WBCIS.'),
(10, 'Livestock Insurance',                'Covers death of cattle, buffalo, goats, sheep, poultry.');

-- Personal Accident sub-categories (category_id = 11)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(11, 'Individual Personal Accident',       'Covers accidental death and disability for individuals. Available as standalone policy.'),
(11, 'Group Personal Accident',            'Employer-sponsored PA cover for groups of employees.'),
(11, 'PMSBY',                              'Pradhan Mantri Suraksha Bima Yojana. Rs. 2 lakh accidental death/disability cover at Rs. 20/year.');

-- Miscellaneous sub-categories (category_id = 12)
INSERT INTO insurance.insurance_sub_categories (category_id, name, description) VALUES
(12, 'Surety Bond Insurance',     'Alternative to bank guarantees for infrastructure projects. IRDAI Guidelines 2022. Bid, performance, advance payment bonds.'),
(12, 'Credit Insurance',          'Protects against buyer default on trade receivables.'),
(12, 'Cyber Insurance (Retail)',   'Individual/retail cyber fraud protection. IRDAI-approved retail policy wordings.'),
(12, 'Fidelity Guarantee',        'Covers employer losses from employee fraud/dishonesty (embezzlement, forgery).'),
(12, 'SME Package Insurance',     'Combined fire, burglary, money, liability, PA coverage for small businesses.'),
(12, 'Shopkeeper Insurance',      'Bharat Sookshma Udyam Suraksha and Laghu Udyam Suraksha standard IRDAI products for micro/small enterprises.');

-- ======================== COMPANIES =========================
-- ============================================================
-- 02_companies.sql - All IRDAI-registered insurance companies
-- Source: https://irdai.gov.in/list-of-life-insurers1
--         https://irdai.gov.in/list-of-general-insurers
--         https://irdai.gov.in/list-of-health-insurers
-- Last verified: 2026-02-20 (IRDAI page updated 2026-01-28)
-- ============================================================

SET search_path TO insurance, public;

-- ===================== LIFE INSURANCE COMPANIES (26) =====================

INSERT INTO insurance.insurance_companies (legal_name, short_name, registration_number, company_type, sector, ceo_name, website, irdai_page_url, headquarters, established_year, data_confidence) VALUES
('Life Insurance Corporation of India',                  'LIC',              '512', 'life', 'public',  'R. Doraiswamy',                    'https://licindia.in',                     'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       1956, 'verified'),
('HDFC Life Insurance Company Limited',                  'HDFC Life',        '101', 'life', 'private', 'Vibha Padalkar',                   'https://www.hdfclife.com',                'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2000, 'verified'),
('ICICI Prudential Life Insurance Company Limited',      'ICICI Pru Life',   '105', 'life', 'private', 'Anup Bagchi',                      'https://www.iciciprulife.com',            'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2000, 'verified'),
('SBI Life Insurance Company Limited',                   'SBI Life',         '111', 'life', 'private', 'Amit Jhingran',                    'https://www.sbilife.co.in',               'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2000, 'verified'),
('Axis Max Life Insurance Limited',                      'Max Life',         '104', 'life', 'private', 'Sumit Madan',                      'https://www.axismaxlife.com',             'https://irdai.gov.in/list-of-life-insurers1', 'New Delhi',    2000, 'verified'),
('Kotak Mahindra Life Insurance Company Limited',        'Kotak Life',       '107', 'life', 'private', 'Mahesh Balasubramanian',           'https://www.kotaklife.com',               'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2001, 'verified'),
('Aditya Birla Sun Life Insurance Company Limited',      'ABSLI',            '109', 'life', 'private', 'Kamlesh Rao',                      'https://www.adityabirlacapital.com',      'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2000, 'verified'),
('TATA AIA Life Insurance Company Limited',              'TATA AIA',         '110', 'life', 'private', 'Venkatachalam Iyer',               'https://www.tataaia.com',                 'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2000, 'verified'),
('Bajaj Life Insurance Limited',                         'Bajaj Life',       '116', 'life', 'private', 'Tarun Chugh',                      'https://www.bajajlifeinsurance.com',       'https://irdai.gov.in/list-of-life-insurers1', 'Pune',         2001, 'verified'),
('PNB MetLife India Insurance Company Limited',          'PNB MetLife',      '117', 'life', 'private', 'Sameer Bansal',                    'https://www.pnbmetlife.com',              'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2001, 'verified'),
('IndusInd Nippon Life Insurance Company Limited',       'IndusInd Nippon',  '121', 'life', 'private', 'Ashish Vohra',                     'https://www.indusindnipponlife.com',      'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2001, 'verified'),
('Aviva Life Insurance Company India Limited',           'Aviva Life',       '122', 'life', 'private', 'Asit Rath',                        'https://www.avivaindia.com',              'https://irdai.gov.in/list-of-life-insurers1', 'Gurugram',     2002, 'verified'),
('Sahara India Life Insurance Company Limited',          'Sahara Life',      '127', 'life', 'private', 'A K Dasgupta',                     'https://www.saharalife.com',              'https://irdai.gov.in/list-of-life-insurers1', 'Lucknow',      2004, 'verified'),
('Shriram Life Insurance Company Limited',               'Shriram Life',     '128', 'life', 'private', 'Casparus J H Kromhout',            'https://www.shriramlife.com',             'https://irdai.gov.in/list-of-life-insurers1', 'Hyderabad',    2005, 'verified'),
('Bharti AXA Life Insurance Company Limited',            'Bharti AXA Life',  '130', 'life', 'private', 'Parag Raja',                       'https://www.bharti-axalife.com',          'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2006, 'verified'),
('Generali Central Life Insurance Company Limited',      'Generali Life',    '133', 'life', 'private', 'Alok Rungta',                      'https://www.generalicentrallife.com',     'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2007, 'verified'),
('Ageas Federal Life Insurance Company Limited',         'Ageas Federal',    '135', 'life', 'private', 'Jude Pijush Gomes',                'https://www.ageasfederal.com',            'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2007, 'verified'),
('Canara HSBC Life Insurance Company Limited',           'Canara HSBC',      '136', 'life', 'private', 'Anuj Mathur',                      'https://www.canarahsbclife.com',          'https://irdai.gov.in/list-of-life-insurers1', 'Gurugram',     2008, 'verified'),
('Bandhan Life Insurance Limited',                       'Bandhan Life',     '138', 'life', 'private', 'Satishwar Balakrishnan',            'https://www.bandhanlife.com',             'https://irdai.gov.in/list-of-life-insurers1', 'Kolkata',      2008, 'verified'),
('Pramerica Life Insurance Company Limited',             'Pramerica Life',   '140', 'life', 'private', 'Pankaj Gupta',                     'https://www.pramericalife.in',            'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2008, 'verified'),
('Star Union Dai-Ichi Life Insurance Company Limited',   'SUD Life',         '142', 'life', 'private', 'Abhay Tewari',                     'https://www.sudlife.in',                  'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2009, 'verified'),
('IndiaFirst Life Insurance Company Limited',            'IndiaFirst Life',  '143', 'life', 'private', 'Rushabh Gandhi',                   'https://www.indiafirstlife.com',          'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2009, 'verified'),
('Edelweiss Life Insurance Company Limited',             'Edelweiss Life',   '147', 'life', 'private', 'Sumit Rai',                        'https://www.edelweisslife.in',            'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2011, 'verified'),
('CreditAccess Life Insurance Limited',                  'CreditAccess Life','163', 'life', 'private', 'Diwakar Ram Boddupolli',           'https://www.creditaccesslife.in',         'https://irdai.gov.in/list-of-life-insurers1', 'Bengaluru',    2023, 'verified'),
('Acko Life Insurance Limited',                          'Acko Life',        '164', 'life', 'private', NULL,                               'https://www.acko.com/life-insurance',     'https://irdai.gov.in/list-of-life-insurers1', 'Mumbai',       2024, 'verified'),
('Go Digit Life Insurance Limited',                      'Digit Life',       '165', 'life', 'private', 'Sabyasachi Sarkar',                'https://www.godigit.com/life',            'https://irdai.gov.in/list-of-life-insurers1', 'Bengaluru',    2024, 'verified');

-- ===================== GENERAL INSURANCE COMPANIES (27) =====================

INSERT INTO insurance.insurance_companies (legal_name, short_name, registration_number, company_type, sector, ceo_name, website, irdai_page_url, headquarters, established_year, data_confidence) VALUES
('The New India Assurance Company Limited',              'New India',        '190', 'general', 'public',  'Girija Subramanian',              'https://www.newindia.co.in',              'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       1919, 'verified'),
('National Insurance Company Limited',                   'National Ins',     '170', 'general', 'public',  'Rajeshwari Singh Muni',           'https://www.nationalinsurance.nic.co.in', 'https://irdai.gov.in/list-of-general-insurers', 'Kolkata',      1906, 'verified'),
('The Oriental Insurance Company Limited',               'Oriental Ins',     '180', 'general', 'public',  'Sanjay Joshi',                    'https://www.orientalinsurance.org.in',    'https://irdai.gov.in/list-of-general-insurers', 'New Delhi',    1947, 'verified'),
('United India Insurance Company Limited',               'United India',     '160', 'general', 'public',  'Bhupesh Sushil Rahul',            'https://www.uiic.co.in',                 'https://irdai.gov.in/list-of-general-insurers', 'Chennai',      1938, 'verified'),
('ICICI Lombard General Insurance Company Limited',      'ICICI Lombard',    '115', 'general', 'private', 'Sanjeev Mantri',                  'https://www.icicilombard.com',            'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2001, 'verified'),
('HDFC ERGO General Insurance Company Limited',          'HDFC ERGO',        '146', 'general', 'private', 'Anuj Tyagi',                      'https://www.hdfcergo.com',                'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2002, 'verified'),
('Bajaj General Insurance Limited',                      'Bajaj Allianz GI', '113', 'general', 'private', 'Tapan Singhel',                   'https://www.bajajallianz.com',            'https://irdai.gov.in/list-of-general-insurers', 'Pune',         2001, 'verified'),
('Tata AIG General Insurance Company Limited',           'Tata AIG',         '108', 'general', 'private', 'Amit S. Ganorkar',                'https://www.tataaig.com',                 'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2001, 'verified'),
('Cholamandalam MS General Insurance Company Limited',   'Chola MS',         '123', 'general', 'private', 'Venkateswaran Suryanarayanan',    'https://www.cholainsurance.com',          'https://irdai.gov.in/list-of-general-insurers', 'Chennai',      2001, 'verified'),
('SBI General Insurance Company Limited',                'SBI General',      '144', 'general', 'private', 'Naveen Chandra Jha',              'https://www.sbigeneral.in',               'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2009, 'verified'),
('Go Digit General Insurance Limited',                   'Digit GI',         '158', 'general', 'private', 'Jasleen Kohli',                   'https://www.godigit.com',                 'https://irdai.gov.in/list-of-general-insurers', 'Bengaluru',    2016, 'verified'),
('IFFCO TOKIO General Insurance Company Limited',        'IFFCO Tokio',      '106', 'general', 'private', 'Subrata Mondal',                  'https://www.iffcotokio.co.in',            'https://irdai.gov.in/list-of-general-insurers', 'Gurugram',     2000, 'verified'),
('Royal Sundaram General Insurance Company Limited',     'Royal Sundaram',   '102', 'general', 'private', 'Vedanarayanan',                   'https://www.royalsundaram.in',            'https://irdai.gov.in/list-of-general-insurers', 'Chennai',      2000, 'verified'),
('Zurich Kotak General Insurance Company Limited',       'Zurich Kotak',     '152', 'general', 'private', 'Alok Agarwal',                    'https://www.zurichkotak.com',             'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2015, 'verified'),
('Shriram General Insurance Company Limited',            'Shriram GI',       '137', 'general', 'private', 'Anil Kumar Aggarwal',             'https://www.shriramgi.com',               'https://irdai.gov.in/list-of-general-insurers', 'Jaipur',       2008, 'verified'),
('Universal Sompo General Insurance Company Limited',    'Universal Sompo',  '134', 'general', 'private', 'Sharad Mathur',                   'https://www.universalsompo.com',          'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2007, 'verified'),
('Acko General Insurance Limited',                       'Acko GI',          '157', 'general', 'private', 'Animesh Kumar Das',               'https://www.acko.com',                    'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2016, 'verified'),
('Generali Central Insurance Company Limited',           'Generali GI',      '132', 'general', 'private', 'Anup Rau',                        'https://www.futuregenerali.in',           'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2007, 'verified'),
('IndusInd General Insurance Company Limited',           'IndusInd GI',      '103', 'general', 'private', 'Rakesh Jain',                     'https://www.reliancegeneral.co.in',       'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2000, 'verified'),
('Raheja QBE General Insurance Company Limited',         'Raheja QBE',       '129', 'general', 'private', 'Rajeev Dogra',                    'https://www.rahejaqbe.com',               'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2007, 'verified'),
('Liberty General Insurance Limited',                    'Liberty GI',       '150', 'general', 'private', 'Parag Ved',                       'https://www.libertyinsurance.in',          'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2013, 'verified'),
('Magma General Insurance Limited',                      'Magma GI',         '151', 'general', 'private', 'Rajive Kumaraswami',              'https://www.magma-hdi.co.in',             'https://irdai.gov.in/list-of-general-insurers', 'Kolkata',      2014, 'verified'),
('Navi General Insurance Limited',                       'Navi GI',          '156', 'general', 'private', 'Vaibhav Goyal',                   'https://www.naviinsurance.com',            'https://irdai.gov.in/list-of-general-insurers', 'Bengaluru',    2016, 'verified'),
('Zuno General Insurance Limited',                       'Zuno',             '149', 'general', 'private', 'Shubhdarshini Ghosh',             'https://www.hizuno.com',                  'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       2016, 'verified'),
('Kshema General Insurance Limited',                     'Kshema',           '159', 'general', 'private', 'Rajeshnani Venkata Dasari',       'https://www.kshema.co',                   'https://irdai.gov.in/list-of-general-insurers', 'Hyderabad',    2020, 'verified'),
('Agriculture Insurance Company of India Limited',       'AIC',              '131', 'general', 'specialized', 'Lavanya R. Mundayur',         'https://www.aicofindia.com',              'https://irdai.gov.in/list-of-general-insurers', 'New Delhi',    2002, 'verified'),
('ECGC Limited',                                         'ECGC',             '114', 'general', 'specialized', 'Sristiraj Ambastha',          'https://www.ecgc.in',                     'https://irdai.gov.in/list-of-general-insurers', 'Mumbai',       1957, 'verified');

-- ===================== STANDALONE HEALTH INSURANCE COMPANIES (7) =====================

INSERT INTO insurance.insurance_companies (legal_name, short_name, registration_number, company_type, sector, ceo_name, website, irdai_page_url, headquarters, established_year, data_confidence) VALUES
('Star Health and Allied Insurance Company Limited',     'Star Health',      '129', 'health', 'private', 'Anand Roy',                       'https://www.starhealth.in',               'https://irdai.gov.in/list-of-health-insurers', 'Chennai',      2006, 'verified'),
('Care Health Insurance Limited',                        'Care Health',      '148', 'health', 'private', 'Anuj Gulati',                     'https://www.careinsurance.com',            'https://irdai.gov.in/list-of-health-insurers', 'Gurugram',     2012, 'verified'),
('Niva Bupa Health Insurance Company Limited',           'Niva Bupa',        '145', 'health', 'private', 'Krishnan Ramachandran',            'https://www.nivabupa.com',                'https://irdai.gov.in/list-of-health-insurers', 'New Delhi',    2008, 'verified'),
('Aditya Birla Health Insurance Company Limited',        'AB Health',        '153', 'health', 'private', 'Mayank Bathwal',                   'https://www.adityabirlahealthinsurance.com','https://irdai.gov.in/list-of-health-insurers', 'Mumbai',       2015, 'verified'),
('Manipal Cigna Health Insurance Company Limited',       'Manipal Cigna',    '148', 'health', 'private', NULL,                               'https://www.manipalcigna.com',             'https://irdai.gov.in/list-of-health-insurers', 'Bengaluru',    2013, 'verified'),
('Galaxy Health Insurance Company Limited',              'Galaxy Health',    '161', 'health', 'private', 'G. Srinivasan',                    'https://www.galaxyhealth.com',             'https://irdai.gov.in/list-of-health-insurers', 'Chennai',      2020, 'verified'),
('Narayana Health Insurance Limited',                    'Narayana Health',  '162', 'health', 'private', 'Sheela Ananth',                    'https://www.narayanahealth.insurance',     'https://irdai.gov.in/list-of-health-insurers', 'Bengaluru',    2022, 'verified');
