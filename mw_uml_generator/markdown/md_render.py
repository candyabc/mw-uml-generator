from mistune import Markdown,preprocessing,Renderer,escape,escape_link
class InlineRenderer(Renderer):
    def __init__(self, **kwargs):
        self.options = kwargs

    def placeholder(self):
        return []

    def compose_it(self,blocktype,text,**args):
        re = {'type':blocktype,'text':text}
        re.update(args)
        return [re]

    def block_code(self, code, lang=None):
        """Rendering block level code. ``pre > code``.

        :param code: text content of the code block.
        :param lang: language of the given code.
        """
        code = code.rstrip('\n')
        code = escape(code, smart_amp=False)
        return self.compose_it('code',code)


    def block_quote(self, text):
        """Rendering <blockquote> with the given text.

        :param text: text content of the blockquote.
        """
        return self.compose_it('blockuote',  text.rstrip('\n'))

    def block_html(self, html):
        """Rendering block level pure html content.

        :param html: text content of the html snippet.
        """
        if self.options.get('skip_style') and \
           html.lower().startswith('<style'):
            return self.compose_it('html','')
        if self.options.get('escape'):
            return self.compose_it('html',escape(html))
        return self.compose_it('html', html.rstrip('\n'))

    def header(self, text, level, raw=None):
        """Rendering header/heading tags like ``<h1>`` ``<h2>``.

        :param text: rendered text content for the header.
        :param level: a number for the header level, for example: 1.
        :param raw: raw text content of the header.
        """
        return self.compose_it('header', text,level=level)


    def hrule(self):
        return self.compose_it('hr','')
    def list(self, body, ordered=True):
        """Rendering list tags like ``<ul>`` and ``<ol>``.

        :param body: body contents of the list.
        :param ordered: whether this list is ordered or not.
        """

        return self.compose_it('list','',items =body)

    def list_item(self, text):
        """Rendering list item snippet. Like ``<li>``."""
        return self.compose_it('li',text)


    def paragraph(self, text):
        """Rendering paragraph tags. Like ``<p>``."""
        return self.compose_it('p',text)

    def table(self, header, body):
        """Rendering table element. Wrap header and body in it.

        :param header: header part of the table.
        :param body: body part of the table.
        """

        return self.compose_it('table','',header =header,rows=body)

    def table_row(self, content):
        """Rendering a table row. Like ``<tr>``.

        :param content: content of current table row.
        """
        # return self.compose_it('row',content)
        return [content]


    def table_cell(self, content, **flags):
        """Rendering a table cell. Like ``<th>`` ``<td>``.

        :param content: content of current table cell.
        :param header: whether this is header or not.
        :param align: align of current table cell.
        """
        # if flags['header']:
        #     tag = 'th'
        # else:
        #     tag = 'td'
        # align = flags['align']
        # if not align:
        #     return '<%s>%s</%s>\n' % (tag, content, tag)
        # return '<%s style="text-align:%s">%s</%s>\n' % (
        #     tag, align, content, tag
        # )
        return self.compose_it('cell',content)
        # return content

    def double_emphasis(self, text):
        """Rendering **strong** text.

        :param text: text content for emphasis.
        """
        return self.compose_it('strong',text)

    def emphasis(self, text):
        """Rendering *emphasis* text.

        :param text: text content for emphasis.
        """
        return self.compose_it('em',text)

    def codespan(self, text):
        """Rendering inline `code` text.

        :param text: text content for inline code.
        """
        text = escape(text.rstrip(), smart_amp=False)

        return self.compose_it('codespan',text)

    def linebreak(self):

        return self.compose_it('br','')

    def strikethrough(self, text):
        """Rendering ~~strikethrough~~ text.

        :param text: text content for strikethrough.
        """
        return self.compose_it('del',text)

    def text(self, text):
        """Rendering unformatted text.

        :param text: text content.
        """
        if not self.options.get('parse_block_html'):
            text = escape(text)
        return [text]

    def escape(self, text):
        """Rendering escape sequence.

        :param text: text content.
        """
        return self.compose_it('escape', escape(text))

    def autolink(self, link, is_email=False):
        """Rendering a given link or email address.

        :param link: link content or email address.
        :param is_email: whether this is an email or not.
        """
        text = link = escape_link(link)
        if is_email:
            link = 'mailto:%s' % link
        # return '<a href="%s">%s</a>' % (link, text)
        return self.compose_it('autolink',text,link=link)

    def link(self, link, title, text):
        """Rendering a given link with content and title.

        :param link: href link for ``<a>`` tag.
        :param title: title content for `title` attribute.
        :param text: text content for description.
        """
        link = escape_link(link)
        if not title:
            return self.compose_it('link',text,title='')

        title = escape(title, quote=True)
        return  self.compose_it('link',text,title=title)


    def image(self, src, title, text):
        """Rendering a image with title and text.

        :param src: source link of the image.
        :param title: title text of the image.
        :param text: alt text of the image.
        """
        src = escape_link(src)
        text = escape(text, quote=True)
        if title:
            title = escape(title, quote=True)
        else:
            title =''

        return self.compose_it('img',text,src=src,title=title)

    def inline_html(self, html):
        """Rendering span level pure html content.

        :param html: text content of the html snippet.
        """
        if self.options.get('escape'):
            return escape(html)
        else:
            return self.compose_it('inlinehtml',html)

    def newline(self):
        """Rendering newline element."""
        return self.compose_it('newline','')

    def footnote_ref(self, key, index):
        """Rendering the ref anchor of a footnote.

        :param key: identity key for the footnote.
        :param index: the index count of current footnote.
        """

        self.compose_it('ftref','',key=escape(key),index=index)

    def footnote_item(self, key, text):

        return self.compose_it('rtitem',text,key = escape(key))

    def footnotes(self, text):

        return self.compose_it('ft',text)