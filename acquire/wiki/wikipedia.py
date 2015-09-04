
from acquire.pagereader import PageReader

class Wikipedia(PageReader):

    def _get_tags(self, tag, attrs):
        return self.soup.find_all(tag, attrs)

    @property
    def nickname(self):
        nickname = None
        attrs = { 'title' : 'Athletic nickname' }
        try:
            tag = self._get_tags('a', attrs)[0]
            if tag.text != 'nickname':
                nickname = tag.next.next.next.text
        except IndexError:
            try:
                tag = self.soup.find_all(text='Nickname')[0]
                nickname = tag.next.next.text
            except IndexError:
                pass
        return nickname

    @property
    def arena(self):
        try:
            tag = self.soup.find_all('b', text='Arena')[0].parent
            sib = tag.find_next_sibling('td')
            return sib.text
        except:
            return None

    @property
    def colors(self):
        attrs = { 'title' : 'School colors' }
        primary = None
        alt = None
        try:
            tag = self._get_tags('a', attrs)[0]
            colors = tag.parent.parent.find_all('span')
            primary = colors[0].get('style').split(';')[0].split(':')[1].replace('#', '')
            alt = colors[1].get('style').split(';')[0].split(':')[1].replace('#', '')
        except:
            try:
                tag = self.soup.find_all(text='Colors')[0]
            except IndexError, ex:
                try:
                    tag = self.soup.find_all(text='Team colors')[0]
                except IndexError, ex1:
                    try:
                        tag = self.soup.find_all(text='Team colours')[0]
                    except IndexError:
                        return dict(primary=primary, alt=alt)
            colors = tag.next.next.find_all('span')
            try:
                primary = colors[0].get('style').split(';')[0].split(':')[1].replace('#', '')
                try:
                    alt = colors[1].get('style').split(';')[0].split(':')[1].replace('#', '')
                except:
                    alt = 'ffffff'
            except:
                try:
                    primary = colors[2].get('style').split(';')[0].split(':')[1].replace('#', '')
                    try:
                        alt = colors[3].get('style').split(';')[0].split(':')[1].replace('#', '')
                    except:
                        alt = 'ffffff'
                except:
                    pass
        return dict(primary=primary, alt=alt)
