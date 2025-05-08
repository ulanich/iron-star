import requests
from bs4 import BeautifulSoup


def is_registration_open(url, search_string='Регистрация скоро откроется'):
    # Fetch the webpage
    response = requests.get(url, verify=False)
    response.raise_for_status()  # Raise exception for HTTP errors

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    res = soup.find_all(
        string=lambda text: search_string.lower() in str(text).lower()
    )
    return not len(res) > 0


# Example usage
if __name__ == "__main__":
    website_url = "https://iron-star.com/event/ironstar-1-8-sirius-sochi-2025/"  # Replace with your target URL
    string_to_find = "Регистрация скоро откроется"  # Replace with your search string

    print(f"Searching for '{string_to_find}' in {website_url}...")
    try:
        result = is_registration_open(website_url, string_to_find)
    except:
        print('Ошибки соединения с сервером')

    print('Регистрация открыта' if result else 'Регистрация все еще недоступна')
