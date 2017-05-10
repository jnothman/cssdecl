"""Python CSS declaration computer

"""

import re
import warnings
from collections import defaultdict

try:
    import tinycss2
    import tinycss2.color3
except ImportError:
    # currently needed for setup.cfg to get version :(
    pass

__version__ = '0.1.3+dev'


__all__ = ['CSSWarning', 'CSS22Resolver']


class CSSWarning(UserWarning):
    """Warning for when this CSS syntax cannot currently be parsed"""
    pass


def match_tokens(tokens, matchers, remainder):
    out = defaultdict(list)
    for tok in tokens:
        for k, matcher in matchers.items():
            if matcher(tok):
                out[k].append(tok)
                break
        else:
            out[remainder].append(tok)
    out.default_factory = None
    return out


def match_color_token(token):
    return tinycss2.color3.parse_color(token) is not None


def match_size_token(token):
    return (token.type == 'dimension' or token.type == 'percentage'
            or (token.type == 'ident' and token.lower_value in {
                'medium', 'thin', 'thick', 'smaller', 'larger', 'xx-small',
                'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'}))


class _BaseCSSResolver(object):
    """Base class for parsing and resolving CSS to atomic properties

    """

    def __init__(self, initial=None):
        self.initial = initial or {}

    def resolve_string(self, declarations_str, inherited=None):
        """Resolve the given declarations to atomic properties

        Parameters
        ----------
        declarations_str : str
            A list of CSS declarations
        inherited : dict, optional
            Atomic properties indicating the inherited style context in which
            declarations_str is to be resolved. ``inherited`` should already
            be resolved, i.e. valid output of this method.

        Returns
        -------
        props : dict
            Atomic CSS 2.2 properties mapped to their values as strings

        Examples
        --------
        >>> resolver = CSS22Resolver()
        >>> inherited = {'font-family': 'serif', 'font-weight': 'bold'}
        >>> out = resolver.resolve_string('''
        ...               border-color: BLUE RED;
        ...               font-size: 1em;
        ...               font-size: 2em;
        ...               font-weight: normal;
        ...               font-weight: inherit;
        ...               ''', inherited)
        >>> sorted(out.items())  # doctest: +NORMALIZE_WHITESPACE
        [('border-bottom-color', 'blue'),
         ('border-left-color', 'red'),
         ('border-right-color', 'red'),
         ('border-top-color', 'blue'),
         ('font-family', 'serif'),
         ('font-size', '24pt'),
         ('font-weight', 'bold')]
        """

        props = dict(self._atomize(self._parse(declarations_str)))
        if inherited is None:
            inherited = {}

        # 1. resolve inherited, initial
        for prop, val in inherited.items():
            if prop not in props:
                props[prop] = val

        for prop, val in list(props.items()):
            if val == 'inherit':
                val = inherited.get(prop, 'initial')
            if val == 'initial':
                val = self.initial.get(prop)

            if val is None:
                # we do not define a complete initial stylesheet
                del props[prop]
            else:
                props[prop] = val

        # 2. resolve relative font size
        if props.get('font-size'):
            if 'font-size' in inherited:
                em_pt = inherited['font-size']
                assert em_pt[-2:] == 'pt'
                em_pt = float(em_pt[:-2])
            else:
                em_pt = None
            props['font-size'] = self._size_to_pt(
                props['font-size'], em_pt, conversions=self.FONT_SIZE_RATIOS)

            font_size = float(props['font-size'][:-2])
        else:
            font_size = None

        # 3. TODO: resolve other font-relative units
        for side in self.SIDES:
            prop = 'border-%s-width' % side
            if prop in props:
                props[prop] = self._size_to_pt(
                    props[prop], em_pt=font_size,
                    conversions=self.BORDER_WIDTH_RATIOS)
            for prop in ['margin-%s' % side, 'padding-%s' % side]:
                if prop in props:
                    # TODO: support %
                    props[prop] = self._size_to_pt(
                        props[prop], em_pt=font_size,
                        conversions=self.MARGIN_RATIOS)

        return props

    UNIT_RATIOS = {
        'rem': ('pt', 12),
        'ex': ('em', .5),
        # 'ch':
        'px': ('pt', .75),
        'pc': ('pt', 12),
        'in': ('pt', 72),
        'cm': ('in', 1 / 2.54),
        'mm': ('in', 1 / 25.4),
        'q': ('mm', .25),
        '!!default': ('em', 0),
    }

    FONT_SIZE_RATIOS = UNIT_RATIOS.copy()
    FONT_SIZE_RATIOS.update({
        '%': ('em', .01),
        'xx-small': ('rem', .5),
        'x-small': ('rem', .625),
        'small': ('rem', .8),
        'medium': ('rem', 1),
        'large': ('rem', 1.125),
        'x-large': ('rem', 1.5),
        'xx-large': ('rem', 2),
        'smaller': ('em', 1 / 1.2),
        'larger': ('em', 1.2),
        '!!default': ('em', 1),
    })

    MARGIN_RATIOS = UNIT_RATIOS.copy()
    MARGIN_RATIOS.update({
        'none': ('pt', 0),
    })

    BORDER_WIDTH_RATIOS = UNIT_RATIOS.copy()
    BORDER_WIDTH_RATIOS.update({
        'none': ('pt', 0),
        'thick': ('px', 4),
        'medium': ('px', 2),
        'thin': ('px', 1),
        # Default: medium only if solid
    })

    def _size_to_pt(self, in_val, em_pt=None, conversions=UNIT_RATIOS):
        def _error():
            warnings.warn('Unhandled size: %r' % in_val, CSSWarning)
            return self._size_to_pt('1!!default', conversions=conversions)

        try:
            val, unit = re.match(r'^(\S*?)([a-zA-Z%!].*)', in_val).groups()
        except AttributeError:
            return _error()
        if val == '':
            # hack for 'large' etc.
            val = 1
        else:
            try:
                val = float(val)
            except ValueError:
                return _error()

        while unit != 'pt':
            if unit == 'em':
                if em_pt is None:
                    unit = 'rem'
                else:
                    val *= em_pt
                    unit = 'pt'
                continue

            try:
                unit, mul = conversions[unit]
            except KeyError:
                return _error()
            val *= mul

        val = round(val, 5)
        if int(val) == val:
            size_fmt = '%d'
        else:
            size_fmt = '%f'
        return (size_fmt + 'pt') % val

    def _atomize(self, declarations):
        for prop, value in declarations:
            attr = 'expand_' + prop.replace('-', '_')
            try:
                expand = getattr(self, attr)
            except AttributeError:
                yield prop, value
            else:
                for prop, value in expand(prop, value):
                    yield prop, value

    def _clean_tokens(self, tokens):
        cleaned = []
        for tok in tokens:
            if tok.type == 'comment' or tok.type == 'whitespace':
                pass
            elif tok.type == 'error':
                # TODO: indicate error context (requires
                warnings.warn('Error parsing CSS: %r' % tok.message,
                              CSSWarning)
            else:
                cleaned.append(tok)
        return cleaned

    def _parse(self, declarations_str):
        """Generates (prop, value) pairs from declarations

        In a future version may generate parsed tokens from tinycss/tinycss2
        """
        decls = tinycss2.parse_declaration_list(declarations_str)
        decls = self._clean_tokens(decls)
        for decl in decls:
            value_str = tinycss2.serialize(decl.value).strip().lower()
            yield decl.lower_name, value_str


