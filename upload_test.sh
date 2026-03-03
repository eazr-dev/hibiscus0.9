#!/bin/bash
# Upload insurance PDFs in batches and save responses
# Usage: bash upload_test.sh

API_URL="http://localhost:8001/api/policy/upload"
DIR=~/Downloads/Insurance
OUT_DIR=~/Downloads/Insurance/responses
mkdir -p "$OUT_DIR"

# Clear old responses
rm -f "$OUT_DIR"/response_*.json 2>/dev/null

# MongoDB cleanup skipped — user handles manually
echo ">>> Skipping MongoDB cleanup (manual)"
echo ""

upload_file() {
    local file="$1"
    local name="$2"
    local gender="$3"
    local dob="$4"
    local num="$5"
    local outfile="$OUT_DIR/response_${num}.json"

    echo ">>> [$num] Uploading: $(basename "$file")"
    curl -s -X POST "$API_URL" \
        --max-time 300 \
        -F "policyDocument=@$file" \
        -F "policyFor=self" \
        -F "name=$name" \
        -F "gender=$gender" \
        -F "dateOfBirth=$dob" \
        -F "relationship=self" \
        -F "uploadedAt=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" \
        -F "userId=282" \
        -o "$outfile" \
        -w "    HTTP %{http_code} | Size: %{size_download} bytes | Time: %{time_total}s\n"
    echo ""
}

echo "============================================"
echo " BATCH 1: Health files 1-5"
echo "============================================"

upload_file "$DIR/anushka mediclaim policy.pdf" "Anushka Rajen Jariwala" "female" "1990-05-15" "01"
upload_file "$DIR/OICL-policy-2025-26.pdf" "Rajen Arvind Jariwala" "male" "1965-08-20" "02"
upload_file "$DIR/policy_84769225_06062025.pdf" "Mukhtar Mehboob Bagwan" "male" "1975-03-10" "03"
upload_file "$DIR/12-8428-0000512271-02_0.pdf" "Jugnu Gosrani" "male" "1980-01-01" "04"
upload_file "$DIR/99387584_20250323.pdf" "Salim Hasanali Bootwala" "male" "1970-06-25" "05"

echo ">>> Waiting 65 seconds for rate limit reset..."
sleep 65

echo ""
echo "============================================"
echo " BATCH 2: Health files 6-11"
echo "============================================"

upload_file "$DIR/30747822202203 2.pdf" "Priyanka Manish Rabhadia" "female" "1988-11-12" "06"
upload_file "$DIR/ASIF POLICY COPY.pdf" "Asif Ali Khan" "male" "1982-04-18" "07"
upload_file "$DIR/Policy-0238864404-04.pdf" "Jugnu Gosrani" "male" "1980-01-01" "08"
upload_file "$DIR/POLICY_DOCUMENTpdf.pdf" "Shailesh Parmar" "male" "1978-09-05" "09"
upload_file "$DIR/test1.pdf" "Rajen Jariwala" "male" "1965-08-20" "10"

echo ">>> Waiting 65 seconds for rate limit reset..."
sleep 65

upload_file "$DIR/test3.pdf" "Nimish Rajkumar Khattar" "male" "1985-07-30" "11"

echo ""
echo "============================================"
echo " BATCH 3: Motor files 12-16"
echo "============================================"

upload_file "$DIR/1811_POLICY_SCHEDULE_MOTOR_NEW_132-02-11-0725-MTP-2010007428.pdf" "Pravin Madanlal Jain" "male" "1970-02-14" "12"
upload_file "$DIR/Farita MH40CH1503 MARUTI SUZ BREZZAZXI policy.pdf" "Farita Minoo Boyce" "female" "1968-12-01" "13"
upload_file "$DIR/VD921436.pdf" "Fahd Bagwan" "male" "1992-08-15" "14"
upload_file "$DIR/document-1.pdf" "Pravin Madanlal Jain" "male" "1970-02-14" "15"

echo ">>> Waiting 65 seconds for rate limit reset..."
sleep 65

upload_file "$DIR/20211008135400_3101523493 1 1.pdf" "Vipinkumar Dhyani" "male" "1975-05-22" "16"

echo ""
echo "============================================"
echo " BATCH 4: Motor files 17-19 + Travel 20-21"
echo "============================================"

upload_file "$DIR/Acko-20251210-b5221787-d650-4386-b6d3-d7b36332fb85.pdf" "Priyanka Manish Rabhadia" "female" "1988-11-12" "17"
upload_file "$DIR/DCOR00832176202_00 2.pdf" "Priyanka Manish Rabhadia" "female" "1988-11-12" "18"
upload_file "$DIR/MH-01-DU-7091.pdf" "Huzefa Hatim Bharmal" "male" "1985-03-25" "19"
upload_file "$DIR/policy_26780965_15012026.pdf" "Farita Minoo Boyce" "female" "1968-12-01" "20"

echo ">>> Waiting 65 seconds for rate limit reset..."
sleep 65

upload_file "$DIR/policy_26781617_15012026.pdf" "Arsis Minoo Boyce" "male" "1995-04-10" "21"

echo ""
echo "============================================"
echo " BATCH 5: Travel file 22"
echo "============================================"

upload_file "$DIR/policy_28397779_11042026.pdf" "Boyce Farita Minoo" "female" "1968-12-01" "22"
upload_file "$DIR/test2.pdf" "Policy Holder" "male" "1990-01-01" "23"

echo ">>> Waiting 65 seconds for rate limit reset..."
sleep 65

echo ""
echo "============================================"
echo " BATCH 6: New policies 24-28"
echo "============================================"

upload_file "$DIR/10251034735465050620251110025795.pdf" "Policy Holder" "male" "1990-01-01" "24"
upload_file "$DIR/26016147_20260103.pdf" "Policy Holder" "male" "1990-01-01" "25"
upload_file "$DIR/KC361141.pdf" "Policy Holder" "male" "1990-01-01" "26"
upload_file "$DIR/policy_original_UPL_291_09ffcdf27470_20260122_080506 1.pdf" "Policy Holder" "male" "1990-01-01" "27"
upload_file "$DIR/pravin_mandal.pdf" "Pravin Mandal" "male" "1985-01-01" "28"

echo ">>> Waiting 65 seconds for rate limit reset..."
sleep 65

echo ""
echo "============================================"
echo " BATCH 7: New policies 29-30"
echo "============================================"

upload_file "$DIR/26073636_20260104 1.pdf" "Policy Holder" "male" "1990-01-01" "29"
upload_file "$DIR/Original_Policy_Documentpdf_1771221081420 1.pdf" "Policy Holder" "male" "1990-01-01" "30"

echo ""
echo "============================================"
echo " ALL UPLOADS COMPLETE (30 files)"
echo "============================================"
echo "Responses saved in: $OUT_DIR/"
ls -la "$OUT_DIR/"
