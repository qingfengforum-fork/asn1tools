"""Convert ASN.1 specifications to Python data structures.

"""

import logging

from pyparsing import Literal
from pyparsing import Keyword
from pyparsing import Word
from pyparsing import ZeroOrMore
from pyparsing import Regex
from pyparsing import printables
from pyparsing import delimitedList
from pyparsing import Group
from pyparsing import Optional
from pyparsing import Forward
from pyparsing import StringEnd
from pyparsing import OneOrMore
from pyparsing import alphanums
from pyparsing import nums
from pyparsing import Suppress
from pyparsing import ParseException
from pyparsing import ParseSyntaxException
from pyparsing import NotAny
from pyparsing import NoMatch
from pyparsing import QuotedString
from pyparsing import Combine


LOGGER = logging.getLogger(__name__)


class ParseError(Exception):
    pass


def convert_number(token):
    if isinstance(token, list):
        token = token[0]

    try:
        return int(token)
    except (ValueError, TypeError):
        return token


def convert_size(tokens):
    if len(tokens) == 0:
        return None
    elif '..' in tokens:
        return [(convert_number(tokens[0]),
                 convert_number(tokens[2]))]
    else:
        return [int(tokens[0])]


def convert_table(tokens):
    tokens = tokens[0]

    try:
        if isinstance(tokens[1][0][0], list):
            defined_object_set = tokens[1][0][0][0]
        else:
            defined_object_set = tokens[1][0][0]
    except IndexError:
        return None

    try:
        component_ids = tokens[4]
    except IndexError:
        return defined_object_set

    return [defined_object_set, component_ids]


def convert_enum_values(tokens):
    number = 0
    values = {}

    for token in tokens:
        if len(token) == 2:
            number = int(token[1])

        values[number] = token[0]
        number += 1

    return values


def convert_tag(tokens):
    if len(tokens) > 0:
        if len(tokens[0]) == 1:
            tag = {
                'number': int(tokens[0][0])
            }
        else:
            tag = {
                'number': int(tokens[0][1]),
                'class': tokens[0][0]
            }

        if tokens[1]:
            tag['kind'] = tokens[1][0] if tokens[1] else None

        return tag


def convert_members(tokens):
    members = []

    for member_tokens in tokens:
        if member_tokens in [['...'], '...']:
            member_tokens = [['...', [], ''], []]

        if member_tokens[:2] == ['COMPONENTS', 'OF']:
            continue

        member_tokens, qualifiers = member_tokens
        member = convert_type(member_tokens[2:])
        member['name'] = member_tokens[0]
        member['optional'] = 'OPTIONAL' in qualifiers

        if 'DEFAULT' in qualifiers:
            member['default'] = convert_number(qualifiers[1][0])

        tag = convert_tag(member_tokens[1])

        if tag:
            member['tag'] = tag

        members.append(member)

    return members


def convert_type(tokens):
    if tokens[0:2] == ['SEQUENCE', '{']:
        converted_type = {
            'type': 'SEQUENCE',
            'members': convert_members(tokens[2])
        }
    elif tokens[0] == 'SEQUENCE' and tokens[2] == 'OF':
        converted_type = {
            'type': 'SEQUENCE OF',
            'element': convert_type(tokens[4:]),
            'size': convert_size(tokens[1][2:-1])
        }

        tag = convert_tag(tokens[3])

        if tag:
            converted_type['element']['tag'] = tag
    elif tokens[0:2] == ['SET', '{']:
        converted_type = {
            'type': 'SET',
            'members': convert_members(tokens[2])
        }
    elif tokens[0] == 'SET' and tokens[2] == 'OF':
        converted_type = {
            'type': 'SET OF',
            'element': convert_type(tokens[4:]),
            'size': convert_size(tokens[1][2:-1])
        }

        tag = convert_tag(tokens[3])

        if tag:
            converted_type['element']['tag'] = tag
    elif tokens[0:2] == ['CHOICE', '{']:
        converted_type = {
            'type': 'CHOICE',
            'members': convert_members(tokens[2])
        }
    elif tokens[0] == 'INTEGER':
        converted_type = {'type': 'INTEGER'}
        restricted_to = []

        if len(tokens) > 2:
            for constraint_tokens in tokens[2]:
                if '..' == constraint_tokens[1]:
                    minimum = convert_number(constraint_tokens[0])
                    maximum = convert_number(constraint_tokens[2])
                    restricted_to.append((minimum, maximum))

            if restricted_to:
                converted_type['restricted-to'] = restricted_to
    elif tokens[0:2] == ['ENUMERATED', '{']:
        converted_type = {
            'type': 'ENUMERATED',
            'values': convert_enum_values(tokens[2])
        }
    elif tokens[0:1] == ['OBJECT IDENTIFIER']:
        converted_type = {'type': 'OBJECT IDENTIFIER'}
    elif tokens[0:1] == ['BIT STRING']:
        converted_type = {'type': 'BIT STRING',
                          'size': convert_size(tokens[2][2:-1])}
    elif tokens[0:1] == ['OCTET STRING']:
        converted_type = {'type': 'OCTET STRING',
                          'size': convert_size(tokens[1][2:-1])}
    elif tokens[0] == 'IA5String':
        converted_type = {'type': 'IA5String'}
    elif tokens[0:3] == ['ANY', 'DEFINED', 'BY']:
        converted_type = {
            'type': 'ANY DEFINED BY',
            'value': tokens[3],
            'choices': {}
        }
    elif '&' in tokens[0]:
        converted_type = {
            'type': tokens[0],
            'table': convert_table(tokens[1:])
        }
    else:
        converted_type = {'type': tokens[0]}

    return converted_type


