#!/usr/bin/env python

import os
import time
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback

from data_receiver import DataReceiver


data_receiver = None


class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")


class MainWSHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        self.data_receiver = DataReceiver()
        self.callback = PeriodicCallback(self._send_message, 100)
        self.callback.start()

    def on_message(self, message):
        print(message)

    def _send_message(self):
        data = {"time": time.time()}
        try:
            ax, ay, az, gx, gy, gz, mx, my, mz = data_receiver.fetch_all_data()
            data["result"] = "successed"
            data["accel"] = [ax, ay, az]
            data["gyro"] = [gx, gy, gz]
            data["mag"] = [mx, my, mz]

        except Exception:
            data["result"] = "failed"
            data["message"] = "no data available."
            # print(traceback.format_exc())
        finally:
            self.write_message(data)

    def on_close(self):
        self.callback.stop()
        print("WebSocket closed")

app = tornado.web.Application([
    (r"/", MainHandler),
    (r"/ws", MainWSHandler)],
    template_path=os.path.join(os.getcwd(),  "templates"),
    static_path=os.path.join(os.getcwd(),  "static"),
)


def start(_data_receiver):
    global data_receiver
    data_receiver = _data_receiver
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
