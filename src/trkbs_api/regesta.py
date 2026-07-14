import re

from bs4 import BeautifulSoup as bsp
from tqdm import tqdm

def tag_empty_lines(xml):
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        if not unicode.contents:
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if 'type:regesta' not in text_line['custom']:
                text_line['custom'] =  custom_attr + ' structure {type:regesta;}'
            else:
                reg_pat = re.compile(r'(\sstructure {type:regesta;}){2,}')
                string = text_line['custom']
                matches = re.findall(reg_pat, string)
                nr_matches = len(matches)
                if nr_matches > 1:
                    text_line['custom'] = re.sub(reg_pat, ' structure {type:regesta;}', string)
    # output_xml = soup.encode('utf-8')
    output_xml = str(soup)
            
    return output_xml

def remove_regesta(xml):
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if 'regesta' in custom_attr:
            text_line.decompose()
    output_xml = str(soup)
        
    return output_xml

def add_regesta(xml, regesta_text):
    soup = bsp(xml, 'xml')
    for unicode in soup.select('TextLine > TextEquiv > Unicode'):
        text_line = unicode.find_parent('TextLine')
        custom_attr = text_line.get('custom')
        if 'regesta' in custom_attr and not unicode.contents:
            unicode.string = regesta_text
    output_xml = str(soup)
            
    return output_xml

def validate_regesta(client, coll, doc, page_start, page_end):
    reg_dict = {}
    for i in tqdm(range(page_start, page_end + 1)):
        xml = client.get_page(coll, doc, i)
        soup = bsp(xml, 'xml')
        reg_counter = 0
        for unicode in soup.select('TextLine > TextEquiv > Unicode'):
            text_line = unicode.find_parent('TextLine')
            custom_attr = text_line.get('custom')
            if 'regesta' in custom_attr:
                reg_counter += 1
                reg_dict.update({f'Page_{i}': f'{reg_counter}'})
    
    return reg_dict