import asyncio
from playwright.async_api import async_playwright
import json

from parse_salary import parse_salary_field


BASE_URL = "https://nofluffjobs.com"
ALL_CATEGORIES = (
    "artificial-intelligence?criteria=requirement%3DPython%20category%3Dsys-administrator,business-analyst,"
    "architecture,backend,data,ux,devops,erp,embedded,frontend,fullstack,game-dev,mobile,project-manager,"
    "security,support,testing,other")
CONCURRENCY_LIMIT = 10
MAX_LOAD_MORE_CLICKS = 1


async def close_overlay(page):
    try:
        await page.keyboard.press('Escape')
    except:
        pass


async def scroll_and_load_more(page, max_clicks=MAX_LOAD_MORE_CLICKS):
    clicks = 0

    while clicks < max_clicks:
        await close_overlay(page)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)

        try:
            btn = page.locator('button:has-text("Pokaż kolejne oferty")')
            await btn.click()
            clicks += 1
            print(f"Click {clicks}")
            await page.wait_for_timeout(1000)
        except:
            break

    return clicks

async def scrape_list_page(page):
    print("Loading...")

    await page.goto(f"{BASE_URL}/pl/{ALL_CATEGORIES}", wait_until="networkidle")

    main_selector = 'a.posting-list-item'
    await page.wait_for_selector(main_selector)

    await scroll_and_load_more(page)

    await page.wait_for_timeout(1000)
    job_cards = await page.locator(main_selector).all()

    job_offers_on_page = []
    for i, card in enumerate(job_cards):
        try:
            # Title search
            title_elem = card.locator('[data-cy="title position on the job offer listing"]')
            title = await title_elem.text_content() if await title_elem.count() > 0 else f"Vacancy #{i + 1}"

            # Raw salary search
            salary_elem = card.locator('[data-cy="salary ranges on the job offer listing"]')
            if await salary_elem.count() > 0:
                salary_raw = (await salary_elem.first.text_content() or "").strip()
            else:
                salary_raw = ""

            # Normalize raw salary
            salary = parse_salary_field(salary_raw, annual_to_month=True)

            # Finding average salary if exist
            if isinstance(salary, list):
                vals = [v for v in salary if isinstance(v, (int, float))]
                salary_avg = int(sum(vals) / len(vals)) if vals else None
            else:
                salary_avg = None

            # Url search
            relative_url = await card.get_attribute("href")
            if not relative_url:
                continue

            # First data of vacancy
            job_offers_on_page.append({
                "title": ' '.join(title.split()) if title else f"Vacancy #{i + 1}",
                "salary": salary,
                "salary_avg": salary_avg,
                "salary_raw": salary_raw,
                "url": f"{BASE_URL}{relative_url}"
            })
        except Exception as e:
            print(f"Something wet wrong with vacancy - {i + 1}: {e}")

    print(f"Collect {len(job_offers_on_page)} vacancies")
    return job_offers_on_page


async def scrape_detail_task(browser, job_info, semaphore):
    async with semaphore:
        url = job_info["url"]
        job_id = url.split('/')[-1]
        print(f"🚀 Starting scrape: {job_id}")

        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # Company name search
            company_loc = page.locator('#postingCompanyUrl')
            company_name = await company_loc.text_content() if await company_loc.count() > 0 else "Undefined"

            # Category search
            category_loc = page.locator('[data-cy="JobOffer_Category"]')
            category = await category_loc.text_content() if await category_loc.count() > 0 else "Undefined"

            # Seniority search
            seniority_loc = page.locator('#posting-seniority')
            seniority = await seniority_loc.inner_text() if await seniority_loc.count() > 0 else "Undefined"

            # Location search
            location_loc = page.locator('[data-cy="location_remote"]')
            location = await location_loc.text_content() if await location_loc.count() > 0 else "Hybrydowo"

            # Requirements seach
            requirements_locators = page.locator('section[branch="musts"] li')
            requirements = [await loc.text_content() for loc in await requirements_locators.all()]

            # Nice to haves search
            nice_to_have_locators = page.locator('section[branch="nices"] li')
            nice_to_have = [await loc.text_content() for loc in await nice_to_have_locators.all()]

            # Full data of vacancy
            full_job_info = {
                **job_info,
                "company_name": company_name.strip(),
                "category": category.strip(),
                "seniority": seniority.strip(),
                "location": location.strip(),
                "requirements": [req.strip() for req in requirements if req],
                "nice_to_have": [nice.strip() for nice in nice_to_have if nice],
            }

            print(f"✅ Successfully scraped: {job_id}")
            return full_job_info

        except Exception as e:
            print(f"❌ Something went wrong with {job_id}: {e}")
            return {
                **job_info,
                "company_name": "Can't collect data",
                "category": "Can't collect data",
                "seniority": "Can't collect data",
                "requirements": ["Can't collect data"],
                "nice_to_have": ["Can't collect data"],
            }
        finally:
            await context.close()


async def main():
    print("Open first page")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        # Creating page for collecting data
        initial_page = await browser.new_page()

        # Setting viewport for correct view
        await initial_page.set_viewport_size({"width": 1920, "height": 1080})

        # Collecting all links for second step
        list_of_jobs = await scrape_list_page(initial_page)
        await initial_page.close()

        if not list_of_jobs:
            print("❌ Something went wrong")
            await browser.close()
            return

        # Parallel collecting data from detail pages
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        tasks = [scrape_detail_task(browser, job_info, semaphore) for job_info in list_of_jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        await browser.close()

    # Collecting results
    all_job_data = []
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ The task ends with error: {result}")
        elif result:
            all_job_data.append(result)

    # Output and saving results
    if all_job_data:
        print(f"\nSuccessfully scraped {len(all_job_data)} detail pages!")

        # Save in .json
        filename = f"nofluff_jobs_extended_{len(all_job_data)}_jobs.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_job_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Data saved in: {filename}")

        # First 5 vacancies for debugging
        print(f"\nFirst 5 vacancies for debugging:")
        for i, item in enumerate(all_job_data):
            print(f"\n--- Vacancy {i + 1} ---")
            print(json.dumps(item, indent=2, ensure_ascii=False))
    else:
        print("❌ Can't collect data")


if __name__ == "__main__":
    asyncio.run(main())