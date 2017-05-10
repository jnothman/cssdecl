import pytest

from cssdecl import CSS22Resolver, CSSWarning


def assert_resolves(css, props, inherited=None):
    resolver = CSS22Resolver()
    actual = resolver.resolve_string(css, inherited=inherited)
    assert props == actual


def assert_same_resolution(css1, css2, inherited=None):
    resolver = CSS22Resolver()
    resolved1 = resolver.resolve_string(css1, inherited=inherited)
    resolved2 = resolver.resolve_string(css2, inherited=inherited)
    assert resolved1 == resolved2


@pytest.mark.parametrize('name,norm,abnorm', [
    ('whitespace', 'hello: world; foo: bar',
     ' \t hello \t :\n  world \n  ;  \n foo: \tbar\n\n'),
    ('case', 'hello: world; foo: bar', 'Hello: WORLD; foO: bar'),
    ('empty-decl', 'hello: world; foo: bar',
     '; hello: world;; foo: bar;\n; ;'),
    ('empty-list', '', ';'),
])
def test_css_parse_normalisation(name, norm, abnorm):
    assert_same_resolution(norm, abnorm)


@pytest.mark.xfail(reason='CSS comments not yet stripped')
def test_css_parse_comments():
    assert_same_resolution('hello: world',
                           'hello/* foo */:/* bar \n */ world /*;not:here*/')


def test_css_parse_specificity():
    assert_same_resolution('font-weight: bold', 'font-weight: bold !important')


@pytest.mark.xfail(reason='Splitting CSS declarations not yet sensitive to '
                          '; in CSS strings')
def test_css_parse_strings():
    # semicolons in strings
    assert_resolves('background-image: url(\'http://blah.com/foo?a;b=c\')',
                    {'background-image': 'url(\'http://blah.com/foo?a;b=c\')'})
    assert_resolves('background-image: url("http://blah.com/foo?a;b=c")',
                    {'background-image': 'url("http://blah.com/foo?a;b=c")'})


@pytest.mark.parametrize(
    'invalid_css,remainder', [
        # No colon
        ('hello-world', ''),
        ('border-style: solid; hello-world', 'border-style: solid'),
        ('border-style: solid; hello-world; font-weight: bold',
         'border-style: solid; font-weight: bold'),
        # Unclosed string
        pytest.mark.xfail(('background-image: "abc', ''),
                          reason='Unclosed CSS strings not detected'),
        pytest.mark.xfail(('font-family: "abc', ''),
                          reason='Unclosed CSS strings not detected'),
        pytest.mark.xfail(('background-image: \'abc', ''),
                          reason='Unclosed CSS strings not detected'),
        pytest.mark.xfail(('font-family: \'abc', ''),
                          reason='Unclosed CSS strings not detected'),
        # Invalid size
        ('font-size: blah', 'font-size: 1em'),
        ('font-size: 1a2b', 'font-size: 1em'),
        ('font-size: 1e5pt', 'font-size: 1em'),
        ('font-size: 1+6pt', 'font-size: 1em'),
        ('font-size: 1unknownunit', 'font-size: 1em'),
        ('font-size: 10', 'font-size: 1em'),
        ('font-size: 10 pt', 'font-size: 1em'),
    ])
def test_css_parse_invalid(invalid_css, remainder):
    with pytest.warns(CSSWarning):
        assert_same_resolution(invalid_css, remainder)

    # TODO: we should be checking that in other cases no warnings are raised


@pytest.mark.parametrize(
    'shorthand,expansions',
    [('margin', ['margin-top', 'margin-right',
                 'margin-bottom', 'margin-left']),
     ('padding', ['padding-top', 'padding-right',
                  'padding-bottom', 'padding-left']),
     ('border-width', ['border-top-width', 'border-right-width',
                       'border-bottom-width', 'border-left-width']),
     ('border-color', ['border-top-color', 'border-right-color',
                       'border-bottom-color', 'border-left-color']),
     ('border-style', ['border-top-style', 'border-right-style',
                       'border-bottom-style', 'border-left-style']),
     ])
def test_css_side_shorthands(shorthand, expansions):
    top, right, bottom, left = expansions

    assert_resolves('%s: 1pt' % shorthand,
                    {top: '1pt', right: '1pt',
                     bottom: '1pt', left: '1pt'})

    assert_resolves('%s: 1pt 4pt' % shorthand,
                    {top: '1pt', right: '4pt',
                     bottom: '1pt', left: '4pt'})

    assert_resolves('%s: 1pt 4pt 2pt' % shorthand,
                    {top: '1pt', right: '4pt',
                     bottom: '2pt', left: '4pt'})

    assert_resolves('%s: 1pt 4pt 2pt 0pt' % shorthand,
                    {top: '1pt', right: '4pt',
                     bottom: '2pt', left: '0pt'})

    with pytest.warns(CSSWarning):
        assert_resolves('%s: 1pt 1pt 1pt 1pt 1pt' % shorthand,
                        {})


@pytest.mark.xfail(reason='CSS font shorthand not yet handled')
@pytest.mark.parametrize('css,props', [
    ('font: italic bold 12pt helvetica,sans-serif',
     {'font-family': 'helvetica,sans-serif',
      'font-style': 'italic',
      'font-weight': 'bold',
      'font-size': '12pt'}),
    ('font: bold italic 12pt helvetica,sans-serif',
     {'font-family': 'helvetica,sans-serif',
      'font-style': 'italic',
      'font-weight': 'bold',
      'font-size': '12pt'}),
])
def test_css_font_shorthand(css, props):
    assert_resolves(css, props)


