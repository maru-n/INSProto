#!/usr/bin/env python

import time
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback
from tornado.options import define, options, parse_command_line

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
            data["accel"] = [ax, ay, az]
            data["gyro"] = [gx, gy, gz]
            data["mag"] = [mx, my, mz]

        except Exception as e:
            data["msg"] = "no data available."
            print(e)
        finally:
            self.write_message(data)

    def on_close(self):
        self.callback.stop()
        print("WebSocket closed")

define("port", default=8080, help="run on the given port", type=int)

app = tornado.web.Application([
    (r"/", MainHandler),
    (r"/ws", MainWSHandler),
])


def start(_data_receiver):
    global data_receiver
    data_receiver = _data_receiver
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
