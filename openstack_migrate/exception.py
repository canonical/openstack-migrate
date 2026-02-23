# SPDX-FileCopyrightText: 2025 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0


class OpenstackMigrateException(Exception):
    msg_fmt = "An exception has been encountered."

    def __init__(self, message=None, **kwargs):
        if not message:
            message = self.msg_fmt % kwargs
        super(OpenstackMigrateException, self).__init__(message)


class Invalid(OpenstackMigrateException):
    msg_fmt = "Invalid data."


class InvalidInput(Invalid):
    msg_fmt = "Invalid input provided."


class NotFound(OpenstackMigrateException):
    msg_fmt = "Resource not found."


class MultipleResourcesFound(OpenstackMigrateException):
    msg_fmt = "Multiple resources found."


class NotSupported(OpenstackMigrateException):
    msg_fmt = "The requested operation is unsupported."