def convert_type_tokens(tokens):
    converted_type = convert_type(tokens[3:])
    tag = convert_tag(tokens[2])

    if tag:
        converted_type['tag'] = tag

    return converted_type


def convert_value_tokens(tokens):
    type_ = tokens[1][0]

    if type_ == 'INTEGER':
        value_type = 'INTEGER'
        value = int(tokens[3][0])
    elif type_ == 'OBJECT IDENTIFIER':
        value_type = 'OBJECT IDENTIFIER'
        value = []

        for value_tokens in tokens[3]:
            if len(value_tokens) == 2:
                value.append((value_tokens[0], int(value_tokens[1])))
            else:
                value.append(convert_number(value_tokens[0]))
    else:
        value_type = type_
        value = tokens[3]

    return {'type': value_type, 'value': value}


def convert_object_class_tokens(tokens):
    members = []

    for member in tokens[3]:
        if member[0][1].islower():
            type_ = member[1]
        else:
            type_ = 'OpenType'

        members.append({
            'name': member[0],
            'type': type_,
            'optional': False
        })

    return {'members': members}


def convert_object_set_tokens(tokens):
    members = []
    for member_tokens in tokens[4]:
        if len(member_tokens[0]) == 1:
            member = member_tokens[0][0]
        else:
            for item_tokens in member_tokens[0]:
                member = {}

                for item_tokens in member_tokens[0]:
                    name = item_tokens[0]
                    value = item_tokens[1]
                    member[name] = convert_number(value)

        members.append(member)

    return {'class': tokens[1], 'members': members}


