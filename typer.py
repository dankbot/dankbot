from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
from queue import Queue
from threading import Thread
import logging


class MessageTyper:
    def __init__(self, url):
        self.msgq = Queue()
        self.thread = Thread(target=self._thread)
        self.url = url

    def start(self):
        self.thread.start()

    def stop(self):
        self.msgq.put(None)
        self.thread.join()

    def send_message(self, msg):
        if msg is None:
            return
        self.msgq.put(msg)

    def _thread(self):
        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir=profiles/theBot")

        driver = webdriver.Chrome(options=options)
        driver.get(self.url)

        while True:
            e = self.msgq.get()
            if e is None:
                break
            while True:
                try:
                    MessageTyper._send_message(driver, e)
                    break
                except Exception as exception:
                    logging.exception("Failed to send message", exception)
                    time.sleep(1)

        driver.close()

    @staticmethod
    def _send_message(driver, txt):
        elem = None
        while elem is None:
            try:
                elem = driver.find_element_by_xpath("//div[contains(@class, 'slateTextArea')]")
            except NoSuchElementException:
                time.sleep(1)
        elem.click()
        elem.send_keys(Keys.CONTROL, 'a')
        elem.send_keys(txt)
        elem.send_keys(Keys.RETURN)
        time.sleep(0.05)

