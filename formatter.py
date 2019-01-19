from parso import parse
from parso.python.prefix import PrefixPart
from parso.tree import Node

too_much_space = """





class        Foo          (

                    object



                    )       :



    def        __init__          (

    self

      )                :


        # comment1



        for      x      in     baz     :       # comment2



            x       +=      1




def         bar          (

         a   ,  # comment3
              *     b
           ,      **
            c
            )       :          # comment4



    class        Nested    :


        pass



    def        nested      (               )     :


        baz        (           )





"""

nicely_formatted = """class Foo(object):
    def __init__(self):
        # comment1
        for x in baz:  # comment2
            x += 1





def bar(
      a,  # comment3 
      *b, 
      **c):  # comment4
    class Nested:
        pass
    def nested():
        baz()
"""


def key_for_node(node):
    if node.type == 'operator' and node.parent.type == 'param':
        return 'param' + node.value

    if node.type in ['operator', 'keyword']:
        return node.value

    return node.type


space_after = """
,
class
def
for
param,
""".strip().split('\n')

space_around = """
in
+
+=
-
-=
*
*=
/
/=
**
**=
~
~=
^
^=
&
&=
=
""".strip().split('\n')

no_space_around = """: ( ) .""".strip().split('\n')


prefix_and_suffix_by_key = dict(
    **{k: ('', ' ') for k in space_after},
    **{k: (' ', ' ') for k in space_around},
    **{k: ('', '') for k in no_space_around},
)


suffix_by_type_and_value = {
    ('operator', '*'): '',
}


def check_same_but_different_prefix(a: Node, b: Node, indent=0):
    assert hasattr(a, 'prefix') == hasattr(b, 'prefix')
    assert hasattr(a, 'children') == hasattr(b, 'children')
    assert hasattr(a, 'value') == hasattr(b, 'value')

    if hasattr(a, 'prefix') and a.type != 'newline':
        assert a.prefix != b.prefix
        print(repr(b.prefix), indent, b.type, b.value, key_for_node(b))

    assert a.type == b.type

    if hasattr(a, 'value'):
        assert a.value == b.value

    if hasattr(a, 'children'):
        if len(a.children) > 2 and a.children[-2].type == 'operator' and a.children[-2].value == ':':
            indent += 1

        assert len(a.children) == len(b.children)
        for ac, bc in zip(a.children, b.children):
            check_same_but_different_prefix(ac, bc, indent=indent)


# check_same_but_different_prefix(parse(too_much_space), parse(nicely_formatted))

parsed = parse(nicely_formatted)


def set_prefix(node, prefix, indent=None):
    parts = list(node._split_prefix())

    if indent is None:
        keep_a_newline = False
        new_parts = []
        for p in parts:
            if p.type == 'comment':
                new_parts.append(p)
                keep_a_newline = True
            elif p.type == 'newline' and keep_a_newline:
                new_parts.append(p)
                keep_a_newline = False

        parts = new_parts

    if not parts or parts[-1].type != 'spacing':
        parts.append(PrefixPart(node, 'spacing', value='', start_pos=node.start_pos))

    if node.get_previous_leaf() and node.get_previous_leaf().type != 'newline':
        # two spaces before inline comments
        for p in parts:
            if p.type == 'comment':
                p.value = '  ' + p.value.strip()
    elif indent:
        # indent comments on their own lines
        for p in parts:
            if p.type == 'comment':
                p.value = ('    ' * indent) + p.value.strip()

    parts[-1].value = prefix
    node.prefix = ''.join(x.value for x in parts)


def reformat_spaces(node: Node, already_handled_prefix_ids=None):
    if already_handled_prefix_ids is None:
        already_handled_prefix_ids = set()

    key = key_for_node(node)
    prefix, suffix = prefix_and_suffix_by_key.get(key, ('', ''))
    if not id(node) in already_handled_prefix_ids:
        if not hasattr(node, 'prefix'):
            assert not prefix
        else:
            set_prefix(node, prefix)

    if suffix:
        right = node.get_next_leaf()
        set_prefix(right, suffix)
        already_handled_prefix_ids.add(id(right))

    if hasattr(node, 'children') and node.children:
        for child in node.children:
            reformat_spaces(child, already_handled_prefix_ids=already_handled_prefix_ids)


def fix_indent(node, indent=0):
    try:
        if hasattr(node, 'prefix') and node.get_previous_leaf().type == 'newline':
            set_prefix(node, indent * '    ', indent=indent)
    except AttributeError:
        # module raises here...
        pass

    if hasattr(node, 'children') and node.children:

        for child in node.children:
            if child.type == 'operator' and child.value == ':':
                indent += 1

            fix_indent(child, indent=indent)


def reformat(source):
    node = parse(source)
    reformat_spaces(node)
    fix_indent(node)
    return node.get_code()


# from json import dumps
#
# def ast_to_dict(node):
#     return {k: v for k, v in dict(
#         type=node.type,
#         value=node.value if hasattr(node, 'value') else None,
#         prefix=node.prefix if hasattr(node, 'prefix') else None,
#         children=[ast_to_dict(x) for x in node.children] if hasattr(node, 'children') else None
#     ).items() if v is not None}
#
#
# print(dumps(ast_to_dict(parsed), indent=4))


print(reformat(nicely_formatted))


assert reformat(nicely_formatted) == reformat(too_much_space)
