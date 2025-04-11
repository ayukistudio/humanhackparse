import requests
import json
import os
import csv
import time


def main():
    path = './all.json'

    if os.path.isfile(path):
        os.remove(path)

    for page in range(1, MAX_PAGE + 1):
        while True:
            url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?dest=-1257786&page={page}&query=плакаты&resultset=catalog&spp=27"
            r = requests.get(url)

            print(f'Url  \t\t>>> "{url}"')
            print(f'Status \t\t>>> {r.status_code}')
            print(f'Content \t>>> {r.content.decode("utf-8")}')
            print()

            if r.status_code == 200:
                raw_data: dict = json.loads(r.content.decode('utf-8'))
                if type(raw_data) is not dict: break

                data: dict = raw_data.get('data')
                if type(data) is not dict: break

                products: list = data.get('products')
                if type(products) is not list: products = []

                all_data = {}
                if os.path.isfile(path):
                    with open(path, 'rt') as r_file:
                        try: all_data = json.loads(r_file.read())
                        except: all_data = {}

                with open(path, 'wt') as w_file:
                    pr: list = all_data.get('products')
                    if type(pr) is not list: pr = []

                    pr.extend(products)
                    w_file.write(json.dumps({'products': pr}))

                break

            else:
                time.sleep(0.05)

    with open(path, 'rt') as r:
        try:
            rr: dict = json.loads(r.read())
            if type(rr) is not dict:
                print('File empty!')
                return

            items: list = rr.get("products")

            print('==========================================================================================================')
            print('==========================================================================================================')
            print('==========================================================================================================')

            l = []
            table = [['index',  'id',  'name',  'feedbacks']]
            for index, item in enumerate(items):
                s = f'Products(index={index}, id={item.get("id")}, name="{item.get("name")}", feedbacks={item.get("feedbacks")})'
                l.append(s)
                table.append([index, item.get('id'), item.get('name'), item.get('feedbacks')])
                print(s)

            with open('./all.txt', 'wt', encoding="utf-8") as w:
                text = str.join('\n', l)
                w.write(text)

            with open('./all.csv', 'w', newline='', encoding="utf-8") as csv_file:
                s = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                s.writerows(table)

        except:
            print('Broken!')
            raise


MAX_PAGE = 62

if __name__ == '__main__':
    main()
