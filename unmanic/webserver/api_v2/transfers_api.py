#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.transfers_api.py

    API handler for active file transfer status between linked installations.

"""

import tornado.log

from unmanic.libs.transfer_tracker import TransferTracker
from unmanic.webserver.api_v2.base_api_handler import BaseApiHandler, BaseApiError
from unmanic.webserver.api_v2.schema.schemas import TransferStatusSuccessSchema


class ApiTransfersHandler(BaseApiHandler):
    params = None

    routes = [
        {
            "path_pattern":      r"/transfers/status",
            "supported_methods": ["GET"],
            "call_method":       "get_transfer_status",
        },
    ]

    def initialize(self, **kwargs):
        self.params = kwargs.get("params")

    async def get_transfer_status(self):
        """
        Transfers - Return the status of all active transfers
        ---
        description: Returns a list of all active file transfers between linked installations.
        responses:
            200:
                description: 'Sample response: Returns the status of all active transfers.'
                content:
                    application/json:
                        schema:
                            TransferStatusSuccessSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            tracker = TransferTracker()
            transfers = tracker.get_all_transfers()

            response = self.build_response(
                TransferStatusSuccessSchema(),
                {
                    'transfers': transfers,
                }
            )
            self.write_success(response)
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()
