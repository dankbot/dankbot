import asyncio

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import sys
from queue import Queue
from threading import Thread, Event, Lock
import logging
import json


logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s %(message)s', stream=sys.stdout)
logging.getLogger("bot").setLevel(logging.DEBUG)


class MessageTyper:
    def __init__(self, profile_id, url):
        self.loop = asyncio.get_event_loop()
        self.msgq = Queue()
        self.thread = Thread(target=self._thread_wrapper)
        self.profile_id = profile_id
        self.url = url
        self.driver_path = "chromedriver"
        self.chrome_path = None
        self.cooldown_lock = Lock()
        self.cooldown_expires = 0
        self.cooldown_notification = Event()
        self.user_id = None
        self.user_id_event = asyncio.Event()
        self.running = False

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.msgq.put(None)
        if self.thread.is_alive():
            self.thread.join()

    async def get_user_id(self):
        await self.user_id_event.wait()
        return self.user_id

    def set_user_id(self, user_id):
        self.user_id = user_id
        self.user_id_event.set()

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

    def _thread_wrapper(self):
        try:
            self._thread()
        except Exception as e:
            logging.getLogger("bot.typer").exception("typer crashed")

    def _thread(self):
        options = webdriver.ChromeOptions()
        if self.chrome_path is not None:
            options.binary_location = self.chrome_path
        options.add_experimental_option('w3c', False)
        options.add_argument("user-data-dir=profiles/" + self.profile_id)

        driver = webdriver.Chrome(executable_path=self.driver_path, options=options)
        try:
            driver.get(self.url)

            while self.running:
                user_id = MessageTyper._get_user_id(driver)
                if user_id is not None and len(user_id) > 0:
                    self.loop.call_soon_threadsafe(self.set_user_id, int(user_id))
                    break
                time.sleep(0.01)

            while True:
                e = self.msgq.get()
                if e is None:
                    break
                if e.startswith("pls "):
                    self.wait_forced_cooldown()
                    self.update_forced_cooldown(10, True)
                while self.running:
                    try:
                        MessageTyper._send_message(driver, e)
                        break
                    except Exception as exception:
                        logging.exception("Failed to send message")
                        time.sleep(1)
        finally:
            driver.close()

    @staticmethod
    def _get_user_id(driver):
        try:
            x = MessageTyper.devtool_cmd(driver, "DOMStorage.getDOMStorageItems", {"storageId": {"isLocalStorage": True, "securityOrigin": "https://discord.com"}})
            for a in x["entries"]:
                if a[0] == "user_id_cache":
                    ret = a[1]
                    if len(ret) > 0 and ret[0] == '"' and ret[-1] == '"':
                        return a[1][1:-1]
        except Exception as exception:
            logging.exception("Failed to get user id")
        return None

    @staticmethod
    def devtool_cmd(driver, cmd, params=None):
        # https://stackoverflow.com/questions/47297877/to-set-mutationobserver-how-to-inject-javascript-before-page-loading-using-sele
        if params is None:
            params = {}
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        if response['status']:
            raise Exception(response.get('value'))
        return response.get('value')

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

