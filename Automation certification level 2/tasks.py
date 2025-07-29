from robocorp.tasks import task

from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    
    open_robot_order_website()
    close_annoying_modal()

    orders = get_orders()
    fill_the_form(orders)
    archive_receipts()

def open_robot_order_website():
    page = browser.page()
    page.goto("https://robotsparebinindustries.com/#/robot-order")

def close_annoying_modal():
    page = browser.page()
    page.click("button:text('OK')")
    
def get_orders():
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders

def submit_order_with_retry(max_retries=5):
    for attempt in range(1, max_retries + 1):
        page = browser.page()
        page.click("button:text('ORDER')")

        if not page.is_visible('div.alert.alert-danger'):
            return True
        
    return False

def fill_the_form(orders):
    page = browser.page()

    for order in orders:
        page.select_option("#head", order["Head"])
        page.click(f'input[name="body"][value="{order["Body"]}"]')
        page.fill('input[placeholder="Enter the part number for the legs"]', str(order["Legs"]))
        page.fill("#address", str(order["Address"]))
        page.click("button:text('Preview')")
        submit_order_with_retry()
        pdf_file = store_receipt_as_pdf(order["Order number"])
        screenshot = screenshot_robot(order["Order number"])
        embed_screenshot_to_receipt(screenshot, pdf_file)
        page.click("button:text('ORDER ANOTHER ROBOT')")
        close_annoying_modal()
        
def store_receipt_as_pdf(order_number):
    """Export the data to a pdf file"""
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    path = f"output/receipts/{order_number}.pdf"

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, path)
    return (path)

def screenshot_robot(order_number):
    """takes screenshot of robot"""
    page = browser.page()
    preview_html = page.locator("#robot-preview-image")
    path = f"output/screenshots/{order_number}.png"
    preview_html.screenshot(path=path)

    return path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True
    )

def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip('./output/receipts', 'output/receipts.zip')
