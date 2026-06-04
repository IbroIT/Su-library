import sys
from copy import copy


def patch_template_context_copy():
    if sys.version_info < (3, 14):
        return

    from django.template.context import BaseContext, Context, RenderContext

    def base_context_copy(self):
        duplicate = object.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    def context_copy(self):
        duplicate = base_context_copy(self)
        duplicate.render_context = copy(self.render_context)
        return duplicate

    def render_context_copy(self):
        duplicate = base_context_copy(self)
        return duplicate

    BaseContext.__copy__ = base_context_copy
    Context.__copy__ = context_copy
    RenderContext.__copy__ = render_context_copy
