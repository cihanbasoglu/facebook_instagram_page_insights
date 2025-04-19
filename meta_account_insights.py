import requests
import pandas as pd
import time
from datetime import timedelta, datetime

user_access_token = "your_long_lived_user_access_token"

#get all page ids and page access tokens under your account
base_url = "https://graph.facebook.com/v22.0/me/accounts"
params = {
    "access_token": user_access_token
}

tokens_and_ids = []
next_url = base_url

while next_url:
    response = requests.get(next_url, params=params if next_url == base_url else None)
    print(f"Status: {response.status_code}")
    print(response.text)

    try:
        json_data = response.json()
    except ValueError:
        print("Response content is not valid JSON")
        break

    error = json_data.get("error")
    if error:
        print("Error subcode:", error.get("error_subcode"))
        break

    tokens_and_ids.extend(json_data.get("data", []))
    next_url = json_data.get("paging", {}).get("next")
    params = None

print(f"Fetched {len(tokens_and_ids)} data entries")

tuples = []
for item in tokens_and_ids:
    tuples.append((
        item['access_token'],
        item['id'],
        item['name']
    ))

#get all instagram accounts via connected facebook page ids
all_ids = []
for token, id, name in tuples:
    fb_page_id = id
    url = f"https://graph.facebook.com/v22.0/{fb_page_id}?fields=instagram_business_account&access_token={user_access_token}"
    response = requests.get(url)
    response = response.json()
    instagram_id = response.get("instagram_business_account", {}).get("id")
    fb_id = response["id"]
    all_ids.append(
        (instagram_id, fb_id, token, name)
    )

#get facebook page insights
until = int(time.time())
dt_30_days_ago = datetime.now() - timedelta(days=30)
since = int(dt_30_days_ago.timestamp())

fb_df = pd.DataFrame()

for instagram_id, fb_id, token, name in all_ids:
    fb_page_id = fb_id
    page_token = token

    url = f"https://graph.facebook.com/v22.0/{fb_page_id}/insights?metric=page_daily_follows&period=day&since={since}&until={until}&access_token={page_token}"

    response = requests.get(url)

    records = []
    for entry in json_data["data"]:
        for v in entry.get("values", []):
            records.append({
                "fb_account_name": name,
                "metric_name": entry.get("name"),
                "period": entry.get("period"),
                "title": entry.get("title"),
                "description": entry.get("description"),
                "id": entry.get("id"),
                "value": v.get("value"),
                "end_time": v.get("end_time")
                })

    df = pd.DataFrame(records)
    fb_df = pd.concat([fb_df, df], ignore_index=True)
    print(f"Fetched {len(df)} records for {name}, response status: {response.status_code}")

#get instagram insights
instagram_df = pd.DataFrame()
until = int(time.time())
dt_30_days_ago = datetime.now() - timedelta(days=30)
since = int(dt_30_days_ago.timestamp())
start_date = (datetime.now() - timedelta(days=30))
end_date = datetime.now()

for instagram_id, fb_id, token, name in all_ids:
    if instagram_id:
        instagram_page_id = instagram_id
        page_token = token
    else: continue

    base_url = f"https://graph.facebook.com/v22.0/{instagram_id}/insights"
    params = {
        "metric": "reach,total_interactions,likes,comments,views",
        "metric_type": "total_value",
        "period": "day",
        "breakdown": "media_product_type",
        "since": since,
        "until": until,
        "access_token": page_token
    }

    all_data = []
    next_url = base_url

    while next_url:
        response = requests.get(next_url, params=params if next_url == base_url else None)
        try:
            json_data = response.json()
        except ValueError:
            print("Response content is not valid JSON")
            break

        error = json_data.get("error")
        if error:
            print("Error subcode:", error.get("error_subcode"))
            break

        all_data.extend(json_data.get("data", []))
        next_url = json_data.get("paging", {}).get("next")
        params = None

    records = []

    for item in all_data:
        metric_name = item["name"]
        title = item["title"]
        description = item["description"]
        total_value = item["total_value"].get("value")
        
        for breakdown in item["total_value"].get("breakdowns", []):
            for result in breakdown.get("results", []):
                media_type = result["dimension_values"][0]
                value = result["value"]

                records.append({
                    "instagram_account_name": name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "metric_name": metric_name,
                    "title": title,
                    "description": description,
                    "total_value": total_value,
                    "media_type": media_type,
                    "breakdown_value": value
                })

    df = pd.DataFrame(records)
    instagram_df = pd.concat([instagram_df, df], ignore_index=True)
    print(f"Fetched {len(df)} records for {name}, response status: {response.status_code}")

#get instagram demographics
instagram_demographics_df = pd.DataFrame()

for instagram_id, fb_id, token, name in all_ids:
    if instagram_id:
        instagram_page_id = instagram_id
        page_token = token
    else: continue

    base_url = f"https://graph.facebook.com/v22.0/{instagram_id}/insights"
    params = {
        "metric": "engaged_audience_demographics",
        "period": "lifetime",
        "timeframe": "this_month",
        "metric_type": "total_value",
        "breakdown": "age,gender",
        "access_token": page_token
    }

    all_data = []
    next_url = base_url

    while next_url:
        response = requests.get(next_url, params=params if next_url == base_url else None)

        try:
            json_data = response.json()
        except ValueError:
            print("Response content is not valid JSON")
            break

        error = json_data.get("error")
        if error:
            print("Error subcode:", error.get("error_subcode"))
            break

        all_data.extend(json_data.get("data", []))
        next_url = json_data.get("paging", {}).get("next")
        params = None

    print(f"Fetched {len(all_data)} data entries")

    rows = []

    for data in all_data:
        metric = data["name"]
        title = data["title"]

        for breakdown in data["total_value"].get("breakdowns", []):
            for result in breakdown["results"]:
                age, gender = result["dimension_values"]
                value = result["value"]
                rows.append({
                    "instagram_account_name": name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "metric": metric,
                    "title": title,
                    "age": age,
                    "gender": gender,
                    "value": value
                })

    df = pd.DataFrame(rows)
    instagram_demographics_df = pd.concat([instagram_demographics_df, df], ignore_index=True)
    print(f"Fetched {len(df)} records for {name}, response status: {response.status_code}")
    
fb_df.head()
instagram_df.head()
instagram_demographics_df.head()