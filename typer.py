from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
from queue import Queue
from threading import Thread, Event, Lock
import logging


class MessageTyper:
    def __init__(self, profile_id, url):
        self.msgq = Queue()
        self.thread = Thread(target=self._thread)
        self.profile_id = profile_id
        self.url = url
        self.cooldown_lock = Lock()
        self.cooldown_expires = 0
        self.cooldown_notification = Event()

    def start(self):
        self.thread.start()

    def stop(self):
        self.msgq.put(None)
        self.thread.join()

    def send_message(self, msg):
        if msg is None:
            return
        self.msgq.put(msg)

    def update_forced_cooldown(self, t, force=False):
        self.cooldown_lock.acquire()
        e = time.time() + t
        if e < self.cooldown_expires or force:
            self.cooldown_expires = e
        self.cooldown_notification.set()
        self.cooldown_lock.release()

    def wait_forced_cooldown(self):
        while True:
            self.cooldown_lock.acquire()
            self.cooldown_notification.clear()
            rem = self.cooldown_expires - time.time()
            self.cooldown_lock.release()
            if rem <= 0:
                return
            self.cooldown_notification.wait(rem)

    def _thread(self):
        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir=profiles/" + self.profile_id)

        driver = webdriver.Chrome(options=options)
        driver.get(self.url)

        while True:
            e = self.msgq.get()
            if e is None:
                break
            if e.startswith("pls "):
                self.wait_forced_cooldown()
                self.update_forced_cooldown(10, True)
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

