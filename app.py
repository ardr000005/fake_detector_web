import os
import time
import logging
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager  # Auto-install ChromeDriver

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def detect_fake_image(image_path):
    """Run Selenium to detect fake images."""
    logging.info("Initializing Selenium WebDriver...")

    options = Options()
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())  # Auto-install ChromeDriver
    driver = webdriver.Chrome(service=service, options=options)

    try:
        logging.info("Opening fake image detector website...")
        driver.get("https://www.fakeimagedetector.com/")

        wait = WebDriverWait(driver, 10)

        upload_button = driver.find_element(By.XPATH, "//input[@type='file']")
        upload_button.send_keys(os.path.abspath(image_path))
        time.sleep(5)

        scan_now_button = driver.find_element(By.XPATH, "/html/body/main/section[2]/div/div/div/div[2]/form/div/div[1]/div[3]/div/button[2]")
        ActionChains(driver).move_to_element(scan_now_button).click().perform()
        time.sleep(10)

        result_element = driver.find_element(By.XPATH, "/html/body/main/section/div/div/div/div[2]/div[1]/div[2]/div[1]/label")
        result_text = result_element.text

        return {"status": "success", "result": result_text}

    except Exception as e:
        logging.error(f"Error in Selenium: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()


@app.route("/detect", methods=["POST"])
def detect():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    image = request.files["image"]
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
    image.save(image_path)

    logging.info(f"Image saved at {image_path}, sending to Selenium...")

    response = detect_fake_image(image_path)

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
