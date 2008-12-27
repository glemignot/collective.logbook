# -*- coding: utf-8 -*-
#
# File: logbook.py
#
# Copyright (c) InQuant GmbH
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__author__ = 'Ramon Bartl <ramon.bartl@inquant.de>'
__docformat__ = 'plaintext'

import logging

from DateTime import DateTime

from zope import interface
from zope.app.component import hooks

from plone.memoize.instance import memoize

from Products.statusmessages.interfaces import IStatusMessage
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Acquisition import aq_inner
from zExceptions import Forbidden

from collective.logbook.interfaces import ILogBook
from collective.logbook.interfaces import ILogBookStorage

logger = logging.getLogger("collective.logbook")


class LogBook(BrowserView):
    """ Logbook Form
    """
    interface.implements(ILogBook)

    template = ViewPageTemplateFile('logbook.pt')

    def __init__(self, context, request):
        super(LogBook, self).__init__(context, request)
        self.context = aq_inner(context)
        self.request = request
        self.portal = hooks.getSite()
        self.storage = ILogBookStorage(self.portal)

    @memoize
    def error_log(self):
        """ error_log object
        """
        error_log_path = '/'.join(
                ['/'.join(self.portal.getPhysicalPath()), 'error_log'])
        return self.portal.restrictedTraverse(error_log_path)

    def error(self, err_id):
        """ error object from the zope error_log
        """
        error = self.error_log().getLogEntryById(err_id)
        if error is None:
            return None
        # make human readable time
        error['time'] = DateTime(error['time'])
        return error

    def save_entry(self, err_id):
        """ save the error to the storage
        """
        error = self.error(err_id)
        return self.storage.save_error(error)

    def delete_entry(self, err_id):
        """ deletes an error entry from the storage
        """
        return self.storage.delete_error(err_id)

    def delete_all_errors(self):
        """ delete all errors
        """
        return self.storage.delete_all_errors()

    def delete_all_references(self):
        """ delete all references
        """
        return self.storage.delete_all_references()

    @property
    def saved_entries(self):
        """ storage entries
        """
        errors = self.storage.get_all_errors()
        out = []
        for id, tb in errors:
            out.append(
                    dict(
                        id = id,
                        tb = tb,
                        )
                    )
        return out

    @property
    def error_count(self):
        """ error count
        """
        return self.storage.error_count

    @property
    def reference_count(self):
        """ reference count
        """
        return self.storage.reference_count

    def search_error(self, err_id):
        """ search the storage
        """
        return self.storage.get_error(err_id)

    def __call__(self):
        self.request.set('disable_border', True)
        form = self.request.form

        submitted = form.get('form.submitted', None) is not None
        traceback_button = form.get('form.button.traceback', None) is not None
        delete_traceback_button = form.get('form.button.deletetraceback', None) is not None
        delete_refs_button = form.get('form.button.deleterefs', None) is not None
        delete_all_button = form.get('form.button.deleteall', None) is not None

        if submitted:
            if not self.request.get('REQUEST_METHOD', 'GET') == 'POST':
                raise Forbidden

            if traceback_button:
                err_id = form.get('errornumber', None)
                error = self.search_error(err_id)
                self.request.set('entry', error)

            if delete_traceback_button:
                entries = form.get('entries', [])
                for entry in entries:
                    err_id = entry.get('id')
                    if self.delete_entry(err_id):
                        IStatusMessage(self.request).addStatusMessage(u"Traceback %s deleted" % err_id, type='info')
                    else:
                        IStatusMessage(self.request).addStatusMessage(u"could not delete %s" % err_id, type='warning')

            if delete_all_button:
                self.delete_all_errors()
                IStatusMessage(self.request).addStatusMessage(u"Deleted all Errors", type='info')

            if delete_refs_button:
                self.delete_all_references()
                IStatusMessage(self.request).addStatusMessage(u"Deleted all referenced Error", type='info')

        return self.template()


class LogBookAtomFeed(LogBook):
    """ Logbook Atom Feed
    """
    template = ViewPageTemplateFile('logbook_atom.pt')

    def __init__(self, context, request):
        super(LogBookAtomFeed, self).__init__(context, request)
        self.context = aq_inner(context)
        self.request = request

    def __call__(self):
        return self.template()


class LogBookRSSFeed(LogBook):
    """ Logbook RSS Feed
    """
    template = ViewPageTemplateFile('logbook_rss.pt')

    def __init__(self, context, request):
        super(LogBookRSSFeed, self).__init__(context, request)
        self.context = aq_inner(context)
        self.request = request

    def __call__(self):
        return self.template()

# vim: set ft=python ts=4 sw=4 expandtab :
