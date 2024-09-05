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
    browser.configure(
        slowmo=2000,
    )
    open_robot_order_website()
    close_annoying_modal()
    fill_form_with_csv_data()
    archive_receipts()

def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def close_annoying_modal():
    """Resolve pop up clicking on ok"""
    page = browser.page()
    page.click("button:text('OK')")

def download_csv_file():
    """Downloads csv file from the given URL"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

def fill_and_submit_order_form(order_info):
    """Fills in the order data"""
    page = browser.page()
    page.select_option("#head", order_info['Head'])
    page.click(f"id=id-body-{order_info['Body']}")
    input_legs_selector = "input[placeholder='Enter the part number for the legs']"
    page.wait_for_selector(input_legs_selector, timeout=10000)
    page.fill(input_legs_selector, order_info['Legs'])  
    page.fill("#address", order_info['Address'])
    page.click("button:text('Order')")

def get_orders():
    """Read data from csv and return the orders"""
    tables = Tables()
    table = tables.read_table_from_csv("orders.csv", header=True)
    return table

def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.open_pdf(pdf_file)
    pdf.add_files_to_pdf([pdf_file, screenshot], pdf_file)

def screenshot_robot(order_number) -> str:
    """Take a screenshot of the page"""
    page = browser.page()
    screenshot_path = f"output/receipts_images/{order_number}.png"
    page.screenshot(path=screenshot_path)
    return screenshot_path

def locate_order_completion():
    """Export the data to a pdf file"""
    page = browser.page()
    try:
        page.locator("#order-completion").inner_html()
    except:
        page.click("button:text('Order')")

def store_receipt_as_pdf(order_number):
    """Export the data to a pdf file"""
    tries = 3
    page = browser.page()
    while (tries>0):
        try:
            check_alert_present()
            sales_results_html = page.locator("#order-completion").inner_html()
            pdf = PDF()
            pdf_file = f"output/receipts/{order_number}.pdf"
            pdf.html_to_pdf(sales_results_html, pdf_file)
            return pdf_file
        except:
            tries -=1

def order_another_robot():
    """Order another robot clickin in the button"""
    page = browser.page()
    page.click("button:text('Order another robot')")

def archive_receipts():
    """Create a zip file from receipts"""
    lib = Archive()
    pdf_folder_path = "output/receipts"
    zip_file_path = "output/receipts.zip"
    lib.archive_folder_with_zip(pdf_folder_path, zip_file_path)


def check_alert_present():
    """Check if an alert with class 'alert alert-danger' is present on the page."""
    page = browser.page()
    alert_selector = ".alert.alert-danger"
    try:
        page.wait_for_selector(alert_selector, timeout=1000)  # Wait up to 5 seconds
        page.click("button:text('Order')")
    except Exception:
        pass


def fill_form_with_csv_data():
    """Read data from csv and fill in the order form"""
    orders = get_orders()

    for order in orders:
        order_number = order['Order number']
        fill_and_submit_order_form(order)
        
        pdf_file = store_receipt_as_pdf(order_number)
        screenshot_path = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot_path, pdf_file)
        order_another_robot()
        close_annoying_modal()