@pytest.mark.xfail(reason='CSS background shorthand not yet handled')
@pytest.mark.parametrize('css,props', [
    ('background: blue', {'background-color': 'blue'}),
    ('background: fixed blue',
     {'background-color': 'blue', 'background-attachment': 'fixed'}),
])
def test_css_background_shorthand(css, props):
    assert_resolves(css, props)


@pytest.mark.parametrize('style,equiv', [
    ('border{side}: {width} solid {color}',
     'border{side}-width: {width}; border{side}-style: solid;' +
     'border{side}-color: {color}'),
    ('border{side}: solid {color} {width}',
     'border{side}-width: {width}; border{side}-style: solid;' +
     'border{side}-color: {color}'),
    ('border{side}: {color} solid',
     'border{side}-style: solid; border{side}-color: {color}'),
])
@pytest.mark.parametrize('side', ['', '-top', '-right', '-bottom', '-left'])
@pytest.mark.parametrize('width', ['1px', 'thin'])
@pytest.mark.parametrize('color', ['red', 'rgb(5, 10, 20)',
                                   'RED', 'RGB(5, 10, 20)'])
def test_css_border_shorthand(style, equiv, side, width, color):
    assert_same_resolution(style.format(**locals()), equiv.format(**locals()))


@pytest.mark.parametrize('style,inherited,equiv', [
    ('margin: 1px; margin: 2px', '',
     'margin: 2px'),
    ('margin: 1px', 'margin: 2px',
     'margin: 1px'),
    ('margin: 1px; margin: inherit', 'margin: 2px',
     'margin: 2px'),
    ('margin: 1px; margin-top: 2px', '',
     'margin-left: 1px; margin-right: 1px; ' +
     'margin-bottom: 1px; margin-top: 2px'),
    ('margin-top: 2px', 'margin: 1px',
     'margin: 1px; margin-top: 2px'),
    ('margin: 1px', 'margin-top: 2px',
     'margin: 1px'),
    ('margin: 1px; margin-top: inherit', 'margin: 2px',
     'margin: 1px; margin-top: 2px'),
])
def test_css_precedence(style, inherited, equiv):
    resolver = CSS22Resolver()
    inherited_props = resolver.resolve_string(inherited)
    style_props = resolver.resolve_string(style, inherited=inherited_props)
    equiv_props = resolver.resolve_string(equiv)
    assert style_props == equiv_props


@pytest.mark.parametrize('style,equiv', [
    ('margin: 1px; margin-top: inherit',
     'margin-bottom: 1px; margin-right: 1px; margin-left: 1px'),
    ('margin-top: inherit', ''),
    ('margin-top: initial', ''),
])
def test_css_none_absent(style, equiv):
    assert_same_resolution(style, equiv)


@pytest.mark.parametrize('size,resolved', [
    ('xx-small', '6pt'),
    ('x-small', '%fpt' % 7.5),
    ('small', '%fpt' % 9.6),
    ('medium', '12pt'),
    ('large', '%fpt' % 13.5),
    ('x-large', '18pt'),
    ('xx-large', '24pt'),

    ('8px', '6pt'),
    ('1.25pc', '15pt'),
    ('.25in', '18pt'),
    ('02.54cm', '72pt'),
    ('25.4mm', '72pt'),
    ('101.6q', '72pt'),
    ('101.6q', '72pt'),
])
@pytest.mark.parametrize('relative_to',  # invariant to inherited size
                         [None, '16pt'])
def test_css_absolute_font_size(size, relative_to, resolved):
    if relative_to is None:
        inherited = None
    else:
        inherited = {'font-size': relative_to}
    assert_resolves('font-size: %s' % size, {'font-size': resolved},
                    inherited=inherited)


@pytest.mark.parametrize('size,relative_to,resolved', [
    ('1em', None, '12pt'),
    ('1.0em', None, '12pt'),
    ('1.25em', None, '15pt'),
    ('1em', '16pt', '16pt'),
    ('1.0em', '16pt', '16pt'),
    ('1.25em', '16pt', '20pt'),
    ('1rem', '16pt', '12pt'),
    ('1.0rem', '16pt', '12pt'),
    ('1.25rem', '16pt', '15pt'),
    ('100%', None, '12pt'),
    ('125%', None, '15pt'),
    ('100%', '16pt', '16pt'),
    ('125%', '16pt', '20pt'),
    ('2ex', None, '12pt'),
    ('2.0ex', None, '12pt'),
    ('2.50ex', None, '15pt'),
    ('inherit', '16pt', '16pt'),

    ('smaller', None, '10pt'),
    ('smaller', '18pt', '15pt'),
    ('larger', None, '%fpt' % 14.4),
    ('larger', '15pt', '18pt'),
])
def test_css_relative_font_size(size, relative_to, resolved):
    if relative_to is None:
        inherited = None
    else:
        inherited = {'font-size': relative_to}
    assert_resolves('font-size: %s' % size, {'font-size': resolved},
                    inherited=inherited)
