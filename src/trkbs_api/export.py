from bs4 import BeautifulSoup as bsp

# basic text export with 'regesta' flag (dependant on TRKBS structural tagging)
def get_text(xml, regesta=False):
    soup = bsp(xml, 'xml')
    line_list = []
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        string = unicode.string
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if regesta == False:
            if 'type:regesta' not in custom_attr:
                line_list.append(string)
        else:
            line_list.append(string)

    line_list = [x for x in line_list if x is not None]        

    return '\n'.join(line_list)