class _CommonExpansions(object):
    SIDE_SHORTHANDS = {
        1: [0, 0, 0, 0],
        2: [0, 1, 0, 1],
        3: [0, 1, 2, 1],
        4: [0, 1, 2, 3],
    }
    SIDES = ('top', 'right', 'bottom', 'left')

    def _side_expander(prop_fmt):
        def expand(self, prop, value):
            tokens = self._clean_tokens(tinycss2.parse_component_value_list(value))
            try:
                mapping = self.SIDE_SHORTHANDS[len(tokens)]
            except KeyError:
                warnings.warn('Could not expand "%s: %s"' % (prop, value),
                              CSSWarning)
                return
            for key, idx in zip(self.SIDES, mapping):
                yield prop_fmt % key, tinycss2.serialize(tokens[idx:idx+1])

        return expand

    expand_border_color = _side_expander('border-%s-color')
    expand_border_style = _side_expander('border-%s-style')
    expand_border_width = _side_expander('border-%s-width')
    expand_margin = _side_expander('margin-%s')
    expand_padding = _side_expander('padding-%s')

    def expand_border(self, prop, value, side=None):
        if side is None:
            sides = ['top', 'right', 'bottom', 'left']
        else:
            sides = [side]

        # TODO: clean tokens?
        value = tinycss2.parse_component_value_list(value)
        matched = match_tokens(value,
                               {'width': match_size_token,
                                'color': match_color_token},
                               remainder='style')
        for side in sides:
            for k, v in matched.items():
                if v:
                    v = self._clean_tokens(v)
                    yield 'border-%s-%s' % (side, k), tinycss2.serialize(v)

    def _border_side_expander(side):
        # XXX: functools.partial cannot be bound!
        def expand_border_side(self, prop, value):
            return self.expand_border(prop, value, side)
        return expand_border_side

    expand_border_top = _border_side_expander('top')
    expand_border_right = _border_side_expander('right')
    expand_border_bottom = _border_side_expander('bottom')
    expand_border_left = _border_side_expander('left')


class CSS22Resolver(_BaseCSSResolver, _CommonExpansions):
    """Parses and resolves CSS to atomic CSS 2.2 properties
    """
