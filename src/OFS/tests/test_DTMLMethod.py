# -*- coding: utf-8 -*-
import io
import unittest


class DTMLMethodTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.DTMLMethod import DTMLMethod
        return DTMLMethod

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_class_conforms_to_IWriteLock(self):
        from zope.interface.verify import verifyClass
        from OFS.interfaces import IWriteLock
        verifyClass(IWriteLock, self._getTargetClass())

    def test_edit_taintedstring(self):
        from AccessControl.tainted import TaintedString
        doc = self._makeOne()
        self.assertEqual(doc.read(), '')
        data = TaintedString('hello<br/>')

        doc.manage_edit(data, 'title')
        self.assertEqual(doc.read(), 'hello&lt;br/&gt;')

    def test_manage_upload__bytes(self):
        """It stores uploaded bytes as a native str."""
        doc = self._makeOne()
        data = u'bÿtës'.encode('utf-8')
        self.assertIsInstance(data, bytes)
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)

    def test_manage_upload__str(self):
        """It stores an uploaded str as a native str."""
        doc = self._makeOne()
        data = 'bÿtës'
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)

    def test_manage_upload__StringIO(self):
        """It stores StringIO contents as a native str."""
        doc = self._makeOne()
        data = io.StringIO(u'bÿtës')
        doc.manage_upload(data)
        self.assertIsInstance(doc.read(), str)
        self.assertEqual(doc.read(), 'bÿtës')

    def test_manage_upload__BytesIO(self):
        """It stores BytesIO contents as a native str."""
        doc = self._makeOne()
        data = io.BytesIO(u'bÿtës'.encode('utf-8'))
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)


class FactoryTests(unittest.TestCase):

    def test_defaults_no_standard_html_header(self):
        # see LP #496961
        from OFS.DTMLMethod import addDTMLMethod
        from OFS.DTMLMethod import DTMLMethod
        dispatcher = DummyDispatcher()
        addDTMLMethod(dispatcher, 'id')
        method = dispatcher._set['id']
        self.assertIsInstance(method, DTMLMethod)
        self.assertFalse('standard_html_header' in method.read())
        self.assertFalse('standard_html_footer' in method.read())


class DummyDispatcher(object):

    def __init__(self):
        self._set = {}

    def _setObject(self, key, value):
        self._set[key] = value