def create_grammar():
    '''Return the ASN.1 grammar as Pyparsing objects.

    '''

    # Keywords.
    SEQUENCE = Keyword('SEQUENCE').setName('SEQUENCE')
    CHOICE = Keyword('CHOICE').setName('CHOICE')
    ENUMERATED = Keyword('ENUMERATED').setName('ENUMERATED')
    DEFINITIONS = Keyword('DEFINITIONS').setName('DEFINITIONS')
    BEGIN = Keyword('BEGIN').setName('BEGIN')
    END = Keyword('END').setName('END')
    AUTOMATIC = Keyword('AUTOMATIC').setName('AUTOMATIC')
    TAGS = Keyword('TAGS').setName('TAGS')
    OPTIONAL = Keyword('OPTIONAL').setName('OPTIONAL')
    OF = Keyword('OF').setName('OF')
    SIZE = Keyword('SIZE').setName('SIZE')
    INTEGER = Keyword('INTEGER').setName('INTEGER')
    REAL = Keyword('REAL').setName('REAL')
    BIT_STRING = Keyword('BIT STRING').setName('BIT STRING')
    OCTET_STRING = Keyword('OCTET STRING').setName('OCTET STRING')
    DEFAULT = Keyword('DEFAULT').setName('DEFAULT')
    IMPORTS = Keyword('IMPORTS').setName('IMPORTS')
    EXPORTS = Keyword('EXPORTS').setName('EXPORTS')
    FROM = Keyword('FROM').setName('FROM')
    CONTAINING = Keyword('CONTAINING').setName('CONTAINING')
    IMPLICIT = Keyword('IMPLICIT').setName('IMPLICIT')
    EXPLICIT = Keyword('EXPLICIT').setName('EXPLICIT')
    OBJECT_IDENTIFIER = Keyword('OBJECT IDENTIFIER').setName('OBJECT IDENTIFIER')
    IDENTIFIER = Keyword('IDENTIFIER').setName('IDENTIFIER')
    APPLICATION = Keyword('APPLICATION').setName('APPLICATION')
    PRIVATE = Keyword('PRIVATE').setName('PRIVATE')
    SET = Keyword('SET').setName('SET')
    ANY = Keyword('ANY').setName('ANY')
    DEFINED = Keyword('DEFINED').setName('DEFINED')
    BY = Keyword('BY').setName('BY')
    EXTENSIBILITY = Keyword('EXTENSIBILITY').setName('EXTENSIBILITY')
    IMPLIED = Keyword('IMPLIED').setName('IMPLIED')
    BOOLEAN = Keyword('BOOLEAN').setName('BOOLEAN')
    TRUE = Keyword('TRUE').setName('TRUE')
    FALSE = Keyword('FALSE').setName('FALSE')
    CLASS = Keyword('CLASS').setName('CLASS')
    WITH = Keyword('WITH').setName('WITH')
    SYNTAX = Keyword('SYNTAX').setName('SYNTAX')
    UNIQUE = Keyword('UNIQUE').setName('UNIQUE')
    NULL = Keyword('NULL').setName('NULL')
    COMPONENT = Keyword('COMPONENT').setName('COMPONENT')
    COMPONENTS = Keyword('COMPONENTS').setName('COMPONENTS')
    PRESENT = Keyword('PRESENT').setName('PRESENT')
    ABSENT = Keyword('ABSENT').setName('ABSENT')
    ALL = Keyword('ALL').setName('ALL')
    MIN = Keyword('MIN').setName('MIN')
    MAX = Keyword('MAX').setName('MAX')

    # Various literals.
    word = Word(printables, excludeChars=',(){}[].:=;"|').setName('word')
    identifier = Regex(r'[a-z][a-zA-Z0-9-]*').setName('identifier')
    value_name = Word(alphanums + '-')
    assign = Literal('::=').setName('::=')
    lparen = Literal('(')
    rparen = Literal(')')
    lbrace = Literal('{')
    rbrace = Literal('}')
    lbracket = Literal('[')
    rbracket = Literal(']')
    colon = Literal(':')
    scolon = Literal(';')
    dot = Literal('.')
    range_separator = Literal('..')
    ellipsis = Literal('...')
    left_version_brackets = Literal('[[')
    right_version_brackets = Literal(']]')
    qmark = Literal('"')
    pipe = Literal('|')
    comma = Literal(',')
    at = Literal('@')
    integer = Word(nums)
    real_number = Regex(r'[+-]?\d+\.?\d*([eE][+-]?\d+)?')
    bstring = Regex(r"'[01\s]*'B")
    hstring = Regex(r"'[0-9A-F\s]*'H")
    cstring = NoMatch().setName('"cstring" not implemented')
    number = word
    ampersand = Literal('&')
    less_than = Literal('<')

    # Forward declarations.
    value = Forward()
    type_ = Forward()
    object_ = Forward()
    object_set = Forward()
    primitive_field_name = Forward()
    constraint = Forward()
    element_set_spec = Forward()
    token_or_group_spec = Forward()
    value_reference = Forward().setName('valuereference')
    type_reference = Forward().setName('typereference')
    value_set = Forward().setName('"valueSet" not implemented')
    named_type = Forward()
    root_element_set_spec = Forward()
    defined_object_set = Forward()
    syntax_list = Forward()
    object_from_object = Forward()
    object_set_from_objects = Forward()
    defined_value = Forward()
    component_type_lists = Forward()
    extension_and_exception = Forward()
    optional_extension_marker = Forward()

    value_field_reference = Combine(ampersand + value_reference)
    type_field_reference = Combine(ampersand + type_reference)

    range_ = (word + range_separator + word)

    size = (SIZE
            + lparen
            + delimitedList(range_ | word, delim=pipe)
            + rparen)

    size_paren = (Suppress(Optional(lparen))
                  + size
                  + Suppress(Optional(rparen)))

    parameterized_object = NoMatch().setName('"parameterizedObject" not implemented')
    actual_parameter_list = Group(Suppress(lbrace)
                                  + delimitedList(
                                      Group((value_field_reference
                                             | type_field_reference)
                                            + (word
                                               | QuotedString('"'))))
                                  + Suppress(rbrace))
    parameterized_object_set = NoMatch().setName('"parameterizedObjectSet" not implemented')
    # actual_parameter_list

    tag = Group(Optional(Suppress(lbracket)
                         + Group(Optional(APPLICATION | PRIVATE) + word)
                         + Suppress(rbracket)
                         + Group(Optional(IMPLICIT | EXPLICIT))))

    parameterized_object_class = NoMatch().setName('"parameterizedObjectClass" not implemented')

    any_defined_by_type = (ANY + DEFINED + BY + word)
    any_defined_by_type.setName('ANY DEFINED BY')

    oid = (Suppress(lbrace)
           + ZeroOrMore(Group((value_name
                               + Suppress(lparen)
                               + word
                               + Suppress(rparen))
                              | word))
           + Suppress(rbrace))

    identifier_list = delimitedList(identifier)

    # X.682: 8. General constant specification
    # X.682: 8. General constant specification
    # X.682: 8. General constant specification
    # X.682: 8. General constant specification
    # X.682: 8. General constant specification
    # X.682: 8. General constant specification

    # X.682: 11. Contents constraints
    contents_constraint = NoMatch().setName('"contentsConstraint" not implemented')

    # X.682: 10. Table constraints, including component relation constraints
    level = OneOrMore(dot)
    component_id_list = identifier
    at_notation = (Suppress(at)
                   - (component_id_list
                      | Combine(level + component_id_list)))
    component_relation_constraint = (lbrace
                                     + Group(Group(defined_object_set))
                                     + rbrace
                                     + lbrace
                                     - Group(delimitedList(at_notation))
                                     - rbrace)
    simple_table_constraint = object_set
    table_constraint = (component_relation_constraint
                        | simple_table_constraint)

    # X.682: 9. User-defined constants
    user_defined_constraint = NoMatch().setName('"userDefinedConstraint" not implemented')

    # X.682: 8. General constraint specification
    general_constraint = (user_defined_constraint
                          | table_constraint
                          | contents_constraint)

    # X.681: 7. ASN.1 lexical items
    object_set_reference = type_reference
    value_set_field_reference = NoMatch().setName('"valueSetFieldReference" not implemented')
    object_field_reference = NoMatch().setName('"objectFieldReference" not implemented')
    object_set_field_reference = NoMatch().setName('"objectSetFieldReference" not implemented')
    object_class_reference = type_reference
    object_reference = value_reference

    # X.681: 8. Referencing definitions
    external_object_set_reference = NoMatch().setName('"externalObjectSetReference" not implemented')
    defined_object_set <<= (external_object_set_reference
                            | object_set_reference)
    defined_object = NoMatch().setName('"definedObject" not implemented')
    defined_object_class = object_class_reference

    # X.681: 9. Information object class definition and assignment
    field_name = primitive_field_name
    primitive_field_name <<= (type_field_reference
                              | value_field_reference
                              | value_set_field_reference
                              | object_field_reference
                              | object_set_field_reference)
    object_set_field_spec = NoMatch().setName('"objectSetFieldSpec" not implemented')
    object_field_spec = NoMatch().setName('"objectFieldSpec" not implemented')
    variable_type_value_set_field_spec = NoMatch().setName(
        '"variableTypeValueSetFieldSpec" not implemented')
    fixed_type_value_set_field_spec = NoMatch().setName('"fixedTypeValueSetFieldSpec" not implemented')
    variable_type_value_field_spec = NoMatch().setName('"variableTypeValueFieldSpec" not implemented')
    fixed_type_value_field_spec = (value_field_reference
                                   + type_
                                   + Optional(UNIQUE)
                                   + Optional(OPTIONAL
                                              | (DEFAULT - type_)))
    type_field_spec = (type_field_reference
                       + Optional(OPTIONAL
                                  | (DEFAULT - type_)))
    field_spec = Group(type_field_spec
                       | fixed_type_value_field_spec
                       | variable_type_value_field_spec
                       | fixed_type_value_set_field_spec
                       | variable_type_value_set_field_spec
                       | object_field_spec
                       | object_set_field_spec)
    with_syntax_spec = (WITH + SYNTAX + syntax_list)
    object_class_defn = (CLASS
                         - Suppress(lbrace)
                         - Group(delimitedList(field_spec))
                         - Suppress(rbrace)
                         - Optional(with_syntax_spec))
    object_class = (object_class_defn
                    # | defined_object_class
                    | parameterized_object_class)
    object_class_assignment = (object_class_reference
                               + assign
                               + object_class)

    # X.681: 10. Syntax list
    literal = NoMatch().setName('"literal" not implemented')
    required_token = (literal | primitive_field_name)
    optional_group = (lbracket
                      + token_or_group_spec
                      + rbracket)
    token_or_group_spec <<= (required_token | optional_group)
    syntax_list <<= (lbrace
                     + OneOrMore(token_or_group_spec)
                     + rbrace)

    # X.681: 11. Information object definition and assignment
    setting = (type_ | value | value_set | object_ | object_set | QuotedString('"'))
    field_setting =  Group(primitive_field_name + setting)
    default_syntax = (Suppress(lbrace)
                      + delimitedList(field_setting)
                      + Suppress(rbrace))
    defined_syntax = NoMatch().setName('"definedSyntax" not implemented')
    object_defn = Group(default_syntax | defined_syntax)
    object_ <<= (defined_object
                 | object_defn
                 | object_from_object
                 | parameterized_object)
    object_assignment = (object_reference
                         + Group(defined_object_class)
                         + assign
                         + object_)

    # X.681: 12. Information object set definition and assignment
    object_set_elements = (object_
                           | defined_object_set
                           | object_set_from_objects
                           | parameterized_object_set)
    object_set_spec = delimitedList(root_element_set_spec)
    object_set <<= (lbrace + Group(object_set_spec) + rbrace)
    object_set_assignment = (object_set_reference
                             + defined_object_class
                             - assign
                             - object_set)

    # X.681: 13. Associated tables

    # X.681: 14. Notation for the object class field type
    object_class_field_value = oid
    object_class_field_type = Combine(defined_object_class
                                      + dot
                                      + field_name)
    object_class_field_type.setName('ObjectClassFieldType')

    # X.681: 15. Information from objects
    object_set_from_objects <<= NoMatch().setName('"objectSetFromObjects" not implemented')
    object_from_object <<= NoMatch().setName('"objectFromObject" not implemented')

    # X.680: 49. The exception identifier
    exception_spec = NoMatch().setName('"exceptionSpec" not implemented')

    # X.680: 47. Subtype elements
    pattern_constraint = NoMatch().setName('"patternConstraint" not implemented')
    value_constraint = constraint
    presence_constraint = (PRESENT | ABSENT | OPTIONAL)
    component_constraint = Optional(value_constraint | presence_constraint)
    named_constraint = (identifier + component_constraint)
    type_constraints = delimitedList(named_constraint)
    full_specification = (lbrace + type_constraints + rbrace)
    partial_specification = (lbrace + ellipsis + comma + type_constraints + rbrace)
    single_type_constraint = constraint
    multiple_type_constraints = (full_specification | partial_specification)
    inner_type_constraints = ((WITH + COMPONENT + single_type_constraint)
                              | (WITH + COMPONENTS + multiple_type_constraints))
    permitted_alphabet = Suppress(FROM
                                  + delimitedList(qmark + word + qmark
                                                  + range_separator
                                                  + qmark + word + qmark,
                                                  delim=pipe))
    type_constraint = NoMatch().setName('"typeConstraint" not implemented')
    size_constraint = NoMatch().setName('"sizeConstraint" not implemented')
    upper_end_value = (value | MAX)
    lower_end_value = (value | MIN)
    upper_endpoint = (Optional(less_than) + upper_end_value)
    lower_endpoint = (lower_end_value + Optional(less_than))
    value_range = (lower_endpoint + range_separator + upper_endpoint)
    contained_subtype = NoMatch().setName('"containedSubtype" not implemented')
    single_value = value
    subtype_elements = (contained_subtype
                        | size_constraint
                        | permitted_alphabet
                        | value_range
                        | type_constraint
                        | inner_type_constraints
                        | single_value
                        | pattern_constraint)

    # X.680: 46. Element set specification
    elements = Group(subtype_elements
                     | object_set_elements
                     | (lparen + element_set_spec + rparen))
    intersections = elements
    unions = delimitedList(intersections, delim=pipe)
    element_set_spec <<= unions
    root_element_set_spec <<= element_set_spec
    root_element_set_specs = root_element_set_spec
    element_set_specs = root_element_set_specs

    # X.680: 45. Constrained types
    subtype_constraint = element_set_specs
    constraint_spec = (size
                       | general_constraint
                       | subtype_constraint)
    constraint <<= (Suppress(lparen)
                    + constraint_spec
                    + Suppress(rparen))

    # X.680: 40. Definition of unrestricted character string types
    unrestricted_character_string_value = NoMatch().setName(
        '"unrestrictedCharacterStringValue" not implemented')

    # X.680: 39. Canonical order of characters

    # X.680: 38. Specification of the ASN.1 module "ASN.1-CHARACTER-MODULE"

    # X.680: 37. Definition of restricted character string types
    group = number
    plane = number
    row = number
    cell = number
    quadruple = (lbrace
                 + group + comma
                 + plane + comma
                 + row + comma +
                 cell
                 + rbrace)
    table_column = number
    table_row = number
    tuple_ = (lbrace + table_column + comma + table_row + rbrace)
    charsyms = NoMatch().setName('"charsyms" not implemented')
    character_string_list = (lbrace + charsyms + rbrace)
    restricted_character_string_value = (cstring
                                         | character_string_list
                                         | quadruple
                                         | tuple_)

    # X.680: 36. Notation for character string types
    character_string_value = (restricted_character_string_value
                              | unrestricted_character_string_value)

    # X.680: 35. The character string types

    # X.680: 34. Notation for the external type

    # X.680: 33. Notation for embedded-pdv type

    # X.680: 32. Notation for relative object identifier type

    # X.680: 31. Notation for object identifier type
    object_identifier_type = (OBJECT_IDENTIFIER
                              + Optional(lparen
                                         + delimitedList(word, delim='|')
                                         + rparen))
    object_identifier_type.setName('OBJECT IDENTIFIER')
    object_identifier_value = oid

    # X.680: 30. Notation for tagged types

    # X.680: 29. Notation for selection types

    # X.680: 28. Notation for the choice types
    choice_type = (CHOICE
                   - lbrace
                   + Group(Optional(delimitedList(
                       Group(Group(identifier
                                   - tag
                                   - type_)
                             + Group(Optional(OPTIONAL)
                                     + Optional(DEFAULT + word))
                             | ellipsis))))
                   - rbrace)
    choice_type.setName('CHOICE')
    choice_value = (identifier + colon + value)

    # X.680: 27. Notation for the set-of types
    set_of_type = (SET
                   + Group(Optional(size))
                   + OF
                   + Optional(Suppress(identifier))
                   - tag
                   - type_)
    set_of_type.setName('SET OF')

    # X.680: 26. Notation for the set types
    set_type = (SET
                - lbrace
                + Group(Optional(component_type_lists
                                 | (extension_and_exception
                                    + optional_extension_marker)))
                - rbrace)
    set_type.setName('SET')

    # X.680: 25. Notation for the sequence-of types
    sequence_of_type = (SEQUENCE
                        + Group(Optional(size_paren))
                        + OF
                        + Optional(Suppress(identifier))
                        - tag
                        - type_)
    sequence_of_type.setName('SEQUENCE OF')

    # X.680: 24. Notation for the sequence types
    component_type = Group(named_type
                           + Group(Optional(OPTIONAL
                                            | (DEFAULT + value)))
                           | (COMPONENTS + OF + type_))
    version_number = (number + Suppress(colon))
    extension_addition_group = (Suppress(left_version_brackets)
                                + Suppress(Group(Optional(version_number)))
                                + delimitedList(component_type)
                                + Suppress(right_version_brackets))
    extension_and_exception <<= (ellipsis + Optional(exception_spec))
    extension_addition = (component_type | extension_addition_group)
    extension_addition_list = delimitedList(extension_addition)
    extension_additions = Optional(Suppress(comma) + extension_addition_list)
    extension_end_marker = (Suppress(comma) + ellipsis)
    optional_extension_marker <<= Optional(Suppress(comma) + ellipsis)
    component_type_list = delimitedList(component_type)
    root_component_type_list = component_type_list
    component_type_lists <<= ((root_component_type_list
                               + Optional(Suppress(comma)
                                          + extension_and_exception
                                          + extension_additions
                                          + ((extension_end_marker
                                              + Suppress(comma)
                                              + root_component_type_list)
                                             | optional_extension_marker)))
                              | (extension_and_exception
                                 + extension_additions
                                 + ((extension_end_marker
                                     + Suppress(comma)
                                     + root_component_type_list)
                                    | optional_extension_marker)))
    sequence_type = (SEQUENCE
                     - lbrace
                     + Group(Optional(component_type_lists
                                    | (extension_and_exception
                                       + optional_extension_marker)))
                     - rbrace)
    sequence_type.setName('SEQUENCE')

    # X.680: 23. Notation for the null type
    null_type = NULL

    # X.680: 22. Notation for the octetstring type
    octet_string_type = (OCTET_STRING
                         + Group(Optional(Suppress(lparen)
                                          + (size | (CONTAINING + word))
                                          + Suppress(rparen))))
    octet_string_type.setName('OCTET STRING')

    # X.680: 21. Notation for the bitstring type
    bit_string_type = (BIT_STRING
                       + Group(Optional(lbrace
                                        + Group(delimitedList(word
                                                              + lparen
                                                              + word
                                                              + rparen))
                                        + rbrace)))
    bit_string_type.setName('BIT STRING')
    bit_string_value = (bstring
                        | hstring
                        | (lbrace + Optional(identifier_list) + rbrace)
                        | (CONTAINING - value))

    # X.680: 20. Notation for the real type
    real_type = (REAL
                 + Optional(lparen
                            + ((integer + dot + range_separator)
                               | (integer + range_separator)
                               | (real_number + range_separator))
                            + real_number
                            + rparen))
    real_type.setName('REAL')

    # X.680: 19. Notation for the enumerated type
    enumerated_type = (ENUMERATED
                       - lbrace
                       + Group(delimitedList(Group((word
                                                    + Optional(Suppress(lparen)
                                                               + word
                                                               + Suppress(rparen)))
                                                   | ellipsis)))
                       - rbrace)
    enumerated_type.setName('ENUMERATED')

    # X.680: 18. Notation for the integer type
    signed_number = number
    named_number = (identifier
                    + lparen
                    + (signed_number | defined_value)
                    + rparen)
    named_number_list = delimitedList(named_number)
    integer_type = (INTEGER
                    + Group(Optional(lbrace
                                     + named_number_list
                                     + rbrace)))
    integer_type.setName('INTEGER')

    # X.680: 17. Notation for boolean type
    boolean_type = BOOLEAN
    boolean_value = (TRUE | FALSE)

    # X.680: 16. Definition of types and values
    referenced_value = NoMatch().setName('"referencedValue" not implemented')
    builtin_value = (bit_string_value
                     | boolean_value
                     | character_string_value
                     | choice_value
                     | word)
    value <<= Group(object_class_field_value
                    | referenced_value
                    | builtin_value)
    named_type <<= Group(identifier
                         - tag
                         - type_)
    referenced_type = type_reference
    referenced_type.setName('ReferencedType')
    builtin_type = (choice_type
                    | integer_type
                    | null_type
                    | real_type
                    | bit_string_type
                    | octet_string_type
                    | enumerated_type
                    | sequence_of_type
                    | sequence_type
                    | object_class_field_type
                    | set_of_type
                    | set_type
                    | object_identifier_type
                    | boolean_type)
    type_ <<= ((builtin_type
                | any_defined_by_type
                | referenced_type)
               + Group(Optional(constraint)))

    # X.680: 15. Assigning types and values
    type_reference <<= (NotAny(END) + Regex(r'[A-Z][a-zA-Z0-9-]*'))
    value_reference <<= Regex(r'[a-z][a-zA-Z0-9-]*')
    value_set <<= NoMatch().setName('"valueSet" not implemented')
    type_assignment = (type_reference
                       - assign
                       - tag
                       - type_)
    value_assignment = (value_reference
                        - Group(INTEGER
                                | type_)
                        - assign
                        - value)

    # X.680: 14. Notation to support references to ASN.1 components

    # X.680: 13. Referencing type and value definitions
    defined_value <<= value_reference

    # X.680: 12. Module definition
    module_reference = word
    assigned_identifier = Suppress(Optional(object_identifier_value
                                            | (defined_value + ~comma)))
    global_module_reference = (module_reference + assigned_identifier)
    symbol_list = Group(delimitedList(word))
    symbols_from_module = (symbol_list
                           + FROM
                           + global_module_reference)
    symbols_imported = OneOrMore(Group(symbols_from_module))
    imports = Group(Optional(IMPORTS
                             - symbols_imported
                             - scolon))
    symbols_exported = OneOrMore(symbol_list)
    exports = Suppress(Group(Optional(EXPORTS
                                      - (ALL
                                         | (symbols_exported + scolon)))))
    assignment = Group(object_set_assignment
                       | object_assignment
                       | object_class_assignment
                       | type_assignment
                       | value_assignment)
    assignment_list = Group(ZeroOrMore(assignment))
    module_body = (exports + imports + assignment_list)
    definitive_identification = Group(Optional(oid))
    module_identifier = (module_reference + definitive_identification)
    tag_default = Group(Optional((AUTOMATIC | EXPLICIT | IMPLICIT) + TAGS))
    extension_default = Group(Optional(EXTENSIBILITY + IMPLIED))
    module_definition = Group(Group(module_identifier
                                    - DEFINITIONS
                                    + tag_default
                                    + extension_default
                                    - assign
                                    - BEGIN)
                              + module_body
                              - END)

    # The whole specification.
    specification = OneOrMore(module_definition) + StringEnd()
    comment = (Regex(r"--[\s\S]*?(--|\n)") | Regex(r"--(?:\\\n|[^\n])*"))
    specification.ignore(comment)

    return specification


