#!/bin/bash

fetch_court_data() {
    # Get attorney last name from parameter or use default
    local attorney_last_name="${1:-Pesantes}"

    # Get current date in UTC and format it
    local start_date=$(date -u +"%Y-%m-%dT05:00:00.000Z")

    # Calculate end date (1 month from now)
    # Using date command to add 1 month
    local end_date=$(date -u -d "+1 month" +"%Y-%m-%dT05:00:00.000Z")

    echo "Fetching court data for attorney: $attorney_last_name"
    echo "Start date: $start_date"
    echo "End date: $end_date"
    echo "---"

    # Make the curl request
    curl "https://publiccourts.traviscountytx.gov/DSA/api/dockets/settings?criteriaId=attorney&start=${start_date}&end=${end_date}&courtCode=&causeNumber=&defendantLastName=&defendantFirstName=&attorneyLastName=${attorney_last_name}&attorneyFirstName=&Mni=" \
        -H 'Accept: application/json, text/plain, */*' \
        -H 'Accept-Language: en-US,en;q=0.5' \
        -H 'Connection: keep-alive' \
        -H 'Referer: https://publiccourts.traviscountytx.gov/DSA' \
        -H 'Sec-Fetch-Dest: empty' \
        -H 'Sec-Fetch-Mode: cors' \
        -H 'Sec-Fetch-Site: same-origin' \
        -H 'Sec-GPC: 1' \
        -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' \
        -H 'sec-ch-ua: "Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"' \
        -H 'sec-ch-ua-mobile: ?0' \
        -H 'sec-ch-ua-platform: "macOS"'
}

# Call the function with command line argument or default
fetch_court_data "$1"
