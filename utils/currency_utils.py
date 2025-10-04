import requests
from config import Config

def get_all_countries_currencies():
    try:
        response = requests.get(Config.COUNTRIES_API, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        countries_data = []
        for country in data:
            if 'currencies' in country and country['currencies']:
                country_name = country['name']['common']
                for currency_code, currency_data in country['currencies'].items():
                    countries_data.append({
                        'country': country_name,
                        'currency_code': currency_code,
                        'currency_name': currency_data.get('name', currency_code)
                    })
        
        countries_data.sort(key=lambda x: x['country'])
        return countries_data
    except Exception as e:
        print(f"Currency API Error: {e}")
        return []

def convert_currency(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    
    try:
        response = requests.get(f"{Config.CURRENCY_API_BASE}{from_currency}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if to_currency in data['rates']:
            rate = data['rates'][to_currency]
            return round(amount * rate, 2)
        else:
            print(f"Currency conversion failed: {to_currency} not found")
            return amount
    except Exception as e:
        print(f"Currency conversion error: {e}")
        return amount

def get_supported_currencies():
    try:
        response = requests.get(f"{Config.CURRENCY_API_BASE}USD", timeout=10)
        response.raise_for_status()
        data = response.json()
        return sorted(data['rates'].keys())
    except:
        return ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'AUD', 'CAD']
