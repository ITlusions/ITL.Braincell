from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("file:///D:/repos/ITL.BrainCell/examples/braincell-local/install.html")
    page.wait_for_timeout(500)
    page.evaluate("document.getElementById('install').scrollIntoView()")
    page.wait_for_timeout(200)
    page.screenshot(path="D:/repos/ITL.BrainCell/examples/braincell-local/shot-install2.png", clip={"x":0,"y":0,"width":1440,"height":900})
    browser.close()
print("done")
