# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import templeton
import web
from mozpool import config
from mozpool.db import data
from mozpool.bmm import api as bmm_api

# URLs go here. "/api/" will be automatically prepended to each.
urls = (
  # /device methods
  "/device/list/?", "device_list",
  "/device/([^/]+)/status/?", "device_status",
  "/device/([^/]+)/boot/([^/]+)/?", "device_boot",
  "/device/([^/]+)/reboot/?", "device_reboot",
  "/device/([^/]+)/bootcomplete/?", "device_bootcomplete",
  "/device/([^/]+)/config/?", "device_config",
  # /bootimage methods
  "/bootimage/list/?", "bootimage_list",
  "/bootimage/([^/]+)/details/?", "bootimage_details",
)

def deviceredirect(function):
    """
    Generate a redirect when a request is made for a device that is not
    managed by this instance of the service.
    """
    def wrapped(self, id, *args):
        try:
            server = data.get_server_for_device(id)
        except data.NotFound:
            raise web.notfound()
        if server != config.get('server', 'fqdn'):
            raise web.found("http://%s%s" % (server, web.ctx.path))
        return function(self, id, *args)
    return wrapped

# device handlers
class device_list:
    @templeton.handlers.json_response
    def GET(self):
        args, _ = templeton.handlers.get_request_parms()
        if 'details' in args:
            return dict(devices=data.dump_devices())
        else:
            return data.list_devices()

class device_status:
    @templeton.handlers.json_response
    def GET(self, id):
        return data.device_status(id)

    @templeton.handlers.json_response
    def POST(self, id):
        args, body = templeton.handlers.get_request_parms()
        return {"status": data.set_device_status(id, body["status"])}

class device_boot:
    @deviceredirect
    @templeton.handlers.json_response
    def POST(self, name, image):
        args, body = templeton.handlers.get_request_parms()
        # TODO: verify we own this device
        bmm_api.set_pxe(name, image, body)
        bmm_api.powercycle(name)
        return {}

class device_reboot:
    @deviceredirect
    @templeton.handlers.json_response
    def POST(self, name):
        # TODO: verify we own this device
        bmm_api.clear_pxe(name)
        bmm_api.powercycle(name)
        return {}

class device_bootcomplete:
    @deviceredirect
    @templeton.handlers.json_response
    def POST(self, name):
        # TODO: verify we own this device
        bmm_api.clear_pxe(name)
        return {}

class device_config:
    @templeton.handlers.json_response
    def GET(self, id):
        return data.device_config(id)

# bootimage handlers
class bootimage_list:
    @templeton.handlers.json_response
    def GET(self):
        return data.list_bootimages()

class bootimage_details:
    @templeton.handlers.json_response
    def GET(self, id):
        return data.bootimage_details(id)