def parse_string(string):
    """Parse given ASN.1 specification string and return a dictionary of
    its contents.

    >>> with open('foo.asn') as fin:
    ...     foo = asn1tools.parse_string(fin.read())

    """

    grammar = create_grammar()

    try:
        tokens = grammar.parseString(string).asList()
    except (ParseException, ParseSyntaxException) as e:
        raise ParseError("Invalid ASN.1 syntax at line {}, column {}: '{}': {}.".format(
            e.lineno,
            e.column,
            e.markInputline(),
            e.msg))

    modules = {}

    for module in tokens:
        module_name = module[0][0]

        LOGGER.debug("Found module '%s'.", module_name)

        imports = {}
        types = {}
        values = {}
        object_classes = {}
        object_sets = {}

        imports_tokens = module[1]

        if imports_tokens:
            for from_tokens in imports_tokens[1:-1]:
                from_name = from_tokens[2]
                LOGGER.debug("Found imports from '%s'.", from_name)
                imports[from_name] = from_tokens[0]

        assignment_tokens = module[2]

        for assignment in assignment_tokens:
            name = assignment[0]

            if name[0].isupper():
                if assignment[1:3] == ['::=', 'CLASS']:
                    LOGGER.debug("Found object class '%s'.", name)
                    object_classes[name] = convert_object_class_tokens(assignment)
                elif assignment[2:4] == ['::=', '{']:
                    LOGGER.debug("Found object set '%s'.", name)
                    object_sets[name] = convert_object_set_tokens(assignment)
                else:
                    LOGGER.debug("Found type '%s'.", name)
                    types[name] = convert_type_tokens(assignment)
            else:
                LOGGER.debug("Found value '%s'.", name)
                values[name] = convert_value_tokens(assignment)

        modules[module_name] = {
            'imports': imports,
            'types': types,
            'values': values,
            'object-classes': object_classes,
            'object-sets': object_sets
        }

        if module[0][3]:
            modules[module_name]['tags'] = module[0][3][0]

        modules[module_name]['extensibility-implied'] = (module[0][4] != [])

    return modules


def parse_files(filenames):
    """Parse given ASN.1 specification file(s) and return a dictionary of
    its/their contents.

    >>> foo = asn1tools.parse_files('foo.asn')

    """

    if isinstance(filenames, str):
        filenames = [filenames]

    string = ''

    for filename in filenames:
        with open(filename, 'r') as fin:
            string += fin.read()
            string += '\n'

    return parse_string(string)
