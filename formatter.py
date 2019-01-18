from parso import parse
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

         a   ,     *     b
           ,      **
            c
            )       :          # comment3



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

def bar(a, *b, **c):  # comment3
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


def reformat(node: Node, indent=0, already_handled_prefix_ids=None):
    if already_handled_prefix_ids is None:
        already_handled_prefix_ids = set()

    # TODO: handle prefix via _split_prefix to not destroy comments
    # if hasattr(node, 'prefix'):
        # split_prefix = list(node._split_prefix())


    key = key_for_node(node)
    prefix, suffix = prefix_and_suffix_by_key.get(key, ('', ''))
    if not id(node) in already_handled_prefix_ids:
        if not hasattr(node, 'prefix'):
            assert not prefix
        else:
            node.prefix = prefix

    if suffix:
        right = node.get_next_leaf()
        right.prefix = suffix
        already_handled_prefix_ids.add(id(right))

    # TODO: prefix that includes indent
    try:
        if node.get_previous_sibling().type == 'newline':
            node.prefix = indent * '    '
    except AttributeError:
        # module raises here...
        pass

    if hasattr(node, 'children') and node.children:
        if len(node.children) > 2 and node.children[-2].type == 'operator' and node.children[-2].value == ':':
            indent += 1

        for child in node.children:
            reformat(child, indent=indent, already_handled_prefix_ids=already_handled_prefix_ids)

print(parsed)

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

reformat(parsed)


print(parsed.get_code())
