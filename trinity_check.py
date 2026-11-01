"""Read the normal Trinity booking page; never bypass queues or bot checks."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

TARGET = {"date": "2026-11-08", "origin": "FUK", "destination": "PUS",
          "flight": "TW236", "departure": "20:00", "adults": 1}
URL = "https://www.trinityairways.com/app/main?langCode=en-US&regionCode=KR"


def classify(observation):
    if observation.get("target") != TARGET:
        return "UNKNOWN"
    fares = observation.get("fares", [])
    if {f.get("type") for f in fares} != {"EventFare", "SmartFare", "NormalFare"} or len(fares) != 3:
        return "UNKNOWN"
    if all(f.get("disabled") is True and f.get("sold_out") is True for f in fares):
        return "SOLD_OUT"
    if any(f.get("disabled") is False and f.get("sold_out") is False
           and f.get("positive_price") is True and f.get("selection_verified") is True for f in fares):
        return "AVAILABLE"
    return "UNKNOWN"


def check():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(30000)
            response = page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            if not response or response.status != 200:
                body = page.locator('body').inner_text().lower()
                blocked = any(word in body for word in ('access denied', 'verify you are human', 'automated', 'just a moment', 'security check'))
                code = response.status if response else 0
                raise RuntimeError(f"homepage_http_{code}_security_screen_{blocked}")
            page.wait_for_function("typeof chooseItinerary === 'function'")
            # Populate the site's ordinary search form, then use its own submit
            # handler. Queue, CSRF and session behavior remain entirely intact.
            page.evaluate("""target => {
                const form = document.querySelector('#airAvailabilityRQ');
                const values = {
                    'availabilitySearches[0].depAirport': target.origin,
                    'availabilitySearches[0].arrAirport': target.destination,
                    'availabilitySearches[0].flightDate': target.date,
                    'paxCountDetails[0].paxCount': '1',
                    'paxCountDetails[1].paxCount': '0',
                    'paxCountDetails[2].paxCount': '0'
                };
                for (const [name, value] of Object.entries(values)) form.elements.namedItem(name).value = value;
                form.querySelector('#tripType_OW').checked = true;
            }""", TARGET)
            page.evaluate("chooseItinerary()")
            page.wait_for_url("**/app/booking/chooseItinerary", timeout=45000)
            # The page's own NetFunnel queue loads this result. No direct calls
            # to layerAvailabilityList or queue manipulation are used.
            row = page.locator('li.price_list').filter(has=page.locator('[data-dispflightnumber="TW236"]')).first
            row.wait_for(state="visible", timeout=60000)
            row.locator('a.section_list_box').click()
            info = row.locator('.service_section_box')
            if info.get_attribute('data-routeinfo') != 'FUK/PUS':
                raise RuntimeError('route_mismatch')
            if info.locator('.service_name.first .tit').inner_text().strip() != TARGET['departure']:
                raise RuntimeError('departure_mismatch')
            if 'Direct flight' not in info.inner_text():
                raise RuntimeError('nonstop_not_verified')
            summary = page.locator('#default_summary_flightDate1').inner_text()
            if TARGET['date'] not in summary or 'Adult 1' not in page.locator('body').inner_text():
                raise RuntimeError('search_context_not_verified')
            fares = []
            for radio in row.locator('input.tripInfo').all():
                if any(radio.get_attribute(k) != v for k, v in {
                    'data-date': TARGET['date'], 'data-depairport': 'FUK',
                    'data-arrairport': 'PUS', 'data-flightnumber': '236'}.items()):
                    raise RuntimeError('fare_context_mismatch')
                box = radio.locator('xpath=following-sibling::div[1]')
                price_text = box.locator('.rate_price').inner_text().strip()
                import re
                fare = {'type': radio.get_attribute('data-faretype'),
                        'disabled': not radio.is_enabled(),
                        'sold_out': price_text == 'Sold out',
                        'positive_price': bool(re.search(r'[1-9][0-9,]*', price_text)),
                        'selection_verified': False}
                if not fare['disabled'] and not fare['sold_out'] and fare['positive_price']:
                    # Selecting a fare does not reserve or purchase a ticket.
                    box.locator('label').first.click()
                    selected = page.locator('#default_summary_flightDate1').inner_text()
                    fare['selection_verified'] = radio.is_checked() and TARGET['date'] in selected and TARGET['flight'] in selected
                fares.append(fare)
            observation = {'target': TARGET, 'fares': fares}
            return {'status': classify(observation), **observation}
        finally:
            browser.close()


if __name__ == '__main__':
    try:
        result = check()
    except Exception as exc:
        # Do not log exception messages: browser errors can contain session URLs.
        result = {'status': 'UNKNOWN', 'target': TARGET, 'error_type': type(exc).__name__}
        if type(exc) is RuntimeError:
            result['reason'] = str(exc)
    result['checked_at'] = datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    print(json.dumps(result, ensure_ascii=False))
    with open('result.json', 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    raise SystemExit(2 if result['status'] == 'UNKNOWN' else 0)
