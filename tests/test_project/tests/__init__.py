class CreateMixin(object):
    def _create_book(self, **kwargs):
        options = dict(name='test-book',
                       author='test-author')
        options.update(kwargs)
        b = self.book_model(**options)
        b.full_clean()
        b.save()
        return b

    def _create_shelf(self, **kwargs):
        options = dict(name='test-shelf')
        options.update(kwargs)
        s = self.shelf_model(**options)
        s.full_clean()
        s.save()
        return s

    def _get_defaults(self, opts, model=None):
        options = {}
        options.update(opts)
        return options

    def _create_radius_accounting(self, **kwargs):
        options = self._get_defaults(kwargs)
        ra = self.accounting_model(**options)
        ra.full_clean()
        ra.save()
        return ra
