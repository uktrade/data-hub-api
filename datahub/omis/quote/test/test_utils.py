from decimal import Decimal
from pathlib import PurePath
from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.core.constants import Country
from datahub.omis.order.constants import VATStatus
from datahub.omis.order.test.factories import (
    HourlyRateFactory,
    OrderAssigneeFactory,
    OrderFactory,
)
from datahub.omis.quote.utils import (
    calculate_quote_expiry_date,
    escape_markdown,
    generate_quote_content,
    generate_quote_reference,
)


COMPILED_QUOTE_TEMPLATE = PurePath(__file__).parent / 'support/compiled_content.md'


@pytest.mark.django_db
class TestGenerateQuoteReference:
    """Tests for the generate_quote_reference logic."""

    @mock.patch('datahub.omis.quote.utils.get_random_string')
    def test_reference(self, get_random_string):
        """Test that the quote reference is generated as expected."""
        get_random_string.side_effect = ['DE', 4]

        order = mock.Mock(
            reference='ABC123',
        )

        reference = generate_quote_reference(order)
        assert reference == 'ABC123/Q-DE4'


@pytest.mark.django_db
class TestGenerateQuoteContent:
    """Tests for the generate_quote_content logic."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_content(self):
        """Test that the quote content is populated as expected."""
        hourly_rate = HourlyRateFactory(rate_value=1250, vat_value=Decimal(17.5))
        company = CompanyFactory(
            name='My *Coorp',
            registered_address_1='line 1',
            registered_address_2='*line 2',
            registered_address_town='London',
            registered_address_county='County',
            registered_address_postcode='SW1A 1AA',
            registered_address_country_id=Country.united_kingdom.value.id,
            company_number='123456789',
        )
        contact = ContactFactory(
            company=company,
            first_name='John',
            last_name='*Doe',
        )
        order = OrderFactory(
            delivery_date=dateutil_parse('2017-06-20'),
            company=company,
            contact=contact,
            reference='ABC123',
            primary_market_id=Country.france.value.id,
            description='lorem *ipsum',
            discount_value=100,
            hourly_rate=hourly_rate,
            assignees=[],
            vat_status=VATStatus.UK,
            contact_email='contact-email@mycoorp.com',
        )
        OrderAssigneeFactory(
            order=order,
            adviser=AdviserFactory(
                first_name='Foo',
                last_name='*Bar',
            ),
            estimated_time=150,
            is_lead=True,
        )

        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date(),
        )
        with open(COMPILED_QUOTE_TEMPLATE, 'r', encoding='utf-8') as f:
            expected_content = f.read()

        assert content == expected_content

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_minimal_address(self):
        """
        Test that if the company address doesn't have line2, county and country
        it's formatted correctly.
        """
        company = CompanyFactory(
            address_1='line 1',
            address_2='',
            address_town='London',
            address_county='',
            address_postcode='SW1A 1AA',
            address_country_id=None,

            registered_address_1='',
            registered_address_2='',
            registered_address_town='',
            registered_address_county='',
            registered_address_postcode='',
            registered_address_country_id=None,
        )
        order = OrderFactory(
            company=company,
            contact=ContactFactory(company=company),
        )
        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date(),
        )

        assert 'line 1, London, SW1A 1AA' in content

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_pricing_format(self):
        """Test that the pricing is formatted as expected (xx.yy)"""
        hourly_rate = HourlyRateFactory(rate_value=1250, vat_value=Decimal(20))
        order = OrderFactory(
            discount_value=0,
            hourly_rate=hourly_rate,
            assignees=[],
            vat_status=VATStatus.UK,
        )
        OrderAssigneeFactory(
            order=order,
            estimated_time=120,
            is_lead=True,
        )

        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date(),
        )

        assert '25.00' in content


class TestCalculateQuoteExpiryDate:
    """Tests for the calculate_quote_expiry_date logic."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_delivery_date_in_far_future(self):
        """
        Now = 18/04/2017
        delivery date = 20/06/2017 (in 2 months)

        Therefore expiry date = 18/05/2017 (in 30 days)
        """
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-06-20').date(),
        )
        expiry_date = calculate_quote_expiry_date(order)
        assert expiry_date == dateutil_parse('2017-05-18').date()

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_close_delivery_date(self):
        """
        Now = 18/04/2017
        delivery date = 11/05/2017 (in 23 days)

        Therefore expiry date = 20/04/2017 (in 2 days)
        """
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-05-11').date(),
        )
        expiry_date = calculate_quote_expiry_date(order)
        assert expiry_date == dateutil_parse('2017-04-20').date()

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_too_close_delivery_date(self):
        """
        Now = 18/04/2017
        delivery date = 08/05/2017 (in 20 days)

        Therefore expiry date would be passed so an exception is raised.
        """
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-05-08').date(),
        )

        with pytest.raises(ValidationError):
            calculate_quote_expiry_date(order)


