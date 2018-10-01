# Coding style

## Table of contents

* [Introduction](#introduction)
* [Indentation](#indentation)
* [Imports](#imports)
* [import_module vs from x import y](#import_module)

## <a name="introduction"></a>Introduction

We enforce coding style and consistency with [flake8](http://flake8.pycqa.org/en/latest/) which is automatically installed when you run ``pip install -r requirements.txt``.

You can run ``flake8 .`` anytime or install a [pre-commit hook](http://flake8.pycqa.org/en/latest/user/using-hooks.html#using-version-control-hooks) to check against our coding style.

Not everything is covered by flake8 though so you should also make sure you read and understand this guide.

We follow [PEP8](https://www.python.org/dev/peps/pep-0008/) but this guide takes precedence and sets agreed conventions when different acceptable options exist.

Consistency is very important; if you are making agreed changes to this guide always refactor the existing code to keep it consistent.

## <a name="indentation"></a>Indentation

Use four space hanging indentation rather than vertical alignment:

Yes:
```
foo = long_function_name(
    var_one,
    var_two,
    var_three,
    var_four,
)

my_list = [
    1,
    2,
    3,
    4,
    5,
    6,
]
```

No:
```
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

foo = long_function_name(
    var_one, var_two,
    var_three, var_four,
)

foo = long_function_name(
        var_one,
        var_two,
        var_three,
        var_four,
    )

def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)

foo = long_function_name(
    var_one, var_two,
    var_three, var_four)

my_list = [
    1, 2, 3,
    4, 5, 6,
    ]
```

## <a name="imports"></a>Imports

We follow PEP8 recommendations and always use absolute imports as they are more readable and tend to be better behaved.

Never use relative imports.

Yes:
```
from datahub.core.models import BaseModel
```

No:
```
from .models import BaseModel
```

## <a name="import_module"></a>import_module vs from x import y

If you need to import another module just to make some django magic work use ``import_module``.

E.g. ``datahub/company/admin/__init__.py``
```
from importlib import import_module

import_module('datahub.company.admin.adviser')  # makes AdviserAdmin discoverable
```

If you really want to encapsulate some logic and split things into different files just to make the implementation more maintanable, use ``from x import y`` and ``__all__ = ('y', )``.

E.g. ``datahub/core/validators/__init__.py``
```
from datahub.core.validators.address import AddressValidator

__all__ = (
    'AddressValidator',
)
```

If you are not sure, think about how you would like the inner module to be imported from a different place in the codebase.
If you don't want to announce the existence of the inner module (e.g. ``from datahub.core.validators import AddressValidator``), you probably want to use ``from x import y``.
