from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["tenders"]
zg = db.zg

# new_tender = {
#     "_id": '02564984844',
#     "name": 'tender_name',
#     "url": 'http://hard-porno.hd',
#     "customer": 'Main producer',
#     "customer_url": 'http://go-to-customer.ru',
#     "price": 1599,
#     "release_date": 'new era',
#     "refreshing_date": 'refreshing data',
#     "ending_date": 'whole end'
# }
# res = zg.insert_one(new_tender)
# if res.acknowledged:
#     print('ok')
# else:
#     print('error happens')

check_tender = zg.find_one({
    "_id": '02564984844'
})
print(check_tender['customer'])