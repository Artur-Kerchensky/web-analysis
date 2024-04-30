import requests
import datetime
import csv

api_key = 'key'

current_date = datetime.datetime.now().date()

base_url = 'https://api.openweathermap.org/data/2.5/weather?'

weekdays = [current_date + datetime.timedelta(days=x) for x in range(7)]
temp = []
date = []

for weekday in weekdays:
    formatted_date = weekday.strftime('%Y-%m-%d')
    url = f'{base_url}q=Москва&appid={api_key}&units=metric&dt={formatted_date}'

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        temp_day = data['main']['temp']
        temp.append(temp_day)
        date.append(formatted_date)


with open('weather_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Дата', 'Температура'])
    for i in range(len(date)):
        writer.writerow([date[i], temp[i]])