class TestEscapeMarkdown:
    """Tests for the escape_markdown logic."""

    CONTENT = r"""# noqa: E501
from https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet

    Headers

# H1
## H2
### H3
#### H4
##### H5
###### H6

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------

    Emphasis

Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

    Lists

1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list.
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses

    Links

[I'm an inline-style link](https://www.google.com)

[I'm an inline-style link with title](https://www.google.com "Google's Homepage")

[I'm a reference-style link][Arbitrary case-insensitive reference text]

[I'm a relative reference to a repository file](../blob/master/LICENSE)

[You can use numbers for reference-style link definitions][1]

Or leave it empty and use the [link text itself].

URLs and URLs in angle brackets will automatically get turned into links.
http://www.example.com or <http://www.example.com> and sometimes
example.com (but not on Github, for example).

Some text to show that the reference links can follow later.

[arbitrary case-insensitive reference text]: https://www.mozilla.org
[1]: http://slashdot.org
[link text itself]: http://www.reddit.com

    Images

Here's our logo (hover to see the title text):

Inline-style:
![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

Reference-style:
![alt text][logo]

[logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"

    Code and Syntax Highlighting

Inline `code` has `back-ticks around` it.

```javascript
var s = "JavaScript syntax highlighting";
alert(s);
```

```python
s = "Python syntax highlighting"
print s
```

```
No language indicated, so no syntax highlighting.
But let's throw in a <b>tag</b>.
```

    Tables

Colons can be used to align columns.

| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |

There must be at least 3 dashes separating each header cell.
The outer pipes (|) are optional, and you don't need to make the
raw Markdown line up prettily. You can also use inline Markdown.

Markdown | Less | Pretty
--- | --- | ---
*Still* | `renders` | **nicely**
1 | 2 | 3

    Blockquotes

> This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can *put* **Markdown** into a blockquote.

    Inline HTML

<dl>
  <dt>Definition list</dt>
  <dd>Is something people use sometimes.</dd>

  <dt>Markdown in HTML</dt>
  <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
</dl>

    Horizontal Rule

Three or more...

---

Hyphens

***

Asterisks

___

Underscores

    Line Breaks

Here's a line for us to start with.

This line is separated from the one above by two newlines, so it will be a *separate paragraph*.

This line is also a separate paragraph, but...
This line is only separated by a single newline, so it's a separate line in the *same paragraph*.

    YouTube Videos

<a href="http://www.youtube.com/watch?feature=player_embedded&v=YOUTUBE_VIDEO_ID_HERE
" target="_blank"><img src="http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg"
alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10" /></a>

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg)](http://www.youtube.com/watch?v=YOUTUBE_VIDEO_ID_HERE)
"""

    def test_escape_including_html(self):
        """Test that all markdown syntax is escaped including html chars."""
        escaped_content = escape_markdown(self.CONTENT)
        expected_content = (
            r"""\# noqa: E501 """
            r"""from https://github.com/adam\-p/markdown\-here/wiki/Markdown\-Cheatsheet """
            r"""Headers \# H1 \#\# H2 \#\#\# H3 \#\#\#\# H4 \#\#\#\#\# H5 \#\#\#\#\#\# H6 """
            r"""Alternatively, for H1 and H2, an underline\-ish style: Alt\-H1 """
            r"""====== Alt\-H2 \-\-\-\-\-\- Emphasis Emphasis, aka italics, """
            r"""with \*asterisks\* or \_underscores\_. Strong emphasis, aka bold, """
            r"""with \*\*asterisks\*\* or \_\_underscores\_\_. Combined emphasis with """
            r"""\*\*asterisks and \_underscores\_\*\*. Strikethrough uses two tildes. """
            r"""\~\~Scratch this.\~\~ Lists 1. First ordered list item 2. Another item """
            r"""⋅⋅\* Unordered sub\-list. 1. Actual numbers don&#x27;t matter, """
            r"""just that it&#x27;s a number ⋅⋅1. Ordered sub\-list 4. And another item. """
            r"""⋅⋅⋅You can have properly indented paragraphs within list items. """
            r"""Notice the blank line above, and the leading spaces """
            r"""\(at least one, but we&#x27;ll use three here to also align the raw Markdown\). """
            r"""⋅⋅⋅To have a line break without a paragraph, you will need to use """
            r"""two trailing spaces.⋅⋅ ⋅⋅⋅\(This is contrary to the typical """
            r"""GFM line break behaviour, where trailing spaces are not required.\) """
            r"""\* Unordered list can use asterisks \- Or minuses \+ Or pluses Links """
            r"""\[I&#x27;m an inline\-style link\]\(https://www.google.com\) """
            r"""\[I&#x27;m an inline\-style link with title\]"""
            r"""\(https://www.google.com &quot;Google&#x27;s Homepage&quot;\) """
            r"""\[I&#x27;m a reference\-style link\]\[Arbitrary case\-insensitive """
            r"""reference text\] \[I&#x27;m a relative reference to a repository """
            r"""file\]\(../blob/master/LICENSE\) \[You can use numbers for reference\-style """
            r"""link definitions\]\[1\] Or leave it empty and use the \[link text itself\]. """
            r"""URLs and URLs in angle brackets will automatically get turned into links. """
            r"""http://www.example.com or &lt;http://www.example.com&gt; and sometimes """
            r"""example.com \(but not on Github, for example\). Some text to show that """
            r"""the reference links can follow later. \[arbitrary case\-insensitive """
            r"""reference text\]: https://www.mozilla.org \[1\]: http://slashdot.org """
            r"""\[link text itself\]: http://www.reddit.com Images Here&#x27;s our """
            r"""logo \(hover to see the title text\): Inline\-style: !\[alt text\]"""
            r"""\(https://github.com/adam\-p/markdown\-here/raw/master/"""
            r"""src/common/images/icon48.png &quot;Logo Title Text 1&quot;\) """
            r"""Reference\-style: !\[alt text\]\[logo\] \[logo\]: """
            r"""https://github.com/adam\-p/markdown\-here/raw/master/"""
            r"""src/common/images/icon48.png &quot;Logo Title Text 2&quot; """
            r"""Code and Syntax Highlighting Inline \`code\` has \`back\-ticks around\` """
            r"""it. \`\`\`javascript var s = &quot;JavaScript syntax highlighting&quot;; """
            r"""alert\(s\); \`\`\` \`\`\`python s = &quot;Python syntax highlighting&quot; """
            r"""print s \`\`\` \`\`\` No language indicated, so no syntax highlighting. """
            r"""But let&#x27;s throw in a &lt;b&gt;tag&lt;/b&gt;. \`\`\` Tables Colons """
            r"""can be used to align columns. | Tables | Are | Cool | """
            r"""| \-\-\-\-\-\-\-\-\-\-\-\-\- |:\-\-\-\-\-\-\-\-\-\-\-\-\-:| \-\-\-\-\-:| | """
            r"""col 3 is | right\-aligned | $1600 | | col 2 is | centered | $12 | | """
            r"""zebra stripes | are neat | $1 | There must be at least 3 """
            r"""dashes separating each header cell. The outer pipes \(|\) are optional, """
            r"""and you don&#x27;t need to make the raw Markdown line up prettily. """
            r"""You can also use inline Markdown. Markdown | Less | Pretty \-\-\- """
            r"""| \-\-\- | \-\-\- \*Still\* | \`renders\` | \*\*nicely\*\* 1 | 2 | 3 """
            r"""Blockquotes &gt; This is a very long line that will still be quoted """
            r"""properly when it wraps. Oh boy let&#x27;s keep writing to make sure """
            r"""this is long enough to actually wrap for everyone. Oh, you """
            r"""can \*put\* \*\*Markdown\*\* into a blockquote. Inline HTML &lt;dl&gt; """
            r"""&lt;dt&gt;Definition list&lt;/dt&gt; &lt;dd&gt;Is something people """
            r"""use sometimes.&lt;/dd&gt; &lt;dt&gt;Markdown in HTML&lt;/dt&gt; """
            r"""&lt;dd&gt;Does \*not\* work \*\*very\*\* well. Use HTML """
            r"""&lt;em&gt;tags&lt;/em&gt;.&lt;/dd&gt; &lt;/dl&gt; Horizontal """
            r"""Rule Three or more... \-\-\- Hyphens \*\*\* Asterisks \_\_\_ """
            r"""Underscores Line Breaks Here&#x27;s a line for us to start with. """
            r"""This line is separated from the one above by two newlines, so it will be """
            r"""a \*separate paragraph\*. This line is also a separate paragraph, but... """
            r"""This line is only separated by a single newline, so it&#x27;s a separate """
            r"""line in the \*same paragraph\*. YouTube Videos &lt;a """
            r"""href=&quot;http://www.youtube.com/watch?feature=player\_embedded&amp;"""
            r"""v=YOUTUBE\_VIDEO\_ID\_HERE &quot; target=&quot;\_blank&quot;&gt;&lt;img """
            r"""src=&quot;http://img.youtube.com/vi/YOUTUBE\_VIDEO\_ID\_HERE/0.jpg&quot; """
            r"""alt=&quot;IMAGE ALT TEXT HERE&quot; width=&quot;240&quot; height=&quot;"""
            r"""180&quot; border=&quot;10&quot; /&gt;&lt;/a&gt; \[!\[IMAGE ALT TEXT HERE\]"""
            r"""\(http://img.youtube.com/vi/YOUTUBE\_VIDEO\_ID\_HERE/0.jpg\)\]"""
            r"""\(http://www.youtube.com/watch?v=YOUTUBE\_VIDEO\_ID\_HERE\) """
        )
        assert escaped_content == expected_content

    def test_escape_excluding_html(self):
        """
        Test that all markdown syntax is escaped excluding html characters.
        This is useful when using templates as Django already escapes html
        when rendering variables so it would result in escaping them twice.
        """
        escaped_content = escape_markdown(self.CONTENT, escape_html=False)
        expected_content = (
            r"""\# noqa: E501 """
            r"""from https://github.com/adam\-p/markdown\-here/wiki/Markdown\-Cheatsheet """
            r"""Headers \# H1 \#\# H2 \#\#\# H3 \#\#\#\# H4 \#\#\#\#\# H5 \#\#\#\#\#\# H6 """
            r"""Alternatively, for H1 and H2, an underline\-ish style: Alt\-H1 """
            r"""====== Alt\-H2 \-\-\-\-\-\- Emphasis Emphasis, aka italics, """
            r"""with \*asterisks\* or \_underscores\_. Strong emphasis, aka bold, """
            r"""with \*\*asterisks\*\* or \_\_underscores\_\_. Combined emphasis with """
            r"""\*\*asterisks and \_underscores\_\*\*. Strikethrough uses two tildes. """
            r"""\~\~Scratch this.\~\~ Lists 1. First ordered list item 2. Another item """
            r"""⋅⋅\* Unordered sub\-list. 1. Actual numbers don't matter, """
            r"""just that it's a number ⋅⋅1. Ordered sub\-list 4. And another item. """
            r"""⋅⋅⋅You can have properly indented paragraphs within list items. """
            r"""Notice the blank line above, and the leading spaces """
            r"""\(at least one, but we'll use three here to also align the raw Markdown\). """
            r"""⋅⋅⋅To have a line break without a paragraph, you will need to use """
            r"""two trailing spaces.⋅⋅ ⋅⋅⋅\(This is contrary to the typical """
            r"""GFM line break behaviour, where trailing spaces are not required.\) """
            r"""\* Unordered list can use asterisks \- Or minuses \+ Or pluses Links """
            r"""\[I'm an inline\-style link\]\(https://www.google.com\) """
            r"""\[I'm an inline\-style link with title\]"""
            r"""\(https://www.google.com "Google's Homepage"\) """
            r"""\[I'm a reference\-style link\]\[Arbitrary case\-insensitive """
            r"""reference text\] \[I'm a relative reference to a repository """
            r"""file\]\(../blob/master/LICENSE\) \[You can use numbers for reference\-style """
            r"""link definitions\]\[1\] Or leave it empty and use the \[link text itself\]. """
            r"""URLs and URLs in angle brackets will automatically get turned into links. """
            r"""http://www.example.com or <http://www.example.com> and sometimes """
            r"""example.com \(but not on Github, for example\). Some text to show that """
            r"""the reference links can follow later. \[arbitrary case\-insensitive """
            r"""reference text\]: https://www.mozilla.org \[1\]: http://slashdot.org """
            r"""\[link text itself\]: http://www.reddit.com Images Here's our """
            r"""logo \(hover to see the title text\): Inline\-style: !\[alt text\]"""
            r"""\(https://github.com/adam\-p/markdown\-here/raw/master/"""
            r"""src/common/images/icon48.png "Logo Title Text 1"\) """
            r"""Reference\-style: !\[alt text\]\[logo\] \[logo\]: """
            r"""https://github.com/adam\-p/markdown\-here/raw/master/"""
            r"""src/common/images/icon48.png "Logo Title Text 2" """
            r"""Code and Syntax Highlighting Inline \`code\` has \`back\-ticks around\` """
            r"""it. \`\`\`javascript var s = "JavaScript syntax highlighting"; """
            r"""alert\(s\); \`\`\` \`\`\`python s = "Python syntax highlighting" """
            r"""print s \`\`\` \`\`\` No language indicated, so no syntax highlighting. """
            r"""But let's throw in a <b>tag</b>. \`\`\` Tables Colons """
            r"""can be used to align columns. | Tables | Are | Cool | """
            r"""| \-\-\-\-\-\-\-\-\-\-\-\-\- |:\-\-\-\-\-\-\-\-\-\-\-\-\-:| \-\-\-\-\-:| | """
            r"""col 3 is | right\-aligned | $1600 | | col 2 is | centered | $12 | | """
            r"""zebra stripes | are neat | $1 | There must be at least 3 """
            r"""dashes separating each header cell. The outer pipes \(|\) are optional, """
            r"""and you don't need to make the raw Markdown line up prettily. """
            r"""You can also use inline Markdown. Markdown | Less | Pretty \-\-\- """
            r"""| \-\-\- | \-\-\- \*Still\* | \`renders\` | \*\*nicely\*\* 1 | 2 | 3 """
            r"""Blockquotes > This is a very long line that will still be quoted """
            r"""properly when it wraps. Oh boy let's keep writing to make sure """
            r"""this is long enough to actually wrap for everyone. Oh, you """
            r"""can \*put\* \*\*Markdown\*\* into a blockquote. Inline HTML <dl> """
            r"""<dt>Definition list</dt> <dd>Is something people """
            r"""use sometimes.</dd> <dt>Markdown in HTML</dt> """
            r"""<dd>Does \*not\* work \*\*very\*\* well. Use HTML """
            r"""<em>tags</em>.</dd> </dl> Horizontal """
            r"""Rule Three or more... \-\-\- Hyphens \*\*\* Asterisks \_\_\_ """
            r"""Underscores Line Breaks Here's a line for us to start with. """
            r"""This line is separated from the one above by two newlines, so it will be """
            r"""a \*separate paragraph\*. This line is also a separate paragraph, but... """
            r"""This line is only separated by a single newline, so it's a separate """
            r"""line in the \*same paragraph\*. YouTube Videos <a """
            r"""href="http://www.youtube.com/watch?feature=player\_embedded&"""
            r"""v=YOUTUBE\_VIDEO\_ID\_HERE " target="\_blank"><img """
            r"""src="http://img.youtube.com/vi/YOUTUBE\_VIDEO\_ID\_HERE/0.jpg" """
            r"""alt="IMAGE ALT TEXT HERE" width="240" height="""
            r""""180" border="10" /></a> \[!\[IMAGE ALT TEXT HERE\]"""
            r"""\(http://img.youtube.com/vi/YOUTUBE\_VIDEO\_ID\_HERE/0.jpg\)\]"""
            r"""\(http://www.youtube.com/watch?v=YOUTUBE\_VIDEO\_ID\_HERE\) """
        )
        assert escaped_content == expected_content
